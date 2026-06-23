package com.oblixorprime.immersivebopharvest;

import net.neoforged.fml.common.Mod;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Mod(ImmersiveBopHarvest.MOD_ID)
public final class ImmersiveBopHarvest {
    public static final String MOD_ID = "immersive_bop_harvest";
    public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

    public ImmersiveBopHarvest() {
        LOGGER.info("Loaded Immersive BOP_Harvest data compatibility");
    }
}
