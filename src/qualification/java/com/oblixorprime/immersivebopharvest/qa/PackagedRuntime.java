package com.oblixorprime.immersivebopharvest.qa;

import blusunrize.immersiveengineering.api.multiblocks.blocks.registry.MultiblockBlockEntityMaster;
import blusunrize.immersiveengineering.common.blocks.multiblocks.logic.sawmill.SawmillLogic;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BarrelBlockEntity;
import net.neoforged.fml.ModList;
import net.neoforged.fml.loading.FMLLoader;
import net.neoforged.fml.loading.FMLPaths;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import vectorwing.farmersdelight.common.block.entity.CuttingBoardBlockEntity;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.concurrent.CompletableFuture;

/** Explicitly armed test-only instrumentation for disposable production instances. */
public final class PackagedRuntime {
    private static final Map<String,Object> REPORT=new LinkedHashMap<>();
    private static final List<Map<String,Object>> CHECKS=new ArrayList<>();
    private static final List<Map<String,Object>> CASES=new ArrayList<>();
    private static final BlockPos CASE_POS=new BlockPos(0,90,16);
    private static JsonObject plan;
    private static Path gameDirectory;
    private static String phase;
    private static MinecraftServer server;
    private static List<QualificationChecks.Case> cases;
    private static QualificationChecks.Case pending;
    private static FormedSawmills sawmills;
    private static FormedSawmills.Continuity continuity;
    private static CompletableFuture<Void> reload;
    private static int tick, index, due, state;
    private static long started;
    private static volatile boolean finished;

    static void install() {
        if(System.getProperty("bop.qa.phase")==null) return;
        try {
            phase=System.getProperty("bop.qa.phase");
            if(!List.of("baseline-create","baseline-restart","candidate-upgrade","candidate-restart","multiplayer","client-one","client-two").contains(phase)) throw new IllegalArgumentException("Unknown explicit QA profile");
            gameDirectory=FMLPaths.GAMEDIR.get().toRealPath();
            plan=JsonParser.parseString(Files.readString(gameDirectory.resolve("bop-qa-plan.json"))).getAsJsonObject();
            equal("owned disposable instance",plan.get("nonce").getAsString(),Files.readString(gameDirectory.resolve(".bop-qa-owner")).trim());
            equal("explicit launch profile",phase,plan.get("phase").getAsString());
            equal("production loader",true,FMLLoader.isProduction());
            var identities=new ArrayList<Map<String,Object>>();
            for(var row:plan.getAsJsonArray("mods")) {
                var expected=row.getAsJsonObject();
                String mod=expected.get("modId").getAsString();
                Path actual=ModList.get().getModFileById(mod).getFile().getFilePath().toRealPath();
                equal("regular packaged mod "+mod,true,Files.isRegularFile(actual));
                equal("packaged mod path "+mod,gameDirectory.resolve("mods").resolve(expected.get("name").getAsString()).toRealPath().toString(),actual.toString());
                equal("packaged mod hash "+mod,expected.get("sha256").getAsString(),hash(actual));
                equal("packaged mod size "+mod,expected.get("size").getAsLong(),Files.size(actual));
                identities.add(Map.of("modId",mod,"path",actual.toString(),"sha256",hash(actual),"size",Files.size(actual)));
            }
            try(var files=Files.list(gameDirectory.resolve("mods"))) {
                equal("exact staged mod jar count",7L,files.filter(p->p.toString().endsWith(".jar")).count());
            }
            REPORT.put("schemaVersion",1); REPORT.put("executionMode","packaged-production");
            REPORT.put("phase",phase);REPORT.put("nonce",plan.get("nonce").getAsString());
            REPORT.put("candidateVersion",ModList.get().getModContainerById("immersive_bop_harvest").orElseThrow().getModInfo().getVersion().toString());
            REPORT.put("loadedJarIdentities",identities);REPORT.put("testHarnessIsSeparate",true);
            REPORT.put("checks",CHECKS); REPORT.put("phaseStatus","STARTED");write();
            NeoForge.EVENT_BUS.addListener(PackagedRuntime::started);
            NeoForge.EVENT_BUS.addListener(PackagedRuntime::tick);
            if(phase.equals("multiplayer")||phase.equals("client-one"))ClientInteractions.install();
        } catch(Exception e) { throw new IllegalStateException("Cannot arm disposable packaged QA",e); }
    }

