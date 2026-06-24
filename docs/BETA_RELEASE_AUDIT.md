# Beta Release Audit

Date: 2026-06-23
Project: Immersive BOP_Harvest
Version: `0.1.1-alpha.4`
Base pushed commit before this title-screen proof update: `6314f3e30d66d4ce40b3d660c7b253e6694b32bb`

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
| GameTests | Passed | `.\\gradlew.bat --no-configuration-cache runGameTestServer --stacktrace`, 2 required tests, all 103 generated recipe IDs checked |
| Datagen/runtime dependency load | Passed | `.\\gradlew.bat --no-configuration-cache runData --stacktrace` |
| Dedicated server smoke | Passed | bounded `runServer` smoke reached `Done` |
| Test play install | Passed | source and installed SHA-256 matched |
| Remaining installed jars | Passed | checker scans installed jars by embedded `modId` and finds exactly 1 jar for `immersive_bop_harvest` |
| Live client title-screen smoke | Passed | Prism `1.21.1 TesT play` loaded alpha.4 by log markers and wrote no new crash report |
| Alpha.4 visual title-screen screenshot | Passed | `build\live-client-smoke\test-play-client-alpha4-title-20260623-224522.png` shows the `Minecraft NeoForge* 1.21.1` title window |
| Notion project paper | Passed | page readback includes current proof, icon, and banner |
| Branding | Passed | original vector logo and vector banner are present |

## Current Installed Artifact

Installed jar:

```text
C:\Users\Emmanuel Tremblay\AppData\Roaming\PrismLauncher\instances\1.21.1 TesT play\minecraft\mods\immersive_bop_harvest-0.1.1-alpha.4.jar
```

SHA-256:

```text
067275f2467feec22813f7ad868cc2d809e95435e5299e645400e634f30c7da7
```

The installed jar metadata currently reports version `0.1.1-alpha.4`.

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

A full gameplay/world interaction smoke was not performed in this pass. That is
useful before broad release, but it is separate from the currently blocking
license decision.
