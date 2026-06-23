# Changelog

## [0.1.1-alpha.3] - 2026-06-23

### Added
- Added `scripts/qa_alpha_resources.py` as a deterministic generated-resource QA gate.
- Added `scripts/sync_runtime_deps.ps1` and Gradle `syncRuntimeDeps` wiring for local Test play runtime dependencies.
- Added GameTests for server runtime boot and representative generated recipe loading.
- Added the empty GameTest structure template required by `runGameTestServer`.
- Added beta release audit, legal reuse inventory, release notes draft, and `scripts/check_beta_release_gate.py`.
- Hardened the beta release checker with built-jar hash, installed-jar hash, source/install equality, and duplicate installed-jar metadata checks.

### Changed
- Updated the private install target to the `1.21.1 TesT play` Prism modpack.
- Updated Biomes O' Plenty compatibility metadata to `21.1.0.14`.
- Hardened install-script hashing with .NET SHA-256/SHA-512 calculation.

### Verified
- `.\gradlew.bat --no-configuration-cache check --stacktrace`
- `.\gradlew.bat --no-configuration-cache clean build --stacktrace`
- `.\gradlew.bat --no-configuration-cache runGameTestServer --stacktrace`
- `.\gradlew.bat --no-configuration-cache runData --stacktrace`
- private Prism Test play install with matching source/target SHA-256 and one installed jar for this mod.
- bounded dedicated-server smoke reached `Done`.
- Prism Test play live-client smoke reached the Minecraft title screen with `immersive_bop_harvest` 0.1.1-alpha.3 loaded.
- `python scripts/check_beta_release_gate.py` reports the expected license blockers while built/install hash proof and duplicate installed-jar checks pass.

### Known release blockers
- Public binary release still needs a license decision.
- Full gameplay/world interaction smoke was not performed in this pass.

## [0.1.1-alpha.1] - 2026-06-23

### Added
- Bootstrapped the NeoForge 1.21.1 Gradle project and minimal mod entrypoint.
- Generated playable-alpha Farmer's Delight Cutting Board recipes from `spec/*.json`.
- Generated playable-alpha Immersive Engineering Sawmill recipes for BOP wood families.
- Generated data-driven direct-harvest loot modifiers and compatibility loot tables.
- Added common item tags for BOP barley and toadstool.
- Added `scripts/generate_alpha_resources.py` for repeatable resource generation.
- Added `scripts/install_alpha_to_lab.ps1` for Prism LAB install proof and dependency verification.

### Verified
- `python scripts/validate_specs.py`
- generated JSON parse check
- `.\gradlew.bat clean build --stacktrace`
- private Prism LAB install with matching source/target SHA-256 and one installed jar for this mod.

### Known release blockers
- Public binary release still needs a license decision.
- Live-client and dedicated-server smoke tests remain open.

## [0.1.0] - Planned

### Added
- Original branding asset set: logo, icons, banners, page backgrounds and branding guide.
- Conservative BOP/Farmer's Delight Cutting Board compatibility.
- BOP wood stripping with Farmer's Delight tree bark.
- BOP wood processing in the Immersive Engineering Sawmill.
- Low-yield knife harvesting for selected grasses, shrubs and fibrous blocks.
- Common-tag integration for BOP barley and toadstool.
- Automated specification validation.
- English and French metadata templates.

### Explicitly excluded
- New items or blocks.
- Garden Cloche, Crusher, Squeezer and Fermenter recipes.
- Hemp fiber or hemp seeds from unrelated vegetation.
- Rare, magical, metal, gem, mob or dimension-specific resource shortcuts.
