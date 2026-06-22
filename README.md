# Immersive BOP_Harvest

**Status:** professional implementation package / pre-development specification  
**Target:** Minecraft 1.21.1, NeoForge  
**Mod ID:** `immersive_bop_harvest`

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
- `templates/` — neutral metadata templates
- `scripts/validate_specs.py` — specification validator

## Validate the package

```bash
python scripts/validate_specs.py
```

## Release gate

The project must pass every item in `docs/QA_ACCEPTANCE.md`.  
A software license must be selected before publication.

## Branding assets

The package keeps the original vector project mark and branding guide. Raster
PNG assets from the source pack were intentionally omitted from this repo pass.

- vector SVG logo;
- branding guide.

See `docs/BRANDING_GUIDE.md`.
