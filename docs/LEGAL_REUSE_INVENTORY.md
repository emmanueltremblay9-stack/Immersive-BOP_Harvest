# Legal Reuse Inventory

Date: 2026-06-23
Project: Immersive BOP_Harvest
Version audited: `0.1.1-alpha.3`

## Release Status

Public binary release is blocked until the project owner selects a software
license and the chosen license is applied consistently.

Current blocker:
- `gradle.properties` has `mod_license=LICENSE_PENDING`.
- No `LICENSE` file is present.
- The installed alpha.3 jar was built with `license="LICENSE_PENDING"`.

## Authored Project Material

The following material is original project content in this repository:

- Java entrypoint and GameTest code under `src/main/java/`.
- Project specs under `spec/`.
- Generated data resources under `src/main/resources/`.
- Build scripts and QA scripts under `scripts/`.
- Documentation under `docs/`, `README.md`, `CHANGELOG.md`, and
  `VALIDATION_REPORT.txt`.
- Vector branding under `assets/branding/`.

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

The project logo and banner are original vector SVG assets:

- `assets/branding/transparent/immersive_bop_harvest_logo_vector.svg`
- `assets/branding/cover/immersive_bop_harvest_banner_vector.svg`

PNG assets from the source pack remain omitted per scope correction: `forget .png`.

## Required Before Public Binary Release

1. Owner selects the project license.
2. Add the chosen `LICENSE` file.
3. Set `mod_license` in `gradle.properties`.
4. Rebuild the jar so `META-INF/neoforge.mods.toml` contains the chosen license.
5. Reinstall and verify the rebuilt jar in Prism `1.21.1 TesT play`.
6. Update README, changelog, Notion, and release metadata with the chosen license.
7. Re-run `scripts/check_beta_release_gate.py` and require a passing result.
