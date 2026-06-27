# Changelog

## [0.1.1-alpha.5] - 2026-06-27

### Fixed
- Fixed direct-harvest shears exclusion to use BOP's actual `#biomesoplenty:shears` item tag instead of the unsupported `#c:tools/shear` tag in the current Test play stack.

### Added
- Added a GameTest assertion that BOP's shears tag includes vanilla shears.
- Added generated-resource QA coverage to reject `#c:tools/shear` in direct-harvest loot modifiers.

### Changed
- Bumped the private Test play build from `0.1.1-alpha.4` to `0.1.1-alpha.5`.
- Regenerated all 19 direct-harvest loot modifiers so shears keep native BOP behavior while knife/sword compatibility drops remain active.

### Verified
- `python scripts/validate_specs.py`
- `python scripts/generate_alpha_resources.py`
- `python scripts/qa_alpha_resources.py`
- `.\\gradlew.bat --no-configuration-cache compileJava --stacktrace`
- `.\\gradlew.bat --no-configuration-cache check --stacktrace`
- `.\\gradlew.bat --no-configuration-cache runGameTestServer --stacktrace`
- `.\\gradlew.bat --no-configuration-cache clean build --stacktrace`
- `.\\gradlew.bat --no-configuration-cache runData --stacktrace`
- private Prism Test play install with matching source/target SHA-256 and one installed jar for this mod.
- installed JAR readback: 19 direct-harvest modifiers, 19 `#biomesoplenty:shears` exclusions, 0 `#c:tools/shear` references.
- bounded dedicated-server smoke reached `Done` with alpha.5 loaded.

### Known release blockers
- Public binary release still needs a license decision.
- Fresh alpha.5 Prism client smoke was attempted, but Prism opened the Test play console and did not spawn a Minecraft JVM; no alpha.5 title-screen proof is claimed.
- Full gameplay/world interaction smoke was not performed in this pass.

## [0.1.1-alpha.4] - 2026-06-23

### Added
- Expanded GameTest recipe coverage: `allGeneratedRecipesLoad` now checks all 103 generated recipe IDs at runtime.

### Changed
- Bumped the private Test play build from `0.1.1-alpha.3` to `0.1.1-alpha.4`.
- Recorded corrected Prism title-screen visual proof for the alpha.4 Test play install.

### Verified
- `python scripts/validate_specs.py`
- `.\\gradlew.bat --no-configuration-cache compileJava --stacktrace`
- `.\\gradlew.bat --no-configuration-cache check --stacktrace`
- `.\\gradlew.bat --no-configuration-cache clean build --stacktrace`
- `.\\gradlew.bat --no-configuration-cache runGameTestServer --stacktrace`
- `.\\gradlew.bat --no-configuration-cache runData --stacktrace`
- private Prism Test play install with matching source/target SHA-256 and one installed jar for this mod.
- bounded dedicated-server smoke reached `Done` with alpha.4 loaded.
- Prism Test play client log-marker smoke discovered `immersive_bop_harvest-0.1.1-alpha.4.jar`, listed `Immersive BOP_Harvest 0.1.1-alpha.4`, logged `Loaded Immersive BOP_Harvest data compatibility`, and reached `Sound engine started` without writing a new crash report.
- Prism Test play title-screen capture verified the `Minecraft NeoForge* 1.21.1` window at `build\live-client-smoke\test-play-client-alpha4-title-20260623-224522.png`.
- `python scripts/check_beta_release_gate.py` reports the expected license blockers while alpha.4 built/install hash proof and duplicate installed-jar checks pass.

### Known release blockers
- Public binary release still needs a license decision.
- Full gameplay/world interaction smoke was not performed in this pass.

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
