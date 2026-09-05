package com.oblixorprime.immersivebopharvest.qa;

import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTestGenerator;
import net.minecraft.gametest.framework.TestFunction;
import net.neoforged.neoforge.gametest.GameTestHolder;

import java.util.Collection;

@GameTestHolder("immersive_bop_harvest")
public final class QualificationGameTests {
    @GameTestGenerator
    public static Collection<TestFunction> scopedCompatibility() {
        return QualificationChecks.cases().stream().map(test -> new TestFunction(
                "bop_qa", "bop_qa." + test.id(), "immersive_bop_harvest:empty", 100, 0, true,
                helper -> {
                    BlockPos pos = helper.absolutePos(new BlockPos(1, 2, 1));
                    test.run(helper.getLevel(), pos);
                    if (test.settleTicks() > 0) {
                        helper.runAfterDelay(test.settleTicks(), () -> {
                            test.finish(helper.getLevel(), pos);
                            helper.succeed();
                        });
                    } else helper.succeed();
                })).toList();
    }
}
