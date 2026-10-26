---
name: gradle-modrinth-curseforge-release-audit
description: Read-only audit of Gradle and distribution-release configuration with evidence-backed checks and bounded remediation.
---

# Gradle Distribution Release Audit

## Scope
Use for Immersive BOP_Harvest release-configuration reviews. This skill is audit-only unless a separate active task explicitly authorizes source remediation.

Never create or publish a GitHub Release, upload to a distribution service, change secrets, or weaken an existing release gate.

## Workflow
1. Read the current repository instructions and exact task boundary.
2. Inspect Gradle release settings, distribution workflow files, release manifests, publisher tests, and release documentation that are relevant to the claim.
3. Compare expected identity, versions, artifact metadata, dependency relations, permissions, retention, and release-state gates against current evidence.
4. Prefer current workspace or connector readback over stale summaries; label historical evidence as historical.
5. Classify each checkpoint PASS, FAIL, PARTIAL, BLOCKED, NOT_APPLICABLE, or NOT_AUTHORIZED.
6. Recommend only the smallest source-side remediation inside the confirmed task scope.

## Validation
- Tie every conclusion to an inspected file, command result, artifact, or connector readback.
- Keep publication and credential-bearing operations outside this skill.
- Do not turn a template rejection, fixture result, historical CI run, or waived runtime check into live publication proof.
- Report unrun checks as unrun.

## Output
Report the audited surface, evidence used, checkpoint status, blockers, and next authorized verification step.
