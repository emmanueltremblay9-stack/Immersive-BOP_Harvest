# Stable readiness maintenance audit — 2026-09-05

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
