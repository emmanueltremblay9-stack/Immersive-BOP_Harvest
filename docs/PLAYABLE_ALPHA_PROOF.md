# Playable Alpha Proof

Date: 2026-06-23
Version: 0.1.1-alpha.3
Loader: NeoForge 21.1.233
Minecraft: 1.21.1
Mod ID: `immersive_bop_harvest`
Target instance: `C:\Users\Emmanuel Tremblay\AppData\Roaming\PrismLauncher\instances\1.21.1 TesT play`

## Scope

This alpha is a conservative data-compatibility build for Biomes O' Plenty,
Farmer's Delight, and Immersive Engineering. It adds generated recipes, common
tags, and data-driven loot modifiers. It does not add blocks, items, textures,
screen code, or custom runtime mechanics.

## Commands Run

```powershell
.\gradlew.bat --no-configuration-cache check --stacktrace
.\gradlew.bat --no-configuration-cache clean build --stacktrace
.\gradlew.bat --no-configuration-cache runGameTestServer --stacktrace
.\gradlew.bat --no-configuration-cache runData --stacktrace
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install_alpha_to_lab.ps1
```

All commands above exited with status 0 during the 2026-06-23 alpha.3 proof pass.

## Built Artifact

```text
C:\Users\Emmanuel Tremblay\AI Depot\Codex Documents\Immersive BOP_Harvest\build\libs\immersive_bop_harvest-0.1.1-alpha.3.jar
```

Size: 64,578 bytes
SHA-256: `2a143596de0a7e5896cba9fe5292212840fe2cedae78ac8b2bfc3a83a708a64c`

## Installed Artifact

```text
C:\Users\Emmanuel Tremblay\AppData\Roaming\PrismLauncher\instances\1.21.1 TesT play\minecraft\mods\immersive_bop_harvest-0.1.1-alpha.3.jar
```

Size: 64,578 bytes
SHA-256: `2a143596de0a7e5896cba9fe5292212840fe2cedae78ac8b2bfc3a83a708a64c`
Hash match: true
Previous installed version: `0.1.1-alpha.2`
Deleted old jar: `immersive_bop_harvest-0.1.1-alpha.2.jar`
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

Installed jar resource counts from `build/install-report.json`:

- Farmer's Delight cutting recipes: 64
- Immersive Engineering sawmill recipes: 39
- Direct-harvest loot modifiers: 19
- Direct-harvest loot tables: 19
- Common item tags: 2
- NeoForge global loot modifier index: present
- GameTest class: present
- Empty GameTest structure: present

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
- `runGameTestServer`: passed 2 required tests.
- Representative generated recipes asserted by GameTest:
  - `immersive_bop_harvest:cutting/barley`
  - `immersive_bop_harvest:sawmill/fir_log`
  - `immersive_bop_harvest:sawmill/stripped_fir`
- `runData`: loaded `immersive_bop_harvest` 0.1.1-alpha.3 and all required runtime dependency jars.

## Dedicated-Server Smoke

A bounded `runServer` smoke reached the server-ready signal and then the process
tree was stopped.

Evidence:

- `Loaded Immersive BOP_Harvest data compatibility`
- `DedicatedServer`: `Done`
- wrapper exit status: 0
- no remaining Gradle/Java process for this repo after cleanup

## Remaining Release Gates

- Public binary release is blocked until `LICENSE_DECISION_REQUIRED.md` is resolved.
- Live-client smoke has not been completed.
