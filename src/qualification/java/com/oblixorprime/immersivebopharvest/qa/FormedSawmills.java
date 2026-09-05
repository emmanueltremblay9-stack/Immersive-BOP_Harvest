package com.oblixorprime.immersivebopharvest.qa;

import blusunrize.immersiveengineering.api.crafting.SawmillRecipe;
import blusunrize.immersiveengineering.api.multiblocks.blocks.registry.MultiblockBlockEntityMaster;
import blusunrize.immersiveengineering.api.multiblocks.blocks.registry.MultiblockPartBlock;
import blusunrize.immersiveengineering.api.multiblocks.blocks.util.RelativeBlockFace;
import blusunrize.immersiveengineering.common.blocks.multiblocks.SawmillMultiblock;
import blusunrize.immersiveengineering.common.blocks.multiblocks.logic.sawmill.SawmillLogic;
import blusunrize.immersiveengineering.common.config.IEServerConfig;
import com.google.gson.JsonObject;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BarrelBlockEntity;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.common.util.FakePlayerFactory;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.TreeMap;

/** Uses actual template formation, block interactions, capabilities and world ticks. */
final class FormedSawmills {
    private final List<Machine> machines = new ArrayList<>();
    private record Machine(String input, BlockPos master, BlockPos primary, BlockPos secondary,
                           int energyBefore, int expectedEnergy, int bladeBefore,
                           Map<String,Integer> mainOutput, Map<String,Integer> secondaryOutput) {}

    void start(ServerLevel level) {
        // The previous snapshot was checked before resetting these owned fixtures.
        for(int i=0;i<52;i++) {
            BlockPos origin=new BlockPos(32+(i%8)*9,90,32+(i/8)*8);
            for(BlockPos pos:BlockPos.betweenClosed(origin.offset(-1,0,-1),origin.offset(6,4,4)))
                level.setBlockAndUpdate(pos,Blocks.AIR.defaultBlockState());
        }
        level.getEntitiesOfClass(ItemEntity.class,new AABB(30,88,30,104,98,87)).forEach(ItemEntity::discard);
        int index=0;
        for (var row : PackagedRuntime.spec("wood_families").getAsJsonArray("families")) {
            JsonObject family=row.getAsJsonObject();
            for (String key : List.of("log","wood","stripped_log","stripped_wood")) {
                BlockPos origin=new BlockPos(32+(index%8)*9, 90, 32+(index/8)*8);
                level.setChunkForced(origin.getX()>>4, origin.getZ()>>4, true);
                level.setChunkForced((origin.getX()+6)>>4, (origin.getZ()+5)>>4, true);
                for (BlockPos pos:BlockPos.betweenClosed(origin.offset(-1,-1,-1),origin.offset(6,-1,4)))
                    level.setBlockAndUpdate(pos, Blocks.STONE.defaultBlockState());
                SawmillMultiblock template=new SawmillMultiblock();
                for (var info:template.getStructure(level)) {
                    BlockPos pos=origin.offset(info.pos());
                    level.setBlockAndUpdate(pos,info.state());
                    if (info.nbt()!=null) Objects.requireNonNull(level.getBlockEntity(pos)).loadWithComponents(info.nbt().copy(),level.registryAccess());
                }
                var player=FakePlayerFactory.getMinecraft(level);
                PackagedRuntime.equal("formed "+index,true,template.createStructure(level,origin.offset(template.getTriggerOffset()),Direction.SOUTH,player));
                BlockPos masterPos=origin.offset(2,1,1);
                var master=(MultiblockBlockEntityMaster<?>) Objects.requireNonNull(level.getBlockEntity(masterPos));
                var mb=master.getHelper().getContext().getLevel();
                var state=(SawmillLogic.State)master.getHelper().getState();
                BlockPos primary=mb.toAbsolute(new BlockPos(5,1,1));
                BlockPos secondary=mb.toAbsolute(new BlockPos(3,0,3));
                level.setBlockAndUpdate(primary,Blocks.BARREL.defaultBlockState());
                level.setBlockAndUpdate(secondary,Blocks.BARREL.defaultBlockState());
                ItemStack blade=PackagedRuntime.stack("immersiveengineering:sawblade");
                player.setItemInHand(InteractionHand.MAIN_HAND,blade);
                var blockState=level.getBlockState(masterPos);
                var interaction=((MultiblockPartBlock<?>)blockState.getBlock()).useItemOn(blade,blockState,level,masterPos,player,InteractionHand.MAIN_HAND,new BlockHitResult(Vec3.atCenterOf(masterPos),Direction.UP,masterPos,false));
                PackagedRuntime.equal("blade interaction "+index,true,interaction.consumesAction());
                PackagedRuntime.equal("blade installed "+index,"immersiveengineering:sawblade",BuiltInRegistries.ITEM.getKey(state.sawblade.getItem()).toString());
                PackagedRuntime.equal("blade consumed from hand "+index,true,player.getMainHandItem().isEmpty());
                var energy=Objects.requireNonNull(level.getCapability(Capabilities.EnergyStorage.BLOCK,mb.toAbsolute(new BlockPos(2,1,0)),mb.toAbsolute(RelativeBlockFace.UP)));
                PackagedRuntime.equal("power port accepts energy "+index,true,energy.receiveEnergy(100000,false)>0);
                var input=Objects.requireNonNull(level.getCapability(Capabilities.ItemHandler.BLOCK,mb.toAbsolute(new BlockPos(0,1,1)),mb.toAbsolute(RelativeBlockFace.RIGHT)));
                String source=family.get(key).getAsString();
                var recipe=Objects.requireNonNull(SawmillRecipe.findRecipe(level,PackagedRuntime.stack(source)));
                int before=energy.getEnergyStored();
                PackagedRuntime.equal("simulated insertion accepted "+index,true,input.insertItem(0,PackagedRuntime.stack(source),true).isEmpty());
                PackagedRuntime.equal("simulation leaves queue empty "+index,true,state.sawmillProcessQueue.isEmpty());
                PackagedRuntime.equal("actual insertion consumed "+index,true,input.insertItem(0,PackagedRuntime.stack(source),false).isEmpty());
                PackagedRuntime.equal("one queued input "+index,1,state.sawmillProcessQueue.size());
                String dust=BuiltInRegistries.ITEM.getKey(recipe.secondaryOutputs.get().getFirst().getItem()).toString();
                machines.add(new Machine(source,masterPos,primary,secondary,before,
                    recipe.getTotalProcessTime()*(recipe.getTotalProcessEnergy()/recipe.getTotalProcessTime()),state.sawblade.getDamageValue(),
                    Map.of(family.get("planks").getAsString(),6),Map.of(dust,key.startsWith("stripped_")?1:2)));
                index++;
            }
        }
        PackagedRuntime.equal("formed machine count",52,machines.size());
    }

