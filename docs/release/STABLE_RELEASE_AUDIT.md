# Stable readiness maintenance audit — 2026-09-05

## Current S3-A/S4/S5 follow-up

S3-A PR #4 merged at `ee525b9d9406b030e17d87249219c007f97af47c`.
Main run `33982279621` attempt 1 and archive digest were independently read
back by the implemented verifier, exit 0. Stable CLI still returned exit 2.

S4 PR #5 merged as `1b84049fe53d59b1b263ee11942be304c441cab6`, tree
`61653629b81a4632b119d7b9ea46f872269e904d`. Canonical main run
`33984397632`, attempt 1 passed both jobs; independent readback returned exit 0.
Artifact `9974753888` matched archive SHA-256
`fe22c5c62fcc8a71c2e6c64df38c3232b96212363e6c4d459ed609b49c29e98f`.
The exact CI candidate is 1,606,581 bytes, SHA-256
`efd4446ee0cff2fa36f9d2e00c92f4f2200de1b582491dd7c926b69006b93a53`.
Code Reviewer and Reality Checker accepted S4 before merge.

The S4 alpha.10 harness has 302 scoped runtime cases plus the
three existing GameTests. Clean compile/resources/test/build, all 305 GameTests,
two datagen passes and 44 CI Python regressions passed locally. The final report
contains 4,488 recorded assertions. The initial harness
return-type mistake and independent-review findings were corrected without
changing gameplay: copy emissions each tick, observe natural scheduled
cascades with a sufficient capture margin, and reject omitted state/tool/tag
assertions. Final source review, canonical CI, independent merge verdict
and raw report readback passed.

S5 adds an explicit production launcher and seven-phase receipt validator.
Four local server phases have passed with one frozen harness: fresh alpha.9,
clean restart, alpha.10 upgrade and clean restart. They exercise all 302 scoped
cases, 52 formed sawmills with actual ports, 100 repeated board operations,
datapack reload, a saved board input and a redstone-paused in-flight sawmill.
The complete final4 local packet now passes all seven phases and the strict
independent Python validator, exit 0. Frozen harness SHA-256 is
`eebbe989715f5e43450bb6abaa46a699f4b43f3734f9909f128e55830bc6a193`.
Client-one completed actual FD, IE and harvest interactions. Both clients
completed simultaneous board use, tool conservation/retrieval, reconnect and
clean exits. Every process
exited 0 without timeout or abort. Canonical S5 CI/readback remains pending.
The partial client run reached title, created a world and passed real FD, IE
blade and knife-harvest interactions; its disconnect wait was a harness defect,
so that run is retained as failed evidence. Shared-library download races were
also fixed in the launcher. Neither fix changes addon gameplay.
The earlier multiplayer test incorrectly assumed an empty FD board after
repeated clicks. Saved NBT and FD bytecode confirmed normal axe storage; the
final test measures tools and outputs before/after a genuine empty-hand pickup.

Final local phase durations were 40.626, 24.622, 47.445, 20.178, 120.639,
103.533 and 103.511 seconds respectively (the clients and multiplayer phase
overlap). Upgrade/full-baseline ratio was 1.168; log sizes were 14,380 versus
14,244 bytes. These bounded observations are not a general performance SLA.
The baseline JAR was rebuilt from the fixed S3-A source commit: 1,607,128 bytes,
SHA-256 `0b8fd189a5baff1175f65bcb1dfb861a2288989fbc00bcb2bd1a6d914d1668c8`.
It is distinct from the historical published file and earlier CI artifact.

Independent screenshot review matched seven images to their byte hashes.
The title, world, sawmill models and multiplayer clients are visibly rendered.
The initial world image does not frame machines, and the board-result image
does not frame the board. Actual server observations, rather than those two
frames, prove machine/output quantities and conservation.
See [packaged qualification runbook](PACKAGED_RUNTIME_QUALIFICATION.md).
No public upload, tag/Release or publisher dispatch.
The separate harness has been verified absent from the built production JAR.
The old alpha.9 waiver is unchanged and does not apply to alpha.10.

