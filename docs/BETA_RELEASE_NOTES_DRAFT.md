# Beta Release Notes Draft

This is a draft for the first public beta release. The artifact and deterministic
release gate are verified within the owner-selected reduced runtime-test scope.

## Immersive BOP_Harvest `0.1.1-alpha.9`

Immersive BOP_Harvest is a conservative compatibility addon for Biomes O'
Plenty, Farmer's Delight, and Immersive Engineering on Minecraft 1.21.1 with
NeoForge.

## Highlights

- Adds Farmer's Delight Cutting Board compatibility for scoped Biomes O' Plenty
  vegetation and wood.
- Adds Immersive Engineering Sawmill recipes for 13 Biomes O' Plenty wood
  families.
- Adds low-yield direct harvest data for selected fibrous plants and web-like
  blocks.
- Keeps native BOP shear behavior by excluding `#biomesoplenty:shears` from
  compatibility direct-harvest drops.
- Scopes every direct-harvest loot modifier to its matching BOP block loot table
  with `neoforge:loot_table_id`.
- Adds common tag compatibility for barley and toadstool.
- Adds manifest-ledger validation and expanded wood-processing compatibility
  coverage in the QA pass.
- Avoids new blocks, new items, copied assets, magic drops, free glowstone, and
  progression-breaking conversions.

## Requirements

- Minecraft `1.21.1`
- NeoForge `21.1.233` or newer in the same 21.1 line
- Biomes O' Plenty `21.1.0.14` or newer
- GlitchCore `2.1.0.2` or newer
- TerraBlender `4.1.0.8` or newer
- Farmer's Delight `1.3.2` or newer
- Immersive Engineering `12.4.2-194` or newer

## Verified In Private QA

- Specification validation passed with 181 compatibility coverage IDs.
- Generated-resource QA passed with 146 generated JSON files.
- Stale common-tag cleanup repro passed.
- Clean Gradle build passed.
- GameTest server passed 3 required tests, including all 103 generated recipe IDs
  and BOP shears-tag coverage.
- Datagen/runtime dependency load passed.
- Dedicated server smoke reached `Done`.
- Prism `1.21.1 TesT play` install was hash-verified.
- Installed JAR readback found 64 cutting recipes, 39 sawmill recipes, 19
  direct-harvest modifiers, 19 direct-harvest loot tables, 2 common item tags,
  and a direct-harvest `neoforge:loot_table_id` guard.
- The owner selected `All Rights Reserved`; redistribution and derivative use
  require prior written permission.

## Known Limits

- Fresh alpha.9 Prism client title-screen smoke is `NOT_PERFORMED / OWNER_WAIVED` and is not claimed as passed.
- Full gameplay/world interaction smoke was not performed in the latest pass.
- Client startup and full gameplay therefore remain explicit residual risks.

## Publication Checklist

Before publishing this draft:

1. Confirm the rebuilt jar metadata includes `All Rights Reserved`.
2. Confirm the alpha.9 automated/server evidence and owner client-smoke waiver are current.
3. Run `scripts/check_beta_release_gate.py` and require `BETA RELEASE GATE: PASS`.
4. Attach the rebuilt jar, checksum, dependency list, and final release notes.
