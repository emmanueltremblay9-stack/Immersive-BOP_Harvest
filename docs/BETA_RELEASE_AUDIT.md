# Beta Release Audit

Date: 2026-07-13
Project: Immersive BOP_Harvest
Version: `0.1.1-alpha.9`

## Current Result

Technical build, data, server and installation gates pass. The owner selected
`All Rights Reserved`, the final JAR embeds that license, and the supplied PNG
is used by the README and packaged as the NeoForge mod logo.

The owner explicitly instructed Codex to skip the remaining Prism client test
phase. The fresh alpha.9 title-screen smoke is therefore `NOT_PERFORMED` and
`OWNER_WAIVED`, not passed. The deterministic release gate accepts this only
when the manifest contains a complete, non-ambiguous waiver record.

Final checker result: `BETA RELEASE GATE: PASS`, exit `0`.

## Proven Gates

| Gate | Status | Evidence |
|---|---|---|
| Specification validation | PASS | exit 0; 181 coverage IDs |
| Generator determinism | PASS | identical binary diff after two successive generations |
| Generated-resource QA | PASS | exit 0; 146 JSON files |
| Release-checker regression tests | PASS | 7 unittest cases |
| Clean build | PASS | `clean build`, exit 0 |
| GameTests | PASS | 3 required tests; all 103 generated recipe IDs |
| Datagen/runtime load | PASS | `runData`, exit 0 |
| Dedicated server | PASS | alpha.9 loaded and fresh `Done (` marker observed |
| License | PASS | `LICENSE`, Gradle property and installed metadata are `All Rights Reserved` |
| Logo | PASS | packaged PNG SHA matches owner attachment SHA |
| Prism install | PASS | source/install hashes match; exactly one project JAR remains |
| Fresh alpha.9 client title screen | NOT_PERFORMED / OWNER_WAIVED | Explicit owner instruction: skip this test phase |

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

## Owner-Selected Release Scope

- Fresh alpha.9 client title-screen smoke: `NOT_PERFORMED / OWNER_WAIVED`.
- Full gameplay/world interaction smoke: `NOT_PERFORMED`.
- The waiver does not claim client runtime success and cannot coexist with a
  `live_client_smoke_tested=true` claim.
- All remaining automated, artifact, metadata, server, install and legal gates
  must pass without waiver.

Client startup and full gameplay remain explicitly reported residual risks.
