# Playable Alpha Proof

Date: 2026-06-23
Version: 0.1.1-alpha.1
Loader: NeoForge 21.1.233
Minecraft: 1.21.1
Mod ID: `immersive_bop_harvest`

## Scope

This alpha is a conservative data-compatibility build for Biomes O' Plenty,
Farmer's Delight, and Immersive Engineering. It adds generated recipes, common
tags, and data-driven loot modifiers. It does not add blocks, items, textures,
screen code, or custom runtime mechanics.

## Commands Run

```powershell
python scripts\validate_specs.py
python scripts\generate_alpha_resources.py
.\gradlew.bat clean build --stacktrace
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install_alpha_to_lab.ps1
```

All commands above exited with status 0 during the 2026-06-23 alpha proof pass.

## Built Artifact

```text
C:\Users\Emmanuel Tremblay\AI Depot\Codex Documents\Immersive BOP_Harvest\build\libs\immersive_bop_harvest-0.1.1-alpha.1.jar
```

Size: 62,394 bytes
SHA-256: `a7e776f242828bd75c356edc5a22890e2428be05ac1eabd04ca63898600dcf1e`

## Installed Artifact

```text
C:\Users\Emmanuel Tremblay\AppData\Roaming\PrismLauncher\instances\1.21.1 TesT LaB\minecraft\mods\immersive_bop_harvest-0.1.1-alpha.1.jar
```

Size: 62,394 bytes
SHA-256: `a7e776f242828bd75c356edc5a22890e2428be05ac1eabd04ca63898600dcf1e`
Hash match: true
Remaining installed jars for `immersive_bop_harvest`: 1

## Runtime Dependencies

The installer verified and installed these required BOP-side dependencies in the
same Prism LAB mods directory:

- `biomesoplenty` 21.1.0.13
- `glitchcore` 2.1.0.2
- `terrablender` 4.1.0.8

The installer also verified exactly one installed jar for existing required
dependencies:

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

Installed metadata requires:

- NeoForge `[21.1.233,)`
- Minecraft `[1.21.1]`
- GlitchCore `[2.1.0.2,)`
- TerraBlender `[4.1.0.8,)`
- Biomes O' Plenty `[21.1.0.13,)`
- Farmer's Delight `[1.3.2,)`
- Immersive Engineering `[12.4.2-194,)`

## Remaining Release Gates

- Public binary release is blocked until `LICENSE_DECISION_REQUIRED.md` is resolved.
- Live-client smoke has not been completed.
- Dedicated-server smoke has not been completed.
- No GameTests exist yet for recipe or loot-modifier behavior.
