---
name: manual-prompt-scope-guard
description: "Handle large Notion or manual prompts with explicit exclusions, restate excluded scope, and execute only the remaining work. Broader workflow: $codex-user-rescope-pivot."
---

# Manual Prompt Scope Guard

**Role:** Explicit specialist skill under `$codex-user-rescope-pivot`.

## When to use

Use this only when the request explicitly targets this narrow failure mode. For wider work, invoke `$codex-user-rescope-pivot` and treat this checklist as a focused phase.

Scope: Handle large Notion or manual prompts with explicit exclusions, restate excluded scope, and execute only the remaining work.

**Do not use:** Do not expand the request beyond the newest confirmed scope.

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

1. Identify the newest user request and every explicit inclusion, exclusion, correction, and language-specific command.
2. Restate the active scope and excluded items internally before executing.
3. Discard assumptions and queued work invalidated by the correction.
4. Execute only the remaining scope and keep progress updates aligned with it.
5. Before finalizing, verify that no excluded item was modified or claimed.

## Scope-specific acceptance checks

- Directly satisfy this capability: Handle large Notion or manual prompts with explicit exclusions, restate excluded scope, and execute only the remaining work.
- Verify every named path, task, field, metadata value, resource family, or external record in the request.
- Record anything not found or not runnable as an explicit gap instead of guessing.
- Confirm that no excluded or unrelated area was changed.

## Required evidence

- active-scope statement.
- exclusion list.
- touched-file/output comparison.

## Guardrails

- Do not carry stale scope across compaction or resume.
- Do not reinterpret 'ne pas inclure' as optional.
- Keep changes narrowly scoped and list every touched file or external record.
- Use direct evidence from files, command exits, hashes, logs, screenshots, or connector readback.
- State uncertainty and remaining risks; never convert an unrun check into a pass.

## Definition of done

- The requested change or analysis is complete within the confirmed scope.
- All mandatory verification steps ran successfully, or skipped/blocked steps are named with reasons.
- Exact changed files, commands, exit statuses, artifacts, hashes, screenshots, or connector readback are reported as applicable.
- Unrelated user changes remain intact.

## Related capabilities

Canonical parent: `$codex-user-rescope-pivot`
