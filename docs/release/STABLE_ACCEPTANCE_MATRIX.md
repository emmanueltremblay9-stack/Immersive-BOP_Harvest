# Stable acceptance matrix

Current qualification follow-up: S4 passed canonical run `33984397632`, attempt 1,
at merge `1b84049fe53d59b1b263ee11942be304c441cab6`, with independent readback.
It adds 302 runtime cases in the separate
qualification harness for alpha.10; see `tools/ci/qualification_report.py` for
the exact source-derived case inventory and required observed assertions.
Cases map Cutting Board inputs, every wood form, direct-harvest blocks and
the native-only coverage inventory directly to the corresponding spec IDs.
Four plant-cascade tests wait for scheduled destruction. S3-A authenticates
the CI execution and report against the expected source commit.
S5 adds a seven-phase production runner with formed machines, actual client
packets, multiplayer tool/output conservation and clean world migration.
All seven local S5 phases and the strict validator passed against the frozen
canonical S4 JAR. S5 CI and canonical authentication remain pending; see the
[runbook](PACKAGED_RUNTIME_QUALIFICATION.md) and [audit](STABLE_RELEASE_AUDIT.md).

The rows below retain their future **final stable candidate** meaning; alpha.10
development tests do not satisfy packaged client/server/multiplayer, formed
sawmill ports, save/reload or final-version obligations. The previous text about
missing runtime authority is historical: the owner now authorized S3-A/S4/S5.

Maintenance baseline: afc9237294faa5c86d56d8228f64ac4e1bfbb2f1.
This is a requirement-to-evidence map, not a runtime result. Every row below is
NOT_PERFORMED for a future stable candidate. Static generators/checks exist in
scripts/validate_specs.py and scripts/qa_alpha_resources.py. Existing GameTests
prove namespace, 103 recipe presence and vanilla-shears tag membership only.
Those original three tests alone do not prove FD/IE processing, direct harvest,
save/reload or multiplayer. The current S4/S5 harness provides the additional
observations; the table retains its separate final-version requirement.

Receipt kinds client/server/multiplayer/gameplay/save_reload are mandatory in
addition to automated checks. Title-screen evidence cannot substitute for
other kinds. Chance rules need deterministic controlled-random tests, not
unbounded sampling. Wood tests must cover all 13 families and both forms;
harvest tests must include hand/wrong tool/shears/Silk Touch/Fortune, foreign
loot contexts, duplicate application, lower halves and destroyed segments.
Missing runtime authority remains NOT_AUTHORIZED, not NOT_APPLICABLE.

The catalog is derived by check_stable_release_gate.acceptance_catalog from
all 39 QA checkboxes and every top-level spec entry/policy. IDs bind to the
source commit/tree; a changed spec/QA document requires a new candidate.

