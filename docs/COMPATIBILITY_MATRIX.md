# Compatibility Matrix

Every scoped block is classified. Wood-family details are in `spec/wood_families.json`.

## Fleurs

| ID | Décision | Justification |
|---|---|---|
| `biomesoplenty:rose` | `CUTTING_DYE_PARITY_OR_EXISTING_BOP_UTILITY` | Keep native self-drop and existing BOP dye/compost behavior; add only a same-yield Cutting Board alternative. |
| `biomesoplenty:violet` | `CUTTING_DYE_PARITY_OR_EXISTING_BOP_UTILITY` | Keep native self-drop and existing BOP dye/compost behavior; add only a same-yield Cutting Board alternative. |
| `biomesoplenty:lavender` | `CUTTING_DYE_PARITY_OR_EXISTING_BOP_UTILITY` | Keep native self-drop and existing BOP dye/compost behavior; add only a same-yield Cutting Board alternative. |
| `biomesoplenty:tall_lavender` | `CUTTING_DYE_PARITY_OR_EXISTING_BOP_UTILITY` | Keep native self-drop and existing BOP dye/compost behavior; add only a same-yield Cutting Board alternative. |
| `biomesoplenty:white_lavender` | `CUTTING_DYE_PARITY_OR_EXISTING_BOP_UTILITY` | Keep native self-drop and existing BOP dye/compost behavior; add only a same-yield Cutting Board alternative. |
| `biomesoplenty:tall_white_lavender` | `CUTTING_DYE_PARITY_OR_EXISTING_BOP_UTILITY` | Keep native self-drop and existing BOP dye/compost behavior; add only a same-yield Cutting Board alternative. |
| `biomesoplenty:blue_hydrangea` | `CUTTING_DYE_PARITY_OR_EXISTING_BOP_UTILITY` | Keep native self-drop and existing BOP dye/compost behavior; add only a same-yield Cutting Board alternative. |
| `biomesoplenty:goldenrod` | `CUTTING_DYE_PARITY_OR_EXISTING_BOP_UTILITY` | Keep native self-drop and existing BOP dye/compost behavior; add only a same-yield Cutting Board alternative. |
| `biomesoplenty:orange_cosmos` | `CUTTING_DYE_PARITY_OR_EXISTING_BOP_UTILITY` | Keep native self-drop and existing BOP dye/compost behavior; add only a same-yield Cutting Board alternative. |
| `biomesoplenty:pink_daffodil` | `CUTTING_DYE_PARITY_OR_EXISTING_BOP_UTILITY` | Keep native self-drop and existing BOP dye/compost behavior; add only a same-yield Cutting Board alternative. |
| `biomesoplenty:pink_hibiscus` | `CUTTING_DYE_PARITY_OR_EXISTING_BOP_UTILITY` | Keep native self-drop and existing BOP dye/compost behavior; add only a same-yield Cutting Board alternative. |
| `biomesoplenty:wildflower` | `CUTTING_DYE_PARITY_OR_EXISTING_BOP_UTILITY` | Keep native self-drop and existing BOP dye/compost behavior; add only a same-yield Cutting Board alternative. |
| `biomesoplenty:white_petals` | `CUTTING_DYE_PARITY_OR_EXISTING_BOP_UTILITY` | Keep native self-drop and existing BOP dye/compost behavior; add only a same-yield Cutting Board alternative. |
| `biomesoplenty:icy_iris` | `CUTTING_DYE_PARITY_OR_EXISTING_BOP_UTILITY` | Keep native self-drop and existing BOP dye/compost behavior; add only a same-yield Cutting Board alternative. |
| `biomesoplenty:glowflower` | `CUTTING_DYE_PARITY_OR_EXISTING_BOP_UTILITY` | Keep native self-drop and existing BOP dye/compost behavior; add only a same-yield Cutting Board alternative. |
| `biomesoplenty:wilted_lily` | `CUTTING_DYE_PARITY_OR_EXISTING_BOP_UTILITY` | Keep native self-drop and existing BOP dye/compost behavior; add only a same-yield Cutting Board alternative. |
| `biomesoplenty:burning_blossom` | `CUTTING_DYE_PARITY_OR_EXISTING_BOP_UTILITY` | Keep native self-drop and existing BOP dye/compost behavior; add only a same-yield Cutting Board alternative. |
| `biomesoplenty:endbloom` | `CUTTING_DYE_PARITY_OR_EXISTING_BOP_UTILITY` | Keep native self-drop and existing BOP dye/compost behavior; add only a same-yield Cutting Board alternative. |

