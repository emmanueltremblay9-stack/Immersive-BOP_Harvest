# Master Plan

## Product definition

Immersive BOP_Harvest is a small NeoForge compatibility addon. Its purpose is not to redesign Biomes O' Plenty; it only closes obvious integration gaps with Farmer's Delight and Immersive Engineering.

## Implementation pillars

### 1. Existing behavior is authoritative

BOP already supplies:
- native flower dye recipes;
- compost values for most vegetation;
- sapling and stick drops from leaves;
- pot-content drops;
- huge-mushroom drops;
- selected parity recipes such as willow vine for mossy stone.

The addon must not duplicate these systems with stronger outputs.

### 2. Cutting Board as a controlled conversion layer

Collected decorative vegetation can be processed into one obvious low-value material:
- dried grasses → straw;
- small woody growth → sticks;
- web/silk/sinew/hair → string;
- flesh blocks → partial rotten-flesh salvage;
- flowers → same dye yield as BOP's existing crafting recipe.

### 3. Correct-tool direct harvesting

Only a narrow list receives direct tool-harvest outputs:
- knife on grasses/shrubs;
- knife or sword on web-like blocks;
- knife on sinew/hair.

Hand harvesting gains nothing. Cisailles and Silk Touch preserve BOP behavior.

### 4. Wood machine parity

All 13 BOP wood families receive:
- Farmer's Delight axe stripping with one tree bark;
- Immersive Engineering Sawmill recipes matching vanilla IE values.

### 5. Explicit no-change decisions

Potted plants, mushrooms, mosses and rare organic blocks are included in the compatibility audit even when no new recipe is justified.
