# QA and Acceptance Criteria

## Specification
- [ ] `python scripts/validate_specs.py` passes.
- [ ] All scoped IDs are present in the compatibility matrix.
- [ ] No forbidden output is generated.
- [ ] No potted block is targeted by a loot modifier.

## Datagen
- [ ] `runData` completes.
- [ ] A second `runData` creates no diff.
- [ ] No generated file is written under `data/biomesoplenty/`.
- [ ] Recipe and modifier IDs are unique.

## Build
- [ ] Full Gradle build passes.
- [ ] Dedicated server starts without registry/datapack errors.
- [ ] No client classes are loaded server-side.

## Farmer's Delight
- [ ] All 13 wood families strip to the correct counterpart plus one tree bark.
- [ ] Flower Cutting Board output never exceeds BOP's existing dye yield.
- [ ] Plant processing matches `spec/plant_cutting_recipes.json`.
- [ ] Barley is accepted through `c:crops/grain`.
- [ ] Toadstool is accepted through `c:mushrooms`.

## Immersive Engineering
- [ ] Unstripped log and wood recipes use 1600 energy.
- [ ] Stripped log/wood recipes use 800 energy.
- [ ] Every result is six matching BOP planks.
- [ ] Wood dust uses `#c:dusts/wood`.
- [ ] No extra IE machine recipes exist.

## Harvest behavior
- [ ] Hand gives no compatibility bonus.
- [ ] Correct knife/sword gives only the configured output.
- [ ] Shears give native BOP loot only.
- [ ] Silk Touch gives native BOP loot only.
- [ ] Fortune does not alter compatibility outputs.
- [ ] Barley triggers only from the lower half.
- [ ] Webbing yields at most one string.
- [ ] Strand plants do not duplicate output beyond destroyed segments.
- [ ] Stringy cobweb remains unchanged unless a pure data solution is verified.

## Potted and special blocks
- [ ] Potted blocks still return normal contents.
- [ ] No bonus is produced by a potted block.
- [ ] Glowshroom/moss do not create glowstone.
- [ ] Spider egg, pus bubble, barnacles, wispjelly, null blocks and anomaly remain unchanged.

## Release
- [ ] README and compatibility matrix are current.
- [ ] Changelog is current.
- [ ] License has been selected.
- [ ] Version and dependency ranges are correct.
- [ ] Release JAR has been tested in a clean instance.
