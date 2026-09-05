package com.oblixorprime.immersivebopharvest.qa;

import blusunrize.immersiveengineering.api.crafting.SawmillRecipe;
import blusunrize.immersiveengineering.common.blocks.multiblocks.logic.sawmill.SawmillProcess;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.TagKey;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.crafting.CraftingInput;
import net.minecraft.world.item.crafting.CraftingRecipe;
import net.minecraft.world.item.enchantment.Enchantments;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.FlowerPotBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.block.state.properties.DoubleBlockHalf;
import net.minecraft.world.level.levelgen.LegacyRandomSource;
import net.minecraft.world.level.storage.loot.LootContext;
import net.minecraft.world.level.storage.loot.LootParams;
import net.minecraft.world.level.storage.loot.LootTable;
import net.minecraft.world.level.storage.loot.parameters.LootContextParamSets;
import net.minecraft.world.level.storage.loot.parameters.LootContextParams;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.common.CommonHooks;
import net.neoforged.neoforge.common.util.FakePlayerFactory;
import net.neoforged.neoforge.energy.EnergyStorage;
import vectorwing.farmersdelight.common.block.entity.CuttingBoardBlockEntity;
import vectorwing.farmersdelight.common.crafting.CuttingBoardRecipe;
import vectorwing.farmersdelight.common.crafting.CuttingBoardRecipeInput;

import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collection;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.TreeMap;
import java.util.function.BiConsumer;

/** Assertions against decoded runtime data and real FD/IE processing APIs.
 * The specification is copied verbatim into this separate test JAR; expected
 * results are not read from the generated addon resources being tested. */
public final class QualificationChecks {
    private static final Map<String, List<Map<String, Object>>> OBSERVATIONS = new LinkedHashMap<>();
    private static String activeCase;

    public record Case(String id, BiConsumer<ServerLevel, BlockPos> action, BiConsumer<ServerLevel, BlockPos> settled, int settleTicks) {
        public Case(String id, BiConsumer<ServerLevel, BlockPos> action) { this(id, action, null, 0); }
        public void run(ServerLevel level, BlockPos pos) {
            if (OBSERVATIONS.putIfAbsent(id, new ArrayList<>()) != null)
                throw new IllegalStateException("Duplicate qualification execution " + id);
            within(() -> action.accept(level, pos));
        }
        public void finish(ServerLevel level, BlockPos pos) { within(() -> settled.accept(level, pos)); }
        private void within(Runnable run) {
            String previous = activeCase;
            activeCase = id;
            try { run.run(); } finally { activeCase = previous; }
        }
    }

    public static Map<String, List<Map<String, Object>>> observations() { return OBSERVATIONS; }

    private static JsonObject spec(String name) {
        try (var stream = Objects.requireNonNull(QualificationChecks.class.getResourceAsStream("/bop_qa/spec/" + name + ".json"));
             var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            return JsonParser.parseReader(reader).getAsJsonObject();
        } catch (Exception e) { throw new IllegalStateException("Missing qualification specification " + name, e); }
    }

