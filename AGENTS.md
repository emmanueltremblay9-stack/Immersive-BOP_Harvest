# AGENTS.md

Scope: this repository, `Immersive BOP_Harvest`.

Default mode: pragmatic, verification-first, no false completion. Work directly
inside this project; do not ask Emmanuel to run PowerShell manually unless a
step truly requires user-only runtime validation.

## Project Surface

- Real project root: `C:\Users\Emmanuel Tremblay\AI Depot\Codex Documents\Immersive BOP_Harvest`
- Build system: Gradle wrapper, NeoForge ModDev, Java 21
- Primary config files: `settings.gradle`, `build.gradle`, `gradle.properties`,
  `src/main/templates/META-INF/neoforge.mods.toml`
- Mod ID: `immersive_bop_harvest`
- Runtime artifact: `build/libs/immersive_bop_harvest-<version>.jar`
- Local install/proof script: `scripts/install_alpha_to_lab.ps1`
- Current configured Prism target: `C:\Users\Emmanuel Tremblay\AppData\Roaming\PrismLauncher\instances\1.21.1 TesT play\minecraft\mods`

## Default Workflow

1. Inspect the project first: root, dirty state, loader, mod id/name/version,
   build system, relevant configs, and exact target output.
2. Use CodeGraph first when `.codegraph/` exists and is healthy. If there is no
   `.codegraph/`, continue with targeted file reads and `rg`.
3. Make only the requested changes and preserve unrelated dirty work.
4. Do not publish, upload, release, tag, or push release artifacts without
   explicit approval.
5. Use CI/sandbox workflow when present. If missing, do not add GitHub Actions
   unless requested.

## Minimum Checks After Changes

For code or resource changes, run the project wrapper from this repo:

```powershell
.\gradlew.bat compileJava processResources --stacktrace
.\gradlew.bat build --stacktrace
```

Run tests when tests exist or Java logic changed:

```powershell
.\gradlew.bat test --stacktrace
```

Use the existing project QA gates when the changed surface touches specs,
generated data, release proof, or manifest state:

```powershell
python scripts\validate_specs.py
python scripts\generate_alpha_resources.py
python scripts\qa_alpha_resources.py
python scripts\check_beta_release_gate.py
```

`check_beta_release_gate.py` may intentionally fail while license/client-smoke
release blockers remain; report that as blocked, not as a successful public
release gate.

## Runtime-Impacting Changes

- Run `.\gradlew.bat runClient --stacktrace` when client, render, GUI, model,
  language, registry, or content behavior changed and automated launch is
  feasible.
- Run `.\gradlew.bat runServer --stacktrace` when server, shared, datapack,
  loot, recipe, worldgen, or networking behavior changed and automated launch is
  feasible.
- Do not run full manual Minecraft validation after every tiny build.
- If runtime testing cannot be fully automated, record the exact untested manual
  runtime validation note.

## Release Prep Gate

Before considering release prep complete, require:

- clean build;
- CI pass if CI exists and is runnable;
- final jar path identified;
- changelog and version checked;
- runtime validation notes clear, including anything not tested;
- no public release blockers hidden or downgraded.

For this project, public release is still blocked while `mod_license` is
`LICENSE_PENDING`, no `LICENSE` file exists, or fresh client smoke is not
proven.

Owner exception for `0.1.1-alpha.9`: on 2026-07-13 Emmanuel explicitly
instructed Codex to skip the remaining Prism client test phase. Preserve the
client smoke as `NOT_PERFORMED / OWNER_WAIVED`; never convert it into a pass.
The release checker may accept only the complete, explicit waiver record in
`PROJECT_MANIFEST.json`. All other automated, artifact, install, metadata,
server and legal gates remain mandatory.

## Required Report

Report:

- files changed;
- exact commands run;
- PASS/FAIL result and exit status;
- warnings/errors that matter;
- final jar path if built;
- artifacts produced;
- anything not tested;
- safe to launch Minecraft: yes/no, only when supported by the evidence.

## Bounded Dedicated-Server Smoke

Gradle `runServer` does not reliably forward redirected standard input to the
Minecraft server console in this project. Use `scripts/run_server_smoke.ps1`.
The smoke passes only after a fresh log reaches the dedicated-server `Done (`
marker with the current mod version loaded. The script may then terminate the
known process tree to keep the run bounded; report that termination and the
underlying Gradle process exit separately. Any exit or crash before `Done (` is
a failed smoke, and production code must never be changed to hide it.
