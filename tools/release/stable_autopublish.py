#!/usr/bin/env python3
"""Evaluate fail-closed stable auto-publication eligibility without mutating remotes.

This entry point authenticates source and runtime preconditions.  It has no
tag, Release, upload, secret-value, or POST capability.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any
import urllib.parse


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.ci import candidate_evidence, final_release_bundle
from tools.release import publish_curseforge


EXPECTED_REPOSITORY = candidate_evidence.REPOSITORY
EXPECTED_WORKFLOW_NAME = "Build and validate"
EXPECTED_WORKFLOW_PATH = candidate_evidence.WORKFLOW
EXPECTED_MANIFEST = "tools/release/curseforge_release_0.1.1.json"
EXPECTED_NOTES = "docs/release/0.1.1.md"
EXPECTED_TAG = "v0.1.1"
EXPECTED_VERSION = "0.1.1"
EXPECTED_MOD_ID = "immersive_bop_harvest"
STABLE_AUTOPUBLISH_POLICY = final_release_bundle.STABLE_AUTOPUBLISH_POLICY
MAX_TAG_DEREFERENCE = 8
PUBLICATION_PENDING = ("GITHUB_TAG", "GITHUB_RELEASE", "CURSEFORGE")
AUTO_PUBLISH_GATE_NAMES = (
    "canonicalWorkflow",
    "exactCurrentMain",
    "authenticatedStableGate",
    "candidateIdentity",
    "versionedManifest",
    "releaseNotesHash",
    "credentialAvailable",
    "curseForgeProjectIdentity",
    "historicalFileRelations",
    "historicalProjectRelations",
    "targetRelations",
    "gitTagNonDivergent",
    "githubReleaseNonDivergent",
    "githubAssetNonDivergent",
    "curseForgeArtifactNonDivergent",
    "stableRelease",
    "automaticInvocation",
    "modrinthNotApplicable",
)
EXPECTED_HISTORICAL_RELATIONS = (
    (220318, "biomes-o-plenty", "RequiredDependency"),
    (398521, "farmers-delight", "RequiredDependency"),
    (231951, "immersive-engineering", "RequiredDependency"),
)
EXPECTED_TARGET_RELATIONS = (
    (220318, "biomes-o-plenty", "RequiredDependency"),
    (955399, "glitchcore", "RequiredDependency"),
    (940057, "terrablender-neoforge", "RequiredDependency"),
    (398521, "farmers-delight", "RequiredDependency"),
    (231951, "immersive-engineering", "RequiredDependency"),
)


class ReadinessError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReadinessError(message)


def positive_int(value: Any) -> bool:
    return type(value) is int and value > 0


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=candidate_evidence.unique,
    )
    require(isinstance(value, dict), f"Expected JSON object: {path.name}")
    return value


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def validate_workflow_run(event: dict[str, Any]) -> dict[str, Any]:
    require(isinstance(event, dict), "Workflow event must be an object")
    run = event.get("workflow_run")
    require(isinstance(run, dict), "workflow_run payload is missing")
    repository = event.get("repository")
    require(
        isinstance(repository, dict) and repository.get("full_name") == EXPECTED_REPOSITORY,
        "Unexpected event repository",
    )
    require(
        run.get("name") == EXPECTED_WORKFLOW_NAME
        and run.get("path") == EXPECTED_WORKFLOW_PATH,
        "Unexpected upstream workflow",
    )
    require(
        run.get("event") == "push" and run.get("head_branch") == "main",
        "Only a canonical main push is eligible",
    )
    require(
        run.get("status") == "completed" and run.get("conclusion") == "success",
        "Upstream workflow did not complete successfully",
    )
    require(
        isinstance(run.get("head_repository"), dict)
        and run["head_repository"].get("full_name") == EXPECTED_REPOSITORY,
        "Upstream source repository differs",
    )
    require(positive_int(run.get("id")) and positive_int(run.get("run_attempt")),
            "Invalid upstream run identity")
    require(isinstance(run.get("head_sha"), str)
            and re.fullmatch(r"[0-9a-f]{40}", run["head_sha"]) is not None,
            "Invalid upstream head SHA")
    return {
        "id": run["id"],
        "attempt": run["run_attempt"],
        "headSha": run["head_sha"],
        "event": run["event"],
        "branch": run["head_branch"],
        "workflow": run["path"],
    }


def verify_current_main(api: candidate_evidence.GitHub, expected_sha: str) -> None:
    reference = api.get("git/ref/heads/main")
    require(
        isinstance(reference, dict)
        and isinstance(reference.get("object"), dict)
        and reference["object"].get("type") == "commit"
        and reference["object"].get("sha") == expected_sha,
        "Upstream head is no longer current main",
    )


def verify_checkout(repo_root: Path, expected_sha: str) -> None:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    require(result.returncode == 0 and result.stdout.strip() == expected_sha,
            "Checked-out source is not the upstream head")


def relation_tuples(values: Any, *, upload: bool = False) -> tuple[tuple[int, str, str], ...]:
    require(isinstance(values, list), "Relation set must be an explicit array")
    key = "projectID" if upload else "projectId"
    mapped = []
    for row in values:
        require(isinstance(row, dict), "Relation entry must be an object")
        relation_type = row.get("type")
        if upload:
            require(relation_type == "requiredDependency", "Unexpected upload relation type")
            relation_type = "RequiredDependency"
        mapped.append((row.get(key), row.get("slug"), relation_type))
    return tuple(mapped)


def validate_release_contract(repo_root: Path, candidate: dict[str, Any]) -> dict[str, Any]:
    manifest_path = repo_root / EXPECTED_MANIFEST
    notes_path = repo_root / EXPECTED_NOTES
    require(manifest_path.is_file() and notes_path.is_file(), "Versioned stable release inputs are missing")
    manifest = publish_curseforge.validate_manifest(read_json(manifest_path))
    require(manifest["schemaVersion"] == 3, "Stable manifest must use schema 3")
    release = manifest["release"]
    require(
        release["tag"] == EXPECTED_TAG
        and release["version"] == EXPECTED_VERSION
        and release["modId"] == EXPECTED_MOD_ID,
        "Stable manifest release identity differs",
    )
    require(
        candidate == {
            "modId": release["modId"],
            "version": release["version"],
            "license": "All Rights Reserved",
            "name": release["assetName"],
            "size": release["assetSize"],
            "sha256": release["assetSha256"],
        },
        "Stable manifest is not bound to authenticated candidate bytes",
    )
    notes = notes_path.read_bytes()
    require(
        release["changelogPath"] == EXPECTED_NOTES
        and release["changelogSha256"] == sha256(notes),
        "Stable notes path or hash differs",
    )
    notes_text = notes.decode("utf-8")
    require(EXPECTED_VERSION in notes_text
            and "NOT_PERFORMED / OWNER_WAIVED" in notes_text
            and "Modrinth" in notes_text and "forbidden" in notes_text.lower(),
            "Stable notes omit a required release boundary")
    baseline = manifest["baseline"]
    require(
        baseline["mode"] == "previousPublicFile"
        and baseline["previousPublicFileId"] == 8426397
        and baseline["releaseType"] == "alpha"
        and baseline["gameVersionNames"] == ["Client", "1.21.1", "NeoForge"]
        and relation_tuples(baseline["previousFileRelations"])
            == EXPECTED_HISTORICAL_RELATIONS
        and baseline["projectRelations"] == [],
        "Historical CurseForge baseline differs",
    )
    curseforge = manifest["curseforge"]
    require(
        curseforge["projectId"] == 1609013
        and curseforge["projectSlug"] == "immersive-bop-harvest"
        and curseforge["releaseType"] == "release"
        and relation_tuples(curseforge["expectedPublicRelations"])
            == EXPECTED_TARGET_RELATIONS
        and relation_tuples(curseforge["uploadRelations"], upload=True)
            == EXPECTED_TARGET_RELATIONS,
        "Target CurseForge identity or relations differ",
    )
    forbidden_keys = {
        key.lower()
        for value in (manifest,)
        for key in _keys(value)
        if "secret" in key.lower() or "authority" in key.lower() or "token" in key.lower()
    }
    require(not forbidden_keys, "Release manifest must not carry secret or authority switches")
    return {
        "path": EXPECTED_MANIFEST,
        "sha256": sha256(manifest_path.read_bytes()),
        "notesPath": EXPECTED_NOTES,
        "notesSha256": sha256(notes),
        "tag": release["tag"],
        "projectId": curseforge["projectId"],
        "projectSlug": curseforge["projectSlug"],
        "historicalFileRelations": len(baseline["previousFileRelations"]),
        "historicalProjectRelations": len(baseline["projectRelations"]),
        "targetRelations": len(curseforge["expectedPublicRelations"]),
    }


def _keys(value: Any):
    if isinstance(value, dict):
        for key, nested in value.items():
            yield str(key)
            yield from _keys(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _keys(nested)


def reconcile_exact(kind: str, existing: Any, expected: Any) -> str:
    require(kind in {"GITHUB_TAG", "GITHUB_RELEASE", "CURSEFORGE_FILE"},
            "Unknown reconciliation target")
    if existing is None:
        return "ABSENT_READY"
    if existing == expected:
        return "EXACT_RECONCILED"
    raise ReadinessError(f"{kind}_DIVERGENT_STOP")


def evaluate_auto_publish_eligibility(
    gate_evidence: dict[str, Any],
    *,
    extra_blockers: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Apply the standing policy to a closed, strict-boolean runtime gate map."""
    require(isinstance(gate_evidence, dict), "Runtime gate evidence must be an object")
    expected = set(AUTO_PUBLISH_GATE_NAMES)
    actual = set(gate_evidence)
    blockers = list(extra_blockers)
    blockers.extend(f"GATE_MISSING:{name}" for name in sorted(expected - actual))
    blockers.extend(f"GATE_UNKNOWN:{name}" for name in sorted(actual - expected))
    normalized: dict[str, bool | None] = {}
    for name in AUTO_PUBLISH_GATE_NAMES:
        value = gate_evidence.get(name)
        normalized[name] = value if type(value) is bool else None
        if value is not True:
            blockers.append(f"GATE_NOT_VERIFIED:{name}")
    blockers = list(dict.fromkeys(blockers))
    eligible = (
        STABLE_AUTOPUBLISH_POLICY == "AUTHORIZED_WHEN_ELIGIBLE"
        and not blockers
    )
    return {
        "publicationAuthority": STABLE_AUTOPUBLISH_POLICY,
        "runtimeGates": normalized,
        "autoPublishEligible": eligible,
        "autoPublishBlockers": blockers,
    }