    public static List<Case> cases() {
        List<Case> tests = new ArrayList<>();
        for (var element : spec("wood_families").getAsJsonArray("families")) {
            JsonObject family = element.getAsJsonObject();
            for (String key : List.of("log", "wood")) {
                String source = family.get(key).getAsString();
                Map<String, Integer> outputs = Map.of(family.get("stripped_" + key).getAsString(), 1, "farmersdelight:tree_bark", 1);
                tests.add(new Case("cutting_" + path(source), (level, pos) -> cutting(level, pos, source, outputs, true)));
            }
            for (String key : List.of("log", "wood", "stripped_log", "stripped_wood")) {
                tests.add(new Case("sawmill_" + path(family.get(key).getAsString()), (level, pos) -> sawmill(level, family, key)));
            }
        }
        for (String file : List.of("flower_cutting_recipes", "plant_cutting_recipes")) {
            for (var element : spec(file).getAsJsonArray("recipes")) {
                JsonObject recipe = element.getAsJsonObject();
                String source = recipe.get("source").getAsString();
                Map<String, Integer> outputs = new TreeMap<>();
                if (recipe.has("outputs")) {
                    for (var output : recipe.getAsJsonArray("outputs")) {
                        JsonObject row = output.getAsJsonObject();
                        outputs.put(row.get("item").getAsString(), row.has("count") ? row.get("count").getAsInt() : 1);
                    }
                } else outputs.put(recipe.get("output").getAsString(), recipe.has("count") ? recipe.get("count").getAsInt() : 1);
                tests.add(new Case("cutting_" + path(source), (level, pos) -> cutting(level, pos, source, outputs, false)));
            }
        }
        Set<String> harvest = new HashSet<>();
        for (var element : spec("direct_harvest_rules").getAsJsonArray("rules")) {
            JsonObject rule = element.getAsJsonObject();
            for (var block : rule.getAsJsonArray("blocks")) {
                String id = block.getAsString(); harvest.add(id);
                tests.add(new Case("harvest_" + path(id), (level, pos) -> harvest(level, pos, id, rule)));
            }
        }
        Set<String> excluded = new java.util.TreeSet<>();
        for (var group : spec("coverage_inventory").entrySet()) {
            if (group.getValue().isJsonArray()) {
                for (var row : group.getValue().getAsJsonArray()) {
                    String id = row.getAsJsonObject().get("id").getAsString();
                    if (!harvest.contains(id)) excluded.add(id);
                }
            }
        }
        for (String id : excluded) tests.add(new Case("native_" + path(id), (level, pos) -> nativeOnly(level, pos, id)));
        for (String[] strand : List.of(new String[]{"high_grass", "high_grass_plant", "up", "farmersdelight:straw"},
                new String[]{"glowworm_silk", "glowworm_silk_strand", "down", "minecraft:string"},
                new String[]{"hanging_cobweb", "hanging_cobweb_strand", "down", "minecraft:string"},
                new String[]{"flesh_tendons", "flesh_tendons_strand", "down", "minecraft:string"})) {
            tests.add(new Case("cascade_" + strand[0], (level, pos) -> cascadeStart(level, pos, strand),
                    (level, pos) -> cascadeFinish(level, pos, strand), 10));
        }
        tests.add(new Case("runtime_tags", QualificationChecks::tags));
        if (tests.stream().map(Case::id).distinct().count() != tests.size()) throw new IllegalStateException("Duplicate test ID");
        return tests;
    }

    private static ResourceLocation id(String value) { return ResourceLocation.parse(value); }
    private static String path(String value) { return id(value).getPath(); }
    private static ItemStack stack(String value) {
        if (!BuiltInRegistries.ITEM.containsKey(id(value))) throw new IllegalStateException("Unknown item " + value);
        return new ItemStack(BuiltInRegistries.ITEM.get(id(value)));
    }
    private static Block block(String value) {
        if (!BuiltInRegistries.BLOCK.containsKey(id(value))) throw new IllegalStateException("Unknown block " + value);
        return BuiltInRegistries.BLOCK.get(id(value));
    }
    private static void equal(String label, Object expected, Object actual) {
        OBSERVATIONS.get(activeCase).add(Map.of("check", label, "expected", evidenceValue(expected), "actual", evidenceValue(actual)));
        if (!expected.equals(actual)) throw new IllegalStateException(activeCase + ": " + label + " expected=" + expected + " actual=" + actual);
    }
    private static Object evidenceValue(Object value) {
        return value instanceof String || value instanceof Number || value instanceof Boolean || value instanceof Map<?, ?>
                ? value : String.valueOf(value);
    }
    private static void atMost(String label, int maximum, int actual) {
        OBSERVATIONS.get(activeCase).add(Map.of("check", label, "comparison", "atMost", "expected", maximum, "actual", actual));
        if (actual > maximum) throw new IllegalStateException(activeCase + ": " + label + " maximum=" + maximum + " actual=" + actual);
    }
    private static Map<String, Integer> counts(Collection<ItemStack> values) {
        Map<String, Integer> output = new TreeMap<>();
        for (ItemStack value : values) if (!value.isEmpty()) output.merge(BuiltInRegistries.ITEM.getKey(value.getItem()).toString(), value.getCount(), Integer::sum);
        return output;
    }
    private static List<ItemEntity> entities(ServerLevel level, BlockPos pos) {
        return level.getEntitiesOfClass(ItemEntity.class, new AABB(pos).inflate(1.8));
    }
    private static Map<String, Integer> collect(ServerLevel level, BlockPos pos) {
        List<ItemEntity> entities = entities(level, pos);
        Map<String, Integer> output = counts(entities.stream().map(ItemEntity::getItem).toList());
        entities.forEach(ItemEntity::discard);
        return output;
    }