## Plantes

| ID | Décision | Justification |
|---|---|---|
| `biomesoplenty:sprout` | `NO_CHANGE_ALREADY_COVERED` | Already has a native wheat-seed chance and compost behavior. |
| `biomesoplenty:bush` | `CUTTING_AND_KNIFE_LOW_YIELD` | One stick on the board; 50% stick with a knife. |
| `biomesoplenty:high_grass` | `CUTTING_AND_KNIFE_LOW_YIELD` | One straw on the board; 50% straw per destroyed segment with a knife. |
| `biomesoplenty:high_grass_plant` | `ALIAS_DIRECT_HARVEST_ONLY` | Body segment; no inventory cutting recipe. |
| `biomesoplenty:clover` | `NO_CHANGE_COMPOST_ONLY` | No emeralds, seeds, or speculative green dye. |
| `biomesoplenty:huge_clover_petal` | `NO_CHANGE_COMPOST_ONLY` | Decorative and compostable; no resource conversion. |
| `biomesoplenty:huge_lily_pad` | `NO_CHANGE` | No credible conservative conversion. |
| `biomesoplenty:waterlily` | `CUTTING_DYE_PARITY` | Same red-dye yield as BOP crafting. |
| `biomesoplenty:dune_grass` | `CUTTING_AND_KNIFE_LOW_YIELD` | One straw on the board; 50% knife harvest. |
| `biomesoplenty:desert_grass` | `CUTTING_AND_KNIFE_LOW_YIELD` | One straw on the board; 50% knife harvest. |
| `biomesoplenty:dead_grass` | `CUTTING_AND_KNIFE_LOW_YIELD` | One straw on the board; 50% knife harvest. |
| `biomesoplenty:tundra_shrub` | `CUTTING_AND_KNIFE_LOW_YIELD` | One stick on the board; 50% knife harvest. |
| `biomesoplenty:enderphyte` | `NO_CHANGE_ALREADY_USEFUL` | BOP already uses it for algal end stone; no chorus fruit or pearl. |
| `biomesoplenty:lumaloop` | `NO_CHANGE_COMPOST_ONLY` | No direct glowstone or glow berries. |
| `biomesoplenty:lumaloop_plant` | `NO_CHANGE_ALIAS` | Body segment; no independent conversion. |
| `biomesoplenty:barley` | `TAG_AND_STRAW_INTEGRATION` | Add to c:crops/grain and allow straw recovery; never convert it to wheat. |
| `biomesoplenty:sea_oats` | `CUTTING_AND_KNIFE_LOW_YIELD` | One straw on the board; 50% knife harvest. |
| `biomesoplenty:cattail` | `CUTTING_DYE_PARITY` | Same two brown dyes as BOP crafting. |
| `biomesoplenty:reed` | `CUTTING_AND_KNIFE_LOW_YIELD` | One straw on the board; never convert to sugar cane. |
| `biomesoplenty:watergrass` | `NO_CHANGE_COMPOST_ONLY` | No realistic conversion to kelp or seagrass. |
| `biomesoplenty:tiny_cactus` | `NO_CHANGE_ALREADY_USEFUL` | BOP already smelts it into green dye. |
| `biomesoplenty:bramble` | `CUTTING_ONLY` | One stick on the Cutting Board. |
| `biomesoplenty:bramble_leaves` | `KNIFE_LOW_YIELD_ONLY` | 25% stick with a knife; no berries or string. |

## Arbres sans famille de bois

| ID | Décision | Justification |
|---|---|---|
| `biomesoplenty:origin_sapling` | `NO_CHANGE_ALREADY_COVERED` | Native self-drop and compost behavior. |
| `biomesoplenty:flowering_oak_sapling` | `NO_CHANGE_ALREADY_COVERED` | Native self-drop and compost behavior. |
| `biomesoplenty:cypress_sapling` | `NO_CHANGE_ALREADY_COVERED` | Native self-drop and compost behavior. |
| `biomesoplenty:snowblossom_sapling` | `NO_CHANGE_ALREADY_COVERED` | Native self-drop and compost behavior. |
| `biomesoplenty:rainbow_birch_sapling` | `NO_CHANGE_ALREADY_COVERED` | Native self-drop and compost behavior. |
| `biomesoplenty:origin_leaves` | `NO_CHANGE_ALREADY_COVERED` | Native sapling/stick drops and compost behavior. |
| `biomesoplenty:flowering_oak_leaves` | `NO_CHANGE_ALREADY_COVERED` | Native sapling/stick drops and compost behavior. |
| `biomesoplenty:cypress_leaves` | `NO_CHANGE_ALREADY_COVERED` | Native sapling/stick drops and compost behavior. |
| `biomesoplenty:snowblossom_leaves` | `NO_CHANGE_ALREADY_COVERED` | Native sapling/stick drops and compost behavior. |
| `biomesoplenty:rainbow_birch_leaves` | `NO_CHANGE_ALREADY_COVERED` | Native sapling/stick drops and compost behavior. |

