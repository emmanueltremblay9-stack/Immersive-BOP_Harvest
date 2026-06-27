# Playable Alpha Proof

Date: 2026-06-27
Version: 0.1.1-alpha.5
Loader: NeoForge 21.1.233
Minecraft: 1.21.1
Mod ID: `immersive_bop_harvest`
Target instance: `C:\Users\Emmanuel Tremblay\AppData\Roaming\PrismLauncher\instances\1.21.1 TesT play`

## Scope

This alpha is a conservative data-compatibility build for Biomes O' Plenty,
Farmer's Delight, and Immersive Engineering. It adds generated recipes, common
tags, and data-driven loot modifiers. It does not add blocks, items, textures,
screen code, or custom runtime mechanics.

## Alpha.5 Fix

Direct-harvest modifiers previously excluded shears with `#c:tools/shear`.
The installed BOP stack exposes shears through `#biomesoplenty:shears`, so the
old exclusion could allow compatibility drops during native BOP shear behavior.

Alpha.5 regenerates all 19 direct-harvest modifiers with
`#biomesoplenty:shears`, adds QA to reject `#c:tools/shear`, and adds a GameTest
that asserts BOP's shears tag contains vanilla shears.

## Commands Run

```powershell
python scripts\validate_specs.py
python scripts\generate_alpha_resources.py
python scripts\qa_alpha_resources.py
.\gradlew.bat --no-configuration-cache compileJava --stacktrace
.\gradlew.bat --no-configuration-cache check --stacktrace
.\gradlew.bat --no-configuration-cache runGameTestServer --stacktrace
.\gradlew.bat --no-configuration-cache clean build --stacktrace
.\gradlew.bat --no-configuration-cache runData --stacktrace
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install_alpha_to_lab.ps1
```

All commands above exited with status 0 during the 2026-06-27 alpha.5 proof pass.

## Built Artifact

```text
C:\Users\Emmanuel Tremblay\AI Depot\Codex Documents\Immersive BOP_Harvest\build\libs\immersive_bop_harvest-0.1.1-alpha.5.jar
```

Size: 66,516 bytes
SHA-256: `74c61d8965598afc6646c58d739e85f83e00dcf14a2e3b677368ea480a9120f8`

## Installed Artifact

```text
C:\Users\Emmanuel Tremblay\AppData\Roaming\PrismLauncher\instances\1.21.1 TesT play\minecraft\mods\immersive_bop_harvest-0.1.1-alpha.5.jar
```

Size: 66,516 bytes
SHA-256: `74c61d8965598afc6646c58d739e85f83e00dcf14a2e3b677368ea480a9120f8`
Hash match: true
Previous installed version: `0.1.1-alpha.4`
Deleted old jar: `immersive_bop_harvest-0.1.1-alpha.4.jar`
Remaining installed jars for `immersive_bop_harvest`: 1

## Runtime Dependencies

The installer verified exactly one installed jar for each required dependency in
the same Prism Test play mods directory:

- `biomesoplenty` 21.1.0.14
- `glitchcore` 2.1.0.2
- `terrablender` 4.1.0.8
- `farmersdelight` 1.3.2
- `immersiveengineering` 12.4.2-194

## Jar Contents

Installed jar resource counts from `build/install-report.json` and zip readback:

- Farmer's Delight cutting recipes: 64
- Immersive Engineering sawmill recipes: 39
- Direct-harvest loot modifiers: 19
- Direct-harvest loot tables: 19
- Common item tags: 2
- NeoForge global loot modifier index: present
- GameTest class: present
- Empty GameTest structure: present
- Direct-harvest shears exclusions: 19 `#biomesoplenty:shears`, 0 `#c:tools/shear`

Installed metadata requires:

- NeoForge `[21.1.233,)`
- Minecraft `[1.21.1]`
- GlitchCore `[2.1.0.2,)`
- TerraBlender `[4.1.0.8,)`
- Biomes O' Plenty `[21.1.0.14,)`
- Farmer's Delight `[1.3.2,)`
- Immersive Engineering `[12.4.2-194,)`

## Automated QA

- `qaAlphaResources`: passed with 146 generated JSON files.
- `runGameTestServer`: passed 3 required tests.
- `allGeneratedRecipesLoad`: asserted all 103 generated recipe IDs.
- `bopShearsTagContainsVanillaShears`: asserted BOP's shears tag includes vanilla shears.
- Direct-harvest spec readback: 19 spec block IDs, 19 generated modifiers, 19 generated loot tables, 0 missing files.
- `runData`: loaded `immersive_bop_harvest` 0.1.1-alpha.5 and all required runtime dependency jars.

## Dedicated-Server Smoke

A bounded `runServer` smoke reached the server-ready signal and then the process
tree was stopped.

Evidence:

- `Loaded Immersive BOP_Harvest data compatibility`
- alpha.5 marker present in the run log
- `DedicatedServer`: `Done`
- Java-only cleanup readback exit status: 0
- output log: `build\runServer-smoke-alpha5-20260627-163738.out.log`
- no remaining Java server process for this repo after cleanup

## Live-Client Title-Screen Smoke

Fresh alpha.5 client title-screen proof is not claimed.

The Prism CLI run identified `1.21.1 TesT play`, refreshed auth, resolved the
instance, and opened the Prism instance console, but it did not spawn a new
Minecraft JVM and did not update the Test play `latest.log`. No new crash report
was written during the attempt.

The previous visual title-screen proof remains alpha.4-only:
`build\live-client-smoke\test-play-client-alpha4-title-20260623-224522.png`.

## Remaining Release Gates

- Public binary release is blocked until `LICENSE_DECISION_REQUIRED.md` is resolved.
- Fresh alpha.5 live-client title-screen smoke remains open.
- Full gameplay/world interaction smoke was not performed in this pass.