    private static void cutting(ServerLevel level, BlockPos pos, String source, Map<String, Integer> expected, boolean wood) {
        ItemStack input = stack(source);
        ItemStack tool = wood ? new ItemStack(Items.IRON_AXE) : stack("farmersdelight:iron_knife");
        var holder = level.getRecipeManager().byKey(id("immersive_bop_harvest:cutting/" + path(source))).orElseThrow();
        equal("decoded recipe type", true, holder.value() instanceof CuttingBoardRecipe);
        CuttingBoardRecipe recipe = (CuttingBoardRecipe)holder.value();
        equal("correct input/tool matches", true, recipe.matches(new CuttingBoardRecipeInput(input, tool), level));
        equal("wrong tool rejects", false, recipe.matches(new CuttingBoardRecipeInput(input, new ItemStack(Items.IRON_PICKAXE)), level));
        equal("wrong input rejects", false, recipe.matches(new CuttingBoardRecipeInput(new ItemStack(Items.DIAMOND), tool), level));
        equal("decoded exact outputs", expected, counts(recipe.getResults()));
        if (!wood && expected.keySet().stream().allMatch(name -> name.endsWith("_dye"))) {
            CraftingInput grid = CraftingInput.of(1, 1, List.of(input.copy()));
            int nativeYield = level.getRecipeManager().getRecipes().stream()
                    .filter(row -> row.id().getNamespace().equals("biomesoplenty") && row.value() instanceof CraftingRecipe)
                    .map(row -> (CraftingRecipe)row.value()).filter(nativeRecipe -> nativeRecipe.matches(grid, level))
                    .map(nativeRecipe -> nativeRecipe.assemble(grid, level.registryAccess()))
                    .filter(result -> expected.containsKey(BuiltInRegistries.ITEM.getKey(result.getItem()).toString()))
                    .mapToInt(ItemStack::getCount).max().orElse(0);
            equal("native BOP dye conversion exists", true, nativeYield > 0);
            equal("flower output does not exceed native yield", true, expected.values().stream().mapToInt(Integer::intValue).sum() <= nativeYield);
        }
        for (var result : recipe.getRollableResults()) equal("guaranteed result", 1.0F, result.chance());
        // Exercise the placed board's real consume/spawn/durability path.
        collect(level, pos);
        level.setBlockAndUpdate(pos.below(), Blocks.STONE.defaultBlockState());
        level.setBlockAndUpdate(pos, block("farmersdelight:cutting_board").defaultBlockState());
        CuttingBoardBlockEntity board = (CuttingBoardBlockEntity)level.getBlockEntity(pos);
        equal("insert input has no remainder", true, board.addItem(input.copy()).isEmpty());
        equal("wrong tool operation rejects", false, board.processStoredItemUsingTool(new ItemStack(Items.IRON_PICKAXE), null));
        equal("rejected operation retains input", Map.of(source, 1), counts(List.of(board.getStoredItem())));
        equal("rejected operation emits nothing", Map.of(), collect(level, pos));
        equal("correct tool processes", true, board.processStoredItemUsingTool(tool, null));
        equal("consumes exactly one input", true, board.isEmpty());
        equal("tool durability", 1, tool.getDamageValue());
        equal("actual emitted outputs", expected, collect(level, pos));
        equal("second processing rejects empty input", false, board.processStoredItemUsingTool(tool, null));
        equal("no repeat output", Map.of(), collect(level, pos));
        level.setBlockAndUpdate(pos, Blocks.AIR.defaultBlockState());
    }

