# Changelog

## [0.1.1-alpha.10] - qualification in progress

- Use a fresh alpha version for the authorized S4/S5 qualification passes.
- Add a separate test harness for decoded recipes, actual Cutting Board
  processing, sawmill process/save state, harvest tools and native loot.
- Authenticate CI candidate evidence against the exact GitHub run and archive.
- Add disposable production-loader client/server, formed-machine, multiplayer,
  reconnect and in-flight save/migration qualification with strict CI readback.
- S4 canonical CI passed 305 GameTests. The complete seven-phase local S5
  packet passed with byte-bound receipts; canonical S5 CI/readback is pending.
  The historical alpha.9 client waiver does not apply to this candidate.

## [Unreleased automation] - 2026-09-05

- Share LF-canonical source-ledger checks across refresh and beta validation.
- Add explicit historical metadata in publisher schema 3 for guarded type transitions.
- Add strict stable-candidate bundle checks and Windows regression CI; stable runtime remains unqualified.

- Add a reusable fail-closed CurseForge publisher and inherited/portability regressions.
- Add schema 2 first-publication and previous-public-file manifests, explicit empty relations, exact-tag durable state, and non-production CI.
- Correct current handoff authority and resolved-license wording without changing gameplay or version.
- Integrate the verified CurseForge target project ID `1609013`, slug `immersive-bop-harvest`, and existing public file baseline `8426397`; no GitHub tag/release or CurseForge upload is authorized in this change. Publication remains gated because no canonical GitHub Release/approved versioned manifest exists and the public relation readback is still empty.


## [0.1.1-alpha.9] - 2026-07-13

### Fixed
- Prevented stale generated common item tags from surviving removal from the tag specification.
- Required all BOP wood-processing IDs in the compatibility coverage inventory.
- Scoped every direct-harvest modifier to its matching native BOP block loot table.
- Hardened the beta release checker so malformed ledger entries become blockers instead of crashes.
- Rejected manifest ledger paths that resolve outside the project root.
- Added regression coverage for valid, malformed and path-escaping manifest entries.

### Added
- Added the owner-selected `All Rights Reserved` license and synchronized NeoForge metadata.
- Added the owner-provided 1024 x 1024 PNG as the README/project logo.
- Packaged that exact PNG as `immersive_bop_harvest_logo.png` and declared it with `logoFile`.
- Added deterministic manifest-ledger refresh and bounded dedicated-server smoke scripts.

### Changed
- Bumped the final verification build to `0.1.1-alpha.9`; the intermediate alpha.8 install was not reused after runtime-logo integration.
- Expanded the compatibility inventory/matrix with the 65 BOP wood-processing scope IDs.

### Verified
- Resource generation was byte-for-byte stable across two successive runs.
- Specification validation passed with 181 coverage IDs.
- Generated-resource QA passed with 146 JSON files.
- Seven release-checker regression tests passed, including explicit owner-waiver acceptance and fail-closed rejection cases.
- Clean Gradle build, `runData` and all 3 required GameTests passed.
- Dedicated-server smoke reached `Done (` with alpha.9 loaded; bounded termination is reported separately.
- Source and installed JARs are 1,607,220 bytes with matching SHA-256 `20110892574faabf2fd2c47807ade1eca38ab0b2b248ac8187bdbf779c1c61cc`.
- Installed metadata reports alpha.9 and `All Rights Reserved`; exactly one project JAR remains.
- Packaged logo SHA-256 matches the owner attachment: `8f88fdedc1872f35814227472d5b84c157411d0e506c6cfb5c1d75af2dcda31a`.
- Final deterministic checker returned exit `0` and `BETA RELEASE GATE: PASS` under the explicit owner waiver.

### Owner-selected test scope
- The owner explicitly instructed Codex to skip the fresh alpha.9 Prism title-screen test phase.
- Client title-screen smoke is recorded as `NOT_PERFORMED / OWNER_WAIVED`, never as a pass.
- Full gameplay/world interaction smoke was not performed and remains a documented residual risk.
- The release checker now fails closed unless an unperformed client smoke has a complete explicit waiver record.