## Plantes en pot

| ID | Décision | Justification |
|---|---|---|
| `biomesoplenty:potted_origin_sapling` | `NO_CHANGE_UNDERLYING_PLANT_COVERAGE` | BOP already drops the pot contents. No bonus, replacement, or conversion on the potted block. |
| `biomesoplenty:potted_flowering_oak_sapling` | `NO_CHANGE_UNDERLYING_PLANT_COVERAGE` | BOP already drops the pot contents. No bonus, replacement, or conversion on the potted block. |
| `biomesoplenty:potted_cypress_sapling` | `NO_CHANGE_UNDERLYING_PLANT_COVERAGE` | BOP already drops the pot contents. No bonus, replacement, or conversion on the potted block. |
| `biomesoplenty:potted_snowblossom_sapling` | `NO_CHANGE_UNDERLYING_PLANT_COVERAGE` | BOP already drops the pot contents. No bonus, replacement, or conversion on the potted block. |
| `biomesoplenty:potted_rainbow_birch_sapling` | `NO_CHANGE_UNDERLYING_PLANT_COVERAGE` | BOP already drops the pot contents. No bonus, replacement, or conversion on the potted block. |
| `biomesoplenty:potted_fir_sapling` | `NO_CHANGE_UNDERLYING_PLANT_COVERAGE` | BOP already drops the pot contents. No bonus, replacement, or conversion on the potted block. |
| `biomesoplenty:potted_pine_sapling` | `NO_CHANGE_UNDERLYING_PLANT_COVERAGE` | BOP already drops the pot contents. No bonus, replacement, or conversion on the potted block. |
| `biomesoplenty:potted_red_maple_sapling` | `NO_CHANGE_UNDERLYING_PLANT_COVERAGE` | BOP already drops the pot contents. No bonus, replacement, or conversion on the potted block. |
| `biomesoplenty:potted_orange_maple_sapling` | `NO_CHANGE_UNDERLYING_PLANT_COVERAGE` | BOP already drops the pot contents. No bonus, replacement, or conversion on the potted block. |
| `biomesoplenty:potted_yellow_maple_sapling` | `NO_CHANGE_UNDERLYING_PLANT_COVERAGE` | BOP already drops the pot contents. No bonus, replacement, or conversion on the potted block. |
| `biomesoplenty:potted_redwood_sapling` | `NO_CHANGE_UNDERLYING_PLANT_COVERAGE` | BOP already drops the pot contents. No bonus, replacement, or conversion on the potted block. |
| `biomesoplenty:potted_mahogany_sapling` | `NO_CHANGE_UNDERLYING_PLANT_COVERAGE` | BOP already drops the pot contents. No bonus, replacement, or conversion on the potted block. |
| `biomesoplenty:potted_jacaranda_sapling` | `NO_CHANGE_UNDERLYING_PLANT_COVERAGE` | BOP already drops the pot contents. No bonus, replacement, or conversion on the potted block. |
| `biomesoplenty:potted_palm_sapling` | `NO_CHANGE_UNDERLYING_PLANT_COVERAGE` | BOP already drops the pot contents. No bonus, replacement, or conversion on the potted block. |
| `biomesoplenty:potted_willow_sapling` | `NO_CHANGE_UNDERLYING_PLANT_COVERAGE` | BOP already drops the pot contents. No bonus, replacement, or conversion on the potted block. |
| `biomesoplenty:potted_dead_sapling` | `NO_CHANGE_UNDERLYING_PLANT_COVERAGE` | BOP already drops the pot contents. No bonus, replacement, or conversion on the potted block. |
| `biomesoplenty:potted_magic_sapling` | `NO_CHANGE_UNDERLYING_PLANT_COVERAGE` | BOP already drops the pot contents. No bonus, replacement, or conversion on the potted block. |
| `biomesoplenty:potted_umbran_sapling` | `NO_CHANGE_UNDERLYING_PLANT_COVERAGE` | BOP already drops the pot contents. No bonus, replacement, or conversion on the potted block. |
| `biomesoplenty:potted_hellbark_sapling` | `NO_CHANGE_UNDERLYING_PLANT_COVERAGE` | BOP already drops the pot contents. No bonus, replacement, or conversion on the potted block. |
| `biomesoplenty:potted_empyreal_sapling` | `NO_CHANGE_UNDERLYING_PLANT_COVERAGE` | BOP already drops the pot contents. No bonus, replacement, or conversion on the potted block. |
| `biomesoplenty:potted_rose` | `NO_CHANGE_UNDERLYING_PLANT_COVERAGE` | BOP already drops the pot contents. No bonus, replacement, or conversion on the potted block. |
| `biomesoplenty:potted_violet` | `NO_CHANGE_UNDERLYING_PLANT_COVERAGE` | BOP already drops the pot contents. No bonus, replacement, or conversion on the potted block. |
| `biomesoplenty:potted_lavender` | `NO_CHANGE_UNDERLYING_PLANT_COVERAGE` | BOP already drops the pot contents. No bonus, replacement, or conversion on the potted block. |
| `biomesoplenty:potted_white_lavender` | `NO_CHANGE_UNDERLYING_PLANT_COVERAGE` | BOP already drops the pot contents. No bonus, replacement, or conversion on the potted block. |
| `biomesoplenty:potted_orange_cosmos` | `NO_CHANGE_UNDERLYING_PLANT_COVERAGE` | BOP already drops the pot contents. No bonus, replacement, or conversion on the potted block. |
| `biomesoplenty:potted_pink_daffodil` | `NO_CHANGE_UNDERLYING_PLANT_COVERAGE` | BOP already drops the pot contents. No bonus, replacement, or conversion on the potted block. |
| `biomesoplenty:potted_pink_hibiscus` | `NO_CHANGE_UNDERLYING_PLANT_COVERAGE` | BOP already drops the pot contents. No bonus, replacement, or conversion on the potted block. |
| `biomesoplenty:potted_glowflower` | `NO_CHANGE_UNDERLYING_PLANT_COVERAGE` | BOP already drops the pot contents. No bonus, replacement, or conversion on the potted block. |
| `biomesoplenty:potted_wilted_lily` | `NO_CHANGE_UNDERLYING_PLANT_COVERAGE` | BOP already drops the pot contents. No bonus, replacement, or conversion on the potted block. |
| `biomesoplenty:potted_burning_blossom` | `NO_CHANGE_UNDERLYING_PLANT_COVERAGE` | BOP already drops the pot contents. No bonus, replacement, or conversion on the potted block. |
| `biomesoplenty:potted_endbloom` | `NO_CHANGE_UNDERLYING_PLANT_COVERAGE` | BOP already drops the pot contents. No bonus, replacement, or conversion on the potted block. |
| `biomesoplenty:potted_sprout` | `NO_CHANGE_UNDERLYING_PLANT_COVERAGE` | BOP already drops the pot contents. No bonus, replacement, or conversion on the potted block. |
| `biomesoplenty:potted_tiny_cactus` | `NO_CHANGE_UNDERLYING_PLANT_COVERAGE` | BOP already drops the pot contents. No bonus, replacement, or conversion on the potted block. |
| `biomesoplenty:potted_toadstool` | `NO_CHANGE_UNDERLYING_PLANT_COVERAGE` | BOP already drops the pot contents. No bonus, replacement, or conversion on the potted block. |
| `biomesoplenty:potted_glowshroom` | `NO_CHANGE_UNDERLYING_PLANT_COVERAGE` | BOP already drops the pot contents. No bonus, replacement, or conversion on the potted block. |

