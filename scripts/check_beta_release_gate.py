#!/usr/bin/env python3
"""Check whether Immersive BOP_Harvest is ready for public beta release."""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PENDING_LICENSE_VALUES = {"", "LICENSE_PENDING", "PENDING", "UNLICENSED"}


def read_properties(path: Path) -> dict[str, str]:
    props: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        props[key.strip()] = value.strip()
    return props


def sha256_file(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check(condition: bool, ok: str, fail: str, failures: list[str]) -> None:
    if condition:
        print(f"PASS: {ok}")
    else:
        print(f"BLOCKER: {fail}")
        failures.append(fail)


def read_installed_metadata(jar_path: Path) -> str:
    with zipfile.ZipFile(jar_path) as jar:
        with jar.open("META-INF/neoforge.mods.toml") as metadata:
            return metadata.read().decode("utf-8", errors="replace")


def main() -> int:
    failures: list[str] = []

    props_path = ROOT / "gradle.properties"
    manifest_path = ROOT / "PROJECT_MANIFEST.json"
    props = read_properties(props_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    build = manifest["build_summary"]

    mod_version = props.get("mod_version", "")
    mod_license = props.get("mod_license", "")

    print(f"Project: {manifest.get('project')}")
    print(f"Version: {mod_version}")
    print(f"License: {mod_license}")
    print()

    check(
        mod_version == manifest.get("version"),
        "gradle.properties version matches PROJECT_MANIFEST.json",
        "gradle.properties version does not match PROJECT_MANIFEST.json",
        failures,
    )
    check(
        mod_license not in PENDING_LICENSE_VALUES,
        "mod_license is selected",
        "mod_license is still pending",
        failures,
    )
    check(
        (ROOT / "LICENSE").is_file(),
        "LICENSE file exists",
        "LICENSE file is missing",
        failures,
    )

    required_truth_files = [
        "README.md",
        "CHANGELOG.md",
        "VALIDATION_REPORT.txt",
        "docs/PLAYABLE_ALPHA_PROOF.md",
        "docs/RELEASE_CHECKLIST.md",
        "docs/BETA_RELEASE_AUDIT.md",
        "docs/BETA_RELEASE_NOTES_DRAFT.md",
        "docs/LEGAL_REUSE_INVENTORY.md",
    ]
    for rel_path in required_truth_files:
        check(
            (ROOT / rel_path).is_file(),
            f"{rel_path} exists",
            f"{rel_path} is missing",
            failures,
        )

    boolean_gates = {
        "hash_match": "installed jar hash matched source jar",
        "runData_passed": "runData passed",
        "game_tests_passed": "GameTests passed",
        "dedicated_server_smoke_tested": "dedicated server smoke passed",
        "live_client_smoke_tested": "live client title-screen smoke passed",
    }
    for key, label in boolean_gates.items():
        check(bool(build.get(key)), label, f"{key} is not proven in PROJECT_MANIFEST.json", failures)

    installed_jar = Path(build["installed_jar"])
    check(installed_jar.is_file(), "installed jar exists", f"installed jar is missing: {installed_jar}", failures)

    if installed_jar.is_file():
        installed_sha = sha256_file(installed_jar)
        check(
            installed_sha == build.get("installed_sha256"),
            "installed jar SHA-256 matches manifest",
            "installed jar SHA-256 does not match manifest",
            failures,
        )
        metadata = read_installed_metadata(installed_jar)
        check(
            f'version="{mod_version}"' in metadata,
            "installed jar metadata has current version",
            "installed jar metadata does not have current version",
            failures,
        )
        check(
            f'license="{mod_license}"' in metadata and mod_license not in PENDING_LICENSE_VALUES,
            "installed jar metadata has selected license",
            "installed jar metadata still lacks a selected license",
            failures,
        )

    if failures:
        print()
        print("BETA RELEASE GATE: BLOCKED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print()
    print("BETA RELEASE GATE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
