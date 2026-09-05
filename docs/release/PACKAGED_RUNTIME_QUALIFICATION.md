# Packaged runtime qualification (S5)

You use this procedure to qualify `immersive_bop_harvest` **0.1.1-alpha.10**
under the production NeoForge loader, with disposable worlds and rendered
clients. The target is Minecraft 1.21.1, NeoForge 21.1.233 and Java 21.
The complete local seven-phase run passed on 2026-09-05; canonical-main S5
evidence readback remains **pending** in this source snapshot. See the
[audit](STABLE_RELEASE_AUDIT.md) for measured results and screenshot limits.
Commands below describe the repeatable procedure.

See [the release plan](STABLE_RELEASE_PLAN.md) for authorization and
[the acceptance matrix](STABLE_ACCEPTANCE_MATRIX.md) for remaining coverage.
S4's 305 development GameTests are a separate evidence class. Their result
does not establish a packaged client, multiplayer session or saved-world upgrade.

## Inputs and isolation

Run commands from the repository root with Python 3.11 or later, Java 21 and
Git on `PATH`. The client launcher supports Windows x64 and Linux x64. Linux
rendering requires a working display; CI supplies Xvfb and software OpenGL.
Prepare the exact five dependencies from
[`runtime-dependencies.lock.json`](../../tools/ci/runtime-dependencies.lock.json)
and a complete Minecraft asset directory containing the verified asset index
`17`. The existing ModDev runtime preparation records its asset directory in
`build/moddev/minecraft_assets.properties` as `assets_root`.

Choose a new runtime root outside personal Prism instances and worlds, such as
a fresh directory below `C:\AI-Work`. Each attempt owns only `server`,
`client-one` and `client-two` below that root. Preparation creates official
server and client launchers; optional installer, metadata, vanilla-JAR and
library caches supply hash-checked inputs. Downloads may be required.

Each running instance contains exactly seven mod JARs: the addon, the five
locked dependencies and the separate `bop_harvest_qa` harness. The production
addon excludes `src/qualification`. The harness runs only with an explicit
`bop.qa.phase`, matching ownership marker and nonce. It observes
`FMLLoader.isProduction()` and the actual loaded JAR paths, sizes and SHA-256
hashes. The five dependencies and harness stay identical across all seven
phases. Only the planned alpha.9-to-alpha.10 addon replacement is permitted;
subsequent candidate phases use identical alpha.10 bytes.

The runners reject linked/reparse paths, unowned nonempty mod directories,
unexpected files and changed staged bytes. Restarts require the immediately
preceding successful receipt, matching nonce, unchanged log and saved world.
Upgrade additionally requires a separate, verified copy of the complete
alpha.9 world. Preserve a failed attempt and choose a fresh runtime root;
do not manufacture a predecessor receipt or reuse phase output filenames.

The dedicated server binds to `127.0.0.1:25575`, permits two players and uses
offline identities `BopQaOne` and `BopQaTwo`. The launcher supplies dummy
authentication values. It does not read personal account profiles. The runner
writes `eula=true` and explicit test server properties inside its disposable
instance. This setup exercises local networking and inventory synchronization;
it does not validate online authentication or a public server deployment.

## Seven phases

The orchestrator runs the first four phases sequentially, makes the verified
backup after `baseline-restart`, then starts `multiplayer` and waits for its
fresh `Done (` log marker before launching both clients concurrently.

| Phase | Addon | Required behavior |
| --- | --- | --- |
| `baseline-create` | alpha.9 | Create a flat world; execute 302 scoped cases, 52 formed sawmills, a datapack reload and 100 repeated board operations. Save inventory, board input and an actual sawmill process paused halfway by redstone, then stop cleanly. |
| `baseline-restart` | alpha.9 | Compare persisted fixtures, process the retained board input, resume the saved sawmill queue and verify remaining energy/output without duplication. Save another paused process and stop. |
| `candidate-upgrade` | alpha.10 | Load the backed-up alpha.9 world, verify and operate restored state, then repeat the full scoped/machine/reload/repetition suite and save fresh continuity fixtures. |
| `candidate-restart` | alpha.10 | Verify and operate candidate save state, preserve another paused process, then stop cleanly. |
| `multiplayer` | alpha.10 | Load the candidate world; observe two real clients competing for one board input, exactly one tool durability cost and the combined authoritative outputs. Verify client-one's sawblade installation, machine outputs and knife harvest; confirm its disconnect/reconnect identity and inventory, then save after both clients leave. |
| `client-one` | alpha.10 | Capture the actual title screen; create a flat world through the client UI; run the full suite on its integrated server. Send actual board, sawblade and supported-webbing break interactions. Leave singleplayer, join the dedicated server, repeat the client interactions, reconnect and exit through the harness. |
| `client-two` | alpha.10 | Capture the title screen, join the same dedicated server, send competing board interactions, observe the server-confirmed result and client-one reconnect, then disconnect and exit. |