    private static void started(ServerStartedEvent event) {
        if(phase.equals("client-two")) return;
        server=event.getServer();started=System.nanoTime();
        REPORT.put("dedicatedServer",!server.isSingleplayer());
        REPORT.put("serverStarted",true);
        ServerLevel level=server.overworld();
        level.setChunkForced(0,0,true);level.setChunkForced(0,1,true);
        cases=QualificationChecks.cases();
        System.out.println("BOP_QA: production server started profile="+phase);
    }

    private static void tick(ServerTickEvent.Post event) {
        if(server==null||event.getServer()!=server||finished)return;
        try {
            tick++;
            if(tick>6000) throw new IllegalStateException("Explicit 6000 server-tick budget exhausted");
            if(tick<20)return;
            if(phase.equals("multiplayer"))return;
            ServerLevel level=server.overworld();
            if(state==0) {
                if(!level.areEntitiesLoaded(net.minecraft.world.level.ChunkPos.asLong(CASE_POS.getX()>>4,CASE_POS.getZ()>>4))||!level.isPositionEntityTicking(CASE_POS))return;
                equal("case arena entities loaded",true,true);
                if(plan.has("expectedSnapshot")) {
                    JsonObject expected=plan.getAsJsonObject("expectedSnapshot");
                    equal("persisted world state",expected,JsonParser.parseString(new GsonBuilder().create().toJson(snapshot(level))));
                }
                if(plan.has("expectedSnapshot")) {
                    continuity=new FormedSawmills.Continuity(level);continuity.resume();
                    var board=(CuttingBoardBlockEntity)Objects.requireNonNull(level.getBlockEntity(new BlockPos(1,90,2)));
                    equal("restored board processes retained input",true,board.processStoredItemUsingTool(new ItemStack(net.minecraft.world.item.Items.IRON_AXE),null));
                    equal("restored board consumes retained input",true,board.isEmpty());
                    Map<String,Integer> drops=new java.util.TreeMap<>();
                    for(var item:level.getEntitiesOfClass(net.minecraft.world.entity.item.ItemEntity.class,new net.minecraft.world.phys.AABB(new BlockPos(1,90,2)).inflate(3))) {
                        drops.merge(BuiltInRegistries.ITEM.getKey(item.getItem().getItem()).toString(),item.getItem().getCount(),Integer::sum);item.discard();
                    }
                    equal("restored board actual output",Map.of("biomesoplenty:stripped_fir_log",1,"farmersdelight:tree_bark",1),drops);
                    state=7;due=tick+150;return;
                }
                state=1;
            }
            if(state==1) {
                if(pending!=null) {
                    if(tick<due)return;
                    pending.finish(level,CASE_POS);recordCase(pending);pending=null;return;
                }
                if(index<cases.size()) {
                    var test=cases.get(index++);test.run(level,CASE_POS);
                    if(test.settleTicks()>0){pending=test;due=tick+test.settleTicks();}else recordCase(test);
                    return;
                }
                REPORT.put("scopedCases",CASES);REPORT.put("scopedAssertions",new LinkedHashMap<>(QualificationChecks.observations()));
                REPORT.put("scopedDurationNanos",System.nanoTime()-started);
                sawmills=new FormedSawmills();sawmills.start(level);state=2;due=tick+400;
            } else if(state==2) {
                if(sawmills.complete(level)) {sawmills.verify(level);state=3;}
                else if(tick>due)throw new IllegalStateException("Formed sawmills exceeded 400-tick budget");
            } else if(state==3) {
                reload=server.reloadResources(server.getPackRepository().getSelectedIds());state=4;
            } else if(state==4) {
                if(!reload.isDone())return;
                reload.join();equal("datapack reload",true,true);
                // Fixed repeated-operation budget; reuse the real board operation action.
                var board=cases.stream().filter(c->c.id().startsWith("cutting_")).findFirst().orElseThrow();
                long before=System.nanoTime();
                for(int loop=0;loop<100;loop++)new QualificationChecks.Case("repeat_board_"+loop,board.action()).run(level,CASE_POS);
                REPORT.put("repeatedBoardOperations",100);REPORT.put("repeatedDurationNanos",System.nanoTime()-before);
                Map<String,Object> repeated=new LinkedHashMap<>();
                QualificationChecks.observations().forEach((name,observations)->{if(name.startsWith("repeat_board_"))repeated.put(name,observations);});
                REPORT.put("repeatedAssertions",repeated);
                continuity=new FormedSawmills.Continuity(level);continuity.begin();state=5;due=tick+150;
            } else if(state==5) {
                if(continuity.halfProcessed()){continuity.pause();state=6;due=tick+5;}
                else if(tick>due)throw new IllegalStateException("Cannot reach bounded in-flight save point");
            } else if(state==6&&tick>=due) {
                continuity.verifyPaused();saveAndFinish(level);
            } else if(state==7) {
                if(continuity.finished()) {
                    continuity.verifyResumed();
                    if(phase.endsWith("restart")){continuity.begin();state=5;due=tick+150;}
                    else state=1;
                } else if(tick>due)throw new IllegalStateException("Restored machine did not finish within budget");
            }
        } catch(Throwable e) {
            REPORT.put("phaseStatus","FAIL");REPORT.put("error",e.toString());e.printStackTrace();
            try{write();}catch(Exception problem){problem.printStackTrace();}
            finished=true;
            if(!server.isSingleplayer())server.halt(false);
        }
    }