Final S5 local checks passed: clean compile/resources/build and qualification
JAR build; 305 development GameTests; repeated datagen with no resource drift;
85 CI Python tests (one Windows symlink-privilege skip). Java `test` remains
NO-SOURCE. The clean build also ran 69 publisher and 21 release-checker tests.
The later frozen harness rebuild, GameTests and datagen used the final Java
source. The real beta CLI exited 1 because its historical build/install record
still targets alpha.9 and the personal Prism installation remains alpha.9.
That legacy installed-release gate does not validate the disposable S5 packet;
its failure is retained and neither record nor personal installation was altered.
Local actionlint was NOT_PERFORMED because Go/actionlint is unavailable; the
existing CI lint step remains mandatory. Source/parser review independently
revalidated the actual frozen packet and passed. Final canonical CI is pending.

Local S4 commands (all exit 0):

```text
gradlew.bat --no-configuration-cache clean compileJava processResources test build -PbopHarvestIsolatedDependencies=<isolated locked-dependencies> --stacktrace
gradlew.bat --no-configuration-cache qualificationJar runGameTestServer runData -x syncRuntimeDeps -PbopHarvestIsolatedDependencies=<isolated locked-dependencies> -PbopHarvestQualificationGameDir=<disposable game directory> --stacktrace
gradlew.bat --no-configuration-cache runData -x syncRuntimeDeps -PbopHarvestIsolatedDependencies=<isolated locked-dependencies> --stacktrace
python -W error::ResourceWarning -m unittest discover -s tools/ci -p test_*.py -v
git diff --exit-code -- src/main/resources src/generated/resources
git diff --check
```

Raw commands, exits and log hashes are retained in `s4-commands.json` in the
isolated qualification evidence directory. The session used only an isolated
`jdk.net.unixdomain.tmpdir` property for the previously reproduced Java selector
failure. The clean build took 2m 6s; the combined final runtime/datagen task 40s;
the repeated datagen 15s. Java `test` was NO-SOURCE; the 305 runtime GameTests
are a separate executed gate. The build also ran 69 publisher and 21 release
checker regressions. No new test replaces a failed acceptance requirement.

Local production JAR: `immersive_bop_harvest-0.1.1-alpha.10.jar`, 1,607,221 bytes,
SHA-256 `ec303db83243d71eb478a61204a66fd90e4d03eb1141218aeb3d4f340e406944`.
This is a pre-integration Windows build; it is not claimed byte-identical to a
future CI build. The qualification classes and copied specs are excluded.

```text
AUTOMATION_ROUTE: compatibility QA -> Code Reviewer -> Reality Checker
AGENTS_ACTUALLY_USED: s3a_review (Code Reviewer); stable_gate_design (Software Architect); baseline_review (Evidence Collector); reality_check (Reality Checker); production_evidence (Minimal Change Engineer); s5_runbook (Technical Writer)
FALLBACKS_OR_NO_DELEGATION: existing Codebase Memory plus affected source/log/report reads
SINGLE_WRITE_OWNER: root
EVIDENCE_GATE: PASS for canonical S4 and measured local S5; S5 canonical CI/readback pending
REVIEW_GATE: PASS for S4 and final S5 source/parser/local packet
REALITY_CHECK_GATE: S3-A and S4 PASS; local S5 PASS-WITH-GAPS; final CI verdict pending
UNRESOLVED_GAPS: S5 canonical CI/readback; screenshot framing limits; S6 final stable version
FINAL_VERDICT: PASS-WITH-GAPS
```

## Historical maintenance evidence

Historical snapshot: PR #3 subsequently merged as
`37e6d8225819abdd079ec55e9317b53f5f235f1f`; its main CI run `33980036391`,
attempt 1 passed. The owner then authorized S3-A -> S4 -> S5. Current execution
is tracked in `STABLE_RELEASE_READINESS.json.current_qualification` and the
current section of `STABLE_RELEASE_PLAN.md`. Statements below about unavailable
runtime authority/local Gradle describe the preceding maintenance packet.

This records the pre-integration maintenance source at baseline `afc9237294faa5c86d56d8228f64ac4e1bfbb2f1`.
Final PR/head/CI/merge readback belongs to the task's final receipts and Notion
entry; this committed report does not claim its own future final-head CI.

## Implementation and validation

- Shared LF-canonical source-ledger validation fixes reproduced CRLF rejection.
  Raw JAR/changelog identities remain byte-exact. Duplicate/missing/unsafe and
  exact Git inventory checks remain required. July build_summary is preserved.
- Additive schema 3 binds explicit historical type and labels separately from
  target type and labels. Legacy schema 1/2 and schema 2 template retained.
  Missing historical/target metadata and relation gates fail closed.