def _github_optional(path: str) -> dict[str, Any] | None:
    result = subprocess.run(
        [
            "gh", "api", "--method", "GET",
            f"repos/{EXPECTED_REPOSITORY}/{path}",
        ],
        capture_output=True,
        timeout=90,
    )
    if result.returncode == 0:
        value = candidate_evidence.read_json(result.stdout)
        require(isinstance(value, dict), "GitHub readback must be an object")
        return value
    error = result.stderr.decode("utf-8", errors="replace")
    if "HTTP 404" in error:
        return None
    raise ReadinessError("GitHub publication-state readback unavailable")


def _github_tag_state(source_sha: str) -> str:
    tag = urllib.parse.quote(EXPECTED_TAG, safe="")
    reference = _github_optional(f"git/ref/tags/{tag}")
    if reference is None:
        return reconcile_exact("GITHUB_TAG", None, {"commitSha": source_sha})
    obj = reference.get("object")
    require(isinstance(obj, dict), "GitHub tag reference is malformed")
    seen: set[str] = set()
    target_sha = None
    for _ in range(MAX_TAG_DEREFERENCE):
        kind, target = obj.get("type"), obj.get("sha")
        require(isinstance(target, str), "GITHUB_TAG_AMBIGUOUS_STOP")
        if kind == "commit":
            target_sha = target
            break
        require(kind == "tag" and target not in seen, "GITHUB_TAG_AMBIGUOUS_STOP")
        seen.add(target)
        annotated = _github_optional(f"git/tags/{target}")
        require(isinstance(annotated, dict), "Annotated Git tag object is missing")
        obj = annotated.get("object")
        require(isinstance(obj, dict), "GITHUB_TAG_AMBIGUOUS_STOP")
    require(target_sha is not None, "GITHUB_TAG_AMBIGUOUS_STOP")
    return reconcile_exact(
        "GITHUB_TAG",
        {"commitSha": target_sha},
        {"commitSha": source_sha},
    )