## [0.1.1-alpha.7] - 2026-07-05

### Fixed
- Fixed generated direct-harvest global loot modifiers so each modifier is scoped to its matching Biomes O' Plenty block loot table with `neoforge:loot_table_id`.
- This prevents additive knife/sword compatibility drops from being eligible outside the intended BOP block loot table when loot context conditions overlap.

### Added
- Added generator support for direct-harvest loot-table-id conditions.
- Added generated-resource QA coverage requiring every direct-harvest modifier to declare the expected `biomesoplenty:blocks/<block>` loot table id.

### Changed
- Bumped the private Test play build from `0.1.1-alpha.6` to `0.1.1-alpha.7`.
- Regenerated all 19 direct-harvest loot modifiers with the new loot-table-id guard.

### Verified
- `python scripts/generate_alpha_resources.py`
- `python scripts/validate_specs.py`
- `python scripts/qa_alpha_resources.py`
- `.\gradlew.bat compileJava processResources --stacktrace`
- `.\gradlew.bat clean build --stacktrace`
- `.\gradlew.bat runData --stacktrace`
- `.\gradlew.bat runGameTestServer --stacktrace`
- bounded `.\gradlew.bat --no-daemon runServer --stacktrace` smoke reached `Done` with alpha.7 loaded.
- private Prism Test play install with matching source/target SHA-256 and one installed jar for this mod.
- installed JAR readback: metadata version `0.1.1-alpha.7`, 64 Cutting Board recipes, 39 Sawmill recipes, 19 direct-harvest modifiers, 19 direct-harvest loot tables, 2 common item tags, and `webbing.json` starting with `neoforge:loot_table_id`.

### Known release blockers
- Public binary release still needs a license decision.
- Fresh alpha.7 Prism client title-screen smoke is not claimed.
- Full gameplay/world interaction smoke was not performed in this pass.

## [0.1.1-alpha.6] - 2026-06-28

### Fixed
- Fixed generated common-tag cleanup so stale `data/c/tags/item/*.json` files are removed when they are no longer declared in `spec/tag_integrations.json`.
- Fixed the spec coverage gate to require wood recipe-scope IDs in the compatibility inventory.
- Fixed the beta release checker so `PROJECT_MANIFEST.json` verifies its file ledger and rejects impossible self-hash entries.

### Added
- Added 65 wood-processing rows to the compatibility matrix for log, wood, stripped variants, and plank recipe-scope IDs.

### Changed
- Bumped the private Test play build from `0.1.1-alpha.5` to `0.1.1-alpha.6`.
- Updated project proof docs and manifest evidence for the alpha.6 build/install pass.

### Verified
- `python scripts/validate_specs.py`
- `python scripts/generate_alpha_resources.py`
- `python scripts/qa_alpha_resources.py`
- `.\\gradlew.bat --no-configuration-cache check --stacktrace`
- `.\\gradlew.bat --no-configuration-cache runGameTestServer --stacktrace`
- `.\\gradlew.bat --no-configuration-cache runData --stacktrace`
- `.\\gradlew.bat --no-configuration-cache clean build --stacktrace`
- private Prism Test play install with matching source/target SHA-256 and one installed jar for this mod.
- installed JAR readback: metadata version `0.1.1-alpha.6`, 64 Cutting Board recipes, 39 Sawmill recipes, 19 direct-harvest modifiers, 19 direct-harvest loot tables, 2 common item tags, and no stale repro tag.
- bounded dedicated-server smoke reached `Done` with alpha.6 loaded.

### Known release blockers
- Public binary release still needs a license decision.
- Fresh alpha.6 Prism client title-screen smoke is not claimed.
- Full gameplay/world interaction smoke was not performed in this pass.

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
