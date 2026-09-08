---
name: codex-final-report-evidence
description: "Require final reports to list changed files, commands, exit status, artifacts, validation evidence, and remaining risks. Broader workflow: $codex-final-evidence-reporter."
---

# Codex Final Report Evidence

**Role:** Explicit specialist skill under `$codex-final-evidence-reporter`.

## When to use

Use this only when the request explicitly targets this narrow failure mode. For wider work, invoke `$codex-final-evidence-reporter` and treat this checklist as a focused phase.

Scope: Require final reports to list changed files, commands, exit status, artifacts, validation evidence, and remaining risks.

**Do not use:** Do not use reporting structure as a substitute for executing required validation.

## Required inputs

- The exact requested outcome and exclusions.
- The authoritative repository, instance, page, database, log, jar, or artifact path.
- Applicable instruction files and the current dirty/remote state.
- The expected proof commands, fields, files, or readback target.

## Preflight

1. Re-read the newest user request, explicit exclusions, and any correction made after the original task.
2. Read applicable AGENTS.md/AGENTS.override.md files and the authoritative configuration or source files before editing.
3. Resolve the real repository or target root; do not write artifacts under Documents or OneDrive-backed Codex scratch folders.
4. Inspect git status or the connector target state and preserve unrelated user work.

## Workflow

1. Provide concise progress updates during long work without narrating low-level operations.
2. Track exact changed files, commands, exit codes, artifacts, hashes, readback evidence, and risks.
3. Generate clickable absolute local-file links for user-facing artifacts when supported.
4. Distinguish completed, partially verified, skipped, and blocked work.
5. Before finalizing, cross-check every completion claim against recorded evidence.

## Scope-specific acceptance checks

- Directly satisfy this capability: Require final reports to list changed files, commands, exit status, artifacts, validation evidence, and remaining risks.
- Verify every named path, task, field, metadata value, resource family, or external record in the request.
- Record anything not found or not runnable as an explicit gap instead of guessing.
- Confirm that no excluded or unrelated area was changed.

## Required evidence

- changed-file list.
- command ledger.
- artifact links.
- validation results.
- risk list.

## Guardrails

- Do not omit failed commands.
- Do not convert warnings into success or failure without classification.
- Do not cite evidence that was not actually produced.
- Keep changes narrowly scoped and list every touched file or external record.
- Use direct evidence from files, command exits, hashes, logs, screenshots, or connector readback.
- State uncertainty and remaining risks; never convert an unrun check into a pass.

## Definition of done

- The requested change or analysis is complete within the confirmed scope.
- All mandatory verification steps ran successfully, or skipped/blocked steps are named with reasons.
- Exact changed files, commands, exit statuses, artifacts, hashes, screenshots, or connector readback are reported as applicable.
- Unrelated user changes remain intact.

## Related capabilities

Canonical parent: `$codex-final-evidence-reporter`
