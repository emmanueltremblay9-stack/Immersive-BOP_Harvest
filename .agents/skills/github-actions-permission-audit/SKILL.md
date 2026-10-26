---
name: github-actions-permission-audit
description: Use to review GitHub Actions token permissions, fork safety, secrets exposure, and artifact access.
---

# GitHub Actions Permission Audit

## When to use

Use this skill when:

- The user asks to review GitHub Actions token permissions, fork safety, secrets exposure, and artifact access.
- A repository, connector, runtime, or artifact decision depends on workflow permissions, pull_request versus pull_request_target, secrets usage, artifact upload/download, and fork trust boundaries.
- The task needs explicit evidence before editing, reporting, deleting, validating, or publishing.

Do not use this skill when a narrower existing skill already covers the whole workflow or when the user supplied a single explicit command that only needs to be run as-is.

## Inputs

- User request, active constraints, and relevant project or connector scope.
- Files, configs, logs, tool results, artifacts, screenshots, or workflow definitions related to GitHub Actions Permission.
- Before/after state when the task involves edits, generated output, runtime validation, or release artifacts.
- Available validation commands, sandbox limits, approval mode, and evidence requirements.

## Workflow

1. **Resolve scope.** Identify the exact paths, commands, services, tool calls, or runtime objects covered by this audit.
2. **Establish source of truth.** Prefer real files, tool schemas, command output, and readback evidence over assumptions or stale summaries.
3. **Inspect checkpoints.** Review workflow permissions, pull_request versus pull_request_target, secrets usage, artifact upload/download, and fork trust boundaries and note any missing, renamed, stale, or conflicting evidence.
4. **Compare expected versus observed behavior.** Separate intentional changes from accidental drift, stale output, environment mismatch, or generated noise.
5. **Classify risk.** Mark each finding as blocker, warning, informational, or not applicable, with the smallest useful validation step.
6. **Route the fix or report.** Send generated-file issues to generators, runtime issues to smoke tests, connector issues to schema/readback checks, and repo issues to targeted commands.

## Validation

Pass criteria:

- The audit scope is explicit and does not silently include unrelated files or sessions.
- Evidence is current, attributable to the relevant command, file, connector object, or runtime state.
- Findings distinguish PASS, FAIL, PARTIAL, and not-applicable states.
- Recommended follow-up commands or edits are minimal, reproducible, and tied to observed evidence.

## Output

Produce:

- Scope summary.
- Checkpoint results for workflow permissions, pull_request versus pull_request_target, secrets usage, artifact upload/download, and fork trust boundaries.
- Risk classification and affected files, commands, or artifacts.
- Recommended validation or remediation steps.

## Failure modes

- Required files or tool output are unavailable: report `PARTIAL` and list the missing evidence.
- Evidence appears stale or from the wrong session: discard it and reacquire current proof before relying on it.
- Generated or derived output differs from source files: route edits to the source generator instead of patching generated output directly.
- A destructive or external action would be required: stop at preflight unless the user explicitly authorized that action.

## Maintenance notes

- Keep trigger wording narrow so this skill does not overlap broad validation, final reporting, or command-running skills.
- Update checkpoints when the related platform, framework, Minecraft/NeoForge version, or connector behavior changes.