    private static void sawmill(ServerLevel level, JsonObject family, String key) {
        String source = family.get(key).getAsString();
        ItemStack input = stack(source);
        boolean stripped = key.startsWith("stripped_");
        SawmillRecipe recipe = Objects.requireNonNull(SawmillRecipe.findRecipe(level, input), "No sawmill selection for " + source);
        Map<String, Integer> output = Map.of(family.get("planks").getAsString(), 6);
        equal("base energy", stripped ? 800 : 1600, recipe.getBaseEnergy());
        equal("six family planks", output, counts(List.of(recipe.output.get())));
        equal("input matches", true, recipe.input.test(input));
        equal("wrong input rejects", false, recipe.input.test(new ItemStack(Items.DIAMOND)));
        equal("stripped intermediate", stripped ? Map.of() : Map.of(family.get("stripped_" + key).getAsString(), 1), counts(List.of(recipe.stripped.get())));
        TagKey<Item> dust = TagKey.create(Registries.ITEM, id("c:dusts/wood"));
        equal("one sawdust secondary", 1, recipe.secondaryOutputs.get().size());
        equal("stripping secondary count", stripped ? 0 : 1, recipe.secondaryStripping.get().size());
        for (ItemStack secondary : recipe.secondaryOutputs.get()) {
            equal("secondary resolves common wood dust", true, secondary.is(dust));
            equal("one sawdust item per sawing secondary", 1, secondary.getCount());
        }
        for (ItemStack secondary : recipe.secondaryStripping.get()) {
            equal("stripping resolves common wood dust", true, secondary.is(dust));
            equal("one sawdust item per stripping secondary", 1, secondary.getCount());
        }
        ItemStack blade = stack("immersiveengineering:sawblade");
        SawmillProcess blocked = new SawmillProcess(input.copy());
        Set<ItemStack> none = new HashSet<>();
        equal("no energy cannot advance", false, blocked.processStep(level, new EnergyStorage(0), blade, none));
        equal("no energy produces no output", Map.of(), counts(none));
        equal("no energy preserves input", Map.of(source, 1), counts(List.of(blocked.getCurrentStack(level, true))));
        String dustItem = BuiltInRegistries.ITEM.getKey(recipe.secondaryOutputs.get().getFirst().getItem()).toString();
        Map<String, Integer> expectedSecondary = Map.of(dustItem, stripped ? 1 : 2);
        for (boolean reload : List.of(false, true)) {
            EnergyStorage energy = new EnergyStorage(100000); energy.receiveEnergy(100000, false);
            SawmillProcess process = new SawmillProcess(input.copy());
            List<ItemStack> secondaries = new ArrayList<>();
            int ticks = 0;
            int budget = recipe.getTotalProcessTime() + 2;
            while (!process.isProcessFinished() && ticks < budget) {
                // Match the real machine: collect and drain a fresh set each
                // tick, then copy into a multiset so cached stack identity
                // cannot hide emissions repeated after save/reload.
                Set<ItemStack> tickOutput = new HashSet<>();
                process.processStep(level, energy, blade, tickOutput);
                tickOutput.stream().map(ItemStack::copy).forEach(secondaries::add);
                ticks++;
                if (reload && ticks == recipe.getTotalProcessTime() / 2)
                    process = SawmillProcess.readFromNBT(process.writeToNBT(level.registryAccess()), level.registryAccess());
            }
            equal("process completes reload=" + reload, true, process.isProcessFinished());
            equal("real process output reload=" + reload, output, counts(List.of(process.getCurrentStack(level, true))));
            equal("real process secondaries reload=" + reload, expectedSecondary, counts(secondaries));
            equal("actual energy consumption reload=" + reload, ticks * (recipe.getTotalProcessEnergy() / recipe.getTotalProcessTime()), 100000 - energy.getEnergyStored());
        }
    }