    private static void recordCase(QualificationChecks.Case test) {
        var row=new LinkedHashMap<String,Object>();row.put("id",test.id());row.put("passed",true);row.put("required",true);row.put("error",null);CASES.add(row);
    }

    private static void saveAndFinish(ServerLevel level) throws Exception {
        {
            BlockPos inventory=new BlockPos(2,90,2);
            level.setBlockAndUpdate(inventory,Blocks.BARREL.defaultBlockState());
            var barrel=(BarrelBlockEntity)Objects.requireNonNull(level.getBlockEntity(inventory));
            barrel.clearContent();barrel.setItem(0,new ItemStack(net.minecraft.world.item.Items.APPLE,7));barrel.setItem(1,stack("biomesoplenty:fir_log"));barrel.setChanged();
            level.setBlockAndUpdate(inventory.east(),Blocks.DIAMOND_BLOCK.defaultBlockState());
            BlockPos boardPos=inventory.west();
            level.setBlockAndUpdate(boardPos.below(),Blocks.STONE.defaultBlockState());
            level.setBlockAndUpdate(boardPos,BuiltInRegistries.BLOCK.get(ResourceLocation.parse("farmersdelight:cutting_board")).defaultBlockState());
            var board=(CuttingBoardBlockEntity)Objects.requireNonNull(level.getBlockEntity(boardPos));
            if(board.isEmpty())equal("save fixture board accepts log",true,board.addItem(stack("biomesoplenty:fir_log")).isEmpty());
            equal("save fixture board retains log","biomesoplenty:fir_log",BuiltInRegistries.ITEM.getKey(board.getStoredItem().getItem()).toString());
            equal("save fixture board input count",1,board.getStoredItem().getCount());
        }
        REPORT.put("savedSnapshot",snapshot(level));
        server.saveEverything(false,true,true);
        REPORT.put("saveCalled",true);REPORT.put("serverTicks",tick);REPORT.put("durationNanos",System.nanoTime()-started);
        REPORT.put("phaseStatus","PASS");write();finished=true;
        System.out.println("BOP_QA: phase passed "+phase);
        if(!server.isSingleplayer())server.halt(false);
    }

