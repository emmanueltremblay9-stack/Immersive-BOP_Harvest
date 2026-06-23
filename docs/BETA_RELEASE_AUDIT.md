# Beta Release Audit

Date: 2026-06-23
Project: Immersive BOP_Harvest
Version: `0.1.1-alpha.3`
Base pushed commit before this audit: `9b1613f63bdbfeacc96dc8c6e029fb54741a2c5a`

## Current Result

The project is a beta QA candidate. The technical proof stack is strong enough
to continue release preparation, but public binary release remains blocked by
the unresolved license decision.

## Proven Technical Gates

| Gate | Status | Evidence |
|---|---|---|
| Specification validation | Passed | `python scripts/validate_specs.py` |
| Generated-resource QA | Passed | `.\\gradlew.bat --no-configuration-cache check --stacktrace` and `qaAlphaResources` |
| Clean build | Passed | `.\\gradlew.bat --no-configuration-cache clean build --stacktrace` |
| GameTests | Passed | `.\\gradlew.bat --no-configuration-cache runGameTestServer --stacktrace`, 2 required tests |
| Datagen/runtime dependency load | Passed | `.\\gradlew.bat --no-configuration-cache runData --stacktrace` |
| Dedicated server smoke | Passed | bounded `runServer` smoke reached `Done` |
| Test play install | Passed | source and installed SHA-256 matched |
| Remaining installed jars | Passed | checker scans installed jars by embedded `modId` and finds exactly 1 jar for `immersive_bop_harvest` |
| Live client smoke | Passed | Prism `1.21.1 TesT play` reached title screen with alpha.3 loaded |
| Notion project paper | Passed | page readback includes current proof, icon, and banner |
| Branding | Passed | original vector logo and vector banner are present |

## Current Installed Artifact

Installed jar:

```text
C:\Users\Emmanuel Tremblay\AppData\Roaming\PrismLauncher\instances\1.21.1 TesT play\minecraft\mods\immersive_bop_harvest-0.1.1-alpha.3.jar
```

SHA-256:

```text
2a143596de0a7e5896cba9fe5292212840fe2cedae78ac8b2bfc3a83a708a64c
```

The installed jar metadata currently reports version `0.1.1-alpha.3`.

## Blocking Gate

License is not selected.

Evidence:
- `gradle.properties` contains `mod_license=LICENSE_PENDING`.
- `LICENSE_DECISION_REQUIRED.md` is still present.
- No `LICENSE` file exists.

This is a release blocker, not a technical test failure. The project owner must
choose the license before any public binary release.

## Work Remaining For Public Beta Release

1. Owner chooses a license.
2. Add `LICENSE`.
3. Update `mod_license`.
4. Rebuild, reinstall, and hash-verify a new jar after the license change.
5. Re-run `scripts/check_beta_release_gate.py`.
6. Update Notion and release notes with the chosen license.
7. Tag and publish only after the checker passes.

## Known Residual Risk

The live-client proof reached the Minecraft title screen. A full gameplay/world
interaction smoke was not performed in this pass. That is useful before broad
release, but it is separate from the currently blocking license decision.
