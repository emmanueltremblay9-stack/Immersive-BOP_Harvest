# Stable readiness work program

## Current authorization: S3-A -> S4 -> S5

S3-A execution is verified: PR #4 merged as
`ee525b9d9406b030e17d87249219c007f97af47c`, tree
`d2554e12f732ee13496246823afe78f156d2fd2b`. Canonical main CI run
`33982279621`, attempt 1 passed. Independent verifier returned exit 0 and
`AUTHENTICATED_DEVELOPMENT_EXECUTION`; the stable CLI returned exit 2 with
`stableReady=false`. Candidate archive `9974143257` matched the service digest
`7a31f7e00f9e0d467e812df70ee54d563987f8e4369737879b672d63c375fc0d`.

S4 uses alpha.10 and a separate `src/qualification` harness. Its 302 cases cover
64 actual Cutting Board operations, 52 sawmill inputs with per-tick emission
and NBT-reload checks, 19 harvest tool/state/foreign-table/explosion matrices,
162 native-loot cases, four scheduled plant cascades, and common tags. The
three existing GameTests remain mandatory. The report validator requires exact
case inventory and actual interaction assertions; CI readback fetches the six
source specifications at the independently expected commit. Development mode
and untested formed-machine ports remain explicit. The test harness is excluded
from the production addon JAR.

S4 is integrated through PR #5, merge `1b84049fe53d59b1b263ee11942be304c441cab6`.
Canonical main run `33984397632`, attempt 1 and its artifact were authenticated
by the verifier, exit 0; Code Reviewer and Reality Checker passed.
S5 implements and validates installed production-loader bytes, actual client
interactions, 52 formed sawmill ports, multiplayer and clean save/restart.
All seven local phases passed with the frozen canonical S4 candidate, including
clean exits and the strict evidence validator. S5 CI must qualify its own built
JAR; that execution and canonical readback remain pending in this source snapshot.
See [packaged qualification](PACKAGED_RUNTIME_QUALIFICATION.md). The current
exact five-mod lock is the qualified dependency baseline; untested future
versions within broad metadata ranges are not implied to be supported by QA.

On 2026-09-05 the owner explicitly requested this sequence after PR #3 merged.
Baseline: main `37e6d8225819abdd079ec55e9317b53f5f235f1f`, tree
`9879736b58d192f60d64bbc26efbdda2dd1afef4`. This authorizes authenticated
evidence producer/readback, tests and necessary fixes for existing scoped
behavior, and disposable runtime qualification. Final stable-version selection
(S6) and production publication remain outside this packet. Personal Prism
instances and worlds remain untouched. The maintenance sections below record
the previous packet's authority and evidence, not the current authorization.

S3-A adds `tools/ci/candidate_evidence.py collect` to the existing successful
CI job. Independent readback uses:

```text
python tools/ci/candidate_evidence.py verify --run-id <id> --attempt <n> --expected-commit <reviewed-main-sha>
python scripts/check_stable_release_gate.py --ci-run-id <id> --ci-attempt <n> --expected-commit <reviewed-main-sha>
```

The verifier obtains the exact run attempt, jobs/required steps, source tree,
dependency lock and artifact through GitHub GET requests. It requires a
successful canonical main push, the expected reviewed commit, a complete
artifact inventory and matching service SHA-256 digest. ZIP entries are bounded
and validated before reading; receipt/file/JAR identities must match the
read-back service state. Local files or a submitted PASS flag cannot authenticate
execution. The trust boundary is GitHub plus the reviewed workflow and harness.
No new secret, write permission, attestation credential or release is needed.

S4 authenticated capabilities are build, 305 development GameTests, repeated
datagen and exact dependency validation. S5 adds separate production receipts,
screenshots and observed state transitions. The verifier accepts these only
when their required CI execution steps and complete bytes validate against
the canonical run. The stable checker still exits 2 and keeps
`stableReady=false`; final stable-version selection is a separate gate. Earlier
maintenance planning required S4/S5 to add real
reviewed assertion producers before those capabilities can advance.

Local Gradle's Windows selector problem is resolved for task processes by a
short isolated socket directory using `jdk.net.unixdomain.tmpdir`; a fresh
loopback/selector probe and Gradle help exited 0. No global setting changed.
Evidence is retained outside cleanable Gradle outputs in the task's isolated
qualification directory. The prior maintenance evidence is preserved there.

## Historical maintenance packet

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
