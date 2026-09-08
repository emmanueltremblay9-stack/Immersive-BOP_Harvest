---
name: codex-final-report-completeness-linter
description: Check final repository reports for required status, files, commands, validation evidence, artifacts, blockers, and risks.
---

# Codex Final Report Completeness Linter

## Scope
Use before sending a final report for Immersive BOP_Harvest repository work. This skill validates reporting completeness only; it cannot turn missing execution into evidence.

## Checklist
1. Require an explicit result status.
2. Require exact changed files or directories when changes occurred.
3. Require each executed validation command or connector action to have a result or exit status.
4. Distinguish executed, skipped, blocked, not applicable, and not authorized work.
5. Require artifacts or remote records to be named only when their existence was read back.
6. Require remaining risks, unresolved integration gates, and preserved user work to be stated.
7. Check that publication authority and runtime/artifact readiness are not overstated.
8. Check that no credential value or derived secret is included in the report.

## Pass criteria
The report is concise, every material completion claim has evidence, and every missing proof remains explicitly missing.

## Output
Return missing or weak fields and the corrected report structure. Never invent validation results.
