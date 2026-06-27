# Immersive BOP_Harvest

- **Status:** private Test play install verified / alpha.5 live-client smoke still pending
- **Target:** Minecraft 1.21.1, NeoForge
- **Mod ID:** `immersive_bop_harvest`
- **Current alpha:** `0.1.1-alpha.5`

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
- `scripts/qa_alpha_resources.py` — generated-resource QA gate
- `scripts/sync_runtime_deps.ps1` — local runtime dependency sync from the configured Prism modpack
- `scripts/install_alpha_to_lab.ps1` — Windows Test play install and hash proof script
- `scripts/check_beta_release_gate.py` — public beta release gate checker with built/installed jar hash and duplicate install checks
- Gradle wrapper and NeoForge build files

## Build and validate

```powershell
python scripts/validate_specs.py
python scripts/generate_alpha_resources.py
.\gradlew.bat --no-configuration-cache check
.\gradlew.bat --no-configuration-cache clean build
.\gradlew.bat --no-configuration-cache runGameTestServer
.\gradlew.bat --no-configuration-cache runData
```

## Install to Prism Test play

The current private NeoForge 1.21.1 modpack target is:

```text
C:\Users\Emmanuel Tremblay\AppData\Roaming\PrismLauncher\instances\1.21.1 TesT play\minecraft\mods
```

Install and verify the project jar plus required runtime dependencies:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install_alpha_to_lab.ps1
```

The script writes `build/install-report.json` with source and installed SHA-256
values, metadata readback, dependency proof, and remaining-jar counts.

## Release gate

The project must pass every item in `docs/QA_ACCEPTANCE.md`.  
A software license must be selected before publication.

Current alpha proof is recorded in `docs/PLAYABLE_ALPHA_PROOF.md`.
The current release audit is recorded in `docs/BETA_RELEASE_AUDIT.md`.
Legal provenance is recorded in `docs/LEGAL_REUSE_INVENTORY.md`.
Draft public notes are in `docs/BETA_RELEASE_NOTES_DRAFT.md`.

Run the release gate checker before any public beta upload:

```powershell
python scripts/check_beta_release_gate.py
```

Public binary release remains blocked until the license decision is complete and
the checker reports `BETA RELEASE GATE: PASS`.

Current alpha.5 note: generated direct-harvest drops are covered by spec QA, GameTest,
installed-JAR readback, and dedicated-server smoke. The fresh Prism CLI client smoke
opened the Test play instance console but did not spawn a Minecraft JVM, so alpha.5
client title-screen proof is not claimed.

## Branding assets

The package keeps the original vector project mark and branding guide. Raster
PNG assets from the source pack were intentionally omitted from this repo pass.

- vector SVG logo;
- branding guide.

See `docs/BRANDING_GUIDE.md`.