def _github_release_state(
    *,
    tag_state: str,
    candidate: dict[str, Any],
    notes: str,
) -> tuple[str, str]:
    tag = urllib.parse.quote(EXPECTED_TAG, safe="")
    release = _github_optional(f"releases/tags/{tag}")
    if release is None:
        return "RELEASE_ABSENT_READY", "ASSET_NOT_APPLICABLE"
    require(tag_state == "EXACT_RECONCILED",
            "GITHUB_RELEASE_DIVERGENT_STOP")
    assets = release.get("assets")
    require(isinstance(assets, list), "GitHub Release assets are malformed")
    require(all(isinstance(asset, dict) for asset in assets),
            "GITHUB_RELEASE_DIVERGENT_STOP")
    observed_release = {
        "tag": release.get("tag_name"),
        "targetCommit": release.get("target_commitish"),
        "draft": release.get("draft"),
        "prerelease": release.get("prerelease"),
        "name": release.get("name"),
        "body": release.get("body"),
    }
    expected_release = {
        "tag": EXPECTED_TAG,
        "targetCommit": candidate["sourceCommit"],
        "draft": False,
        "prerelease": False,
        "name": "Immersive BOP Harvest 0.1.1",
        "body": notes,
    }
    reconcile_exact("GITHUB_RELEASE", observed_release, expected_release)
    if not assets:
        return "RELEASE_EXACT", "ASSET_ABSENT_READY"
    observed_assets = [{
        "name": asset.get("name"),
        "size": asset.get("size"),
        "digest": asset.get("digest"),
    } for asset in assets]
    expected_assets = [{
        "name": candidate["name"],
        "size": candidate["size"],
        "digest": f"sha256:{candidate['sha256']}",
    }]
    if observed_assets != expected_assets:
        raise ReadinessError("GITHUB_ASSET_DIVERGENT_STOP")
    return "RELEASE_EXACT", "ASSET_EXACT"