## Champignons et mousses

| ID | Décision | Justification |
|---|---|---|
| `biomesoplenty:toadstool` | `TAG_COMPAT_ONLY` | Add to c:mushrooms; native drop, rabbit stew use, and compost remain authoritative. |
| `biomesoplenty:toadstool_block` | `NO_CHANGE_ALREADY_COVERED` | Native huge-mushroom drop and compost behavior. |
| `biomesoplenty:glowshroom` | `NO_CHANGE_ALREADY_COVERED` | Native self-drop and compost; no free glowstone. |
| `biomesoplenty:glowshroom_block` | `NO_CHANGE_ALREADY_COVERED` | Native huge-mushroom drop and compost; no free glowstone. |
| `biomesoplenty:glowing_moss_block` | `NO_CHANGE` | Self-dropping decorative block; no glowstone conversion. |
| `biomesoplenty:glowing_moss_carpet` | `NO_CHANGE_ALREADY_COVERED` | Self-drop and compost behavior. |
| `biomesoplenty:mossy_black_sand` | `NO_CHANGE_TERRAIN` | Terrain block, not a renewable plant resource. |
| `biomesoplenty:spanish_moss` | `NO_CHANGE_ALREADY_COVERED` | Shears collection and compost behavior. |
| `biomesoplenty:spanish_moss_plant` | `NO_CHANGE_ALIAS` | Body segment; no independent conversion. |