- Stable checker validates exact bundle identity and 313 coverage obligations.
  Its CLI deliberately cannot return stableReady=true: authenticated runtime
  producer/readback remains unavailable. No fabricated local log can certify it.
- Windows regressions and Linux clean/build, locked dependencies, GameTests,
  repeated datagen and failure-evidence retention are wired in existing CI.

Local Python tests: 69 publisher, 29 CI/source, 19 beta/stable,
all exit 0. Specification validation, two generation passes, generated QA,
resource diff and whitespace check exit 0. Stable checker with absent candidate
exits 1 as expected (negative test, not stable readiness).
Raw commands/exits/log hashes: `build/release-evidence/maintenance-20260905/commands.json`.
Local Gradle help exits 1 before task graph: Unable to establish loopback
connection / Invalid argument: connect. Java 21.0.11, Gradle 9.2.1, Windows 11,
Python 3.12. No JDK/security/runtime workaround performed. Full local build,
install and runtime proof are NOT_PERFORMED; CI remains independent.
After authoritative ledger refresh, the actual beta gate exits 0 against the
existing alpha.9 built/installed bytes and historical owner waiver. This is
current readback of historical artifacts, not a fresh build/install/client pass.
Before refresh it exited 1 for the intentionally changed source ledger.
Local actionlint NOT_PERFORMED (Go unavailable); CI actionlint is required.

Independent Code Reviewer found one manifest identity mismatch and redundant
Gradle test arguments; both corrected before integration. Evidence Collector
verified current specs and limited GameTest coverage; Software Architect
identified the unauthenticated-receipt trust boundary. Reality Checker and
final-head CI remain required before final maintenance verdict.

## Dependencies and current public state

Five DIRECT_RUNTIME_DEPENDENCY mods remain pinned in the unchanged lock:
BOP 21.1.0.14, GlitchCore 2.1.0.2, TerraBlender NeoForge 4.1.0.8,
Farmer's Delight 1.3.2, IE 12.4.2-194. Lock SHA-256 `14564b87c62bbcd00c645d324488e9ed0a88422b90669c313a5eb5adfec166c0`.
GlitchCore/TerraBlender additionally support BOP transitively.
Fresh GET file 8426397 confirms project 1609013, approved status 4, Alpha type 3,
labels Client/1.21.1/NeoForge. Fresh dependencies GET returns zero relations;
local contract still requires five. Project-detail GET returns HTTP 403; no
slug re-verification is claimed from that endpoint. Configuration remains
RESOLVED, not a missing-project blocker. GitHub Release inventory remains empty.

## Readiness and boundaries

SOURCE_READY: BLOCKED (full stable acceptance and final-head qualification).
RUNTIME_READY: BLOCKED (fresh candidate client/server/multiplayer/gameplay/save
receipts and authenticated provenance absent; runtime expansion not granted).
ARTIFACT_READY: BLOCKED (final-version candidate/version authority absent).
PUBLICATION_READY: BLOCKED (authority, canonical Release, immutable manifest,
public relations and final exact readback absent).
Historical alpha.9 client waiver remains NOT_PERFORMED / OWNER_WAIVED.
Production upload count: 0. Tag/Release creation: 0. Publisher dispatch: 0.
No gameplay, personal instance/world, secret or protection changes.
Safe to launch Minecraft: no new build/install proof in this packet.

## Next gates

Complete final-head CI/review, integrate only if passing, then read back main
and Notion. All expanded gameplay/runtime/candidate/publication work remains
explicitly gated. The separate ChatGPT control transport is unavailable:
BLOCKED_BY_MISSING_CODEX_REPORT_CHANNEL; this Codex task supplies the report.

## Routing

AUTOMATION_ROUTE: evidence inventory -> architecture review -> root implementation -> independent review -> CI -> reality check.
AGENTS_ACTUALLY_USED: Evidence Collector; Software Architect; Code Reviewer.
FALLBACKS_OR_NO_DELEGATION: no fallback agents; Go absent locally; specialized
instruction-conflict/Actions/template-drift skill names from input unavailable,
covered by direct source review and existing workflow regressions.
SINGLE_WRITE_OWNER: root.
EVIDENCE_GATE: local tests PASS; final-head CI pending.
REVIEW_GATE: corrections applied; final re-review pending.
REALITY_CHECK_GATE: pending.
UNRESOLVED_GAPS: runtime authority/authenticity, local Gradle, final candidate,
publication authority/prerequisites, separate report transport.
FINAL_VERDICT: BLOCKED for stable; maintenance integration pending.
