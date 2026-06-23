package com.oblixorprime.immersivebopharvest.gametest;

import com.oblixorprime.immersivebopharvest.ImmersiveBopHarvest;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.resources.ResourceLocation;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

@GameTestHolder(ImmersiveBopHarvest.MOD_ID)
@PrefixGameTestTemplate(false)
public final class BopHarvestGameTests {
    private static final String[] GENERATED_RECIPE_PATHS = {
            "cutting/barley",
            "cutting/blue_hydrangea",
            "cutting/bramble",
            "cutting/burning_blossom",
            "cutting/bush",
            "cutting/cattail",
            "cutting/dead_branch",
            "cutting/dead_grass",
            "cutting/dead_log",
            "cutting/dead_wood",
            "cutting/desert_grass",
            "cutting/dune_grass",
            "cutting/empyreal_log",
            "cutting/empyreal_wood",
            "cutting/endbloom",
            "cutting/fir_log",
            "cutting/fir_wood",
            "cutting/flesh",
            "cutting/flesh_tendons",
            "cutting/glowflower",
            "cutting/glowworm_silk",
            "cutting/goldenrod",
            "cutting/hair",
            "cutting/hanging_cobweb",
            "cutting/hellbark_log",
            "cutting/hellbark_wood",
            "cutting/high_grass",
            "cutting/icy_iris",
            "cutting/jacaranda_log",
            "cutting/jacaranda_wood",
            "cutting/lavender",
            "cutting/magic_log",
            "cutting/magic_wood",
            "cutting/mahogany_log",
            "cutting/mahogany_wood",
            "cutting/maple_log",
            "cutting/maple_wood",
            "cutting/orange_cosmos",
            "cutting/palm_log",
            "cutting/palm_wood",
            "cutting/pine_log",
            "cutting/pine_wood",
            "cutting/pink_daffodil",
            "cutting/pink_hibiscus",
            "cutting/porous_flesh",
            "cutting/redwood_log",
            "cutting/redwood_wood",
            "cutting/reed",
            "cutting/rose",
            "cutting/sea_oats",
            "cutting/tall_lavender",
            "cutting/tall_white_lavender",
            "cutting/tundra_shrub",
            "cutting/umbran_log",
            "cutting/umbran_wood",
            "cutting/violet",
            "cutting/waterlily",
            "cutting/webbing",
            "cutting/white_lavender",
            "cutting/white_petals",
            "cutting/wildflower",
            "cutting/willow_log",
            "cutting/willow_wood",
            "cutting/wilted_lily",
            "sawmill/dead_log",
            "sawmill/dead_wood",
            "sawmill/empyreal_log",
            "sawmill/empyreal_wood",
            "sawmill/fir_log",
            "sawmill/fir_wood",
            "sawmill/hellbark_log",
            "sawmill/hellbark_wood",
            "sawmill/jacaranda_log",
            "sawmill/jacaranda_wood",
            "sawmill/magic_log",
            "sawmill/magic_wood",
            "sawmill/mahogany_log",
            "sawmill/mahogany_wood",
            "sawmill/maple_log",
            "sawmill/maple_wood",
            "sawmill/palm_log",
            "sawmill/palm_wood",
            "sawmill/pine_log",
            "sawmill/pine_wood",
            "sawmill/redwood_log",
            "sawmill/redwood_wood",
            "sawmill/stripped_dead",
            "sawmill/stripped_empyreal",
            "sawmill/stripped_fir",
            "sawmill/stripped_hellbark",
            "sawmill/stripped_jacaranda",
            "sawmill/stripped_magic",
            "sawmill/stripped_mahogany",
            "sawmill/stripped_maple",
            "sawmill/stripped_palm",
            "sawmill/stripped_pine",
            "sawmill/stripped_redwood",
            "sawmill/stripped_umbran",
            "sawmill/stripped_willow",
            "sawmill/umbran_log",
            "sawmill/umbran_wood",
            "sawmill/willow_log",
            "sawmill/willow_wood"
    };

    private BopHarvestGameTests() {
    }

    @GameTest(template = "empty", timeoutTicks = 20)
    public static void serverRuntimeBoots(GameTestHelper helper) {
        helper.assertTrue(
                ImmersiveBopHarvest.MOD_ID.equals("immersive_bop_harvest"),
                "mod id must match the registered game-test namespace"
        );
        helper.succeed();
    }

    @GameTest(template = "empty", timeoutTicks = 20)
    public static void allGeneratedRecipesLoad(GameTestHelper helper) {
        for (String path : GENERATED_RECIPE_PATHS) {
            assertRecipePresent(helper, path);
        }
        helper.succeed();
    }

    private static void assertRecipePresent(GameTestHelper helper, String path) {
        ResourceLocation id = ResourceLocation.fromNamespaceAndPath(ImmersiveBopHarvest.MOD_ID, path);
        helper.assertTrue(helper.getLevel().getRecipeManager().byKey(id).isPresent(), "missing recipe " + id);
    }
}
