# Legal Reuse Inventory

Date: 2026-07-13 owner license decision
Project: Immersive BOP_Harvest
Version audited: `0.1.1-alpha.9`

## Release Status

The project owner selected `All Rights Reserved` on 2026-07-13.

Current state:
- `gradle.properties` has `mod_license=All Rights Reserved`.
- `LICENSE` records the proprietary terms and third-party ownership disclaimer.
- The alpha.9 JAR must be rebuilt and inspected before publication evidence can
  claim that the installed metadata contains the selected license.

## Authored Project Material

The following material is original project content in this repository:

- Java entrypoint and GameTest code under `src/main/java/`.
- Project specs under `spec/`.
- Generated data resources under `src/main/resources/`.
- Build scripts and QA scripts under `scripts/`.
- Documentation under `docs/`, `README.md`, `CHANGELOG.md`, and
  `VALIDATION_REPORT.txt`.
- Owner-provided PNG and original vector branding under `assets/branding/`.

## Third-Party Material

No third-party source code, textures, models, sounds, logos, fonts, or binary
assets from Biomes O' Plenty, Farmer's Delight, Immersive Engineering, NeoForge,
Minecraft, or related dependencies are copied into this repository.

The project references third-party registry IDs, mod IDs, dependency metadata,
and public runtime APIs only.

Runtime dependencies are not redistributed by this repository. They are expected
to be installed separately in the Prism test instance or by the end user.

## Generated Resources

Generated recipes, tags, loot modifiers, and loot tables are generated from the
repo-owned specification files. They reference dependency item and block IDs but
do not copy dependency JSON files.

The project intentionally avoids:
- writing files under `data/biomesoplenty/`;
- dependency texture or model reuse;
- new items or blocks;
- progression-breaking conversion recipes;
- magic drops, free glowstone, or hemp shortcuts.

## Branding

The project branding consists of the owner-provided PNG project logo and the
original vector SVG logo/banner:

- `assets/branding/immersive_bop_harvest_logo.png`
- `assets/branding/transparent/immersive_bop_harvest_logo_vector.svg`
- `assets/branding/cover/immersive_bop_harvest_banner_vector.svg`

## Required Before Public Binary Release

1. Rebuild the alpha.9 jar so `META-INF/neoforge.mods.toml` contains `All Rights Reserved`.
2. Reinstall and verify the rebuilt jar in Prism `1.21.1 TesT play`.
3. Update README, changelog, Notion, and release metadata with the selected license.
4. Re-run `scripts/check_beta_release_gate.py` and require a passing result.
