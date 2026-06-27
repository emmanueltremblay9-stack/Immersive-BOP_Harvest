# Beta Release Notes Draft

This is a draft for the first public beta release. Do not publish it until the
license gate is resolved and a rebuilt, license-correct jar is verified.

## Immersive BOP_Harvest `0.1.1-alpha.5`

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
- Adds common tag compatibility for barley and toadstool.
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

- Specification validation passed.
- Generated-resource QA passed with 146 generated JSON files.
- Clean Gradle build passed.
- GameTest server passed 3 required tests, including all 103 generated recipe IDs
  and BOP shears-tag coverage.
- Datagen/runtime dependency load passed.
- Dedicated server smoke reached `Done`.
- Prism `1.21.1 TesT play` install was hash-verified.
- Installed JAR readback found 19 direct-harvest modifiers, 19
  `#biomesoplenty:shears` exclusions, and 0 stale `#c:tools/shear` references.

## Known Limits

- Fresh alpha.5 Prism client title-screen smoke is still open; the CLI opened
  the Test play console but did not spawn Minecraft during this pass.
- Full gameplay/world interaction smoke was not performed in the latest pass.
- Public release is blocked until the owner selects and applies a license.

## Publication Checklist

Before publishing this draft:

1. Replace this draft note with the chosen license name.
2. Confirm the rebuilt jar metadata includes that license.
3. Run `scripts/check_beta_release_gate.py` and require `BETA RELEASE GATE: PASS`.
4. Attach the rebuilt jar, checksum, dependency list, and final release notes.
