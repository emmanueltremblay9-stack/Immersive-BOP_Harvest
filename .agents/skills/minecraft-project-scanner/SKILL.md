---
name: minecraft-project-scanner
description: Inspect a Minecraft mod repository and summarize loader, versions, dependencies, GUI libraries, data assets, and validation commands.
---

# Minecraft Project Scanner

Use before any Minecraft mod edit or when onboarding to an unfamiliar codebase.

## Operating rules
- Inspect the existing project before proposing code.
- Identify Minecraft version, loader, Java version, mappings, source sets, and dependencies before editing.
- Keep client-only rendering/GUI code out of common/server paths.
- Prefer official/current docs for version-sensitive APIs.
- Do not publish, push, upload, or run token-bearing tasks without explicit approval.
- Prefer smallest reliable validation first, then wider runtime tests.

## Procedure
1. Run or adapt `scripts/scan_minecraft_project.py <repo>`.
2. Read build files and mod metadata directly; do not rely only on the scanner.
3. Report likely loader(s), Minecraft version, Java version, mappings, API deps, GUI/config/recipe viewer deps, and source-set layout.
4. Identify whether `runClient`, datagen, test, publish, or release tasks exist.
5. Flag unknown install scripts, suspicious hooks, leaked tokens, or broad publish tasks.

## Output
- Project type and confidence.
- Version matrix.
- Dependency matrix.
- GUI/rendering architecture.
- Build/test commands.
- Risks and unanswered questions.
