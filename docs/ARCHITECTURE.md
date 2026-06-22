# Architecture

## Runtime footprint

The addon should contain minimal runtime Java:
- mod bootstrap;
- optional registration hooks required by NeoForge datagen;
- no custom gameplay objects.

Most functionality is data-driven.

## Generated data

### Farmer's Delight recipes
- Cutting Board flower parity
- Cutting Board plant processing
- Cutting Board wood stripping

### Immersive Engineering recipes
- Sawmill unstripped log
- Sawmill unstripped wood
- Sawmill stripped log/wood

### NeoForge loot integration
- built-in additive loot modifier
- one generated subtable per target block
- tool, enchantment and state predicates

### Common tags
- `c:crops/grain`
- `c:mushrooms`
- `c:mineable/knife` only for blocks that actually gain knife behavior

## Anti-duplication

- Never replace BOP loot tables.
- No direct bonus on potted blocks.
- Lower-half condition for barley.
- At most one string from multiface webbing.
- No Fortune multiplier.
- No compatibility output for shears or Silk Touch.
- Deterministic datagen.

## Compatibility failure policy

When a registry ID or serializer differs:
1. Mark it `VERSION_MISMATCH`.
2. Do not invent a replacement.
3. Keep the build failing until the definition or dependency range is corrected.
