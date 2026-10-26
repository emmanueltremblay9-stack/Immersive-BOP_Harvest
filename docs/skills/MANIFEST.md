# Required sidekick manifest

Source depot: `emmanueltremblay9-stack/Private-Skill-Depot`

Pinned source commit: `612d6ca9ca2fdeed30f0a99395d44dba1956aa1e`

Install roots: `.agents/skills` and `.codex/skills`

The SHA column is the installed Git blob object ID used identically by both roots. It is an object-identity check, not a replacement for release-artifact SHA-256 requirements elsewhere in the project.

| Order | Skill | Source mode | Installed Git blob SHA |
|---:|---|---|---|
| 1 | `agents-instruction-conflict-audit` | pinned depot verbatim | `5e4096a8e36832662e363cfcf4e3eca280204df8` |
| 2 | `codegraph-first-context` | pinned depot verbatim | `202cad533f058de574f7676052244d06cee4bbc0` |
| 3 | `manual-prompt-scope-guard` | pinned depot verbatim | `35b2e67ff6acc732dd741b9d106fa583a91fa310` |
| 4 | `minecraft-project-scanner` | pinned depot verbatim | `70d4d8daeeae957d15fa9a212550369ef645ba43` |
| 5 | `gradle-modrinth-curseforge-release-audit` | project-hardened from pinned depot definition | `66c402b6d0f87a4d6868e71cb7a32d1091e28e8e` |
| 6 | `github-release-artifact-verifier` | pinned depot verbatim | `8a11a984eeab4038fc0dabccde9ab7fb57f21d0c` |
| 7 | `github-actions-permission-audit` | pinned depot verbatim | `a576226eea5755a507aa8129afb1974c5458a899` |
| 8 | `github-actions-secret-scope-audit` | pinned depot verbatim | `64ca49aba938c46d3b177f7aab5ed371623c8e29` |
| 9 | `github-actions-artifact-retention-audit` | pinned depot verbatim | `f64cc1c08225580083365e2c026608a344ef74b5` |
| 10 | `config-template-drift-audit` | pinned depot verbatim | `5fc36e8c78f656fb84abcf97155ac8a59a41fec0` |
| 11 | `notion-progress-readback` | pinned depot verbatim | `365bc8135833e8649a629db61f7e9980e71fea43` |
| 12 | `codex-final-report-evidence` | pinned depot verbatim | `33d2c0dff2840dfbda0b8f1a5adac9d8785c1a1e` |
| 13 | `codex-final-report-completeness-linter` | project-hardened from pinned depot definition | `87c35eedc300b3f9536b6402ebda57e04f217e13` |

## Invariants

- All 13 names must exist under both roots.
- A skill folder name must equal its YAML frontmatter `name`.
- YAML frontmatter must contain a non-empty `description`.
- Both root copies must be byte-identical and have the listed Git blob identity.
- Extra repository-local skills are allowed only if separately authorized; this manifest does not delete or overwrite unrelated skill packs.
- This skillpack grants no gameplay, publication, secret, release, or protection-setting authority.
