# Guarded CurseForge publisher — source integration

## Current boundary

Version remains `0.1.1-alpha.9`; license remains **All Rights Reserved**.
Production CurseForge upload in this task: **NO**.
Publication: `BLOCKED_BY_MISSING_CURSEFORGE_PROJECT_CONFIGURATION`.
No authoritative existing target project ID/slug has been supplied or verified.
No GitHub Release exists at the audited baseline. Creating a project, tag,
release, secret or uploading is not authorized by this migration.

The publisher is source code, not proof of publication. An offline fixture
passing, a CI passing, and a live secret-free dry run are distinct evidence.
The original Prism smoke remains `NOT_PERFORMED / OWNER_WAIVED`.

## Files and provenance

`tools/release/publish_curseforge.py`, inherited tests and portability tests,
`curseforge_release.schema.json`, `curseforge_release_TEMPLATE.json`,
`.github/workflows/publish-curseforge.yml` and `build.yml` form the integration.
Upstream source/license details are in `tools/release/NOTICE.md`.

## Versioned manifests

Schema 2 requires `repository`, `release`, `curseforge` and `baseline`.
`baseline.mode=previousPublicFile` requires a real positive
`baseline.previousPublicFileId`. The parent public file's metadata and exact
relation baseline remain gates. `baseline.mode=firstPublication` contains no
parent ID, verifies the existing project's ID/slug, and requires an empty
public file inventory before a new upload. Accepted-file resume is read-only
and does not require the inventory to remain empty.

Both relation arrays are explicit. `[]` is valid; a missing array is invalid.
An expected empty public relation list rejects any additional public relation.
Legacy schema 1 remains supported with its real `curseforge.previousPublicFileId`.
New configuration should use schema 2. The schema is not a claim that inputs
have been reviewed; the Python validator also checks path confinement,
duplicate JSON keys, lookup-name subsets and the exact repository/tag.

The TEMPLATE is deliberately marked `template: true`, contains null unknowns,
and fails with `TEMPLATE_NOT_PUBLISHABLE` before network use. Its firstPublication
mode is an example, not a finding that a target project exists. An approved
versioned file may be made only after every real value and artifact is verified;
remove the template marker in that separately reviewed file. No alpha.9 approved
manifest was created during this task.

Pin exact JAR basename, bytes, SHA-256, mod ID and version. Pin an immutable
release-note path and SHA-256. The alpha.9 CurseForge release type is `alpha`.
Never repurpose a manifest-pinned changelog for mutable completion evidence.
The canonical GitHub release gate still requires a public, non-draft,
non-prerelease release; this was not silently relaxed for an alpha version.

## Safety protocol

Manual workflow inputs are tag, manifest_path, dry_run (default true), and
optional resume_file_id. The workflow uses contents:read/actions:read and
SHA-pinned actions. Concurrency is tag-scoped and non-cancelling. Publisher
unit tests run before all publication paths. The exact run title
`CurseForge <tag> :: publish` and step
`Persist upload intent before any POST` are durable protocol identifiers.

Prepare computes deterministic metadata/multipart hashes and binds the full
manifest hash. Its upload-intent artifact must be successfully persisted and
read back before one non-retried POST. Results and intents use distinct files.
The accepted file ID is atomically written before polling. A same-run exclusive
local POST journal prevents reuse even before remote result persistence.
Never delete `.cfpub-state/` to reopen an uncertain upload. Cross-run artifact
and job history reconciliation is exact-tag scoped, includes every run attempt,
and rejects malformed, ambiguous or missing result state. The artifact prefix
also hashes the raw tag to avoid lossy sanitization collisions.

Dry-run and explicit resume receive no CurseForge token. Only prepare and the
single upload step use the token. Credentialed HTTP redirects and POST
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

## Non-production validation

```bash
python -W error::ResourceWarning -m unittest discover -s tools/release -p 'test_*.py' -v
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
