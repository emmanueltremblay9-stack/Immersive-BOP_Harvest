# Release Checklist

## Current 0.1.1-alpha.4 status

- [x] Specification validation passed.
- [x] Generated alpha resources parse as JSON and pass `qaAlphaResources`.
- [x] Full Gradle build passed.
- [x] `runData` loads the mod with synchronized Test play runtime dependencies.
- [x] `runGameTestServer` passed 2 required tests, including all 103 generated recipe IDs.
- [x] Dedicated-server smoke reached the server-ready `Done` signal.
- [x] Private Prism Test play install was hash-verified.
- [x] Required BOP runtime dependencies were present and verified.
- [x] Prism Test play client log-marker smoke loaded alpha.4 with no new crash report.
- [x] Alpha.4 visual title-screen screenshot proof is captured.
- [x] Legal reuse inventory is present.
- [x] Beta release notes draft is present.
- [x] Deterministic beta release gate checker is present and verifies built/installed jar hashes plus duplicate installed jars by embedded `modId`.
- [ ] License decision is still open.
- [ ] Public binary release is still blocked.

## Public release gate

1. Resolve `LICENSE_DECISION_REQUIRED.md`.
2. Confirm exact dependency versions and ranges.
3. Run specification validation.
4. Run datagen twice.
5. Run unit/GameTests.
6. Run full build.
7. Test client.
8. Test dedicated server.
9. Test with only required dependencies.
10. Test with the intended modpack.
11. Review generated recipe counts.
12. Review every `INTENTIONALLY_UNCHANGED` decision.
13. Update README and changelog.
14. Run `python scripts/check_beta_release_gate.py` and require `BETA RELEASE GATE: PASS`.
15. Tag the release using semantic versioning.
16. Publish the source and binary only after license review.