| Acceptance ID | Authoritative source | Required receipt | Candidate state |
|---|---|---|---|
| `qa:4` | `docs/QA_ACCEPTANCE.md:4` | automated | NOT_PERFORMED |
| `qa:5` | `docs/QA_ACCEPTANCE.md:5` | automated | NOT_PERFORMED |
| `qa:6` | `docs/QA_ACCEPTANCE.md:6` | automated | NOT_PERFORMED |
| `qa:7` | `docs/QA_ACCEPTANCE.md:7` | automated | NOT_PERFORMED |
| `qa:10` | `docs/QA_ACCEPTANCE.md:10` | automated | NOT_PERFORMED |
| `qa:11` | `docs/QA_ACCEPTANCE.md:11` | automated | NOT_PERFORMED |
| `qa:12` | `docs/QA_ACCEPTANCE.md:12` | automated | NOT_PERFORMED |
| `qa:13` | `docs/QA_ACCEPTANCE.md:13` | automated | NOT_PERFORMED |
| `qa:16` | `docs/QA_ACCEPTANCE.md:16` | automated | NOT_PERFORMED |
| `qa:17` | `docs/QA_ACCEPTANCE.md:17` | server | NOT_PERFORMED |
| `qa:18` | `docs/QA_ACCEPTANCE.md:18` | server | NOT_PERFORMED |
| `qa:21` | `docs/QA_ACCEPTANCE.md:21` | gameplay | NOT_PERFORMED |
| `qa:22` | `docs/QA_ACCEPTANCE.md:22` | gameplay | NOT_PERFORMED |
| `qa:23` | `docs/QA_ACCEPTANCE.md:23` | gameplay | NOT_PERFORMED |
| `qa:24` | `docs/QA_ACCEPTANCE.md:24` | gameplay | NOT_PERFORMED |
| `qa:25` | `docs/QA_ACCEPTANCE.md:25` | gameplay | NOT_PERFORMED |
| `qa:28` | `docs/QA_ACCEPTANCE.md:28` | gameplay | NOT_PERFORMED |
| `qa:29` | `docs/QA_ACCEPTANCE.md:29` | gameplay | NOT_PERFORMED |
| `qa:30` | `docs/QA_ACCEPTANCE.md:30` | gameplay | NOT_PERFORMED |
| `qa:31` | `docs/QA_ACCEPTANCE.md:31` | gameplay | NOT_PERFORMED |
| `qa:32` | `docs/QA_ACCEPTANCE.md:32` | gameplay | NOT_PERFORMED |
| `qa:35` | `docs/QA_ACCEPTANCE.md:35` | gameplay | NOT_PERFORMED |
| `qa:36` | `docs/QA_ACCEPTANCE.md:36` | gameplay | NOT_PERFORMED |
| `qa:37` | `docs/QA_ACCEPTANCE.md:37` | gameplay | NOT_PERFORMED |
| `qa:38` | `docs/QA_ACCEPTANCE.md:38` | gameplay | NOT_PERFORMED |
| `qa:39` | `docs/QA_ACCEPTANCE.md:39` | gameplay | NOT_PERFORMED |
| `qa:40` | `docs/QA_ACCEPTANCE.md:40` | gameplay | NOT_PERFORMED |
| `qa:41` | `docs/QA_ACCEPTANCE.md:41` | gameplay | NOT_PERFORMED |
| `qa:42` | `docs/QA_ACCEPTANCE.md:42` | gameplay | NOT_PERFORMED |
| `qa:43` | `docs/QA_ACCEPTANCE.md:43` | gameplay | NOT_PERFORMED |
| `qa:46` | `docs/QA_ACCEPTANCE.md:46` | gameplay | NOT_PERFORMED |
| `qa:47` | `docs/QA_ACCEPTANCE.md:47` | gameplay | NOT_PERFORMED |
| `qa:48` | `docs/QA_ACCEPTANCE.md:48` | gameplay | NOT_PERFORMED |
| `qa:49` | `docs/QA_ACCEPTANCE.md:49` | gameplay | NOT_PERFORMED |
| `qa:52` | `docs/QA_ACCEPTANCE.md:52` | automated | NOT_PERFORMED |
| `qa:53` | `docs/QA_ACCEPTANCE.md:53` | automated | NOT_PERFORMED |
| `qa:54` | `docs/QA_ACCEPTANCE.md:54` | automated | NOT_PERFORMED |
| `qa:55` | `docs/QA_ACCEPTANCE.md:55` | automated | NOT_PERFORMED |
| `qa:56` | `docs/QA_ACCEPTANCE.md:56` | client | NOT_PERFORMED |
| `spec:coverage_inventory/target` | `spec/coverage_inventory.json#/target` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/root_policy` | `spec/coverage_inventory.json#/root_policy` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/0` | `spec/coverage_inventory.json#/wood_processing/0` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/1` | `spec/coverage_inventory.json#/wood_processing/1` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/2` | `spec/coverage_inventory.json#/wood_processing/2` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/3` | `spec/coverage_inventory.json#/wood_processing/3` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/4` | `spec/coverage_inventory.json#/wood_processing/4` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/5` | `spec/coverage_inventory.json#/wood_processing/5` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/6` | `spec/coverage_inventory.json#/wood_processing/6` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/7` | `spec/coverage_inventory.json#/wood_processing/7` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/8` | `spec/coverage_inventory.json#/wood_processing/8` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/9` | `spec/coverage_inventory.json#/wood_processing/9` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/10` | `spec/coverage_inventory.json#/wood_processing/10` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/11` | `spec/coverage_inventory.json#/wood_processing/11` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/12` | `spec/coverage_inventory.json#/wood_processing/12` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/13` | `spec/coverage_inventory.json#/wood_processing/13` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/14` | `spec/coverage_inventory.json#/wood_processing/14` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/15` | `spec/coverage_inventory.json#/wood_processing/15` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/16` | `spec/coverage_inventory.json#/wood_processing/16` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/17` | `spec/coverage_inventory.json#/wood_processing/17` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/18` | `spec/coverage_inventory.json#/wood_processing/18` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/19` | `spec/coverage_inventory.json#/wood_processing/19` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/20` | `spec/coverage_inventory.json#/wood_processing/20` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/21` | `spec/coverage_inventory.json#/wood_processing/21` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/22` | `spec/coverage_inventory.json#/wood_processing/22` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/23` | `spec/coverage_inventory.json#/wood_processing/23` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/24` | `spec/coverage_inventory.json#/wood_processing/24` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/25` | `spec/coverage_inventory.json#/wood_processing/25` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/26` | `spec/coverage_inventory.json#/wood_processing/26` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/27` | `spec/coverage_inventory.json#/wood_processing/27` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/28` | `spec/coverage_inventory.json#/wood_processing/28` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/29` | `spec/coverage_inventory.json#/wood_processing/29` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/30` | `spec/coverage_inventory.json#/wood_processing/30` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/31` | `spec/coverage_inventory.json#/wood_processing/31` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/32` | `spec/coverage_inventory.json#/wood_processing/32` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/33` | `spec/coverage_inventory.json#/wood_processing/33` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/34` | `spec/coverage_inventory.json#/wood_processing/34` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/35` | `spec/coverage_inventory.json#/wood_processing/35` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/36` | `spec/coverage_inventory.json#/wood_processing/36` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/37` | `spec/coverage_inventory.json#/wood_processing/37` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/38` | `spec/coverage_inventory.json#/wood_processing/38` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/39` | `spec/coverage_inventory.json#/wood_processing/39` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/40` | `spec/coverage_inventory.json#/wood_processing/40` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/41` | `spec/coverage_inventory.json#/wood_processing/41` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/42` | `spec/coverage_inventory.json#/wood_processing/42` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/43` | `spec/coverage_inventory.json#/wood_processing/43` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/44` | `spec/coverage_inventory.json#/wood_processing/44` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/45` | `spec/coverage_inventory.json#/wood_processing/45` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/46` | `spec/coverage_inventory.json#/wood_processing/46` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/47` | `spec/coverage_inventory.json#/wood_processing/47` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/48` | `spec/coverage_inventory.json#/wood_processing/48` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/49` | `spec/coverage_inventory.json#/wood_processing/49` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/50` | `spec/coverage_inventory.json#/wood_processing/50` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/51` | `spec/coverage_inventory.json#/wood_processing/51` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/52` | `spec/coverage_inventory.json#/wood_processing/52` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/53` | `spec/coverage_inventory.json#/wood_processing/53` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/54` | `spec/coverage_inventory.json#/wood_processing/54` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/55` | `spec/coverage_inventory.json#/wood_processing/55` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/56` | `spec/coverage_inventory.json#/wood_processing/56` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/57` | `spec/coverage_inventory.json#/wood_processing/57` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/58` | `spec/coverage_inventory.json#/wood_processing/58` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/59` | `spec/coverage_inventory.json#/wood_processing/59` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/60` | `spec/coverage_inventory.json#/wood_processing/60` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/61` | `spec/coverage_inventory.json#/wood_processing/61` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/62` | `spec/coverage_inventory.json#/wood_processing/62` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/63` | `spec/coverage_inventory.json#/wood_processing/63` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/wood_processing/64` | `spec/coverage_inventory.json#/wood_processing/64` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/flowers/0` | `spec/coverage_inventory.json#/flowers/0` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/flowers/1` | `spec/coverage_inventory.json#/flowers/1` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/flowers/2` | `spec/coverage_inventory.json#/flowers/2` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/flowers/3` | `spec/coverage_inventory.json#/flowers/3` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/flowers/4` | `spec/coverage_inventory.json#/flowers/4` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/flowers/5` | `spec/coverage_inventory.json#/flowers/5` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/flowers/6` | `spec/coverage_inventory.json#/flowers/6` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/flowers/7` | `spec/coverage_inventory.json#/flowers/7` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/flowers/8` | `spec/coverage_inventory.json#/flowers/8` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/flowers/9` | `spec/coverage_inventory.json#/flowers/9` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/flowers/10` | `spec/coverage_inventory.json#/flowers/10` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/flowers/11` | `spec/coverage_inventory.json#/flowers/11` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/flowers/12` | `spec/coverage_inventory.json#/flowers/12` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/flowers/13` | `spec/coverage_inventory.json#/flowers/13` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/flowers/14` | `spec/coverage_inventory.json#/flowers/14` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/flowers/15` | `spec/coverage_inventory.json#/flowers/15` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/flowers/16` | `spec/coverage_inventory.json#/flowers/16` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/flowers/17` | `spec/coverage_inventory.json#/flowers/17` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/plants/0` | `spec/coverage_inventory.json#/plants/0` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/plants/1` | `spec/coverage_inventory.json#/plants/1` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/plants/2` | `spec/coverage_inventory.json#/plants/2` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/plants/3` | `spec/coverage_inventory.json#/plants/3` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/plants/4` | `spec/coverage_inventory.json#/plants/4` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/plants/5` | `spec/coverage_inventory.json#/plants/5` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/plants/6` | `spec/coverage_inventory.json#/plants/6` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/plants/7` | `spec/coverage_inventory.json#/plants/7` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/plants/8` | `spec/coverage_inventory.json#/plants/8` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/plants/9` | `spec/coverage_inventory.json#/plants/9` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/plants/10` | `spec/coverage_inventory.json#/plants/10` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/plants/11` | `spec/coverage_inventory.json#/plants/11` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/plants/12` | `spec/coverage_inventory.json#/plants/12` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/plants/13` | `spec/coverage_inventory.json#/plants/13` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/plants/14` | `spec/coverage_inventory.json#/plants/14` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/plants/15` | `spec/coverage_inventory.json#/plants/15` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/plants/16` | `spec/coverage_inventory.json#/plants/16` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/plants/17` | `spec/coverage_inventory.json#/plants/17` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/plants/18` | `spec/coverage_inventory.json#/plants/18` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/plants/19` | `spec/coverage_inventory.json#/plants/19` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/plants/20` | `spec/coverage_inventory.json#/plants/20` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/plants/21` | `spec/coverage_inventory.json#/plants/21` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/plants/22` | `spec/coverage_inventory.json#/plants/22` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/woodless_trees/0` | `spec/coverage_inventory.json#/woodless_trees/0` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/woodless_trees/1` | `spec/coverage_inventory.json#/woodless_trees/1` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/woodless_trees/2` | `spec/coverage_inventory.json#/woodless_trees/2` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/woodless_trees/3` | `spec/coverage_inventory.json#/woodless_trees/3` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/woodless_trees/4` | `spec/coverage_inventory.json#/woodless_trees/4` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/woodless_trees/5` | `spec/coverage_inventory.json#/woodless_trees/5` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/woodless_trees/6` | `spec/coverage_inventory.json#/woodless_trees/6` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/woodless_trees/7` | `spec/coverage_inventory.json#/woodless_trees/7` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/woodless_trees/8` | `spec/coverage_inventory.json#/woodless_trees/8` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/woodless_trees/9` | `spec/coverage_inventory.json#/woodless_trees/9` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/potted_plants/0` | `spec/coverage_inventory.json#/potted_plants/0` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/potted_plants/1` | `spec/coverage_inventory.json#/potted_plants/1` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/potted_plants/2` | `spec/coverage_inventory.json#/potted_plants/2` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/potted_plants/3` | `spec/coverage_inventory.json#/potted_plants/3` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/potted_plants/4` | `spec/coverage_inventory.json#/potted_plants/4` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/potted_plants/5` | `spec/coverage_inventory.json#/potted_plants/5` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/potted_plants/6` | `spec/coverage_inventory.json#/potted_plants/6` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/potted_plants/7` | `spec/coverage_inventory.json#/potted_plants/7` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/potted_plants/8` | `spec/coverage_inventory.json#/potted_plants/8` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/potted_plants/9` | `spec/coverage_inventory.json#/potted_plants/9` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/potted_plants/10` | `spec/coverage_inventory.json#/potted_plants/10` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/potted_plants/11` | `spec/coverage_inventory.json#/potted_plants/11` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/potted_plants/12` | `spec/coverage_inventory.json#/potted_plants/12` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/potted_plants/13` | `spec/coverage_inventory.json#/potted_plants/13` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/potted_plants/14` | `spec/coverage_inventory.json#/potted_plants/14` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/potted_plants/15` | `spec/coverage_inventory.json#/potted_plants/15` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/potted_plants/16` | `spec/coverage_inventory.json#/potted_plants/16` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/potted_plants/17` | `spec/coverage_inventory.json#/potted_plants/17` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/potted_plants/18` | `spec/coverage_inventory.json#/potted_plants/18` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/potted_plants/19` | `spec/coverage_inventory.json#/potted_plants/19` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/potted_plants/20` | `spec/coverage_inventory.json#/potted_plants/20` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/potted_plants/21` | `spec/coverage_inventory.json#/potted_plants/21` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/potted_plants/22` | `spec/coverage_inventory.json#/potted_plants/22` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/potted_plants/23` | `spec/coverage_inventory.json#/potted_plants/23` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/potted_plants/24` | `spec/coverage_inventory.json#/potted_plants/24` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/potted_plants/25` | `spec/coverage_inventory.json#/potted_plants/25` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/potted_plants/26` | `spec/coverage_inventory.json#/potted_plants/26` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/potted_plants/27` | `spec/coverage_inventory.json#/potted_plants/27` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/potted_plants/28` | `spec/coverage_inventory.json#/potted_plants/28` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/potted_plants/29` | `spec/coverage_inventory.json#/potted_plants/29` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/potted_plants/30` | `spec/coverage_inventory.json#/potted_plants/30` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/potted_plants/31` | `spec/coverage_inventory.json#/potted_plants/31` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/potted_plants/32` | `spec/coverage_inventory.json#/potted_plants/32` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/potted_plants/33` | `spec/coverage_inventory.json#/potted_plants/33` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/potted_plants/34` | `spec/coverage_inventory.json#/potted_plants/34` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/mushrooms_moss/0` | `spec/coverage_inventory.json#/mushrooms_moss/0` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/mushrooms_moss/1` | `spec/coverage_inventory.json#/mushrooms_moss/1` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/mushrooms_moss/2` | `spec/coverage_inventory.json#/mushrooms_moss/2` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/mushrooms_moss/3` | `spec/coverage_inventory.json#/mushrooms_moss/3` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/mushrooms_moss/4` | `spec/coverage_inventory.json#/mushrooms_moss/4` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/mushrooms_moss/5` | `spec/coverage_inventory.json#/mushrooms_moss/5` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/mushrooms_moss/6` | `spec/coverage_inventory.json#/mushrooms_moss/6` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/mushrooms_moss/7` | `spec/coverage_inventory.json#/mushrooms_moss/7` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/mushrooms_moss/8` | `spec/coverage_inventory.json#/mushrooms_moss/8` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/web_fiber/0` | `spec/coverage_inventory.json#/web_fiber/0` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/web_fiber/1` | `spec/coverage_inventory.json#/web_fiber/1` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/web_fiber/2` | `spec/coverage_inventory.json#/web_fiber/2` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/web_fiber/3` | `spec/coverage_inventory.json#/web_fiber/3` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/web_fiber/4` | `spec/coverage_inventory.json#/web_fiber/4` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/web_fiber/5` | `spec/coverage_inventory.json#/web_fiber/5` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/web_fiber/6` | `spec/coverage_inventory.json#/web_fiber/6` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/flesh_organic/0` | `spec/coverage_inventory.json#/flesh_organic/0` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/flesh_organic/1` | `spec/coverage_inventory.json#/flesh_organic/1` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/flesh_organic/2` | `spec/coverage_inventory.json#/flesh_organic/2` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/flesh_organic/3` | `spec/coverage_inventory.json#/flesh_organic/3` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/flesh_organic/4` | `spec/coverage_inventory.json#/flesh_organic/4` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/flesh_organic/5` | `spec/coverage_inventory.json#/flesh_organic/5` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/flesh_organic/6` | `spec/coverage_inventory.json#/flesh_organic/6` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/end_organic/0` | `spec/coverage_inventory.json#/end_organic/0` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/end_organic/1` | `spec/coverage_inventory.json#/end_organic/1` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/end_organic/2` | `spec/coverage_inventory.json#/end_organic/2` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/end_organic/3` | `spec/coverage_inventory.json#/end_organic/3` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/end_organic/4` | `spec/coverage_inventory.json#/end_organic/4` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/end_organic/5` | `spec/coverage_inventory.json#/end_organic/5` | gameplay | NOT_PERFORMED |
| `spec:coverage_inventory/end_organic/6` | `spec/coverage_inventory.json#/end_organic/6` | gameplay | NOT_PERFORMED |
| `spec:direct_harvest_rules/policy` | `spec/direct_harvest_rules.json#/policy` | gameplay | NOT_PERFORMED |
| `spec:direct_harvest_rules/rules/0` | `spec/direct_harvest_rules.json#/rules/0` | gameplay | NOT_PERFORMED |
| `spec:direct_harvest_rules/rules/1` | `spec/direct_harvest_rules.json#/rules/1` | gameplay | NOT_PERFORMED |
| `spec:direct_harvest_rules/rules/2` | `spec/direct_harvest_rules.json#/rules/2` | gameplay | NOT_PERFORMED |
| `spec:direct_harvest_rules/rules/3` | `spec/direct_harvest_rules.json#/rules/3` | gameplay | NOT_PERFORMED |
| `spec:direct_harvest_rules/rules/4` | `spec/direct_harvest_rules.json#/rules/4` | gameplay | NOT_PERFORMED |
| `spec:direct_harvest_rules/rules/5` | `spec/direct_harvest_rules.json#/rules/5` | gameplay | NOT_PERFORMED |
| `spec:direct_harvest_rules/rules/6` | `spec/direct_harvest_rules.json#/rules/6` | gameplay | NOT_PERFORMED |
| `spec:direct_harvest_rules/rules/7` | `spec/direct_harvest_rules.json#/rules/7` | gameplay | NOT_PERFORMED |
| `spec:direct_harvest_rules/rules/8` | `spec/direct_harvest_rules.json#/rules/8` | gameplay | NOT_PERFORMED |
| `spec:direct_harvest_rules/rules/9` | `spec/direct_harvest_rules.json#/rules/9` | gameplay | NOT_PERFORMED |
| `spec:direct_harvest_rules/explicit_exclusion` | `spec/direct_harvest_rules.json#/explicit_exclusion` | gameplay | NOT_PERFORMED |
| `spec:flower_cutting_recipes/policy` | `spec/flower_cutting_recipes.json#/policy` | gameplay | NOT_PERFORMED |
| `spec:flower_cutting_recipes/tool` | `spec/flower_cutting_recipes.json#/tool` | gameplay | NOT_PERFORMED |
| `spec:flower_cutting_recipes/recipes/0` | `spec/flower_cutting_recipes.json#/recipes/0` | gameplay | NOT_PERFORMED |
| `spec:flower_cutting_recipes/recipes/1` | `spec/flower_cutting_recipes.json#/recipes/1` | gameplay | NOT_PERFORMED |
| `spec:flower_cutting_recipes/recipes/2` | `spec/flower_cutting_recipes.json#/recipes/2` | gameplay | NOT_PERFORMED |
| `spec:flower_cutting_recipes/recipes/3` | `spec/flower_cutting_recipes.json#/recipes/3` | gameplay | NOT_PERFORMED |
| `spec:flower_cutting_recipes/recipes/4` | `spec/flower_cutting_recipes.json#/recipes/4` | gameplay | NOT_PERFORMED |
| `spec:flower_cutting_recipes/recipes/5` | `spec/flower_cutting_recipes.json#/recipes/5` | gameplay | NOT_PERFORMED |
| `spec:flower_cutting_recipes/recipes/6` | `spec/flower_cutting_recipes.json#/recipes/6` | gameplay | NOT_PERFORMED |
| `spec:flower_cutting_recipes/recipes/7` | `spec/flower_cutting_recipes.json#/recipes/7` | gameplay | NOT_PERFORMED |
| `spec:flower_cutting_recipes/recipes/8` | `spec/flower_cutting_recipes.json#/recipes/8` | gameplay | NOT_PERFORMED |
| `spec:flower_cutting_recipes/recipes/9` | `spec/flower_cutting_recipes.json#/recipes/9` | gameplay | NOT_PERFORMED |
| `spec:flower_cutting_recipes/recipes/10` | `spec/flower_cutting_recipes.json#/recipes/10` | gameplay | NOT_PERFORMED |
| `spec:flower_cutting_recipes/recipes/11` | `spec/flower_cutting_recipes.json#/recipes/11` | gameplay | NOT_PERFORMED |
| `spec:flower_cutting_recipes/recipes/12` | `spec/flower_cutting_recipes.json#/recipes/12` | gameplay | NOT_PERFORMED |
| `spec:flower_cutting_recipes/recipes/13` | `spec/flower_cutting_recipes.json#/recipes/13` | gameplay | NOT_PERFORMED |
| `spec:flower_cutting_recipes/recipes/14` | `spec/flower_cutting_recipes.json#/recipes/14` | gameplay | NOT_PERFORMED |
| `spec:flower_cutting_recipes/recipes/15` | `spec/flower_cutting_recipes.json#/recipes/15` | gameplay | NOT_PERFORMED |
| `spec:flower_cutting_recipes/recipes/16` | `spec/flower_cutting_recipes.json#/recipes/16` | gameplay | NOT_PERFORMED |
| `spec:flower_cutting_recipes/recipes/17` | `spec/flower_cutting_recipes.json#/recipes/17` | gameplay | NOT_PERFORMED |
| `spec:flower_cutting_recipes/recipes/18` | `spec/flower_cutting_recipes.json#/recipes/18` | gameplay | NOT_PERFORMED |
| `spec:flower_cutting_recipes/recipes/19` | `spec/flower_cutting_recipes.json#/recipes/19` | gameplay | NOT_PERFORMED |
| `spec:forbidden_outputs/forbidden/0` | `spec/forbidden_outputs.json#/forbidden/0` | gameplay | NOT_PERFORMED |
| `spec:forbidden_outputs/forbidden/1` | `spec/forbidden_outputs.json#/forbidden/1` | gameplay | NOT_PERFORMED |
| `spec:forbidden_outputs/forbidden/2` | `spec/forbidden_outputs.json#/forbidden/2` | gameplay | NOT_PERFORMED |
| `spec:forbidden_outputs/forbidden/3` | `spec/forbidden_outputs.json#/forbidden/3` | gameplay | NOT_PERFORMED |
| `spec:forbidden_outputs/forbidden/4` | `spec/forbidden_outputs.json#/forbidden/4` | gameplay | NOT_PERFORMED |
| `spec:forbidden_outputs/forbidden/5` | `spec/forbidden_outputs.json#/forbidden/5` | gameplay | NOT_PERFORMED |
| `spec:forbidden_outputs/forbidden/6` | `spec/forbidden_outputs.json#/forbidden/6` | gameplay | NOT_PERFORMED |
| `spec:forbidden_outputs/forbidden/7` | `spec/forbidden_outputs.json#/forbidden/7` | gameplay | NOT_PERFORMED |
| `spec:forbidden_outputs/forbidden/8` | `spec/forbidden_outputs.json#/forbidden/8` | gameplay | NOT_PERFORMED |
| `spec:forbidden_outputs/forbidden/9` | `spec/forbidden_outputs.json#/forbidden/9` | gameplay | NOT_PERFORMED |
| `spec:forbidden_outputs/forbidden/10` | `spec/forbidden_outputs.json#/forbidden/10` | gameplay | NOT_PERFORMED |
| `spec:forbidden_outputs/forbidden/11` | `spec/forbidden_outputs.json#/forbidden/11` | gameplay | NOT_PERFORMED |
| `spec:forbidden_outputs/forbidden/12` | `spec/forbidden_outputs.json#/forbidden/12` | gameplay | NOT_PERFORMED |
| `spec:forbidden_outputs/rules/0` | `spec/forbidden_outputs.json#/rules/0` | gameplay | NOT_PERFORMED |
| `spec:forbidden_outputs/rules/1` | `spec/forbidden_outputs.json#/rules/1` | gameplay | NOT_PERFORMED |
| `spec:forbidden_outputs/rules/2` | `spec/forbidden_outputs.json#/rules/2` | gameplay | NOT_PERFORMED |
| `spec:plant_cutting_recipes/policy` | `spec/plant_cutting_recipes.json#/policy` | gameplay | NOT_PERFORMED |
| `spec:plant_cutting_recipes/recipes/0` | `spec/plant_cutting_recipes.json#/recipes/0` | gameplay | NOT_PERFORMED |
| `spec:plant_cutting_recipes/recipes/1` | `spec/plant_cutting_recipes.json#/recipes/1` | gameplay | NOT_PERFORMED |
| `spec:plant_cutting_recipes/recipes/2` | `spec/plant_cutting_recipes.json#/recipes/2` | gameplay | NOT_PERFORMED |
| `spec:plant_cutting_recipes/recipes/3` | `spec/plant_cutting_recipes.json#/recipes/3` | gameplay | NOT_PERFORMED |
| `spec:plant_cutting_recipes/recipes/4` | `spec/plant_cutting_recipes.json#/recipes/4` | gameplay | NOT_PERFORMED |
| `spec:plant_cutting_recipes/recipes/5` | `spec/plant_cutting_recipes.json#/recipes/5` | gameplay | NOT_PERFORMED |
| `spec:plant_cutting_recipes/recipes/6` | `spec/plant_cutting_recipes.json#/recipes/6` | gameplay | NOT_PERFORMED |
| `spec:plant_cutting_recipes/recipes/7` | `spec/plant_cutting_recipes.json#/recipes/7` | gameplay | NOT_PERFORMED |
| `spec:plant_cutting_recipes/recipes/8` | `spec/plant_cutting_recipes.json#/recipes/8` | gameplay | NOT_PERFORMED |
| `spec:plant_cutting_recipes/recipes/9` | `spec/plant_cutting_recipes.json#/recipes/9` | gameplay | NOT_PERFORMED |
| `spec:plant_cutting_recipes/recipes/10` | `spec/plant_cutting_recipes.json#/recipes/10` | gameplay | NOT_PERFORMED |
| `spec:plant_cutting_recipes/recipes/11` | `spec/plant_cutting_recipes.json#/recipes/11` | gameplay | NOT_PERFORMED |
| `spec:plant_cutting_recipes/recipes/12` | `spec/plant_cutting_recipes.json#/recipes/12` | gameplay | NOT_PERFORMED |
| `spec:plant_cutting_recipes/recipes/13` | `spec/plant_cutting_recipes.json#/recipes/13` | gameplay | NOT_PERFORMED |
| `spec:plant_cutting_recipes/recipes/14` | `spec/plant_cutting_recipes.json#/recipes/14` | gameplay | NOT_PERFORMED |
| `spec:plant_cutting_recipes/recipes/15` | `spec/plant_cutting_recipes.json#/recipes/15` | gameplay | NOT_PERFORMED |
| `spec:plant_cutting_recipes/recipes/16` | `spec/plant_cutting_recipes.json#/recipes/16` | gameplay | NOT_PERFORMED |
| `spec:plant_cutting_recipes/recipes/17` | `spec/plant_cutting_recipes.json#/recipes/17` | gameplay | NOT_PERFORMED |
| `spec:tag_integrations/policy` | `spec/tag_integrations.json#/policy` | gameplay | NOT_PERFORMED |
| `spec:tag_integrations/integrations/0` | `spec/tag_integrations.json#/integrations/0` | gameplay | NOT_PERFORMED |
| `spec:tag_integrations/integrations/1` | `spec/tag_integrations.json#/integrations/1` | gameplay | NOT_PERFORMED |
| `spec:wood_families/policy` | `spec/wood_families.json#/policy` | gameplay | NOT_PERFORMED |
| `spec:wood_families/families/0` | `spec/wood_families.json#/families/0` | gameplay | NOT_PERFORMED |
| `spec:wood_families/families/1` | `spec/wood_families.json#/families/1` | gameplay | NOT_PERFORMED |
| `spec:wood_families/families/2` | `spec/wood_families.json#/families/2` | gameplay | NOT_PERFORMED |
| `spec:wood_families/families/3` | `spec/wood_families.json#/families/3` | gameplay | NOT_PERFORMED |
| `spec:wood_families/families/4` | `spec/wood_families.json#/families/4` | gameplay | NOT_PERFORMED |
| `spec:wood_families/families/5` | `spec/wood_families.json#/families/5` | gameplay | NOT_PERFORMED |
| `spec:wood_families/families/6` | `spec/wood_families.json#/families/6` | gameplay | NOT_PERFORMED |
| `spec:wood_families/families/7` | `spec/wood_families.json#/families/7` | gameplay | NOT_PERFORMED |
| `spec:wood_families/families/8` | `spec/wood_families.json#/families/8` | gameplay | NOT_PERFORMED |
| `spec:wood_families/families/9` | `spec/wood_families.json#/families/9` | gameplay | NOT_PERFORMED |
| `spec:wood_families/families/10` | `spec/wood_families.json#/families/10` | gameplay | NOT_PERFORMED |
| `spec:wood_families/families/11` | `spec/wood_families.json#/families/11` | gameplay | NOT_PERFORMED |
| `spec:wood_families/families/12` | `spec/wood_families.json#/families/12` | gameplay | NOT_PERFORMED |
| `spec:wood_families/woodless_trees/0` | `spec/wood_families.json#/woodless_trees/0` | gameplay | NOT_PERFORMED |
| `spec:wood_families/woodless_trees/1` | `spec/wood_families.json#/woodless_trees/1` | gameplay | NOT_PERFORMED |
| `spec:wood_families/woodless_trees/2` | `spec/wood_families.json#/woodless_trees/2` | gameplay | NOT_PERFORMED |
| `spec:wood_families/woodless_trees/3` | `spec/wood_families.json#/woodless_trees/3` | gameplay | NOT_PERFORMED |
| `spec:wood_families/woodless_trees/4` | `spec/wood_families.json#/woodless_trees/4` | gameplay | NOT_PERFORMED |