The 302 scoped cases comprise 64 board operations, 52 sawmill input cases,
19 harvest matrices, 162 native-loot cases, four scheduled cascades and common
tags. The additional 52 formed sawmills use real input/energy capabilities,
natural world ticks and receiving inventories at both output ports. The
Concurrent board use may normally leave an axe stored on FD's empty board.
The harness measures both axes, output totals and durability before cleanup,
then uses a single real empty-hand client interaction to retrieve any parked
axe. It checks the same totals again and requires both axes in player inventories.
The client sawmill check uses a real client packet to install the blade; the
harness then inserts the recipe input through the actual machine capability.
The client harvest check breaks supported BOP webbing with an FD knife and
measures the resulting string. These fixtures do not imply coverage of every
player placement action, biome, world configuration or dependency version.

## Run a disposable local attempt

Build the reviewed candidate and its harness before freezing the attempt.
On Windows, use the project wrapper:

```powershell
.\gradlew.bat --no-configuration-cache clean build qualificationJar -x syncRuntimeDeps --stacktrace
```

On Linux, use the equivalent wrapper invocation:

```bash
bash gradlew --no-configuration-cache clean build qualificationJar -x syncRuntimeDeps --stacktrace
```

The explicit `-x syncRuntimeDeps` excludes the personal Prism copy task. Keep
the ordinary S4 development and datagen checks in the workflow; this command
alone does not produce those receipts. If you run additional ModDev runtime
tasks, retain that same exclusion.

Replace `<NEW_BASELINE_DIR>` and `<NEW_RUNTIME_ROOT>` with distinct, unused
absolute directories. Replace `<ASSETS_ROOT>` with the existing complete
asset directory. These Python command templates work in PowerShell and Bash:

```text
python tools/ci/prepare_runtime.py
python tools/ci/build_qualification_baseline.py --output "<NEW_BASELINE_DIR>"
python tools/ci/prepare_production_runtime.py --root "<NEW_RUNTIME_ROOT>"
python tools/ci/qualify_packaged_runtime.py --root "<NEW_RUNTIME_ROOT>" --assets "<ASSETS_ROOT>" --dependencies "build/runtime-deps" --baseline "<NEW_BASELINE_DIR>/immersive_bop_harvest-0.1.1-alpha.9.jar" --candidate "build/libs/immersive_bop_harvest-0.1.1-alpha.10.jar" --harness "build/qualification-harness/bop-harvest-qualification-harness-1.jar" --hide-windows
```

`--hide-windows` hides the local GLFW windows while retaining rendering and
screenshots. Omit it to observe the test windows. On Linux without a desktop,
run the final qualification command inside an existing Xvfb setup using
`xvfb-run -a -s "-screen 0 1280x720x24 -nolisten tcp"` and set
`LIBGL_ALWAYS_SOFTWARE=true`. A missing or unusable renderer is a failed
environment prerequisite, never a client pass.

The baseline builder freezes commit
`ee525b9d9406b030e17d87249219c007f97af47c` and verifies tree
`d2554e12f732ee13496246823afe78f156d2fd2b`. It archives that Git source into a
new directory, performs a clean build and retains the resulting alpha.9 JAR
with its raw hash. It may fetch the fixed commit from `origin` when absent.
This is a **rebuild of reviewed historical source**. It is not proof that the
JAR equals an older published/downloaded alpha.9 file. Identify the actual
baseline by its receipt and bytes; do not substitute historical artifact
identity without independently checking equality.

## Run through CI

The existing [build workflow](../../.github/workflows/build.yml) builds the
harness and fixed baseline after development QA. Its production step uses:

```bash
LIBGL_ALWAYS_SOFTWARE=true xvfb-run -a -s '-screen 0 1280x720x24 -nolisten tcp' python tools/ci/run_production_ci.py
python tools/ci/candidate_evidence.py collect
```