    boolean complete(ServerLevel level) {
        return machines.stream().allMatch(m->((SawmillLogic.State)((MultiblockBlockEntityMaster<?>)Objects.requireNonNull(level.getBlockEntity(m.master))).getHelper().getState()).sawmillProcessQueue.isEmpty());
    }

    void verify(ServerLevel level) {
        for (Machine machine:machines) {
            var state=(SawmillLogic.State)((MultiblockBlockEntityMaster<?>)Objects.requireNonNull(level.getBlockEntity(machine.master))).getHelper().getState();
            PackagedRuntime.equal("primary port "+machine.input,machine.mainOutput,contents(level,machine.primary));
            PackagedRuntime.equal("secondary port "+machine.input,machine.secondaryOutput,contents(level,machine.secondary));
            PackagedRuntime.equal("consumed energy "+machine.input,machine.expectedEnergy,machine.energyBefore-state.getEnergy().getEnergyStored());
            PackagedRuntime.equal("blade wear "+machine.input,IEServerConfig.MACHINES.sawmill_bladeDamage.get(),state.sawblade.getDamageValue()-machine.bladeBefore);
            PackagedRuntime.equal("empty process queue "+machine.input,true,state.sawmillProcessQueue.isEmpty());
            PackagedRuntime.equal("no stray machine output "+machine.input,0,level.getEntitiesOfClass(ItemEntity.class,new AABB(machine.master).inflate(5)).size());
        }
    }

    static Map<String,Integer> contents(ServerLevel level,BlockPos pos) {
        var barrel=(BarrelBlockEntity)Objects.requireNonNull(level.getBlockEntity(pos));
        Map<String,Integer> result=new TreeMap<>();
        for(int slot=0;slot<barrel.getContainerSize();slot++) {
            ItemStack stack=barrel.getItem(slot);
            if(!stack.isEmpty()) result.merge(BuiltInRegistries.ITEM.getKey(stack.getItem()).toString(),stack.getCount(),Integer::sum);
        }
        return result;
    }

