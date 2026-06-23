# Immersive BOP_Harvest

- **Status:** playable alpha source project / private LAB install verified
- **Target:** Minecraft 1.21.1, NeoForge
- **Mod ID:** `immersive_bop_harvest`
- **Current alpha:** `0.1.1-alpha.1`

## Purpose

A conservative compatibility addon connecting Biomes O' Plenty vegetation and wood to Farmer's Delight and Immersive Engineering.

The project deliberately avoids speculative or progression-breaking conversions. It adds:

- Farmer's Delight Cutting Board parity for BOP flowers;
- modest straw, stick, string and rotten-flesh processing;
- knife/sword harvest behavior for a narrow set of fibrous blocks;
- Farmer's Delight tree-bark stripping for BOP wood;
- Immersive Engineering Sawmill parity for 13 BOP wood families;
- common-tag compatibility for barley and toadstool.

It does **not** add new items, blocks, textures, magical drops, hemp from unrelated plants, free glowstone, mob drops from decorative blocks, or automation recipes.

## Package contents

- `00_START_HERE.txt` — handoff instructions
- `01_CODEX_MASTER_PROMPT.txt` — implementation prompt
- `docs/` — design, architecture, QA and release controls
- `spec/` — machine-readable source of truth
- `src/main/resources/` — generated playable-alpha data resources
- `src/main/templates/` — NeoForge metadata template
- `src/main/java/` — minimal NeoForge entrypoint
- `templates/` — neutral metadata templates
- `scripts/validate_specs.py` — specification validator
- `scripts/generate_alpha_resources.py` — source-to-resource generator
- `scripts/install_alpha_to_lab.ps1` — Windows LAB install and hash proof script
- Gradle wrapper and NeoForge build files

## Build and validate

```powershell
python scripts/validate_specs.py
python scripts/generate_alpha_resources.py
.\gradlew.bat clean build
```

## Install to Prism LAB

The default private NeoForge 1.21.1 LAB target is:

```text
C:\Users\Emmanuel Tremblay\AppData\Roaming\PrismLauncher\instances\1.21.1 TesT LaB\minecraft\mods
```

Install and verify the project jar plus required BOP runtime dependencies:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install_alpha_to_lab.ps1
```

The script writes `build/install-report.json` with source and installed SHA-256
values, metadata readback, dependency proof, and remaining-jar counts.

## Release gate

The project must pass every item in `docs/QA_ACCEPTANCE.md`.  
A software license must be selected before publication.

Current alpha proof is recorded in `docs/PLAYABLE_ALPHA_PROOF.md`.

## Branding assets

The package keeps the original vector project mark and branding guide. Raster
PNG assets from the source pack were intentionally omitted from this repo pass.

- vector SVG logo;
- branding guide.

See `docs/BRANDING_GUIDE.md`.
