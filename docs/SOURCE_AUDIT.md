# Source Audit Notes

Baseline inspected: official 1.21.1 branches or equivalent official generated resources.

## Biomes O' Plenty
- `common/src/main/java/biomesoplenty/init/ModBlocks.java`
- `common/src/main/java/biomesoplenty/api/block/BOPBlocks.java`
- `neoforge/src/main/java/biomesoplenty/neoforge/datagen/BOPBlockLoot.java`
- `neoforge/src/main/java/biomesoplenty/neoforge/datagen/provider/BOPRecipeProvider.java`
- `common/src/main/java/biomesoplenty/init/ModVanillaCompat.java`
- `common/src/main/java/biomesoplenty/init/ModTags.java`

Verified design facts:
- BOP already has dye recipes for its flowers.
- BOP already registers compost values for most vegetation.
- Potted BOP blocks already drop their contents.
- Many grasses and fibrous blocks are shears-only.
- BOP contains 13 full wood families in the audited baseline.
- No standalone BOP root block was found in the audited registry.

## Farmer's Delight
- `.../recipe/cutting/oak_log.json`
- `.../recipe/cutting/poppy.json`
- `.../recipe/cutting/wild_rice.json`
- `common/tag/CommonTags.java`

Verified design facts:
- Log stripping returns the stripped block plus one tree bark.
- Knife recipes use the knife item ability and `c:tools/knife`.
- Cutting outputs support chance fields.

## Immersive Engineering
- `.../recipe/sawmill/oak_log.json`
- `.../recipe/sawmill/jungle_wood.json`
- `.../recipe/sawmill/stripped_oak_log.json`
- `common/register/IEItems.java`

Verified design facts:
- Unstripped wood processing uses 1600 energy, six planks, wood dust and a stripped output.
- Stripped wood processing uses 800 energy and six planks plus wood dust.
- IE hemp seed is `immersiveengineering:seed`; this project explicitly forbids producing it from BOP plants.

Codex must re-check these facts against the exact dependency versions in the target workspace.