def collect_runtime_gate_evidence(
    repo_root: Path,
    *,
    run: dict[str, Any],
    candidate: dict[str, Any],
    contract: dict[str, Any],
    credential_available: bool,
) -> tuple[dict[str, bool], dict[str, str], tuple[str, ...]]:
    """Perform the read-only live preflight that can make the standing policy eligible."""
    gates = {name: False for name in AUTO_PUBLISH_GATE_NAMES}
    gates.update({
        "canonicalWorkflow": True,
        "exactCurrentMain": True,
        "authenticatedStableGate": True,
        "candidateIdentity": True,
        "versionedManifest": True,
        "releaseNotesHash": True,
        "credentialAvailable": credential_available is True,
        "targetRelations": contract.get("targetRelations") == 5,
        "stableRelease": candidate.get("version") == EXPECTED_VERSION,
        "automaticInvocation": True,
        "modrinthNotApplicable": True,
    })
    states: dict[str, str] = {}
    blockers: list[str] = []
    manifest = read_json(repo_root / EXPECTED_MANIFEST)
    publisher = publish_curseforge.Publisher(repo_root, manifest)
    try:
        with tempfile.TemporaryDirectory(prefix="stable-autopublish-readback-") as temporary:
            public_state = publisher.preflight_publication_state(Path(temporary))
        baseline = public_state["baseline"]
        identity = baseline.get("projectIdentity")
        gates["curseForgeProjectIdentity"] = (
            isinstance(identity, dict)
            and identity.get("projectId") == 1609013
            and identity.get("projectSlug") == "immersive-bop-harvest"
        )
        gates["historicalFileRelations"] = (
            isinstance(baseline.get("previousFileRelations"), list)
            and len(baseline["previousFileRelations"]) == 3
        )
        gates["historicalProjectRelations"] = (
            baseline.get("projectRelationsCheck") == "MATCHED"
            and baseline.get("projectRelations") == []
        )
        existing = public_state["existingRelease"]
        states["curseForgeArtifact"] = reconcile_exact(
            "CURSEFORGE_FILE",
            None if existing is None else {
                "sha256": existing.get("sha256"),
                "size": existing.get("size"),
            },
            {
                "sha256": candidate["sha256"],
                "size": candidate["size"],
            },
        )
        gates["curseForgeArtifactNonDivergent"] = True
    except publish_curseforge.PublicationError as exc:
        blockers.append(exc.status)
        return gates, states, tuple(blockers)

    try:
        states["gitTag"] = _github_tag_state(run["headSha"])
        gates["gitTagNonDivergent"] = True
        notes = (repo_root / EXPECTED_NOTES).read_text(encoding="utf-8")
        release_candidate = {**candidate, "sourceCommit": run["headSha"]}
        states["githubRelease"], states["githubAsset"] = _github_release_state(
            tag_state=states["gitTag"],
            candidate=release_candidate,
            notes=notes,
        )
        gates["githubReleaseNonDivergent"] = True
        gates["githubAssetNonDivergent"] = True
    except (OSError, UnicodeError, ValueError, KeyError, TypeError,
            subprocess.SubprocessError) as exc:
        blockers.append(str(exc) or "GITHUB_PUBLICATION_STATE_BLOCKED")
    return gates, states, tuple(blockers)


