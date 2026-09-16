"""Build and verify a deterministic final bundle from authenticated CI evidence.

The public entry points deliberately require a fresh GitHub readback snapshot.
Local files can be checked for integrity, but cannot create trusted provenance.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
from pathlib import PurePosixPath
import re
import zipfile

from tools.ci import candidate_evidence
from tools.ci.qualification_report import SPEC_FILES as QUALIFICATION_SPEC_FILES


SCHEMA_VERSION = 3
KINDS = ("automated", "client", "server", "multiplayer", "gameplay", "save_reload")
SPEC_FILES = (*QUALIFICATION_SPEC_FILES, "forbidden_outputs")
SOURCE_PATHS = (
    "PROJECT_MANIFEST.json",
    "README.md",
    "CHANGELOG.md",
    "gradle.properties",
    "build.gradle",
    "LICENSE",
    "tools/ci/runtime-dependencies.lock.json",
    "docs/QA_ACCEPTANCE.md",
    "docs/COMPATIBILITY_MATRIX.md",
    "src/main/templates/META-INF/neoforge.mods.toml",
    ".github/workflows/publish-curseforge.yml",
    "tools/ci/final_release_bundle.py",
    "tools/release/stable_autopublish.py",
    "tools/release/stable_publish.py",
    "tools/release/curseforge_release_0.1.1.json",
    "docs/release/0.1.1.md",
    *(f"spec/{name}.json" for name in SPEC_FILES),
)
STABLE_AUTOPUBLISH_POLICY = "AUTHORIZED_WHEN_ELIGIBLE"
AUTO_PUBLISH_BLOCKERS = ("RUNTIME_PUBLICATION_PREFLIGHT_REQUIRED",)
PUBLICATION_PENDING = ("GITHUB_TAG", "GITHUB_RELEASE", "CURSEFORGE")
RELEASE_POLICY = {
    "targets": ["github", "curseforge"],
    "modrinth": "FORBIDDEN_BY_PROJECT_POLICY",
}
EVIDENCE_BY_KIND = {
    "automated": (
        "receipt.json", "runtime.log", "gradle-build.log", "datagen-repeat.log",
        "runtime-dependencies.json", "qualification-gametests.json",
    ),
    "client": (
        "production-client-one.json", "production-client-one.log",
        "production-client-two.json", "production-client-two.log",
        "production-client-one-title.png", "production-client-two-title.png",
    ),
    "server": (
        "production-baseline-create.json", "production-baseline-create.log",
        "production-baseline-restart.json", "production-baseline-restart.log",
        "production-candidate-upgrade.json", "production-candidate-upgrade.log",
        "production-candidate-restart.json", "production-candidate-restart.log",
    ),
    "multiplayer": (
        "production-multiplayer.json", "production-multiplayer.log",
        "production-client-one-multiplayer-board-result.png",
        "production-client-two-multiplayer-board-result.png",
    ),
    "gameplay": (
        "qualification-gametests.json",
        "production-client-one.json", "production-client-one.log",
        "production-multiplayer.json", "production-multiplayer.log",
        "production-client-one-harvest-client-result-singleplayer.png",
        "production-client-one-harvest-client-result-multiplayer.png",
        "production-client-one-sawmill-client-result-singleplayer.png",
        "production-client-one-sawmill-client-result-multiplayer.png",
    ),
    "save_reload": (
        "production-alpha9-world-backup.json",
        "production-candidate-upgrade.json", "production-candidate-upgrade.log",
        "production-candidate-restart.json", "production-candidate-restart.log",
        "production-client-one-reconnect-complete.png",
        "production-client-two-reconnect-complete.png",
    ),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def exact(value: object, fields: set[str], message: str = "Missing or unknown fields") -> dict:
    require(isinstance(value, dict) and set(value) == fields, message)
    return value


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def parse_json(raw: bytes) -> object:
    return json.loads(raw, object_pairs_hook=candidate_evidence.unique)


def properties(raw: bytes) -> dict[str, str]:
    rows = {}
    for line in raw.decode("utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            key = key.strip()
            require(bool(key), "Empty Gradle property key")
            require(key not in rows, "Duplicate Gradle property")
            rows[key] = value.strip()
    return rows


def acceptance_catalog(sources: dict[str, bytes]) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    section = ""
    for number, line in enumerate(sources["docs/QA_ACCEPTANCE.md"].decode("utf-8").splitlines(), 1):
        if line.startswith("## "):
            section = line[3:]
        if line.startswith("- ["):
            kind = "gameplay" if section in {
                "Farmer's Delight", "Immersive Engineering", "Harvest behavior", "Potted and special blocks"
            } else "automated"
            if "server" in line.lower():
                kind = "server"
            if "clean instance" in line:
                kind = "client"
            rows[f"qa:{number}"] = {
                "source": f"docs/QA_ACCEPTANCE.md:{number}", "criterion": line[6:], "kind": kind,
            }
    for name in sorted(SPEC_FILES):
        value = parse_json(sources[f"spec/{name}.json"])
        require(isinstance(value, dict), "Specification root must be an object")
        for key, entry in value.items():
            values = enumerate(entry) if isinstance(entry, list) else [(None, entry)]
            for index, item in values:
                pointer = key + (f"/{index}" if index is not None else "")
                rows[f"spec:{name}/{pointer}"] = {
                    "source": f"spec/{name}.json#/{pointer}",
                    "criterion": json.dumps(item, ensure_ascii=False, sort_keys=True),
                    "kind": "gameplay",
                }
    require(bool(rows), "Acceptance catalog is empty")
    return rows


def _strings(value: object):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)


def validate_source_claims(snapshot: dict) -> tuple[dict[str, str], dict[str, dict]]:
    """Recompute every source/release invariant used by coverage promotion."""
    report, evidence, sources = snapshot["report"], snapshot["evidence"], snapshot["sources"]
    require(set(sources) == set(SOURCE_PATHS), "Incomplete source snapshot")
    _validate_capabilities(report)
    candidate = report["candidate"]
    props = properties(sources["gradle.properties"])
    identity = candidate_evidence.jar_identity(evidence["candidate.jar"])
    require(candidate == {**identity, "name": f"immersive_bop_harvest-{props['mod_version']}.jar",
                          "size": len(evidence["candidate.jar"]), "sha256": sha(evidence["candidate.jar"])},
            "Candidate/source/JAR identity mismatch")
    require(re.fullmatch(r"\d+\.\d+\.\d+(?:\.\d+)?", candidate["version"]) is not None,
            "Final stable version must not be a prerelease")
    require(candidate["version"] == props.get("mod_version") == "0.1.1"
            and candidate["modId"] == props.get("mod_id")
            and candidate["license"] == props.get("mod_license"), "Wrong final stable source identity")
    from tools.release.publish_curseforge import validate_manifest
    release_manifest = parse_json(sources["tools/release/curseforge_release_0.1.1.json"])
    require(isinstance(release_manifest, dict), "Stable release manifest must be an object")
    validate_manifest(release_manifest)
    release = release_manifest["release"]
    notes = sources["docs/release/0.1.1.md"]
    require(release_manifest["schemaVersion"] == 3
            and release["tag"] == "v0.1.1"
            and release["version"] == candidate["version"]
            and release["modId"] == candidate["modId"]
            and release["assetName"] == candidate["name"]
            and release["assetSize"] == candidate["size"]
            and release["assetSha256"] == candidate["sha256"],
            "Stable release manifest differs from authenticated candidate")
    require(release["changelogPath"] == "docs/release/0.1.1.md"
            and release["changelogSha256"] == sha(notes)
            and b"NOT_PERFORMED / OWNER_WAIVED" in notes
            and b"Modrinth" in notes,
            "Stable release notes are stale or omit required boundaries")
    manifest = parse_json(sources["PROJECT_MANIFEST.json"])
    require(isinstance(manifest, dict) and manifest.get("version") == candidate["version"]
            and manifest.get("mod_id") == candidate["modId"], "Source manifest identity mismatch")
    require(candidate["version"] in sources["CHANGELOG.md"].decode("utf-8"), "Stable changelog entry is missing")
    require(sources["LICENSE"].decode("utf-8").strip() and "All Rights Reserved" in sources["LICENSE"].decode("utf-8"),
            "Stable license source is missing")
    readme = sources["README.md"].decode("utf-8")
    for marker in ("Minecraft 1.21.1", "NeoForge", "immersive_bop_harvest", "0.1.1", "unpublished"):
        require(marker in readme, f"README stable metadata is not current: {marker}")
    matrix = sources["docs/COMPATIBILITY_MATRIX.md"].decode("utf-8")
    inventory = parse_json(sources["spec/coverage_inventory.json"])
    scoped_ids = {value for value in _strings(inventory)
                  if re.fullmatch(r"[a-z0-9_.-]+:[a-z0-9_./-]+", value)}
    require(bool(scoped_ids) and all(value in matrix for value in scoped_ids),
            "Compatibility matrix omits scoped identifiers")
    template = sources["src/main/templates/META-INF/neoforge.mods.toml"].decode("utf-8")
    build = sources["build.gradle"].decode("utf-8")
    require("${mod_version}" in template and "${mod_id}" in template and "${mod_license}" in template,
            "NeoForge metadata is not bound to source properties")
    require("validateSpecs" in build and "qaAlphaResources" in build,
            "Build does not enforce stable source validation")
    gradle_log = evidence["gradle-build.log"].decode("utf-8")
    require("SPEC VALIDATION: PASSED" in gradle_log and "ALPHA RESOURCE QA: PASSED" in gradle_log
            and "BUILD SUCCESSFUL" in gradle_log, "Authenticated build lacks source/resource validator proof")
    require("BUILD SUCCESSFUL" in evidence["datagen-repeat.log"].decode("utf-8"),
            "Authenticated repeated datagen proof is missing")
    require("BUILD SUCCESSFUL" in evidence["runtime.log"].decode("utf-8"),
            "Authenticated runData/GameTest proof is missing")
    candidate_evidence.check_dependency_receipt(evidence["runtime-dependencies.json"],
                                                sources["tools/ci/runtime-dependencies.lock.json"])
    receipt = parse_json(evidence["receipt.json"])
    require(receipt.get("dependencyLockSha256") == sha(sources["tools/ci/runtime-dependencies.lock.json"]),
            "Candidate dependency lock differs")
    return props, acceptance_catalog(sources)


def coverage_proofs(catalog: dict[str, dict]) -> dict[str, list[str]]:
    """Map every criterion to a validator/evidence claim; unknown criteria fail closed."""
    proofs: dict[str, list[str]] = {}
    qa_rules = (
        ("validate_specs.py", ["evidence/gradle-build.log#SPEC_VALIDATION_PASSED"]),
        ("compatibility matrix", ["source/README.md#STABLE_METADATA", "source/docs/COMPATIBILITY_MATRIX.md#SCOPED_IDS"]),
        ("forbidden output", ["evidence/gradle-build.log#ALPHA_RESOURCE_QA_PASSED"]),
        ("potted block is targeted", ["evidence/gradle-build.log#ALPHA_RESOURCE_QA_PASSED"]),
        ("`rundata` completes", ["evidence/runtime.log#BUILD_SUCCESSFUL"]),
        ("second `rundata`", ["evidence/datagen-repeat.log#BUILD_SUCCESSFUL"]),
        ("data/biomesoplenty", ["evidence/gradle-build.log#ALPHA_RESOURCE_QA_PASSED"]),
        ("ids are unique", ["evidence/gradle-build.log#ALPHA_RESOURCE_QA_PASSED"]),
        ("full gradle build", ["evidence/gradle-build.log#BUILD_SUCCESSFUL"]),
        ("dedicated server", ["evidence/production-candidate-restart.json#DEDICATED_SERVER", "evidence/production-candidate-restart.log#DONE"]),
        ("client classes", ["evidence/production-candidate-restart.log#SERVER_LIFECYCLE"]),
        ("changelog is current", ["source/CHANGELOG.md#STABLE_VERSION"]),
        ("license has been selected", ["source/LICENSE#ALL_RIGHTS_RESERVED", "candidate/JAR#LICENSE"]),
        ("version and dependency ranges", ["source/gradle.properties#IDENTITY", "source/src/main/templates/META-INF/neoforge.mods.toml#PROPERTY_BINDING", "evidence/runtime-dependencies.json#LOCK_MATCH"]),
        ("clean instance", ["evidence/production-client-one.json#PACKAGED_CLIENT", "evidence/production-client-one-title.png#TITLE_SCREEN"]),
    )
    for key, row in catalog.items():
        if key.startswith("spec:"):
            spec = key.split("/", 1)[0][5:]
            if spec == "forbidden_outputs":
                proof = ["evidence/gradle-build.log#ALPHA_RESOURCE_QA_PASSED", f"source/spec/{spec}.json"]
            else:
                proof = ["evidence/qualification-gametests.json#SOURCE_DERIVED_CASE_VALIDATION", f"source/spec/{spec}.json"]
        else:
            criterion = row["criterion"].lower()
            proof = next((value for marker, value in qa_rules if marker in criterion), None)
            if proof is None and row["kind"] == "gameplay":
                proof = ["evidence/qualification-gametests.json#SOURCE_DERIVED_CASE_VALIDATION",
                         "evidence/production-client-one.json#PACKAGED_GAMEPLAY"]
            require(proof is not None, f"No explicit authenticated proof mapping for {key}")
        proofs[key] = proof
    require(set(proofs) == set(catalog), "Incomplete explicit acceptance proof mapping")
    return proofs


def reference(raw: bytes) -> dict:
    return {"size": len(raw), "sha256": sha(raw)}


def deterministic_zip(files: dict[str, bytes]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(files):
            require(not PurePosixPath(name).is_absolute() and all(p not in {"", ".", ".."} for p in name.split("/")),
                    "Unsafe final bundle path")
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, files[name])
    return output.getvalue()


def _github_source(api: candidate_evidence.GitHub, path: str, commit: str) -> bytes:
    row = api.get(f"contents/{path}?ref={commit}")
    require(row.get("type") == "file" and row.get("encoding") == "base64", f"Missing GitHub source file: {path}")
    encoded = "".join(row["content"].split())
    raw = base64.b64decode(encoded, validate=True)
    require(row.get("size") == len(raw) and row.get("sha") == git_blob_sha(raw),
            f"GitHub source identity mismatch: {path}")
    return raw


def _pin(report: dict, *, run_id: int, attempt: int, commit: str, tree: str,
         artifact_id: int, archive_sha256: str) -> None:
    expected = {
        "runId": run_id, "runAttempt": attempt, "sourceCommit": commit, "sourceTree": tree,
        "artifactId": artifact_id, "archiveSha256": archive_sha256,
    }
    for key, value in expected.items():
        require(report.get(key) == value, f"Authenticated {key} differs from the independently pinned identity")


def authenticated_snapshot(*, run_id: int, attempt: int, commit: str, tree: str,
                           artifact_id: int, archive_sha256: str,
                           api: candidate_evidence.GitHub | None = None) -> dict:
    """Read and pin service state. This is the only trusted snapshot constructor."""
    require(re.fullmatch(r"[0-9a-f]{40}", tree) is not None, "Expected tree must be supplied independently")
    require(re.fullmatch(r"[0-9a-f]{64}", archive_sha256) is not None, "Expected archive digest must be supplied independently")
    require(type(artifact_id) is int and artifact_id > 0, "Expected artifact ID must be supplied independently")
    api = api or candidate_evidence.GitHub()
    report = candidate_evidence.verify(run_id, attempt, commit, api=api)
    _pin(report, run_id=run_id, attempt=attempt, commit=commit, tree=tree,
         artifact_id=artifact_id, archive_sha256=archive_sha256)
    require(report.get("status") == "AUTHENTICATED_PACKAGED_EXECUTION", "Packaged production execution is required")
    archive = api.get(f"actions/artifacts/{artifact_id}/zip", binary=True)
    require(sha(archive) == archive_sha256, "Fresh artifact bytes differ from the pinned archive digest")
    evidence = candidate_evidence.contents(archive)
    sources = {path: _github_source(api, path, commit) for path in SOURCE_PATHS}
    issues = api.get("issues?state=open&per_page=100")
    require(isinstance(issues, list) and len(issues) < 100, "Incomplete GitHub issue inventory")
    defects = [
        {"number": row["number"], "title": row["title"], "url": row["html_url"]}
        for row in issues if "pull_request" not in row
    ]
    return {"report": report, "evidence": evidence, "sources": sources, "defects": defects}


def _validate_capabilities(report: dict) -> None:
    cap = report.get("capabilities")
    require(isinstance(cap, dict), "Missing authenticated capabilities")
    require(cap.get("sourceBuild") is True and type(cap.get("developmentGameTests")) is int
            and cap["developmentGameTests"] >= 3 and cap.get("repeatedDatagen") is True,
            "Incomplete automated capability")
    for key in ("packagedRuntime", "client", "multiplayer", "saveReload"):
        require(cap.get(key) is True, f"Missing authenticated {key} capability")
    scoped = cap.get("scopedCompatibility")
    require(isinstance(scoped, dict) and type(scoped.get("cases")) is int and scoped["cases"] > 0,
            "Missing scoped gameplay compatibility")


def _compose(snapshot: dict) -> bytes:
    """Pure deterministic composer; callers must authenticate the snapshot."""
    exact(snapshot, {"report", "evidence", "sources", "defects"}, "Invalid authenticated snapshot")
    report = snapshot["report"]
    evidence = snapshot["evidence"]
    sources = snapshot["sources"]
    defects = snapshot["defects"]
    props, catalog = validate_source_claims(snapshot)
    require(isinstance(evidence, dict) and "candidate.jar" in evidence and "receipt.json" in evidence,
            "Incomplete authenticated artifact")
    for names in EVIDENCE_BY_KIND.values():
        require(set(names) <= set(evidence), "Mandatory final receipt evidence is missing")
    candidate = report["candidate"]
    lock = parse_json(sources["tools/ci/runtime-dependencies.lock.json"])
    runtime = parse_json(evidence["runtime-dependencies.json"])
    require(isinstance(lock, dict) and isinstance(runtime, dict), "Invalid dependency evidence")
    proofs = coverage_proofs(catalog)
    receipts = []
    for kind in KINDS:
        receipts.append({
            "kind": kind,
            "tested": True,
            "waived": False,
            "capability": {
                "automated": "sourceBuild", "client": "client", "server": "packagedRuntime",
                "multiplayer": "multiplayer", "gameplay": "scopedCompatibility", "save_reload": "saveReload",
            }[kind],
            "evidence": [f"evidence/{name}" for name in EVIDENCE_BY_KIND[kind]],
            "coverage": sorted(key for key, row in catalog.items() if row["kind"] == kind),
            "proofs": {key: proofs[key] for key in sorted(key for key, row in catalog.items() if row["kind"] == kind)},
        })
    files = {f"source/{name}": raw for name, raw in sources.items()}
    files.update({f"evidence/{name}": raw for name, raw in evidence.items()})
    candidate_path = f"candidate/{candidate['name']}"
    files[candidate_path] = evidence["candidate.jar"]
    identity = {
        "artifactId": report["artifactId"], "version": candidate["version"], "modId": candidate["modId"],
        "license": candidate["license"], "commit": report["sourceCommit"], "tree": report["sourceTree"],
        "jarName": candidate["name"], "jarSize": candidate["size"], "jarSha256": candidate["sha256"],
        "lockSha256": sha(sources["tools/ci/runtime-dependencies.lock.json"]),
    }
    metadata = {
        "schemaVersion": SCHEMA_VERSION,
        "candidate": identity,
        "provenance": {
            "repository": candidate_evidence.REPOSITORY, "workflow": candidate_evidence.WORKFLOW,
            "runId": report["runId"], "runAttempt": report["runAttempt"], "event": "push", "branch": "main",
            "commit": report["sourceCommit"], "tree": report["sourceTree"],
            "artifactId": report["artifactId"], "archiveSha256": report["archiveSha256"],
        },
        "candidatePath": candidate_path,
        "files": {name: reference(raw) for name, raw in sorted(files.items())},
        "installedInventory": {
            "scope": "isolated-ci-runtime",
            "candidate": {"filename": candidate["name"], "size": candidate["size"], "sha256": candidate["sha256"]},
            "dependencies": runtime["dependencies"],
        },
        "receipts": receipts,
        "defects": defects,
        "stableReady": True,
        "autoPublishEligible": False,
        "publicationComplete": False,
        "publicationAuthority": STABLE_AUTOPUBLISH_POLICY,
        "autoPublishBlockers": list(AUTO_PUBLISH_BLOCKERS),
        "publicationPending": list(PUBLICATION_PENDING),
        "releasePolicy": RELEASE_POLICY,
    }
    files["bundle.json"] = canonical_json(metadata)
    return deterministic_zip(files)


def _validate_integrity(raw: bytes, snapshot: dict) -> dict:
    """Validate bytes against a snapshot without making any authentication claim."""
    exact(snapshot, {"report", "evidence", "sources", "defects"}, "Invalid authenticated snapshot")
    report = snapshot["report"]
    props, catalog = validate_source_claims(snapshot)
    files = candidate_evidence.contents(raw)
    require("bundle.json" in files, "Final bundle metadata is missing")
    metadata_raw = files.pop("bundle.json")
    metadata = parse_json(metadata_raw)
    exact(metadata, {"schemaVersion", "candidate", "provenance", "candidatePath", "files", "installedInventory",
                     "receipts", "defects", "stableReady", "autoPublishEligible",
                     "publicationComplete", "publicationAuthority", "autoPublishBlockers",
                     "publicationPending", "releasePolicy"})
    require(type(metadata["schemaVersion"]) is int and metadata["schemaVersion"] == SCHEMA_VERSION,
            "Unsupported final bundle schema")
    require(metadata_raw == canonical_json(metadata), "Final bundle metadata is not canonical JSON")
    declared = metadata["files"]
    require(isinstance(declared, dict) and set(declared) == set(files), "Final bundle file inventory mismatch")
    for name, content in files.items():
        require(declared[name] == reference(content), f"Final bundle file bytes differ: {name}")
    provenance = exact(metadata["provenance"], {
        "repository", "workflow", "runId", "runAttempt", "event", "branch", "commit", "tree",
        "artifactId", "archiveSha256",
    })
    expected_provenance = {
        "repository": candidate_evidence.REPOSITORY, "workflow": candidate_evidence.WORKFLOW,
        "runId": report["runId"], "runAttempt": report["runAttempt"], "event": "push", "branch": "main",
        "commit": report["sourceCommit"], "tree": report["sourceTree"],
        "artifactId": report["artifactId"], "archiveSha256": report["archiveSha256"],
    }
    require(provenance == expected_provenance, "Final bundle provenance differs from authenticated service state")
    for path, content in snapshot["sources"].items():
        require(files.get(f"source/{path}") == content, f"Stale or altered source snapshot: {path}")
    for name, content in snapshot["evidence"].items():
        require(files.get(f"evidence/{name}") == content, f"Stale or altered authenticated evidence: {name}")
    candidate = exact(metadata["candidate"], {
        "artifactId", "version", "modId", "license", "commit", "tree", "jarName", "jarSize", "jarSha256", "lockSha256",
    })
    expected_candidate = report["candidate"]
    require(candidate == {
        "artifactId": report["artifactId"], "version": expected_candidate["version"],
        "modId": expected_candidate["modId"], "license": expected_candidate["license"],
        "commit": report["sourceCommit"], "tree": report["sourceTree"],
        "jarName": expected_candidate["name"], "jarSize": expected_candidate["size"],
        "jarSha256": expected_candidate["sha256"],
        "lockSha256": sha(snapshot["sources"]["tools/ci/runtime-dependencies.lock.json"]),
    }, "Final candidate identity mismatch")
    require(re.fullmatch(r"\d+\.\d+\.\d+(?:\.\d+)?", candidate["version"]) is not None,
            "Wrong stable version")
    candidate_path = metadata["candidatePath"]
    require(candidate_path == f"candidate/{candidate['jarName']}"
            and files.get(candidate_path) == snapshot["evidence"]["candidate.jar"], "Final candidate JAR differs")
    require(candidate_evidence.jar_identity(files[candidate_path]) == {
        "modId": candidate["modId"], "version": candidate["version"], "license": candidate["license"],
    }, "Final candidate JAR metadata mismatch")
    require(candidate["version"] == props.get("mod_version") == "0.1.1", "Wrong stable source version")
    proofs = coverage_proofs(catalog)
    receipts = metadata["receipts"]
    require(isinstance(receipts, list) and len(receipts) == len(KINDS), "Incomplete final receipt set")
    seen: set[str] = set()
    covered: set[str] = set()
    for receipt in receipts:
        exact(receipt, {"kind", "tested", "waived", "capability", "evidence", "coverage", "proofs"})
        kind = receipt["kind"]
        require(kind in KINDS and kind not in seen, "Missing or duplicate final receipt kind")
        seen.add(kind)
        require(receipt["tested"] is True and receipt["waived"] is False, "Untested or waived final receipt")
        expected_capability = {
            "automated": "sourceBuild", "client": "client", "server": "packagedRuntime",
            "multiplayer": "multiplayer", "gameplay": "scopedCompatibility", "save_reload": "saveReload",
        }[kind]
        require(receipt["capability"] == expected_capability, "Wrong final receipt capability")
        require(receipt["evidence"] == [f"evidence/{name}" for name in EVIDENCE_BY_KIND[kind]]
                and all(path in files for path in receipt["evidence"]), "Incomplete final receipt evidence")
        expected_coverage = sorted(key for key, row in catalog.items() if row["kind"] == kind)
        require(receipt["coverage"] == expected_coverage, "Incomplete or wrong acceptance coverage")
        require(receipt["proofs"] == {key: proofs[key] for key in expected_coverage},
                "Incomplete or unsupported acceptance proof mapping")
        require(not (covered & set(expected_coverage)), "Duplicate acceptance coverage")
        covered.update(expected_coverage)
    require(seen == set(KINDS) and covered == set(catalog), "Incomplete final receipt/coverage composition")
    require(metadata["defects"] == snapshot["defects"] == [], "Open defects block stable readiness")
    require(metadata["stableReady"] is True, "Stable readiness state is missing")
    require(metadata["autoPublishEligible"] is False
            and metadata["publicationComplete"] is False
            and metadata["publicationAuthority"] == STABLE_AUTOPUBLISH_POLICY
            and metadata["autoPublishBlockers"] == list(AUTO_PUBLISH_BLOCKERS)
            and metadata["publicationPending"] == list(PUBLICATION_PENDING)
            and metadata["releasePolicy"] == RELEASE_POLICY,
            "Publication state separation is incomplete")
    inventory = exact(metadata["installedInventory"], {"scope", "candidate", "dependencies"})
    runtime = parse_json(snapshot["evidence"]["runtime-dependencies.json"])
    require(inventory == {
        "scope": "isolated-ci-runtime",
        "candidate": {"filename": candidate["jarName"], "size": candidate["jarSize"], "sha256": candidate["jarSha256"]},
        "dependencies": runtime["dependencies"],
    }, "Installed CI inventory differs from authenticated evidence")
    canonical_files = dict(files)
    canonical_files["bundle.json"] = metadata_raw
    require(raw == deterministic_zip(canonical_files), "Final bundle ZIP is not deterministic canonical output")
    return {
        "bundleIntegrity": "PASS", "candidate": candidate, "bundleSha256": sha(raw),
        "autoPublishEligible": False, "publicationComplete": False,
        "publicationAuthority": STABLE_AUTOPUBLISH_POLICY,
        "autoPublishBlockers": list(AUTO_PUBLISH_BLOCKERS),
        "publicationPending": list(PUBLICATION_PENDING), "releasePolicy": RELEASE_POLICY,
    }


def build_authenticated(*, run_id: int, attempt: int, commit: str, tree: str,
                        artifact_id: int, archive_sha256: str,
                        api: candidate_evidence.GitHub | None = None) -> bytes:
    """Authenticate service state first, then compose the deterministic bundle."""
    snapshot = authenticated_snapshot(run_id=run_id, attempt=attempt, commit=commit, tree=tree,
                                      artifact_id=artifact_id, archive_sha256=archive_sha256, api=api)
    return _compose(snapshot)


def validate_authenticated(raw: bytes, *, run_id: int, attempt: int, commit: str, tree: str,
                           artifact_id: int, archive_sha256: str,
                           api: candidate_evidence.GitHub | None = None) -> dict:
    """The sole stable-ready path: fresh service authentication plus bundle integrity."""
    snapshot = authenticated_snapshot(run_id=run_id, attempt=attempt, commit=commit, tree=tree,
                                      artifact_id=artifact_id, archive_sha256=archive_sha256, api=api)
    integrity = _validate_integrity(raw, snapshot)
    report = snapshot["report"]
    return {
        **integrity, "authenticatedExecution": True, "stableReady": True,
        "status": "AUTHENTICATED_STABLE_CANDIDATE", "runId": report["runId"],
        "runAttempt": report["runAttempt"], "sourceCommit": report["sourceCommit"],
        "sourceTree": report["sourceTree"], "artifactId": report["artifactId"],
        "archiveSha256": report["archiveSha256"],
    }
