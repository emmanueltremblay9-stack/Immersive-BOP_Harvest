#!/usr/bin/env python3
"""Validate a candidate bundle read-only; unauthenticated runtime remains blocked.

This maintenance implementation has no trusted runtime producer. It deliberately
cannot certify stable readiness from local JSON or log markers, even when all
bundle integrity checks pass. No production or runtime operation is performed.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tomllib
import zipfile

if __package__:
    from . import refresh_project_manifest as source
else:
    import refresh_project_manifest as source

ROOT = Path(__file__).resolve().parents[1]
KINDS = {"automated", "client", "server", "multiplayer", "gameplay", "save_reload"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def exact(value: object, fields: set[str]) -> dict:
    require(isinstance(value, dict) and set(value) == fields, "Missing or unknown fields")
    return value


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=source.reject_duplicate_keys)
    require(isinstance(value, dict), "JSON root must be an object")
    return value


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def confined(root: Path, name: str) -> Path:
    require(isinstance(name, str) and bool(name) and "\\" not in name and ":" not in name
            and not name.startswith("/") and all(x not in {"", ".", ".."} for x in name.split("/")),
            "Unsafe evidence path")
    path = root / name
    require(path.resolve().is_relative_to(root.resolve()), "Evidence escapes root")
    require(not any(p.is_symlink() for p in [path, *path.parents]), "Symlinked evidence")
    return path


def reference(root: Path, value: dict) -> Path:
    exact(value, {"path", "size", "sha256"})
    require(type(value["size"]) is int and value["size"] > 0, "Invalid raw size")
    require(isinstance(value["sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", value["sha256"]) is not None,
            "Invalid raw hash")
    path = confined(root, value["path"])
    require(path.is_file() and path.stat().st_size == value["size"] and digest(path) == value["sha256"],
            "Missing or altered evidence: " + value["path"])
    return path


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True,
                          text=True, timeout=30).stdout.strip()


def acceptance_catalog(root: Path) -> dict[str, dict]:
    """Derive coverage IDs from authoritative criteria and every scoped spec entry."""
    rows = {}
    section = ""
    for number, line in enumerate((root / "docs/QA_ACCEPTANCE.md").read_text(encoding="utf-8").splitlines(), 1):
        if line.startswith("## "):
            section = line[3:]
        if line.startswith("- ["):
            kind = "gameplay" if section in {"Farmer's Delight", "Immersive Engineering", "Harvest behavior", "Potted and special blocks"} else "automated"
            if "server" in line.lower():
                kind = "server"
            if "clean instance" in line:
                kind = "client"
            rows[f"qa:{number}"] = {"source": f"docs/QA_ACCEPTANCE.md:{number}", "criterion": line[6:], "kind": kind}
    for path in sorted((root / "spec").glob("*.json")):
        for key, value in read_json(path).items():
            values = enumerate(value) if isinstance(value, list) else [(None, value)]
            for index, entry in values:
                pointer = key + (f"/{index}" if index is not None else "")
                rows[f"spec:{path.stem}/{pointer}"] = {
                    "source": f"spec/{path.name}#/{pointer}",
                    "criterion": json.dumps(entry, ensure_ascii=False, sort_keys=True), "kind": "gameplay"}
    require(bool(rows), "Acceptance catalog is empty")
    return rows


def jar_mods(path: Path) -> tuple[dict, list[dict]]:
    with zipfile.ZipFile(path) as archive:
        name = "META-INF/neoforge.mods.toml"
        require(archive.namelist().count(name) == 1 and archive.getinfo(name).file_size <= 65536,
                "Missing, duplicate or oversized NeoForge metadata")
        metadata = tomllib.loads(archive.read(name).decode("utf-8"))
    mods = metadata.get("mods")
    require(isinstance(mods, list) and bool(mods) and all(isinstance(m, dict) and isinstance(m.get("modId"), str) for m in mods),
            "Invalid mod records")
    return metadata, mods


def validate_bundle(root: Path, bundle: dict) -> None:
    exact(bundle, {"schemaVersion", "candidate", "jar", "dependencyLock", "sourceManifest", "changelog",
                   "installedModsDir", "receipts", "defects", "publicationBlockers"})
    require(type(bundle["schemaVersion"]) is int and bundle["schemaVersion"] == 1, "Unsupported schema")
    candidate = exact(bundle["candidate"], {"id", "version", "modId", "license", "commit", "tree", "jarSha256", "lockSha256"})
    require(all(isinstance(v, str) and v for v in candidate.values()), "Invalid candidate identity")
    require(re.fullmatch(r"[A-Za-z0-9_.-]+", candidate["id"]) is not None, "Invalid candidate ID")
    require(re.fullmatch(r"\d+\.\d+\.\d+(?:\.\d+)?", candidate["version"]) is not None, "Stable version required; alpha waiver is historical only")
    require(git(root, "rev-parse", "HEAD") == candidate["commit"]
            and git(root, "rev-parse", "HEAD^{tree}") == candidate["tree"], "Stale source commit/tree")
    require(not git(root, "status", "--porcelain", "--untracked-files=normal"), "Source checkout must be clean")
    props = source.read_properties(root / "gradle.properties")
    for field, prop in (("version", "mod_version"), ("modId", "mod_id"), ("license", "mod_license")):
        require(candidate[field] == props.get(prop), "Candidate differs from source metadata")
    require(candidate["license"] not in {"LICENSE_PENDING", "PENDING", "UNLICENSED"} and (root / "LICENSE").is_file(), "License unresolved")
    manifest = reference(root, bundle["sourceManifest"])
    require(manifest == root / "PROJECT_MANIFEST.json", "Wrong source manifest")
    source_manifest = read_json(manifest)
    require(source_manifest.get("mod_id") == candidate["modId"] and source_manifest.get("version") == candidate["version"],
            "Source manifest identity differs from candidate")
    source.check_file_ledger(source_manifest, root)
    jar = reference(root, bundle["jar"])
    require(jar.name == f"{candidate['modId']}-{candidate['version']}.jar" and digest(jar) == candidate["jarSha256"], "Candidate JAR differs")
    metadata, mods = jar_mods(jar)
    matches = [m for m in mods if m["modId"] == candidate["modId"]]
    require(len(matches) == 1 and matches[0].get("version") == candidate["version"]
            and metadata.get("license") == candidate["license"], "JAR same-record identity mismatch")
    lock_path = reference(root, bundle["dependencyLock"])
    require(lock_path == root / "tools/ci/runtime-dependencies.lock.json" and digest(lock_path) == candidate["lockSha256"], "Wrong dependency lock")
    sys.path.insert(0, str(ROOT)) if str(ROOT) not in sys.path else None
    from tools.ci.prepare_runtime import validate_lock, validate_bytes
    dependencies = validate_lock(read_json(lock_path), props)
    installed = confined(root, bundle["installedModsDir"])
    require(installed.is_dir(), "Missing disposable installation")
    expected_names = {jar.name, *(row["filename"] for row in dependencies)}
    require({p.name for p in installed.glob("*.jar")} == expected_names, "Incomplete or extra installed JAR inventory")
    all_ids = []
    for path in installed.glob("*.jar"):
        confined(root, path.relative_to(root).as_posix())
        _, records = jar_mods(path)
        all_ids.extend(m["modId"] for m in records)
    require(len(all_ids) == len(set(all_ids)), "Duplicate installed mod IDs")
    require(digest(installed / jar.name) == digest(jar) and (installed / jar.name).stat().st_size == jar.stat().st_size, "Installed candidate differs")
    for row in dependencies:
        validate_bytes(row, (installed / row["filename"]).read_bytes())
    changelog = reference(root, bundle["changelog"])
    require(changelog != manifest and changelog.suffix == ".md" and candidate["version"] in changelog.read_text(encoding="utf-8"), "Wrong immutable changelog")
    require(isinstance(bundle["defects"], list) and bundle["defects"] == [], "Unresolved defects require separate review")
    require(isinstance(bundle["publicationBlockers"], list) and all(isinstance(x, str) and x for x in bundle["publicationBlockers"]), "Invalid external blocker list")
    receipts = bundle["receipts"]
    require(isinstance(receipts, list) and len(receipts) == len(KINDS), "Missing mandatory receipts")
    kinds, covered = set(), set()
    catalog = acceptance_catalog(root)
    for ref in receipts:
        receipt = read_json(reference(root, ref))
        exact(receipt, {"kind", "candidate", "tested", "waived", "command", "exitCode", "startedAt", "finishedAt", "log", "coverage"})
        kind = receipt["kind"]
        require(isinstance(kind, str) and kind in KINDS and kind not in kinds, "Missing or duplicate receipt kind")
        kinds.add(kind)
        require(receipt["candidate"] == candidate, "Stale or wrong receipt candidate")
        require(receipt["tested"] is True and receipt["waived"] is False, "Untested or waived receipt")
        require(type(receipt["exitCode"]) is int and receipt["exitCode"] == 0, "Receipt command failed")
        require(isinstance(receipt["command"], list) and bool(receipt["command"]) and all(isinstance(x, str) and x for x in receipt["command"]), "Missing exact command")
        times = []
        for field in ("startedAt", "finishedAt"):
            require(isinstance(receipt[field], str) and receipt[field].endswith("Z"), "Expected UTC receipt time")
            times.append(datetime.fromisoformat(receipt[field].replace("Z", "+00:00")))
        require(times[0] <= times[1] <= datetime.now(timezone.utc), "Invalid receipt chronology")
        reference(root, receipt["log"])
        coverage = receipt["coverage"]
        require(isinstance(coverage, list) and all(isinstance(x, str) for x in coverage)
                and len(coverage) == len(set(coverage)), "Malformed coverage")
        for key in coverage:
            require(key in catalog and catalog[key]["kind"] == kind and key not in covered, "Wrong, duplicate or unknown acceptance coverage")
            covered.add(key)
    require(kinds == KINDS and covered == set(catalog), "Incomplete acceptance coverage")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        validate_bundle(ROOT, read_json(args.bundle))
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile, subprocess.SubprocessError) as exc:
        print(json.dumps({"bundleIntegrity": "FAIL", "stableReady": False, "status": "BLOCKED_INVALID_OR_MISSING_CANDIDATE_EVIDENCE", "reason": str(exc)}))
        return 1
    print(json.dumps({"bundleIntegrity": "PASS", "stableReady": False, "status": "BLOCKED_UNTRUSTED_RUNTIME_PROVENANCE",
                      "reason": "Local receipt hashes do not authenticate execution. Trusted producer/readback integration is still required."}))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