def evaluate_source_readiness(
    event: dict[str, Any],
    repo_root: Path,
    *,
    api: candidate_evidence.GitHub | None = None,
    credential_available: bool = False,
    _runtime_gate_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    run = validate_workflow_run(event)
    api = api or candidate_evidence.GitHub()
    verify_current_main(api, run["headSha"])
    verify_checkout(repo_root, run["headSha"])
    candidate = candidate_evidence.verify(
        run["id"], run["attempt"], run["headSha"], api=api
    )
    pins = {
        "run_id": candidate["runId"],
        "attempt": candidate["runAttempt"],
        "commit": candidate["sourceCommit"],
        "tree": candidate["sourceTree"],
        "artifact_id": candidate["artifactId"],
        "archive_sha256": candidate["archiveSha256"],
    }
    bundle = final_release_bundle.build_authenticated(api=api, **pins)
    stable = final_release_bundle.validate_authenticated(bundle, api=api, **pins)
    require(stable.get("stableReady") is True, "Authenticated stable bundle did not qualify")
    contract = validate_release_contract(repo_root, candidate["candidate"])
    identity = {
        "runId": run["id"],
        "runAttempt": run["attempt"],
        "sourceCommit": run["headSha"],
        "sourceTree": candidate["sourceTree"],
        "artifactId": candidate["artifactId"],
        "archiveSha256": candidate["archiveSha256"],
        "candidateSha256": candidate["candidate"]["sha256"],
        "manifestSha256": contract["sha256"],
        "notesSha256": contract["notesSha256"],
    }
    runtime_states: dict[str, str] = {}
    runtime_blockers: tuple[str, ...] = ()
    if _runtime_gate_evidence is None:
        runtime_gates, runtime_states, runtime_blockers = collect_runtime_gate_evidence(
            repo_root,
            run=run,
            candidate=candidate["candidate"],
            contract=contract,
            credential_available=credential_available,
        )
    else:
        runtime_gates = _runtime_gate_evidence
    eligibility = evaluate_auto_publish_eligibility(
        runtime_gates,
        extra_blockers=runtime_blockers,
    )
    eligible = eligibility["autoPublishEligible"]
    return {
        "schemaVersion": 2,
        "repository": EXPECTED_REPOSITORY,
        "status": "AUTO_PUBLISH_ELIGIBLE" if eligible else "AUTO_PUBLISH_BLOCKED",
        "verdict": "PASS" if eligible else "BLOCKED",
        "sourceReady": True,
        "authenticatedExecution": True,
        "stableReady": True,
        "autoPublishEligible": eligible,
        "publicationComplete": False,
        "publicationAuthority": STABLE_AUTOPUBLISH_POLICY,
        "autoPublishBlockers": eligibility["autoPublishBlockers"],
        "runtimeGates": eligibility["runtimeGates"],
        "runtimeStates": runtime_states,
        "publicationPending": list(PUBLICATION_PENDING),
        "releasePolicy": {
            "targets": ["github", "curseforge"],
            "modrinth": "FORBIDDEN_BY_PROJECT_POLICY",
        },
        "workflowRun": run,
        "authenticatedSource": {
            "runId": run["id"],
            "runAttempt": run["attempt"],
            "sourceCommit": run["headSha"],
            "sourceTree": candidate["sourceTree"],
            "artifactId": candidate["artifactId"],
            "archiveSha256": candidate["archiveSha256"],
        },
        "candidate": candidate["candidate"],
        "releaseContract": contract,
        "finalBundleSha256": final_release_bundle.sha(bundle),
        "idempotenceKey": sha256(final_release_bundle.canonical_json(identity)),
        "recoveryPolicy": {
            "exactExistingTarget": "RECONCILE",
            "divergentExistingTarget": "STOP",
            "acceptedCurseForgeFile": "RESUME_WITHOUT_POST",
            "unknownPostOutcome": "STOP_NO_RETRY",
        },
    }


def write_report(path: Path | None, report: dict[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--report", type=Path)
    parser.add_argument(
        "--credential-available",
        action="store_true",
        help="Confirm only that the authorized job supplied a non-empty credential",
    )
    args = parser.parse_args(argv)
    try:
        report = evaluate_source_readiness(
            read_json(args.event),
            args.repo_root.resolve(),
            credential_available=args.credential_available,
        )
    except (OSError, UnicodeError, ValueError, KeyError, TypeError,
            subprocess.SubprocessError) as exc:
        report = {
            "schemaVersion": 2,
            "status": "SOURCE_READINESS_BLOCKED",
            "verdict": "BLOCKED",
            "sourceReady": False,
            "stableReady": False,
            "autoPublishEligible": False,
            "publicationComplete": False,
            "publicationAuthority": STABLE_AUTOPUBLISH_POLICY,
            "autoPublishBlockers": ["SOURCE_READINESS_BLOCKED"],
            "reason": str(exc),
        }
        write_report(args.report, report)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 1
    write_report(args.report, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["autoPublishEligible"] is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
