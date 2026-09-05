#!/usr/bin/env python3
"""Refresh the Git source ledger, or verify a source ZIP read-only with --check."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "PROJECT_MANIFEST.json"
BINARY_SUFFIXES = frozenset({".jar", ".png", ".nbt"})


def read_properties(path: Path) -> dict[str, str]:
    properties = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            properties[key.strip()] = value.strip()
    return properties


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key in project manifest")
        result[key] = value
    return result


def source_path(name: str, root: Path | None = None) -> Path:
    root = ROOT if root is None else root
    if (not isinstance(name, str) or not name or "\\" in name or ":" in name
            or any(part in {"", ".", ".."} for part in name.split("/"))
            or PurePosixPath(name).is_absolute()
            or name == "PROJECT_MANIFEST.json"):
        raise ValueError("Unsafe or self-referencing source ledger path")
    candidate = root / name
    if not candidate.resolve().is_relative_to(root.resolve()):
        raise ValueError("Source ledger path escapes project root")
    if candidate.is_symlink() or not candidate.is_file():
        raise ValueError(f"Missing or symlinked source file: {name}")
    return candidate


def tracked_paths(root: Path | None = None) -> list[Path]:
    root = ROOT if root is None else root
    # Do not accidentally use the enclosing repository when checking an extracted ZIP.
    if not (root / ".git").exists():
        raise ValueError("Refreshing requires a Git checkout; use --check for a source ZIP")
    top = subprocess.run(["git", "-C", str(root), "rev-parse", "--show-toplevel"],
                         check=True, capture_output=True, text=True)
    if Path(top.stdout.strip()).resolve() != root.resolve():
        raise ValueError("Git worktree root does not match this project")
    result = subprocess.run(["git", "-C", str(root), "ls-files", "-z"],
                            check=True, capture_output=True)
    names = [name.decode("utf-8") for name in result.stdout.split(b"\0") if name]
    paths = []
    for name in names:
        if name != "PROJECT_MANIFEST.json":
            source_path(name, root)
            paths.append(Path(name))
    if not paths or len(paths) != len(set(paths)):
        raise ValueError("Empty or ambiguous tracked-source inventory")
    return sorted(paths, key=lambda path: path.as_posix())


def canonical_source_bytes(relative: Path, root: Path | None = None) -> bytes:
    raw = source_path(relative.as_posix(), root).read_bytes()
    if relative.suffix.lower() in BINARY_SUFFIXES or b"\x00" in raw:
        return raw
    # Match .gitattributes text=eol=lf so the ledger is portable across
    # Windows worktrees and LF-normalized CI/source archives.
    return raw.replace(b"\r\n", b"\n")


def file_entry(relative: Path, root: Path | None = None) -> dict[str, str | int]:
    raw = canonical_source_bytes(relative, root)
    return {"path": relative.as_posix(), "size_bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest()}


def check_manifest(manifest: dict, properties: dict[str, str]) -> int:
    if (manifest.get("version") != properties.get("mod_version")
            or manifest.get("mod_id") != properties.get("mod_id")):
        raise ValueError("Project version/mod ID differs from Gradle properties")
    return check_file_ledger(manifest)


def check_file_ledger(manifest: dict, root: Path | None = None) -> int:
    """Shared LF-canonical source policy; never use for release asset hashes."""
    root = ROOT if root is None else root
    entries = manifest.get("files")
    if not isinstance(entries, list) or not entries:
        raise ValueError("Project source ledger must be a nonempty list")
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"path", "size_bytes", "sha256"}:
            raise ValueError("Malformed source ledger entry")
        name = entry["path"]
        source_path(name, root)
        if name in seen:
            raise ValueError("Duplicate source ledger path")
        seen.add(name)
        if type(entry["size_bytes"]) is not int or entry["size_bytes"] < 0:
            raise ValueError("Invalid source ledger size")
        if not isinstance(entry["sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]):
            raise ValueError("Invalid source ledger hash")
        if entry != file_entry(Path(name), root):
            raise ValueError(f"Source bytes differ from manifest: {name}")
    if (root / ".git").exists():
        if seen != {path.as_posix() for path in tracked_paths(root)}:
            raise ValueError("Manifest does not cover the exact Git source inventory")
    return len(entries)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify without Git or file writes")
    args = parser.parse_args(argv)
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"),
                              object_pairs_hook=reject_duplicate_keys)
        if not isinstance(manifest, dict):
            raise ValueError("Project manifest root must be an object")
        properties = read_properties(ROOT / "gradle.properties")
        if args.check:
            count = check_manifest(manifest, properties)
            print(f"PROJECT SOURCE MANIFEST: PASS / {count} files / read-only; not a release gate")
        else:
            manifest["version"] = properties["mod_version"]
            manifest["files"] = [file_entry(path) for path in tracked_paths()]
            temporary = MANIFEST_PATH.with_suffix(".json.tmp")
            temporary.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            temporary.replace(MANIFEST_PATH)
            print(f"PROJECT MANIFEST REFRESHED: {manifest['version']} / {len(manifest['files'])} tracked files")
    except (OSError, UnicodeError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        print(f"PROJECT SOURCE MANIFEST: FAIL / {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
