---
name: config-template-drift-audit
description: Use to compare `.env.example`, config docs, defaults, and runtime config keys.
---

# Config Template Drift Audit

## When to use

Use this skill when:

- A change adds, removes, or renames configuration keys.
- Runtime errors suggest missing env vars or stale examples.
- Docs, templates, and actual config parsing may be inconsistent.

Do not use this skill for resolving actual secret values in local environments.

## Inputs

- Config parser code and defaults.
- Template files such as `.env.example` or sample YAML.
- Documentation pages.
- Runtime validation errors.

## Workflow

1. **Inventory configuration keys from parser code, schemas, templates, and docs.**
2. **Compare required, optional, deprecated, and defaulted keys across sources.**
3. **Flag missing template entries, stale docs, renamed keys, and inconsistent default values.**
4. **Avoid exposing real local secret values; use key names only.**
5. **Patch the source of truth first, then templates/docs as needed.**
6. **Run config validation or startup check when possible.**

## Validation

Pass criteria:

- Templates and docs match runtime key names.
- Required versus optional status is clear.
- Defaults are consistent or intentionally different.
- No secret values are printed.

## Output

Produce:

- Config drift table.
- Patch recommendations.
- Validation command results.
- Migration notes for renamed keys.

## Failure modes

- Dynamic config keys: document pattern instead of enumerating falsely.
- Multiple environments differ: separate by environment.
- No docs exist: propose minimal template update.
- Secret appears in logs: redact before reporting.

## Maintenance notes

- Pair with local env precedence audit when actual value resolution matters.
- Keep examples non-secret and minimal.
