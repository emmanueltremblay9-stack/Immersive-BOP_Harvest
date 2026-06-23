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
    public static void representativeGeneratedRecipesLoad(GameTestHelper helper) {
        assertRecipePresent(helper, "cutting/barley");
        assertRecipePresent(helper, "sawmill/fir_log");
        assertRecipePresent(helper, "sawmill/stripped_fir");
        helper.succeed();
    }

    private static void assertRecipePresent(GameTestHelper helper, String path) {
        ResourceLocation id = ResourceLocation.fromNamespaceAndPath(ImmersiveBopHarvest.MOD_ID, path);
        helper.assertTrue(helper.getLevel().getRecipeManager().byKey(id).isPresent(), "missing recipe " + id);
    }
}