    /** One persisted real queue, paused by world redstone rather than editing state. */
    static final class Continuity {
        private final ServerLevel level;
        private final MultiblockBlockEntityMaster<SawmillLogic.State> master;
        private final SawmillLogic.State state;
        private final BlockPos primary,secondary,pause;
        private int pauseTick,pauseEnergy,expectedRemaining,bladeBefore;
        private Map<String,Integer> expectedPrimary,expectedSecondary;
        @SuppressWarnings("unchecked") Continuity(ServerLevel level) {
            this.level=level;
            master=(MultiblockBlockEntityMaster<SawmillLogic.State>)Objects.requireNonNull(level.getBlockEntity(new BlockPos(34,91,33)));
            state=master.getHelper().getState();var mb=master.getHelper().getContext().getLevel();
            primary=mb.toAbsolute(new BlockPos(5,1,1));secondary=mb.toAbsolute(new BlockPos(3,0,3));
            pause=mb.toAbsolute(new BlockPos(0,1,2)).west();
        }
        void begin() {
            PackagedRuntime.equal("continuity begins with empty real queue",true,state.sawmillProcessQueue.isEmpty());
            level.setBlockAndUpdate(pause,Blocks.AIR.defaultBlockState());
            var mb=master.getHelper().getContext().getLevel();
            var port=Objects.requireNonNull(level.getCapability(Capabilities.ItemHandler.BLOCK,mb.toAbsolute(new BlockPos(0,1,1)),mb.toAbsolute(RelativeBlockFace.RIGHT)));
            PackagedRuntime.equal("continuity real input accepted",true,port.insertItem(0,PackagedRuntime.stack("biomesoplenty:fir_log"),false).isEmpty());
        }
        boolean halfProcessed(){return state.sawmillProcessQueue.size()==1&&state.sawmillProcessQueue.getFirst().getRelativeProcessStep(level)>=0.5;}
        void pause() {
            level.setBlockAndUpdate(pause,Blocks.REDSTONE_BLOCK.defaultBlockState());
            PackagedRuntime.equal("real redstone pauses machine",false,state.rsState.isEnabled(master.getHelper().getContext()));
            pauseTick=state.sawmillProcessQueue.getFirst().writeToNBT(level.registryAccess()).getInt("processTick");pauseEnergy=state.getEnergy().getEnergyStored();
        }
        void verifyPaused() {
            PackagedRuntime.equal("paused queue still contains input",1,state.sawmillProcessQueue.size());
            PackagedRuntime.equal("redstone preserves queued progress",pauseTick,state.sawmillProcessQueue.getFirst().writeToNBT(level.registryAccess()).getInt("processTick"));
            PackagedRuntime.equal("redstone preserves stored energy",pauseEnergy,state.getEnergy().getEnergyStored());
        }
        void resume() {
            PackagedRuntime.equal("restored queue has exactly one input",1,state.sawmillProcessQueue.size());
            PackagedRuntime.equal("restored machine remains redstone paused",false,state.rsState.isEnabled(master.getHelper().getContext()));
            var process=state.sawmillProcessQueue.getFirst();var nbt=process.writeToNBT(level.registryAccess());
            PackagedRuntime.equal("restored queued input","biomesoplenty:fir_log",BuiltInRegistries.ITEM.getKey(process.getInput().getItem()).toString());
            var recipe=Objects.requireNonNull(SawmillRecipe.findRecipe(level,process.getInput()));
            expectedRemaining=(recipe.getTotalProcessTime()-nbt.getInt("processTick"))*(recipe.getTotalProcessEnergy()/recipe.getTotalProcessTime());
            expectedPrimary=new TreeMap<>(contents(level,primary));expectedPrimary.merge("biomesoplenty:fir_planks",6,Integer::sum);
            String dust=BuiltInRegistries.ITEM.getKey(recipe.secondaryOutputs.get().getFirst().getItem()).toString();
            expectedSecondary=new TreeMap<>(contents(level,secondary));expectedSecondary.merge(dust,(nbt.getBoolean("stripped")?0:1)+(nbt.getBoolean("sawed")?0:1),Integer::sum);
            pauseEnergy=state.getEnergy().getEnergyStored();bladeBefore=state.sawblade.getDamageValue();
            level.setBlockAndUpdate(pause,Blocks.AIR.defaultBlockState());
            PackagedRuntime.equal("restored machine enabled by removing real redstone",true,state.rsState.isEnabled(master.getHelper().getContext()));
        }
        boolean finished(){return state.sawmillProcessQueue.isEmpty();}
        void verifyResumed() {
            PackagedRuntime.equal("restored primary output",expectedPrimary,contents(level,primary));
            PackagedRuntime.equal("restored secondary output without duplicate stripping",expectedSecondary,contents(level,secondary));
            PackagedRuntime.equal("restored remaining energy consumption",expectedRemaining,pauseEnergy-state.getEnergy().getEnergyStored());
            PackagedRuntime.equal("restored blade wear",IEServerConfig.MACHINES.sawmill_bladeDamage.get(),state.sawblade.getDamageValue()-bladeBefore);
        }
    }
}
