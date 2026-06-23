# Release Checklist

## Current 0.1.1-alpha.1 status

- [x] Specification validation passed.
- [x] Generated alpha resources parse as JSON.
- [x] Full Gradle build passed.
- [x] Private Prism LAB install was hash-verified.
- [x] Required BOP runtime dependencies were installed and verified.
- [ ] License decision is still open.
- [ ] Live-client smoke is still open.
- [ ] Dedicated-server smoke is still open.
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
14. Tag the release using semantic versioning.
15. Publish the source and binary only after license review.
