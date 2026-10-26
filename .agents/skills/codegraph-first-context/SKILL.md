---
name: codegraph-first-context
description: Use for any codebase/repository task. Query CodeGraph before broad grep/read exploration, then read only targeted files.
---

# CodeGraph First Context

## Trigger

Use this skill for repository work:
- audits,
- debugging,
- refactoring,
- build failures,
- modding projects,
- release tasks,
- architecture questions,
- tests,
- dependency analysis.

## Required first actions

```powershell
codegraph status --json
```

Then run a focused query:

```powershell
codegraph explore "<question about architecture, impact, entrypoints, dependencies, build, tests, or target feature>"
```

## Reading policy

1. Query CodeGraph first.
2. Use graph output to identify files/symbols.
3. Read only targeted files.
4. Use broad `rg` only when CodeGraph is missing data, stale, or ambiguous.
5. If pending changes exist, refresh/sync/index before trusting stale graph results.

## Good query examples

```text
Identify the client/server boundary, entrypoints, and classloading risks.
Identify build scripts, QA tasks, install scripts, and release metadata.
Find all tooltip rendering paths and config access paths.
Map the impact area for changing recipe viewer integration.
```

## Report requirements

Include:
- CodeGraph version/status,
- pending changes,
- whether reindex is recommended,
- query used,
- files read as a result,
- any stale/ambiguous graph limitations.
