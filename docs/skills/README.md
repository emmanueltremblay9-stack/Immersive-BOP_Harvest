# Repository-scoped Codex sidekicks

Immersive BOP_Harvest vendors the 13 project-required sidekick skills in both supported repository-local roots:

- `.agents/skills/<name>/SKILL.md`
- `.codex/skills/<name>/SKILL.md`

The canonical source snapshot is the private `emmanueltremblay9-stack/Private-Skill-Depot` commit `612d6ca9ca2fdeed30f0a99395d44dba1956aa1e`.

This is a **repository-scoped installation**. It does not claim that a separate user-global `$HOME/.agents/skills` or Codex desktop installation was modified.

## Required invocation order

1. `agents-instruction-conflict-audit`
2. `codegraph-first-context`
3. `manual-prompt-scope-guard`
4. `minecraft-project-scanner`
5. `gradle-modrinth-curseforge-release-audit`
6. `github-release-artifact-verifier`
7. `github-actions-permission-audit`
8. `github-actions-secret-scope-audit`
9. `github-actions-artifact-retention-audit`
10. `config-template-drift-audit`
11. `notion-progress-readback`
12. `codex-final-report-evidence`
13. `codex-final-report-completeness-linter`

Read and apply a skill only when its trigger is relevant. CodeGraph remains first-choice repository context when a healthy callable CodeGraph is available; otherwise use the documented targeted-read fallback and report that limitation.

## Provenance and project hardening

Eleven skills are byte-identical to the pinned depot blobs. Two definitions are intentionally project-hardened because verbatim connector writes were rejected during installation:

- `gradle-modrinth-curseforge-release-audit`: retains release-configuration audit semantics while making the no-publication boundary explicit.
- `codex-final-report-completeness-linter`: retains evidence/completeness linting while removing ambiguous action language.

`MANIFEST.md` records the installed Git blob SHA for every skill. `scripts/validate_skillpack.py` verifies both roots, frontmatter, folder/name agreement, expected Git blob identity, and mirror parity.

## Maintenance

Do not edit one mirror independently. Stage an updated definition, validate it, write the same blob to both roots, update `MANIFEST.md` and the validator's expected SHA map, then run:

```text
python scripts/validate_skillpack.py
```

Skill installation does not grant publication, secret mutation, branch-protection mutation, or gameplay-change authority.
