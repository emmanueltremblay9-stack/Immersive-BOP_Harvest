# Guarded CurseForge publisher — source integration

## Current boundary

Source version is `0.1.1`; license remains **All Rights Reserved**.
Production CurseForge upload in this task: **NO**.
CurseForge project configuration: **RESOLVED**.
The verified target is project ID `1609013`, slug `immersive-bop-harvest`,
with existing public file ID `8426397` for
`immersive_bop_harvest-0.1.1-alpha.9.jar`.
The reviewed source manifest is
`tools/release/curseforge_release_0.1.1.json`; it binds the authenticated
`immersive_bop_harvest-0.1.1.jar` candidate and immutable release notes.
The repository standing policy is
`STABLE_AUTOPUBLISH_POLICY=AUTHORIZED_WHEN_ELIGIBLE`: a canonical stable
release does not require a new one-off owner approval after every fail-closed
runtime gate passes. This source-only implementation still creates no tag,
GitHub Release, secret, or CurseForge upload.

The previous public file has three required relations and the project-level
aggregate has zero. Those historical states are pinned separately from the
five required relations for the new stable file. The publisher rejects drift
in any of the three sets; it does not rewrite historical metadata.

Read-only evidence refreshed 2026-09-16: [target project](https://www.curseforge.com/minecraft/mc-mods/immersive-bop-harvest),
[existing public file](https://www.curseforge.com/minecraft/mc-mods/immersive-bop-harvest/files/8426397),
[public relations](https://www.curseforge.com/minecraft/mc-mods/immersive-bop-harvest/relations/dependencies),
and [repository releases](https://github.com/emmanueltremblay9-stack/Immersive-BOP_Harvest/releases).

The public file and dependency APIs currently expose the exact file/project
binding and the 3/0 historical relation sets. The standalone project identity
API and official HTML page returned HTTP 403 from this runner. The publisher's
official-page fallback is therefore fail-closed: a future publication attempt
must stop with `CURSEFORGE_PROJECT_IDENTITY_BLOCKED` unless that execution can
verify the exact canonical slug and project ID without a secret.

The publisher is source code, not proof of publication. An offline fixture
passing, a CI passing, and a live secret-free dry run are distinct evidence.
The original Prism smoke remains `NOT_PERFORMED / OWNER_WAIVED`.

## Files and provenance

`tools/release/publish_curseforge.py`, `stable_autopublish.py`,
`stable_publish.py`, their tests,
the three release schemas, the versioned `0.1.1` manifest and notes, and
`.github/workflows/publish-curseforge.yml` form the source integration.
`.github/workflows/build.yml` is only the upstream evidence producer and is
not modified by this implementation.
Upstream source/license details are in `tools/release/NOTICE.md`.

## Versioned manifests

Schema 2 requires `repository`, `release`, `curseforge` and `baseline`.
`baseline.mode=previousPublicFile` requires a real positive
`baseline.previousPublicFileId`. The parent public file's metadata and exact
relation baseline remain gates. `baseline.mode=firstPublication` contains no
parent ID, verifies the existing project's ID/slug, and requires an empty
public file inventory before a new upload. Accepted-file resume is read-only
and does not require the inventory to remain empty.

All relation arrays are explicit. `[]` is valid; a missing array is invalid.
An expected empty public relation list rejects any additional public relation.
Legacy schema 1 remains supported with its real `curseforge.previousPublicFileId`.
Schema 2 remains the non-publishable template contract. Intentional type/label transitions use schema 3. The schema is not a claim that inputs
have been reviewed; the Python validator also checks path confinement,
duplicate JSON keys, lookup-name subsets and the exact repository/tag.

The TEMPLATE is deliberately marked `template: true` and fails with
`TEMPLATE_NOT_PUBLISHABLE` before network use. It now contains the verified
target ID/slug and real previous public file baseline, but its release
artifact/changelog fields remain null. The approved stable source manifest is
separate from that template and pins every candidate, changelog,
historical-baseline, and target relation value. It is source preparation, not
evidence of a tag, Release, or upload.

Pin exact JAR basename, bytes, SHA-256, mod ID and version. Pin an immutable
release-note path and SHA-256. The alpha.9 CurseForge release type is `alpha`.
Never repurpose a manifest-pinned changelog for mutable completion evidence.
The canonical GitHub release gate still requires a public, non-draft,
non-prerelease release; this was not silently relaxed for an alpha version.

## Safety protocol

The workflow observes completed `Build and validate` runs through
`workflow_run` and retains manual tag, manifest_path, dry_run (default true),
and optional resume_file_id inputs. It uses contents:read/actions:read and
SHA-pinned actions. The automatic source path accepts only a successful
`push` on current `main`, checks out the exact upstream SHA, authenticates the
candidate/final bundle, validates the versioned manifest, and evaluates a
closed runtime gate map. Only strict `true` for every required gate produces
`autoPublishEligible=true`; missing, unknown, unavailable, or divergent state
stops fail-closed. The job checks only whether the CurseForge credential is
available and never emits its value.

The manual dry-run remains available without a CurseForge token. Manual
non-dry-run prepare, intent persistence, upload, or resume is an exceptional
mode and requires the separate `MANUAL_EXCEPTIONAL_AUTHORITY == GRANTED`
boundary. Manual inputs never inherit standing stable authority and cannot
bypass the canonical `workflow_run` eligibility calculation.
`Persist upload intent before any POST` remains a durable protocol identifier.

The eligibility job remains read-only. A separate automatic job owns the
minimal `contents:write` permission and runs only after the exact upstream gate
returns `autoPublishEligible=true`. It reruns the complete preflight immediately
before mutation, then uses `stable_publish.py` to reconcile the exact tag,
Release and one asset. Absent state is creatable, exact state is reusable, and
divergent, duplicate, malformed, draft or prerelease state stops without repair.
An exact Release with no asset is a resumable state; an incorrect or extra asset
is not. Annotated tags are dereferenced with bounded cycle protection and must
resolve to the authenticated source commit.

The automatic job then calls the existing CurseForge publisher protocol. Its
intent must be durably persisted before the single non-retried POST. The POST
returns an accepted file ID without polling; that ID is persisted as a separate
Actions artifact before a token-free resume step begins public polling. After
the publisher proves the exact stable file, `stable_publish.py finalize` performs
fresh GitHub and CurseForge public readbacks and writes a deterministic final
receipt. `publicationComplete=true` is possible only after the tag, Release,
asset bytes, CurseForge file identity, stable type, exact game-version labels,
five exact relations and JAR SHA-256 all match. A rerun reuses exact public
objects and the publisher's durable state; it does not treat a conflicting
object or an unknown POST outcome as permission to mutate again.

This implementation packet itself is stopped before branching, integration,
dispatch, or any public mutation. The mutation path is source code and test
evidence only until it is separately integrated and qualified on canonical
`main`.

Prepare computes deterministic metadata/multipart hashes and binds the full
manifest hash. Its upload-intent artifact must be successfully persisted and
read back before one non-retried POST. Results and intents use distinct files.
The accepted file ID is atomically written before polling. A same-run exclusive
local POST journal prevents reuse even before remote result persistence.
Never delete `.cfpub-state/` to reopen an uncertain upload. Cross-run artifact
and job history reconciliation is exact-tag scoped, includes every run attempt,
and rejects malformed, ambiguous or missing result state. The artifact prefix
also hashes the raw tag to avoid lossy sanitization collisions.

Dry-run, GitHub reconciliation, finalization and explicit resume receive no
CurseForge token. Credential-presence probes expose only a boolean. Only the
automatic or exceptionally authorized manual prepare step and the single upload
step may use the token. Credentialed HTTP redirects and POST
redirects are refused. Reports redact actual known token values and do not log
headers/bodies. Public readback requires exact project/file IDs, approved state,
name, display name, size, type, game versions, relation tuples, redownload hash,
and same-record NeoForge TOML mod ID/version. An HTTP success alone is not PASS.

## Retention and recovery

Intent/result artifacts retain 90 days. Run/job metadata acts as a conservative
backup while still queryable. Deleting both the artifacts and all corresponding
run history destroys the remote evidence basis; do not regard that as permission
to upload again. Persist external release evidence before retention expires.
Unknown POST outcomes require read-only reconciliation of a known accepted ID,
not a retry. No automatic mechanism claims eternal exactly-once delivery.
The final receipt is stored separately and binds the source commit/tree,
candidate and manifest identities, GitHub object IDs/URLs, CurseForge file ID,
public relation set and completion state. Its artifact name is derived from the
publication key. Before upload, all active same-key receipt artifacts are read
back and compared byte-semantically; an exact receipt is reused, a divergent or
malformed receipt stops, and an absent receipt is uploaded once then downloaded
and verified.

## Non-production validation

```bash
python -W error::ResourceWarning -m unittest discover -s tools/release -p 'test_*.py' -v
python -m unittest tools.ci.test_workflow_contract -v
python scripts/validate_specs.py
python scripts/generate_alpha_resources.py
python scripts/qa_alpha_resources.py
python -m unittest scripts/test_check_beta_release_gate.py -v
python scripts/refresh_project_manifest.py
python scripts/check_beta_release_gate.py
bash gradlew --no-configuration-cache check build
```

The release checker requires actual built/installed artifact evidence and may
be blocked on a clean CI runner; never manufacture `build/install-report.json`.
No new manual Prism smoke is required for publisher-only source changes.

After an existing GitHub Release and a real configured project are available,
a separately reviewed non-production dry run is:

```bash
python tools/release/publish_curseforge.py --dry-run --manifest tools/release/<reviewed-versioned-manifest>.json --tag <reviewed-tag> --report build/cf-dry-run.json
```

The angle-bracket names above are explicit placeholders, not existing paths.
Do not run the production workflow mode as part of this source delivery.

## Portable CI runtime

`tools/ci/runtime-dependencies.lock.json` pins five official project/file IDs,
exact names, versions, sizes and SHA-256 values read from baseline qualification
run `33955499390`. `tools/ci/prepare_runtime.py` downloads only those byte
identities to isolated `build/runtime-deps`, checks the same TOML mod/version,
and rejects extra JARs. It neither reads nor writes the personal Prism folder.
The existing Windows runtime sync task is preserved for its original local use.
CI explicitly skips only that copy task after validating every locked dependency;
all required GameTests and datagen still execute. Dependencies are not bundled
in the source ZIP or uploaded with CI evidence.

## Manifest line-ending correction

The historical manifest ledger contained workstation CRLF identities for many
files whose Git blobs are LF. The authoritative refresh now records the actual
tracked-source bytes. `.gitattributes` fixes text to LF across operating systems
and explicitly preserves binary JAR, PNG and NBT bytes. This changes ledger
hashes, not gameplay behavior; original evidence remains historical.

## Explicit historical metadata transitions (schema 3)

`curseforge_release_v3.schema.json` is additive; schema 1/2 semantics and the
schema 2 template remain unchanged. In schema 3, `previousPublicFile` requires
`previousPublicFileId`, `releaseType`, `gameVersionNames`,
`previousFileRelations`, and `projectRelations` in `baseline`. Those fields
describe the expected approved historical file and project state. The desired new
file still uses `curseforge.releaseType` and `curseforge.gameVersionNames`.
For an intentional Alpha-to-Release transition, historical `releaseType` is
`alpha` and target `releaseType` is `release`. Both label sets are explicit.
Missing fields, unknown fields, incorrect historical identity/status/type/labels
and target public readback mismatches fail closed. The complete manifest is
bound into upload intent; changing historical expectations invalidates intent.
Historical file relations (three), historical project relations (zero), and
target stable relations (five) are compared independently. `firstPublication`
still has no parent or transition fields and requires an empty inventory before
a new upload. This source implementation includes a guarded automatic mutation
stage, but this packet executes no tag, Release, workflow dispatch, secret value
readout, or upload. The stage remains inactive until it is reviewed, integrated,
and qualified on its exact canonical `main` head.