    private static Map<String,Object> snapshot(ServerLevel level) {
        Map<String,Object> snapshot=new LinkedHashMap<>();
        snapshot.put("barrel",FormedSawmills.contents(level,new BlockPos(2,90,2)));
        snapshot.put("marker",BuiltInRegistries.BLOCK.getKey(level.getBlockState(new BlockPos(3,90,2)).getBlock()).toString());
        var board=(CuttingBoardBlockEntity)Objects.requireNonNull(level.getBlockEntity(new BlockPos(1,90,2)));
        snapshot.put("boardInput",Map.of("item",BuiltInRegistries.ITEM.getKey(board.getStoredItem().getItem()).toString(),"count",board.getStoredItem().getCount()));
        List<Map<String,Object>> machines=new ArrayList<>();
        for(int index=0;index<52;index++) {
            BlockPos origin=new BlockPos(32+(index%8)*9,90,32+(index/8)*8);
            var master=(MultiblockBlockEntityMaster<?>)Objects.requireNonNull(level.getBlockEntity(origin.offset(2,1,1)));
            var mb=master.getHelper().getContext().getLevel();var state=(SawmillLogic.State)master.getHelper().getState();
            var processes=state.sawmillProcessQueue.stream().map(process->{var nbt=process.writeToNBT(level.registryAccess());return Map.of("tick",nbt.getInt("processTick"),"stripped",nbt.getBoolean("stripped"),"sawed",nbt.getBoolean("sawed"),"input",BuiltInRegistries.ITEM.getKey(process.getInput().getItem()).toString(),"count",process.getInput().getCount());}).toList();
            machines.add(Map.of("index",index,"primary",FormedSawmills.contents(level,mb.toAbsolute(new BlockPos(5,1,1))),"secondary",FormedSawmills.contents(level,mb.toAbsolute(new BlockPos(3,0,3))),"energy",state.getEnergy().getEnergyStored(),"bladeDamage",state.sawblade.getDamageValue(),"processes",processes,"redstoneEnabled",state.rsState.isEnabled(master.getHelper().getContext())));
        }
        snapshot.put("formedMachines",machines);return snapshot;
    }

    static JsonObject spec(String name) {
        try(var stream=Objects.requireNonNull(PackagedRuntime.class.getResourceAsStream("/bop_qa/spec/"+name+".json"));var reader=new InputStreamReader(stream,StandardCharsets.UTF_8)) {return JsonParser.parseReader(reader).getAsJsonObject();}
        catch(Exception e){throw new IllegalStateException(e);}
    }
    static ItemStack stack(String name) {var id=ResourceLocation.parse(name);if(!BuiltInRegistries.ITEM.containsKey(id))throw new IllegalArgumentException(name);return new ItemStack(BuiltInRegistries.ITEM.get(id));}
    static void equal(String check,Object expected,Object actual) {
        CHECKS.add(Map.of("check",check,"expected",expected,"actual",actual));
        if(!expected.equals(actual))throw new IllegalStateException(check+" expected="+expected+" actual="+actual);
    }
    static String hash(Path file) throws Exception{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(file)));}
    static boolean passed(){return finished&&"PASS".equals(REPORT.get("phaseStatus"));}
    static String failure(){return finished&&"FAIL".equals(REPORT.get("phaseStatus"))?String.valueOf(REPORT.get("error")):null;}
    static void interactionReport(Map<String,Object> observations) {
        REPORT.put("clientInteractions",observations);
        try{write();}catch(Exception e){throw new IllegalStateException(e);}
    }
    static void finishMultiplayer(MinecraftServer instance)throws Exception {
        REPORT.put("savedSnapshot",snapshot(instance.overworld()));instance.saveEverything(false,true,true);
        REPORT.put("saveCalled",true);REPORT.put("phaseStatus","PASS");REPORT.put("serverTicks",tick);write();finished=true;instance.halt(false);
    }
    static void failInteraction(MinecraftServer instance,Throwable error) {
        error.printStackTrace();REPORT.put("phaseStatus","FAIL");REPORT.put("error",error.toString());finished=true;
        try{write();}catch(Exception e){e.printStackTrace();}
        if(!instance.isSingleplayer())instance.halt(false);
    }
    private static void write() throws Exception{Files.writeString(gameDirectory.resolve("bop-qa-result.json"),new GsonBuilder().setPrettyPrinting().create().toJson(REPORT)+"\n");}
}
