# Stable readiness work program

Input: owner request `/goal execute`, attached CODEX_STABLE_RELEASE_PLAN.md,
2026-09-05. The document supplies the work program, not a separate authority.
Its claim that ChatGPT is task authority does not supersede the user's scope.
Current maintenance packet executes phases 0-3 within repository authority.

## Baseline and boundaries

Local checkout was clean at be5390c1a1c7d2765a4bf9c2121223e18be291e5.
A fetch and fast-forward established afc9237294faa5c86d56d8228f64ac4e1bfbb2f1,
tree 108b2887df3a4dbe3f1267d3ed5a5335130479e4. Prior PRs 1/2 are preserved.
Mod immersive_bop_harvest stays 0.1.1-alpha.9; Minecraft 1.21.1,
NeoForge 21.1.233, Java 21, All Rights Reserved. No gameplay/version edits,
Prism launch/install, tag/Release, CurseForge write, production dispatch,
secret/protection change or feature additions are authorized by this packet.
Historical July alpha.9 client waiver remains NOT_PERFORMED / OWNER_WAIVED.

## Task graph and completion

- S0 baseline, scope, acceptance matrix -> S1/S2/S3.
- S1 shared canonical source ledger and Windows/Linux regressions.
- S2 schema 3 explicit historical metadata and offline safety regressions.
- S3 candidate bundle integrity checker and negative/positive fixtures.
- S3-A authenticated runtime producer/readback: BLOCKED; separate runtime scope.
- S4 comprehensive gameplay qualification: NOT_AUTHORIZED; depends S3-A.
- S5 disposable client/server/multiplayer/save qualification: NOT_AUTHORIZED.
- S6 final-version candidate and raw artifact qualification: NOT_AUTHORIZED;
  depends S4/S5 and explicit version decision. Do not silently select 0.1.1.
- S7 reviewed source integration/CI and Notion readback: authorized after review.
- S8 external metadata repair/publication: NOT_AUTHORIZED; depends real candidate,
  canonical GitHub Release, reviewed immutable publication manifest and authority.

Source, runtime, artifact and publication readiness are separate. A completed
maintenance packet is not SOURCE_READY for stable if mandatory acceptance
coverage remains missing. No unresolved P0/P1 defect or evidence gap may pass.
Every task and command is recorded in STABLE_RELEASE_READINESS.json and raw
local receipts under build/release-evidence/maintenance-20260905 (Git-ignored).
The 313-row STABLE_ACCEPTANCE_MATRIX maps 39 QA checkboxes plus all scoped
spec entries/policies. Existing three GameTests provide limited structural proof.

## Source ledger contract

Both refresh_project_manifest.py and check_beta_release_gate.py consume
check_file_ledger. CRLF text is normalized to LF, matching .gitattributes;
JAR/PNG/NBT or NUL-containing files remain raw. The checker rejects empty,
malformed, duplicate, escaping, missing and omitted tracked entries. Do not
use source-ledger hashes as downloadable asset hashes. Release JARs and frozen
changelogs always use exact bytes. Refresh only after intentional path staging;
build_summary remains untouched historical evidence.

## Stable evidence interface

Run `python scripts/check_stable_release_gate.py --bundle <candidate.json>`.
Exit 1 means missing/invalid evidence; exit 2 means integrity verified but
BLOCKED_UNTRUSTED_RUNTIME_PROVENANCE. This maintenance CLI has no exit-0 path.
It performs no writes, launches, network requests or publication. Unit fixtures
prove integrity checks, not Minecraft execution. Even replacing a log and its
hash cannot make the CLI certify runtime. An authenticated evidence producer
and independent readback must be designed, authorized and tested before adding
a stable-ready path; there is no user-controlled trusted/PASS bypass.

Bundle schema 1 has exactly: schemaVersion, candidate, jar, dependencyLock,
sourceManifest, changelog, installedModsDir, receipts, defects, publicationBlockers.
Candidate: id, version, modId, license, commit, tree, jarSha256, lockSha256.
Every file reference: relative path, positive integer size, raw lowercase sha256.
Source must be a clean exact Git HEAD/tree with the authoritative source ledger.
JAR identity is parsed from the matching TOML mod record and document license.
The disposable installation must contain exactly the candidate and five locked
runtime JARs, with matching bytes/metadata and no duplicate mod IDs.
Six separate receipts are required: automated, client, server, multiplayer,
gameplay, save_reload. Each has kind, exact candidate, tested=true, waived=false,
command argv, exitCode=0, UTC startedAt/finishedAt, log reference and coverage
IDs. Unknown fields, malformed types, stale identities, missing logs/coverage,
and wrong receipt-kind coverage fail. Coverage IDs derive from the source tree.
The current checker accepts no unresolved defects; external publication blockers
are explicit and cannot satisfy runtime requirements. Logs/hashes alone cannot
prove freshness, gameplay assertions or execution authenticity.

## Integration and proof policy

Use one write owner (root agent); independent specialists are read-only.
Run all publisher, CI and beta/stable checker regressions, spec/resource checks,
two deterministic generator passes, manifest and diff checks. Linux CI runs
clean, check/build, exact dependency validation, GameTests and two datagen runs.
Windows CI tests source consumers and evidence contracts without Prism.
Local Gradle loopback failures are environment blockers; no machine-security or
production workaround. Keep CI and local proof separate. Merge only after
review and actual final-head CI success; read back merged source tree and CI.
No evidence artifacts are GitHub Releases. The final report channel is this
Codex task; no separate ChatGPT-control transport is available or invented.
