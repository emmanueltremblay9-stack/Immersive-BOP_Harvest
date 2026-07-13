#!/usr/bin/env python3
"""Synchronize PROJECT_MANIFEST.json version and tracked-file ledger."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "PROJECT_MANIFEST.json"


def read_properties(path: Path) -> dict[str, str]:
    properties: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        properties[key.strip()] = value.strip()
    return properties


def tracked_paths() -> list[Path]:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z"],
        check=True,
        capture_output=True,
    )
    paths = []
    for raw_path in result.stdout.split(b"\0"):
        if not raw_path:
            continue
        relative = Path(raw_path.decode("utf-8"))
        if relative.as_posix() == "PROJECT_MANIFEST.json":
            continue
        full_path = ROOT / relative
        if not full_path.is_file():
            raise FileNotFoundError(f"tracked manifest file is missing: {relative.as_posix()}")
        paths.append(relative)
    return sorted(paths, key=lambda path: path.as_posix())


def file_entry(relative: Path) -> dict[str, str | int]:
    full_path = ROOT / relative
    return {
        "path": relative.as_posix(),
        "size_bytes": full_path.stat().st_size,
        "sha256": hashlib.sha256(full_path.read_bytes()).hexdigest(),
    }


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    properties = read_properties(ROOT / "gradle.properties")
    manifest["version"] = properties["mod_version"]
    manifest["files"] = [file_entry(path) for path in tracked_paths()]
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"PROJECT MANIFEST REFRESHED: {manifest['version']} / {len(manifest['files'])} tracked files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
