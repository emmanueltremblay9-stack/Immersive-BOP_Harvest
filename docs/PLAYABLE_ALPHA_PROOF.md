# Playable Alpha Proof

Date: 2026-06-23
Version: 0.1.1-alpha.4
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
python scripts\validate_specs.py
.\gradlew.bat --no-configuration-cache compileJava --stacktrace
.\gradlew.bat --no-configuration-cache check --stacktrace
.\gradlew.bat --no-configuration-cache clean build --stacktrace
.\gradlew.bat --no-configuration-cache runGameTestServer --stacktrace
.\gradlew.bat --no-configuration-cache runData --stacktrace
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install_alpha_to_lab.ps1
```

All commands above exited with status 0 during the 2026-06-23 alpha.4 proof pass.

## Built Artifact

```text
C:\Users\Emmanuel Tremblay\AI Depot\Codex Documents\Immersive BOP_Harvest\build\libs\immersive_bop_harvest-0.1.1-alpha.4.jar
```

Size: 66,042 bytes
SHA-256: `067275f2467feec22813f7ad868cc2d809e95435e5299e645400e634f30c7da7`

## Installed Artifact

```text
C:\Users\Emmanuel Tremblay\AppData\Roaming\PrismLauncher\instances\1.21.1 TesT play\minecraft\mods\immersive_bop_harvest-0.1.1-alpha.4.jar
```

Size: 66,042 bytes
SHA-256: `067275f2467feec22813f7ad868cc2d809e95435e5299e645400e634f30c7da7`
Hash match: true
Previous installed version: `0.1.1-alpha.3`
Deleted old jar: `immersive_bop_harvest-0.1.1-alpha.3.jar`
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
- `allGeneratedRecipesLoad`: asserted all 103 generated recipe IDs.
- `runData`: loaded `immersive_bop_harvest` 0.1.1-alpha.4 and all required runtime dependency jars.

## Dedicated-Server Smoke

A bounded `runServer` smoke reached the server-ready signal and then the process
tree was stopped.

Evidence:

- `Loaded Immersive BOP_Harvest data compatibility`
- `DedicatedServer`: `Done`
- wrapper exit status: 0
- output log: `build\runServer-smoke-alpha4-20260623-175911.out.log`
- no remaining Java server process for this repo after cleanup

## Live-Client Title-Screen Smoke

The actual Prism `1.21.1 TesT play` instance was launched with the installed
alpha.4 jar. The corrected quoted launch reached late startup markers and a
visible Minecraft title-screen window.

Evidence:

- launched through Prism Launcher CLI with the full quoted instance name
- active log path:
  `C:\Users\Emmanuel Tremblay\AppData\Roaming\PrismLauncher\instances\1.21.1 TesT play\minecraft\logs\latest.log`
- log discovered `immersive_bop_harvest-0.1.1-alpha.4.jar` in the Test play `mods` directory
- mod list included `Immersive BOP_Harvest 0.1.1-alpha.4 (immersive_bop_harvest)`
- runtime log emitted `Loaded Immersive BOP_Harvest data compatibility`
- runtime log reached `Sound engine started`
- runtime log created `minecraft:textures/atlas/gui.png-atlas`
- window title: `Minecraft NeoForge* 1.21.1`
- screenshot: `build\live-client-smoke\test-play-client-alpha4-title-20260623-224522.png`
- screenshot SHA-256: `59976d1143562be432f5e7ccdcb0e30bc59159a3c50cbfd7291e4d47c16b2532`
- no new crash report was written during the alpha.4 client smoke attempts
- process cleanup stopped Minecraft/Prism processes for the Test play launch

## Remaining Release Gates

- Public binary release is blocked until `LICENSE_DECISION_REQUIRED.md` is resolved.
- Full gameplay/world interaction smoke was not performed in this pass.
