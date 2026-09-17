---
name: github-actions-artifact-retention-audit
description: Use to audit actions artifact retention in GitHub workflows with evidence-backed checks and bounded remediation.
---

# Github Actions Artifact Retention Audit

## When to use

Use this skill when:

- A task explicitly mentions `github-actions-artifact-retention-audit` behavior, github actions artifact retention audit, or the same workflow intent.
- The request requires you to audit actions artifact retention in GitHub workflows with evidence-backed checks and bounded remediation.
- A completion claim would be weak without targeted inspection, validation, and concrete evidence.

Do not use this skill for ordinary one-turn answers that do not require tool routing, safety checks, repository inspection, or evidence reconciliation.

## Inputs

- Latest user request, active constraints, available tools, workspace state, and prior task evidence.
- Relevant files, command outputs, connector readbacks, logs, screenshots, artifacts, or package metadata.
- Safety, privacy, path, source authority, output-format, and final-report requirements.

## Workflow

1. **Define the actions artifact retention surface, expected behavior, and files or external targets in scope.**
2. **Inspect the real repository, connector, runtime, or artifact state before making claims.**
3. **Build a compact coverage matrix of expected state versus observed state.**
4. **Run the narrowest credible validation command, readback, log parse, or comparison available.**
5. **Classify findings as pass, fail, partial, blocked, or not applicable with evidence for each.**
6. **Report remediation steps without expanding beyond the confirmed task scope.**

## Validation

Pass criteria:

- The relevant files, commands, tool outputs, screenshots, or connector readbacks were inspected before conclusions were made.
- The workflow distinguishes proven facts from assumptions, skipped checks, unsupported inferences, and stale evidence.
- Validation commands, logs, traces, artifacts, or readbacks are tied to the exact claim they support.
- The final output gives concrete paths, affected surfaces, risks, and next verification steps without overstating certainty.

## Output

Produce:

- Github Actions Artifact Retention Audit finding summary.
- Files, commands, tools, or artifacts inspected.
- Pass/fail/partial status with evidence.
- Risks, assumptions, and focused remediation or validation steps.

## Failure modes

- Required files or tools are missing: report the missing evidence and use the safest narrower fallback.
- Evidence conflicts across sources: prefer real workspace state and recent readback over stale summaries.
- Validation is too expensive or unsafe: state the omitted check and provide a bounded alternative.
- The scope grows beyond the request: freeze the current scope and defer unrelated findings to risks or follow-up notes.

## Maintenance notes

- This skill was generated from a compact backlog slug; refine examples and edge cases after the first real workflow use.
- Keep trigger wording aligned with nearby skills so routing stays narrow and non-duplicative.
- Preserve compatibility with both `.agents/skills` and `.codex/skills` mirrored roots.