    private static final class FixedFloat extends LegacyRandomSource {
        private final float value;
        FixedFloat(float value) { super(7361); this.value = value; }
        @Override public float nextFloat() { return value; }
    }
    private static LootParams params(ServerLevel level, BlockPos pos, BlockState state, ItemStack tool) {
        return new LootParams.Builder(level).withParameter(LootContextParams.ORIGIN, Vec3.atCenterOf(pos))
                .withParameter(LootContextParams.BLOCK_STATE, state).withParameter(LootContextParams.TOOL, tool).create(LootContextParamSets.BLOCK);
    }
    private static LootTable table(ServerLevel level, BlockState state) {
        return level.getServer().reloadableRegistries().getLootTable(state.getBlock().getLootTable());
    }
    private static Map<String, Integer> loot(ServerLevel level, BlockPos pos, BlockState state, ItemStack tool, float roll, boolean modified) {
        LootTable table = table(level, state);
        LootParams params = params(level, pos, state, tool);
        if (modified) return counts(table.getRandomItems(params, new FixedFloat(roll)));
        ObjectArrayList<ItemStack> result = new ObjectArrayList<>();
        LootContext context = new LootContext.Builder(params).withOptionalRandomSource(new FixedFloat(roll))
                .withQueriedLootTableId(state.getBlock().getLootTable().location()).create(Optional.empty());
        table.getRandomItemsRaw(context, result::add);
        return counts(result);
    }
    private static ItemStack enchanted(ServerLevel level, ResourceKey<net.minecraft.world.item.enchantment.Enchantment> enchantment) {
        ItemStack tool = stack("farmersdelight:iron_knife");
        tool.enchant(level.registryAccess().lookupOrThrow(Registries.ENCHANTMENT).getOrThrow(enchantment), 3);
        return tool;
    }
    private static void harvest(ServerLevel level, BlockPos pos, String name, JsonObject rule) {
        BlockState state = block(name).defaultBlockState();
        if (rule.get("state_condition").isJsonObject()) state = state.setValue(BlockStateProperties.DOUBLE_BLOCK_HALF, DoubleBlockHalf.LOWER);
        String output = rule.get("output").getAsString();
        int count = rule.get("count").getAsInt();
        float chance = rule.get("chance").getAsFloat();
        Map<String, ItemStack> tools = new LinkedHashMap<>();
        tools.put("hand", ItemStack.EMPTY); tools.put("wrong", new ItemStack(Items.IRON_PICKAXE));
        tools.put("knife", stack("farmersdelight:iron_knife")); tools.put("sword", new ItemStack(Items.IRON_SWORD));
        tools.put("shears", new ItemStack(Items.SHEARS)); tools.put("silk", enchanted(level, Enchantments.SILK_TOUCH));
        tools.put("fortune", enchanted(level, Enchantments.FORTUNE));
        boolean sword = rule.getAsJsonArray("tools_any").toString().contains("#minecraft:swords");
        for (var entry : tools.entrySet()) {
            for (float roll : new float[]{Math.nextDown(chance), chance == 1 ? 0.999F : chance}) {
                Map<String, Integer> expected = new TreeMap<>(loot(level, pos, state, entry.getValue(), roll, false));
                boolean allowed = entry.getKey().equals("knife") || entry.getKey().equals("fortune") || sword && entry.getKey().equals("sword");
                if (allowed && roll < chance) expected.merge(output, count, Integer::sum);
                equal(entry.getKey() + " roll=" + roll, expected, loot(level, pos, state, entry.getValue(), roll, true));
            }
        }
        LootContext foreign = new LootContext.Builder(params(level, pos, state, tools.get("knife")))
                .withOptionalRandomSource(new FixedFloat(0)).withQueriedLootTableId(id("minecraft:blocks/stone")).create(Optional.empty());
        equal("foreign table cannot trigger addon", Map.of(), counts(CommonHooks.modifyLoot(id("minecraft:blocks/stone"), new ObjectArrayList<>(), foreign)));
        LootParams explosion = new LootParams.Builder(level).withParameter(LootContextParams.ORIGIN, Vec3.atCenterOf(pos))
                .withParameter(LootContextParams.BLOCK_STATE, state).withParameter(LootContextParams.TOOL, ItemStack.EMPTY)
                .withParameter(LootContextParams.EXPLOSION_RADIUS, 2.0F).create(LootContextParamSets.BLOCK);
        ObjectArrayList<ItemStack> nativeExplosion = new ObjectArrayList<>();
        table(level, state).getRandomItemsRaw(new LootContext.Builder(explosion).withOptionalRandomSource(new FixedFloat(0.4F))
                .withQueriedLootTableId(state.getBlock().getLootTable().location()).create(Optional.empty()), nativeExplosion::add);
        equal("explosion native only", counts(nativeExplosion), counts(table(level, state).getRandomItems(explosion, new FixedFloat(0.4F))));
        if (name.equals("biomesoplenty:barley")) {
            state = state.setValue(BlockStateProperties.DOUBLE_BLOCK_HALF, DoubleBlockHalf.UPPER);
            equal("upper barley native only", loot(level, pos, state, tools.get("knife"), 0, false), loot(level, pos, state, tools.get("knife"), 0, true));
        }
        if (name.equals("biomesoplenty:webbing")) {
            for (var property : state.getProperties()) if (property instanceof BooleanProperty b) state = state.setValue(b, true);
            equal("six faces at most one string", Map.of("minecraft:string", 1), loot(level, pos, state, tools.get("knife"), 0, true));
        }
    }

