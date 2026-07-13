# Beta Release Audit

Date: 2026-07-13
Project: Immersive BOP_Harvest
Version: `0.1.1-alpha.9`

## Current Result

Technical build, data, server and installation gates pass. The owner selected
`All Rights Reserved`, the final JAR embeds that license, and the supplied PNG
is used by the README and packaged as the NeoForge mod logo.

Public release remains `BLOCKED` only because a fresh alpha.9 Prism client
title-screen capture was interrupted by user input and could not be recovered
reliably in this pass (`BLOCKED-BY-GUI-AUTOMATION-LIMIT`).

## Proven Gates

| Gate | Status | Evidence |
|---|---|---|
| Specification validation | PASS | exit 0; 181 coverage IDs |
| Generator determinism | PASS | identical binary diff after two successive generations |
| Generated-resource QA | PASS | exit 0; 146 JSON files |
| Release-checker regression tests | PASS | 3 unittest cases |
| Clean build | PASS | `clean build`, exit 0 |
| GameTests | PASS | 3 required tests; all 103 generated recipe IDs |
| Datagen/runtime load | PASS | `runData`, exit 0 |
| Dedicated server | PASS | alpha.9 loaded and fresh `Done (` marker observed |
| License | PASS | `LICENSE`, Gradle property and installed metadata are `All Rights Reserved` |
| Logo | PASS | packaged PNG SHA matches owner attachment SHA |
| Prism install | PASS | source/install hashes match; exactly one project JAR remains |
| Fresh alpha.9 client title screen | BLOCKED | GUI recovery error after user-input interruption |

## Artifact Proof

- Built: `build/libs/immersive_bop_harvest-0.1.1-alpha.9.jar`
- Installed: `C:\Users\Emmanuel Tremblay\AppData\Roaming\PrismLauncher\instances\1.21.1 TesT play\minecraft\mods\immersive_bop_harvest-0.1.1-alpha.9.jar`
- Size: `1607220` bytes at source and destination
- SHA-256: `20110892574faabf2fd2c47807ade1eca38ab0b2b248ac8187bdbf779c1c61cc`
- Remaining JARs declaring `immersive_bop_harvest`: `1`
- Logo SHA-256: `8f88fdedc1872f35814227472d5b84c157411d0e506c6cfb5c1d75af2dcda31a`

## Defects Fixed In This Release Candidate

1. Stale generated common item tags could survive spec removal.
2. Wood recipe-scope IDs were not required by the coverage inventory gate.
3. Direct-harvest modifiers lacked a native BOP loot-table ID scope.
4. A malformed manifest ledger entry crashed the release checker.
5. Manifest ledger paths could resolve outside the project root.
6. The owner logo existed only outside the runtime JAR/mod-list metadata.

## Known Non-Project Warnings

Runtime output includes NeoForge/BOP spawn-placement warnings and Mixin class
version debug messages from the dependency stack. They do not originate in this
mod and did not produce a nonzero GameTest or datagen exit.

## Remaining Gate

1. Retry the Prism `1.21.1 TesT play` launch without concurrent user input.
2. Capture the `Minecraft NeoForge* 1.21.1` title window with alpha.9 in the log.
3. Set the manifest client-smoke fields from that proof.
4. Refresh the manifest ledger and require `BETA RELEASE GATE: PASS`.

Full gameplay/world interaction smoke is useful but remains a separately
reported residual risk rather than a title-screen release-gate substitute.
