# Beta Release Audit

Date: 2026-06-27
Project: Immersive BOP_Harvest
Version: `0.1.1-alpha.5`

## Current Result

The project has complete generated drop coverage for the current spec and a
hash-verified private Test play alpha.5 install. It is not ready for public beta
release yet.

Public binary release is blocked by the unresolved license decision and by the
fresh alpha.5 client-smoke gap.

## Proven Technical Gates

| Gate | Status | Evidence |
|---|---|---|
| Specification validation | Passed | `python scripts/validate_specs.py` |
| Generated-resource QA | Passed | `python scripts/qa_alpha_resources.py` and `.\\gradlew.bat --no-configuration-cache check --stacktrace` |
| Direct-harvest drop coverage | Passed | 19 spec block IDs, 19 modifiers, 19 loot tables, 0 missing |
| Shears exclusion bug fix | Passed | installed JAR has 19 `#biomesoplenty:shears` references and 0 `#c:tools/shear` references |
| Clean build | Passed | `.\\gradlew.bat --no-configuration-cache clean build --stacktrace` |
| GameTests | Passed | `.\\gradlew.bat --no-configuration-cache runGameTestServer --stacktrace`, 3 required tests, all 103 generated recipe IDs checked |
| Datagen/runtime dependency load | Passed | `.\\gradlew.bat --no-configuration-cache runData --stacktrace` |
| Dedicated server smoke | Passed | bounded `runServer` smoke reached `Done` with alpha.5 loaded |
| Test play install | Passed | source and installed SHA-256 matched |
| Remaining installed jars | Passed | installer and checker find exactly 1 jar for `immersive_bop_harvest` |
| Branding | Passed | original vector logo and vector banner are present |
| Fresh alpha.5 client title-screen smoke | Open | Prism opened the Test play console but did not spawn a Minecraft JVM |

## Current Installed Artifact

Installed jar:

```text
C:\Users\Emmanuel Tremblay\AppData\Roaming\PrismLauncher\instances\1.21.1 TesT play\minecraft\mods\immersive_bop_harvest-0.1.1-alpha.5.jar
```

SHA-256:

```text
74c61d8965598afc6646c58d739e85f83e00dcf14a2e3b677368ea480a9120f8
```

The installed jar metadata currently reports version `0.1.1-alpha.5`.

## Blocking Gates

License is not selected.

Evidence:
- `gradle.properties` contains `mod_license=LICENSE_PENDING`.
- `LICENSE_DECISION_REQUIRED.md` is still present.
- No `LICENSE` file exists.
- The installed alpha.5 jar was built with `license="LICENSE_PENDING"`.

Fresh alpha.5 client smoke is not complete.

Evidence:
- Prism CLI identified `1.21.1 TesT play` and opened the instance console.
- No new Minecraft JVM spawned for the alpha.5 client-smoke attempt.
- The Test play `latest.log` was not updated by that attempt.
- Crash report count stayed 19, so no new crash report was written.

## Work Remaining For Public Beta Release

1. Owner chooses a license.
2. Add `LICENSE`.
3. Update `mod_license`.
4. Rebuild, reinstall, and hash-verify a new jar after the license change.
5. Complete fresh client title-screen smoke on the rebuilt jar.
6. Re-run `scripts/check_beta_release_gate.py`.
7. Update Notion and release notes with the chosen license and final proof.
8. Tag and publish only after the checker passes.

## Known Residual Risk

A full gameplay/world interaction smoke was not performed in this pass. That is
separate from generated drop coverage, which is complete for the current spec.
