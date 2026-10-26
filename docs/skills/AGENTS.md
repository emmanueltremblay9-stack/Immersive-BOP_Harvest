# docs/skills scope

These instructions apply only under `docs/skills/`.

- Root repository instructions remain authoritative for project scope, validation, Git integration, secrets, and publication boundaries.
- Treat `MANIFEST.md` as the repository-scoped sidekick inventory and provenance record.
- Do not change a skill in only one install root.
- When a skill definition changes, keep `.agents/skills/<name>/SKILL.md` and `.codex/skills/<name>/SKILL.md` byte-identical, update the expected Git blob identity in `MANIFEST.md` and `scripts/validate_skillpack.py`, and run the validator.
- Preserve the required invocation order unless the project task specification explicitly changes it.
- Do not use skill maintenance to authorize gameplay changes, release creation, publication, secret changes, or branch/protection changes.
