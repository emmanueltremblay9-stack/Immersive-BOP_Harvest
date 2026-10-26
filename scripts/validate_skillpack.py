#!/usr/bin/env python3
"""Validate the repository-scoped Codex sidekick pack."""

from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOTS = (ROOT / ".agents" / "skills", ROOT / ".codex" / "skills")
SOURCE_COMMIT = "612d6ca9ca2fdeed30f0a99395d44dba1956aa1e"
EXPECTED = {
    "agents-instruction-conflict-audit": "5e4096a8e36832662e363cfcf4e3eca280204df8",
    "codegraph-first-context": "202cad533f058de574f7676052244d06cee4bbc0",
    "manual-prompt-scope-guard": "35b2e67ff6acc732dd741b9d106fa583a91fa310",
    "minecraft-project-scanner": "70d4d8daeeae957d15fa9a212550369ef645ba43",
    "gradle-modrinth-curseforge-release-audit": "66c402b6d0f87a4d6868e71cb7a32d1091e28e8e",
    "github-release-artifact-verifier": "8a11a984eeab4038fc0dabccde9ab7fb57f21d0c",
    "github-actions-permission-audit": "a576226eea5755a507aa8129afb1974c5458a899",
    "github-actions-secret-scope-audit": "64ca49aba938c46d3b177f7aab5ed371623c8e29",
    "github-actions-artifact-retention-audit": "f64cc1c08225580083365e2c026608a344ef74b5",
    "config-template-drift-audit": "5fc36e8c78f656fb84abcf97155ac8a59a41fec0",
    "notion-progress-readback": "365bc8135833e8649a629db61f7e9980e71fea43",
    "codex-final-report-evidence": "33d2c0dff2840dfbda0b8f1a5adac9d8785c1a1e",
    "codex-final-report-completeness-linter": "87c35eedc300b3f9536b6402ebda57e04f217e13",
}


def canonical(data: bytes) -> bytes:
    """Normalize checkout line endings to repository LF semantics."""
    return data.replace(b"\r\n", b"\n")


def git_blob_sha(data: bytes) -> str:
    data = canonical(data)
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def frontmatter(data: bytes) -> dict[str, str]:
    text = canonical(data).decode("utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ValueError("missing opening YAML frontmatter delimiter")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError("missing closing YAML frontmatter delimiter") from exc
    values: dict[str, str] = {}
    for line in lines[1:end]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        values[key.strip()] = value
    return values


def main() -> int:
    errors: list[str] = []
    observed: dict[tuple[Path, str], bytes] = {}

    for skill_root in SKILL_ROOTS:
        if not skill_root.is_dir():
            errors.append(f"missing skill root: {skill_root.relative_to(ROOT)}")
            continue

        for child in sorted(p for p in skill_root.iterdir() if p.is_dir()):
            skill_file = child / "SKILL.md"
            if not skill_file.is_file():
                errors.append(f"missing SKILL.md: {skill_file.relative_to(ROOT)}")
                continue
            try:
                meta = frontmatter(skill_file.read_bytes())
            except (OSError, UnicodeError, ValueError) as exc:
                errors.append(f"invalid frontmatter {skill_file.relative_to(ROOT)}: {exc}")
                continue
            if meta.get("name") != child.name:
                errors.append(
                    f"folder/name mismatch {skill_file.relative_to(ROOT)}: "
                    f"frontmatter={meta.get('name')!r}"
                )
            if not meta.get("description", "").strip():
                errors.append(f"missing description: {skill_file.relative_to(ROOT)}")

        for skill, expected_sha in EXPECTED.items():
            skill_file = skill_root / skill / "SKILL.md"
            if not skill_file.is_file():
                errors.append(f"missing required skill: {skill_file.relative_to(ROOT)}")
                continue
            data = canonical(skill_file.read_bytes())
            observed[(skill_root, skill)] = data
            try:
                meta = frontmatter(data)
            except (UnicodeError, ValueError) as exc:
                errors.append(f"invalid frontmatter {skill_file.relative_to(ROOT)}: {exc}")
                continue
            if meta.get("name") != skill:
                errors.append(
                    f"required name mismatch {skill_file.relative_to(ROOT)}: "
                    f"frontmatter={meta.get('name')!r}"
                )
            if not meta.get("description", "").strip():
                errors.append(f"missing required description: {skill_file.relative_to(ROOT)}")
            actual_sha = git_blob_sha(data)
            if actual_sha != expected_sha:
                errors.append(
                    f"blob drift {skill_file.relative_to(ROOT)}: "
                    f"expected={expected_sha} actual={actual_sha}"
                )

    if all(root.is_dir() for root in SKILL_ROOTS):
        left, right = SKILL_ROOTS
        for skill in EXPECTED:
            a = observed.get((left, skill))
            b = observed.get((right, skill))
            if a is not None and b is not None and a != b:
                errors.append(f"mirror drift: {skill}")

    manifest = ROOT / "docs" / "skills" / "MANIFEST.md"
    if not manifest.is_file():
        errors.append("missing docs/skills/MANIFEST.md")
    else:
        text = manifest.read_text(encoding="utf-8")
        if SOURCE_COMMIT not in text:
            errors.append("manifest missing pinned source commit")
        for skill, expected_sha in EXPECTED.items():
            if skill not in text or expected_sha not in text:
                errors.append(f"manifest missing identity for {skill}")

    if errors:
        print("skillpack: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"skillpack: PASS ({len(EXPECTED)} required skills x {len(SKILL_ROOTS)} mirrored roots)")
    print(f"source depot commit: {SOURCE_COMMIT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