## Toiles, soies et fibres

| ID | Décision | Justification |
|---|---|---|
| `biomesoplenty:glowworm_silk` | `CUTTING_AND_DIRECT_STRING` | One string on the board; one string with knife/sword. |
| `biomesoplenty:glowworm_silk_strand` | `DIRECT_STRING_ALIAS` | Body segment only. |
| `biomesoplenty:spider_egg` | `NO_CHANGE_RARE_ORGANIC` | Do not turn a special encounter block into string or spider eyes. |
| `biomesoplenty:hanging_cobweb` | `CUTTING_AND_DIRECT_STRING` | One string on the board; one string with knife/sword. |
| `biomesoplenty:hanging_cobweb_strand` | `DIRECT_STRING_ALIAS` | Body segment only. |
| `biomesoplenty:stringy_cobweb` | `AUDIT_ONLY_NO_EVENT_HACK` | No native loot table. Do not add an event or mixin solely for this block in v1. |
| `biomesoplenty:webbing` | `CUTTING_AND_DIRECT_STRING` | One string maximum, independent of face count. |

## Chair et organique

| ID | Décision | Justification |
|---|---|---|
| `biomesoplenty:flesh` | `CUTTING_SALVAGE` | One block yields two rotten flesh; blood is not recovered. |
| `biomesoplenty:porous_flesh` | `CUTTING_SALVAGE` | One block yields one rotten flesh. |
| `biomesoplenty:flesh_tendons` | `CUTTING_AND_LOW_YIELD_STRING` | Sinew conversion. |
| `biomesoplenty:flesh_tendons_strand` | `DIRECT_STRING_ALIAS` | Body segment only. |
| `biomesoplenty:eyebulb` | `NO_CHANGE` | Do not convert it into spider eyes or other unrelated organs. |
| `biomesoplenty:hair` | `CUTTING_AND_LOW_YIELD_STRING` | Fibrous salvage only. |
| `biomesoplenty:pus_bubble` | `NO_CHANGE_SILK_SPECIAL` | No slime-ball or chemical resource shortcut. |

## Organique spécial de l'End

| ID | Décision | Justification |
|---|---|---|
| `biomesoplenty:barnacles` | `NO_CHANGE` | No prismarine or bone-meal conversion. |
| `biomesoplenty:wispjelly` | `NO_CHANGE` | No slime-ball or glow-ink conversion. |
| `biomesoplenty:algal_end_stone` | `NO_CHANGE_ALREADY_USEFUL` | BOP crafting already links it to enderphyte. |
| `biomesoplenty:null_leaves` | `NO_CHANGE_ALREADY_USEFUL` | BOP crafting already uses it for null end stone. |
| `biomesoplenty:null_plant` | `NO_CHANGE` | No chorus fruit or dye conversion. |
| `biomesoplenty:null_block` | `NO_CHANGE_RARE_SPECIAL` | No generic material salvage. |
| `biomesoplenty:anomaly` | `NO_CHANGE_RARE_SPECIAL` | No recipe or drop added. |

## Bois

All 13 families receive Cutting Board stripping and IE Sawmill parity for log/wood forms only. Leaves, saplings and constructed variants retain native behavior.

Families: `fir`, `pine`, `maple`, `redwood`, `mahogany`, `jacaranda`, `palm`, `willow`, `dead`, `magic`, `umbran`, `hellbark`, `empyreal`.

## Racines

No standalone BOP root block is present in the audited 1.21.1 baseline. No ID or recipe may be invented.
