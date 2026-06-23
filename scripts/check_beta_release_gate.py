#!/usr/bin/env python3
"""Check whether Immersive BOP_Harvest is ready for public beta release."""

from __future__ import annotations

import json
import re
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


def resolve_project_path(path_value: str) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return ROOT / path


def read_mod_metadata(jar_path: Path) -> str:
    with zipfile.ZipFile(jar_path) as jar:
        with jar.open("META-INF/neoforge.mods.toml") as metadata:
            return metadata.read().decode("utf-8", errors="replace")


def metadata_declares_mod(metadata: str, mod_id: str) -> bool:
    return re.search(rf'(?m)^\s*modId\s*=\s*"{re.escape(mod_id)}"\s*$', metadata) is not None


def installed_jars_for_mod(mods_dir: Path, mod_id: str) -> list[Path]:
    matches: list[Path] = []
    for jar_path in sorted(mods_dir.glob("*.jar")):
        try:
            metadata = read_mod_metadata(jar_path)
        except (KeyError, OSError, zipfile.BadZipFile):
            continue
        if metadata_declares_mod(metadata, mod_id):
            matches.append(jar_path)
    return matches


def main() -> int:
    failures: list[str] = []

    props_path = ROOT / "gradle.properties"
    manifest_path = ROOT / "PROJECT_MANIFEST.json"
    props = read_properties(props_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    build = manifest["build_summary"]

    mod_id = manifest.get("mod_id", "")
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
        "live_client_smoke_tested": "live client load smoke passed",
    }
    for key, label in boolean_gates.items():
        check(bool(build.get(key)), label, f"{key} is not proven in PROJECT_MANIFEST.json", failures)

    built_jar = resolve_project_path(build["built_jar"])
    installed_jar = resolve_project_path(build["installed_jar"])

    check(built_jar.is_file(), "built jar exists", f"built jar is missing: {built_jar}", failures)
    check(installed_jar.is_file(), "installed jar exists", f"installed jar is missing: {installed_jar}", failures)

    if built_jar.is_file():
        source_sha = sha256_file(built_jar)
        check(
            source_sha == build.get("source_sha256"),
            "built jar SHA-256 matches manifest",
            "built jar SHA-256 does not match manifest",
            failures,
        )

    if installed_jar.is_file():
        installed_sha = sha256_file(installed_jar)
        check(
            installed_sha == build.get("installed_sha256"),
            "installed jar SHA-256 matches manifest",
            "installed jar SHA-256 does not match manifest",
            failures,
        )
        if built_jar.is_file():
            check(
                sha256_file(built_jar) == installed_sha,
                "built jar and installed jar SHA-256 values match",
                "built jar and installed jar SHA-256 values do not match",
                failures,
            )

        metadata = read_mod_metadata(installed_jar)
        check(
            metadata_declares_mod(metadata, mod_id),
            "installed jar metadata declares the expected mod id",
            "installed jar metadata does not declare the expected mod id",
            failures,
        )
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

        mod_jars = installed_jars_for_mod(installed_jar.parent, mod_id)
        check(
            len(mod_jars) == 1,
            f"exactly one installed jar declares {mod_id}",
            f"expected exactly one installed jar declaring {mod_id}; found {len(mod_jars)}",
            failures,
        )
        if len(mod_jars) == 1:
            check(
                mod_jars[0].resolve() == installed_jar.resolve(),
                "sole installed mod jar matches PROJECT_MANIFEST.json",
                "sole installed mod jar does not match PROJECT_MANIFEST.json",
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
