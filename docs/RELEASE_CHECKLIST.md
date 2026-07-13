# Release Checklist

## Current 0.1.1-alpha.9 status

- [x] Specification validation passed.
- [x] Generated alpha resources parse as JSON and pass `qaAlphaResources`.
- [x] Direct-harvest drop coverage is complete for the current spec: 19 spec block IDs, 19 modifiers, 19 loot tables.
- [x] Direct-harvest modifiers are scoped to their matching BOP block loot tables with `neoforge:loot_table_id`.
- [x] Direct-harvest shears exclusion uses `#biomesoplenty:shears`; stale `#c:tools/shear` references are rejected.
- [x] Stale generated common item tags are removed when no longer declared in `spec/tag_integrations.json`.
- [x] Wood recipe-scope IDs are present in the compatibility inventory and matrix.
- [x] `PROJECT_MANIFEST.json` file ledger validation is wired into the beta release gate.
- [x] Full Gradle build passed.
- [x] `runData` loads the mod with synchronized Test play runtime dependencies.
- [x] `runGameTestServer` passed 3 required tests, including all 103 generated recipe IDs and BOP shears-tag coverage.
- [x] Dedicated-server smoke reached the server-ready `Done` signal with alpha.9 loaded.
- [x] Private Prism Test play install was hash-verified.
- [x] Required BOP runtime dependencies were present and verified.
- [x] Fresh alpha.9 Prism Test play client title-screen smoke is explicitly `NOT_PERFORMED / OWNER_WAIVED`; it is not represented as a passing test.
- [x] Previous alpha.4 visual title-screen screenshot proof is captured, but it is not alpha.9 proof.
- [x] Legal reuse inventory is present.
- [x] Beta release notes draft is present.
- [x] Deterministic beta release gate checker is present and verifies built/installed jar hashes, duplicate installed jars by embedded `modId`, and manifest file hashes.
- [x] Owner selected `All Rights Reserved`; `LICENSE` and `mod_license` are synchronized.
- [x] Public binary release gate passes under the explicit owner-selected reduced test scope.
- [x] Final `python scripts/check_beta_release_gate.py` returned exit `0` and `BETA RELEASE GATE: PASS`.

## Public release gate

1. Confirm `LICENSE` and `mod_license=All Rights Reserved` remain synchronized.
2. Confirm exact dependency versions and ranges.
3. Run specification validation.
4. Run datagen twice.
5. Run unit/GameTests.
6. Run full build.
7. Test client, or record an explicit owner waiver without claiming a pass.
8. Test dedicated server.
9. Test with only required dependencies.
10. Test with the intended modpack.
11. Review generated recipe counts.
12. Review every `INTENTIONALLY_UNCHANGED` decision.
13. Update README and changelog.
14. Stage the intended release files, then run `python scripts/refresh_project_manifest.py` to refresh the version and tracked-file ledger.
15. Run `python scripts/check_beta_release_gate.py` and require `BETA RELEASE GATE: PASS`.
16. Tag the release using semantic versioning.
17. Publish the source and binary only after license review.