These are CI commands. `run_production_ci.py` requires the actual GitHub
Actions context and `DISPLAY`; it reads ModDev's asset properties and creates
`build/production-runtime`. `collect` requires CI context and the complete
development and packaged evidence. Use the local entry points above for a
local attempt. Both routes execute the same seven-phase orchestrator.

## Budgets and performance interpretation

| Bound or measurement | Meaning |
| --- | --- |
| Baseline build: 600 seconds; each official installer: 1,200 seconds | Separate preparation limits. |
| Dedicated phase: 600 seconds and 6,000 server ticks | Either exhausted budget prevents qualification. The wrapper allows 30 seconds for a requested stop before termination. |
| Client: 900 seconds and 10,000 client ticks | A cancelled client gets 20 seconds for its harness exit; timeout/abort fails even if the process returns zero. |
| Multiplayer readiness: 180 seconds | Clients start only after the server's fresh ready marker. |
| Formed sawmills: 400 ticks; continuity: 150 ticks plus a five-tick pause check | Bounded processing and observed persistence checks. |
| CI orchestrator: 2,400 seconds; Linux CI job: 55 minutes | The orchestrator limit applies after launcher preparation; the job limit covers the workflow. |
| Process wall duration, log byte count, server ticks, scoped/repeated nanoseconds | Recorded per phase where applicable, plus the candidate-upgrade/baseline-create wall-duration ratio. |

Tick limits are not wall-clock equivalences. The duration ratio is diagnostic:
upgrade also resumes restored state, and cache/renderer conditions can differ.
There is no calibrated performance regression threshold, FPS target, heap
growth test, long-duration soak or general modpack performance claim. The
100 repeated board operations establish a bounded repetition workload with
observed outputs and timing.

## Raw evidence and independent readback

Keep the runtime root until its evidence is captured. It contains:

- `receipts/<phase>.json` and `.log` for all seven processes, with exact
  command arguments, exit status, duration, nonce and raw-log identity.
- The preparation and orchestration receipts, installer logs and verified
  `alpha9-world-backup.json` inventory; the baseline directory separately
  retains its source/build receipt, build log and raw JAR.
- Client common runtime receipts, client action receipts and exit-hook
  receipts; nine client-one PNG stages and three client-two PNG stages.
- The actual staged harness and per-instance plans binding the seven JARs.

`production_evidence.collect` copies the fixed inventory into flat
`production-*` files. `production_evidence.validate` checks the phase chain,
exact JARs and embedded specifications, observed assertions, resumed state,
client events, PNG structure/hashes and clean completion. It returns
`INTEGRITY_ONLY_PACKAGED_EXECUTION`, `authenticatedExecution=false` and
`stableReady=false`. PNG validity and hashes do not replace visual inspection
of what the screenshots show.

CI collection adds these files to `build/candidate-evidence`; the workflow
retains `candidate-evidence-<run-id>-<attempt>` for 30 days. Uploading a bundle
alone does not authenticate execution. After reviewed integration, supply the
expected main commit independently and use the existing authenticated `gh`
session for read-only service verification:

```text
python tools/ci/candidate_evidence.py verify --run-id <RUN_ID> --attempt <ATTEMPT> --expected-commit <REVIEWED_MAIN_COMMIT>
python scripts/check_stable_release_gate.py --ci-run-id <RUN_ID> --ci-attempt <ATTEMPT> --expected-commit <REVIEWED_MAIN_COMMIT>
```

The verifier reads the exact GitHub run attempt, required jobs/steps, source
tree, lock, specifications and archive. It requires a successful canonical
`main` push, the expected commit, complete inventory and matching service
SHA-256 digest before it can return `AUTHENTICATED_PACKAGED_EXECUTION`.
Pull-request CI, local receipts and submitted PASS flags do not meet that
provenance contract. Missing, failed, aborted, stale or expired evidence
remains a failed or blocked gate; retain the raw reason.

Even authenticated S5 capabilities leave `stableReady=false`. S6's final
stable-version choice and final release bundle remain outside this procedure,
as do publication, uploads, tags/releases and personal Prism installation.
The historical alpha.9 Prism smoke waiver remains
`NOT_PERFORMED / OWNER_WAIVED`; this disposable qualification does not rewrite it.