    private static void nativeOnly(ServerLevel level, BlockPos pos, String name) {
        BlockState state = block(name).defaultBlockState();
        List<ItemStack> tools = List.of(ItemStack.EMPTY, stack("farmersdelight:iron_knife"), new ItemStack(Items.IRON_SWORD),
                new ItemStack(Items.SHEARS), enchanted(level, Enchantments.SILK_TOUCH), enchanted(level, Enchantments.FORTUNE));
        List<String> names = List.of("hand", "knife", "sword", "shears", "silk", "fortune");
        for (int i = 0; i < tools.size(); i++) {
            ItemStack tool = tools.get(i);
            for (float roll : new float[]{0.13F, 0.91F}) {
                equal("native invariant " + names.get(i) + " roll=" + roll, loot(level, pos, state, tool, roll, false), loot(level, pos, state, tool, roll, true));
            }
        }
        if (state.getBlock() instanceof FlowerPotBlock pot) {
            equal("pot and correct content remain", counts(List.of(new ItemStack(Items.FLOWER_POT), new ItemStack(pot.getPotted()))),
                    loot(level, pos, state, ItemStack.EMPTY, 0.13F, true));
        }
    }

    private static void tags(ServerLevel level, BlockPos pos) {
        for (var element : spec("tag_integrations").getAsJsonArray("integrations")) {
            JsonObject row = element.getAsJsonObject();
            TagKey<Item> tag = TagKey.create(Registries.ITEM, id(row.get("tag").getAsString()));
            for (var value : row.getAsJsonArray("values")) equal("tag " + tag.location() + " accepts " + value.getAsString(), true, stack(value.getAsString()).is(tag));
        }
        equal("native shears tag", true, new ItemStack(Items.SHEARS).is(TagKey.create(Registries.ITEM, id("biomesoplenty:shears"))));
    }

    private static void cascadeStart(ServerLevel level, BlockPos pos, String[] strand) {
        boolean up = strand[2].equals("up");
        int step = up ? 1 : -1;
        BlockPos base = up ? pos : pos.above(3);
        Block head = block("biomesoplenty:" + strand[0]);
        Block body = block("biomesoplenty:" + strand[1]);
        level.setBlock(base.offset(0, -step, 0), up ? Blocks.DIRT.defaultBlockState() : Blocks.STONE.defaultBlockState(), 2);
        List<BlockPos> positions = List.of(base, base.offset(0, step, 0), base.offset(0, 2 * step, 0));
        level.setBlock(positions.get(0), body.defaultBlockState(), 2);
        level.setBlock(positions.get(1), body.defaultBlockState(), 2);
        level.setBlock(positions.get(2), head.defaultBlockState(), 2);
        var player = FakePlayerFactory.getMinecraft(level);
        player.gameMode.changeGameModeForPlayer(net.minecraft.world.level.GameType.SURVIVAL);
        player.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND, stack("farmersdelight:iron_knife"));
        AABB bounds = new AABB(Vec3.atLowerCornerOf(pos.below()), Vec3.atLowerCornerOf(pos.above(6))).inflate(2.0);
        equal("three actual segments placed", 3L, positions.stream().filter(p -> level.getBlockState(p).is(head) || level.getBlockState(p).is(body)).count());
        level.getEntitiesOfClass(ItemEntity.class, bounds).forEach(ItemEntity::discard);
        equal("real player destroys attached segment", true, player.gameMode.destroyBlock(positions.get(0)));
    }

    private static void cascadeFinish(ServerLevel level, BlockPos pos, String[] strand) {
        int step = strand[2].equals("up") ? 1 : -1;
        BlockPos base = step == 1 ? pos : pos.above(3);
        Block head = block("biomesoplenty:" + strand[0]);
        Block body = block("biomesoplenty:" + strand[1]);
        List<BlockPos> positions = List.of(base, base.offset(0, step, 0), base.offset(0, 2 * step, 0));
        AABB bounds = new AABB(Vec3.atLowerCornerOf(pos.below()), Vec3.atLowerCornerOf(pos.above(6))).inflate(2.0);
        List<ItemEntity> emitted = level.getEntitiesOfClass(ItemEntity.class, bounds);
        Map<String, Integer> drops = counts(emitted.stream().map(ItemEntity::getItem).toList());
        atMost("bonus bounded by three destroyed segments", 3, drops.getOrDefault(strand[3], 0));
        if (strand[0].equals("glowworm_silk") || strand[0].equals("hanging_cobweb"))
            equal("guaranteed direct cut yields at least one string", true, drops.getOrDefault(strand[3], 0) > 0);
        equal("all three segments removed by scheduled cascade", 3L, positions.stream().filter(p -> !level.getBlockState(p).is(head) && !level.getBlockState(p).is(body)).count());
        emitted.forEach(ItemEntity::discard);
    }
}
