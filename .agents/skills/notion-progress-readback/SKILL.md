---
name: notion-progress-readback
description: "Update Notion progress or project pages with precise anchors, then refetch and prove the intended block changed. Broader workflow: $codex-connector-readback-verifier."
---

# Notion Progress Readback

**Role:** Explicit specialist skill under `$codex-connector-readback-verifier`.

## When to use

Use this only when the request explicitly targets this narrow failure mode. For wider work, invoke `$codex-connector-readback-verifier` and treat this checklist as a focused phase.

Scope: Update Notion progress or project pages with precise anchors, then refetch and prove the intended block changed.

**Do not use:** Do not use this skill outside its stated scope; route broader work to the relevant canonical skill.

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

1. Fetch the target page/database and schema before writing.
2. Map exact property names, select values, relations, and block anchors.
3. Apply the smallest requested update with plain Markdown fallback when enhanced helpers are unavailable.
4. Refetch the target and verify Active Phase, Current Roadmap, status, risk, priority, and result links as applicable.
5. Report the exact changed properties or blocks.

## Scope-specific acceptance checks

- Directly satisfy this capability: Update Notion progress or project pages with precise anchors, then refetch and prove the intended block changed.
- Verify every named path, task, field, metadata value, resource family, or external record in the request.
- Record anything not found or not runnable as an explicit gap instead of guessing.
- Confirm that no excluded or unrelated area was changed.

## Required evidence

- schema snapshot.
- write result.
- readback values.
- target page identifiers.

## Guardrails

- Do not guess property names or select options.
- Do not treat tool success as proof without readback.
- Keep changes narrowly scoped and list every touched file or external record.
- Use direct evidence from files, command exits, hashes, logs, screenshots, or connector readback.
- State uncertainty and remaining risks; never convert an unrun check into a pass.

## Definition of done

- The requested change or analysis is complete within the confirmed scope.
- All mandatory verification steps ran successfully, or skipped/blocked steps are named with reasons.
- Exact changed files, commands, exit statuses, artifacts, hashes, screenshots, or connector readback are reported as applicable.
- Unrelated user changes remain intact.

## Related capabilities

Canonical parent: `$codex-connector-readback-verifier`
