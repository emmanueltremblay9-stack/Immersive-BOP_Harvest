# Playable Alpha Proof

Date: 2026-07-13
Version: `0.1.1-alpha.9`

## Build and Install

- Clean Gradle build: PASS, exit `0`.
- Built JAR: `build/libs/immersive_bop_harvest-0.1.1-alpha.9.jar`.
- Installed JAR: `C:\Users\Emmanuel Tremblay\AppData\Roaming\PrismLauncher\instances\1.21.1 TesT play\minecraft\mods\immersive_bop_harvest-0.1.1-alpha.9.jar`.
- Source and installed size: `1607220` bytes.
- Source and installed SHA-256: `20110892574faabf2fd2c47807ade1eca38ab0b2b248ac8187bdbf779c1c61cc`.
- Hash match: `true`.
- Remaining installed project JARs: `1`.

## Metadata and Branding

- Mod ID: `immersive_bop_harvest`.
- License: `All Rights Reserved`.
- Logo metadata: `logoFile="immersive_bop_harvest_logo.png"`.
- Packaged logo size: `1554071` bytes.
- Packaged logo SHA-256: `8f88fdedc1872f35814227472d5b84c157411d0e506c6cfb5c1d75af2dcda31a`.
- The packaged logo hash exactly matches the owner-provided attachment.

## Generated Payload

- Farmer's Delight cutting recipes: `64`.
- Immersive Engineering sawmill recipes: `39`.
- Direct-harvest modifiers: `19`.
- Direct-harvest loot tables: `19`.
- Common item tags: `2`.
- Generated JSON files: `146`.
- Compatibility coverage IDs: `181`.

## Runtime Proof

- `runGameTestServer`: PASS, exit `0`, all `3` required tests passed.
- `allGeneratedRecipesLoad`: all `103` generated recipe IDs present.
- `bopShearsTagContainsVanillaShears`: PASS.
- `runData`: PASS, exit `0`, current dependency stack loaded.
- Dedicated-server smoke: fresh alpha.9 log reached `Done (`.
- Server-smoke script exit: `0`.
- Server shutdown mode: bounded process-tree termination after the ready marker;
  underlying Gradle process exit `1` is retained as a harness detail.
- Proof log: `build/server-smoke/runServer-0.1.1-alpha.9-20260713-140412.out.log`.

## Client Smoke

Fresh alpha.9 title-screen proof is not claimed. Computer-use recovery failed
with `foreground window did not report a process id` after Windows detected user
input in the Prism window. This is `BLOCKED-BY-GUI-AUTOMATION-LIMIT`.

The installed artifact is safe for another launch attempt because its build,
hash, metadata, license, logo, dependencies, GameTests, datagen and server boot
are verified. That statement does not substitute for the missing title-screen
proof and does not claim full gameplay validation.
