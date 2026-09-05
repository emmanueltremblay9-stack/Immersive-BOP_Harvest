package com.oblixorprime.immersivebopharvest.qa;

import com.google.gson.GsonBuilder;
import net.minecraft.client.Minecraft;
import net.minecraft.client.Screenshot;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.client.gui.screens.ConnectScreen;
import net.minecraft.client.gui.screens.DisconnectedScreen;
import net.minecraft.client.gui.screens.GenericMessageScreen;
import net.minecraft.network.chat.Component;
import net.minecraft.client.multiplayer.ServerData;
import net.minecraft.client.multiplayer.resolver.ServerAddress;
import net.minecraft.client.gui.screens.worldselection.CreateWorldScreen;
import net.minecraft.client.gui.screens.worldselection.WorldCreationUiState;
import net.minecraft.network.chat.contents.TranslatableContents;
import net.minecraft.world.level.levelgen.presets.WorldPresets;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.core.Direction;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Drives the actual rendered client; every phase is disabled in ordinary runs. */
@EventBusSubscriber(modid="bop_harvest_qa",value=Dist.CLIENT)
public final class ClientQualification {
    private static final Map<String,Object> report=new LinkedHashMap<>();
    private static final List<Map<String,Object>> screenshots=new ArrayList<>();
    private static volatile int state;
    private static int tick,due;
    private static boolean initialized;
    private static volatile boolean requestedStop;
    private static boolean capturing;
    private static boolean multiplayer,reconnect;
    private static int attempts;
    @SubscribeEvent public static void tick(ClientTickEvent.Post event) {
        String phase=System.getProperty("bop.qa.phase","");
        if(!phase.equals("client-one")&&!phase.equals("client-two"))return;
        Minecraft mc=Minecraft.getInstance();
        if(state==99||state==98)return;
        try {
            if(!initialized) {
                initialized=true;
                if(Boolean.getBoolean("bop.qa.hideClient"))org.lwjgl.glfw.GLFW.glfwHideWindow(mc.getWindow().getWindow());
                Runtime.getRuntime().addShutdownHook(new Thread(()->{
                    try {Files.writeString(mc.gameDirectory.toPath().resolve("bop-qa-client-exit.json"),new GsonBuilder().create().toJson(Map.of("state",state,"stopRequestedByHarness",requestedStop))+"\n");}
                    catch(Exception e){e.printStackTrace();}
                },"bop-qa-exit-evidence"));
            }
            tick++;
            if(Files.exists(mc.gameDirectory.toPath().resolve(".bop-qa-cancel-"+Files.readString(mc.gameDirectory.toPath().resolve(".bop-qa-owner")).trim())))
                throw new IllegalStateException("Client qualification cancelled by its controller");
            if(mc.screen instanceof DisconnectedScreen)throw new IllegalStateException("Client disconnected unexpectedly during phase state "+state);
            if(tick>10000)throw new IllegalStateException("Explicit client 10000-tick budget exhausted");
            if(PackagedRuntime.failure()!=null)throw new IllegalStateException(PackagedRuntime.failure());
            if(state==0&&mc.screen instanceof TitleScreen&&mc.getOverlay()==null) {
                state=1;due=tick+40;report.put("phase",phase);report.put("titleScreen",true);report.put("screenshots",screenshots);
                report.put("nonce",Files.readString(mc.gameDirectory.toPath().resolve(".bop-qa-owner")).trim());
            } else if(state==1&&tick>=due&&!capturing) {
                state=2;capture(mc,"title",()->{state=3;});
            } else if(state==3) {
                if(phase.equals("client-two")){state=20;due=tick+20;}
                else {state=4;CreateWorldScreen.openFresh(mc,mc.screen);}
            } else if(state==4&&mc.screen instanceof CreateWorldScreen create) {
                create.getUiState().setName("BOP qualification disposable");
                create.getUiState().setSeed("9052026");
                create.getUiState().setGameMode(WorldCreationUiState.SelectedGameMode.CREATIVE);
                create.getUiState().setAllowCommands(true);
                create.getUiState().setWorldType(create.getUiState().getNormalPresetList().stream().filter(p->p.preset()!=null&&p.preset().is(WorldPresets.FLAT)).findFirst().orElseThrow());
                state=5;due=tick+20;
            } else if(state==5&&tick>=due&&mc.screen instanceof CreateWorldScreen create) {
                Button button=create.children().stream().filter(w->w instanceof Button b&&b.getMessage().getContents() instanceof TranslatableContents c&&c.getKey().equals("selectWorld.create")).map(w->(Button)w).findFirst().orElseThrow();
                if(button.active&&button.visible){state=6;button.onPress();}
            } else if(state==6&&mc.level!=null&&mc.player!=null&&mc.getSingleplayerServer()!=null) {
                state=7;report.put("createdWorld",true);report.put("integratedServer",true);
                mc.getConnection().sendCommand("tp @s 38 94 30 0 25");
            } else if(state==7&&PackagedRuntime.passed()&&!capturing) {
                state=8;due=tick+40;
            } else if(state==8&&tick>=due&&!capturing) {
                state=9;capture(mc,"world-and-formed-sawmills",()->{state=10;});
            } else if(state==10) {
                state=30;mc.getConnection().sendCommand("bopqa ready");
            } else if(state==20&&tick>=due&&mc.level==null&&mc.screen instanceof TitleScreen) {
                state=21;multiplayer=true;
                String address="127.0.0.1:"+System.getProperty("bop.qa.port","25575");
                ConnectScreen.startConnecting(mc.screen,mc,ServerAddress.parseString(address),new ServerData("Disposable BOP QA",address,ServerData.Type.OTHER),false,null);
            } else if(state==21&&mc.level!=null&&mc.player!=null&&mc.getConnection()!=null) {
                state=22;due=tick+40;report.put("joinedDedicatedServer",true);
            } else if(state==22&&tick>=due) {
                if(reconnect){state=40;mc.getConnection().sendCommand("bopqa rejoined");}
                else {state=30;mc.getConnection().sendCommand("bopqa ready");}
            } else if(state==30&&mc.level.getBlockState(ClientInteractions.MARKER).is(Blocks.GOLD_BLOCK)) {
                state=31;due=tick+20;attempts=0;
            } else if(state==31&&tick>=due) {
                mc.gameMode.useItemOn(mc.player,InteractionHand.MAIN_HAND,new BlockHitResult(Vec3.atCenterOf(ClientInteractions.BOARD),Direction.UP,ClientInteractions.BOARD,false));
                attempts++;
                if(attempts==3){state=32;mc.getConnection().sendCommand("bopqa clicked");}
            } else if((state==32||state==61)&&mc.level.getBlockState(ClientInteractions.MARKER).is(Blocks.EMERALD_BLOCK)) {
                state=33;due=tick+30;report.put(multiplayer?"multiplayerAuthoritativeBoardResult":"singleplayerAuthoritativeBoardResult",true);
            } else if(state==32&&phase.equals("client-one")&&mc.level.getBlockState(ClientInteractions.MARKER).is(Blocks.QUARTZ_BLOCK)) {
                int empty=-1;for(int slot=0;slot<9;slot++)if(mc.player.getInventory().getItem(slot).isEmpty()){empty=slot;break;}
                if(empty<0)throw new IllegalStateException("Tool retrieval needs a free real client inventory slot");
                mc.player.getInventory().selected=empty;state=60;due=tick+10;
            } else if(state==60&&tick>=due) {
                mc.gameMode.useItemOn(mc.player,InteractionHand.MAIN_HAND,new BlockHitResult(Vec3.atCenterOf(ClientInteractions.BOARD),Direction.UP,ClientInteractions.BOARD,false));
                mc.getConnection().sendCommand("bopqa cleared");state=61;
            } else if(state==33&&tick>=due&&!capturing) {
                state=34;capture(mc,multiplayer?"multiplayer-board-result":"singleplayer-board-result",()->{state=35;});
            } else if(state==35) {
                mc.getConnection().sendCommand("bopqa observed");state=36;due=tick+20;
            } else if(state==36&&tick>=due) {
                if(phase.equals("client-one")){state=50;mc.player.getInventory().selected=0;mc.getConnection().sendCommand("bopqa extras");}
                else state=40;
            } else if(state==50&&mc.level.getBlockState(ClientInteractions.MARKER).is(Blocks.COPPER_BLOCK)&&mc.player.getMainHandItem().getItem().toString().equals("immersiveengineering:sawblade")) {
                state=51;due=tick+30;
            } else if(state==51&&tick>=due) {
                mc.gameMode.useItemOn(mc.player,InteractionHand.MAIN_HAND,new BlockHitResult(Vec3.atCenterOf(ClientInteractions.SAW),Direction.UP,ClientInteractions.SAW,false));
                mc.getConnection().sendCommand("bopqa saw-clicked");state=52;
            } else if(state==52&&mc.level.getBlockState(ClientInteractions.MARKER).is(Blocks.LAPIS_BLOCK)&&!capturing) {
                state=53;report.put("actualSawmillInteraction",true);capture(mc,"sawmill-client-result"+(multiplayer?"-multiplayer":"-singleplayer"),()->{state=54;});
            } else if(state==54) {
                mc.getConnection().sendCommand("bopqa harvest-ready");state=55;
            } else if(state==55&&mc.level.getBlockState(ClientInteractions.MARKER).is(Blocks.REDSTONE_BLOCK)&&mc.player.getMainHandItem().getItem().toString().equals("farmersdelight:iron_knife")) {
                mc.gameMode.startDestroyBlock(ClientInteractions.HARVEST,Direction.UP);state=56;
            } else if(state==56) {
                mc.gameMode.continueDestroyBlock(ClientInteractions.HARVEST,Direction.UP);
                if(mc.level.getBlockState(ClientInteractions.HARVEST).isAir()){mc.getConnection().sendCommand("bopqa harvested");state=57;}
            } else if(state==57&&mc.level.getBlockState(ClientInteractions.MARKER).is(Blocks.NETHERITE_BLOCK)&&!capturing) {
                state=58;report.put("actualHarvestInteraction",true);capture(mc,"harvest-client-result"+(multiplayer?"-multiplayer":"-singleplayer"),()->{state=59;due=tick+20;});
            } else if(state==59&&tick>=due) {
                if(!multiplayer){mc.getConnection().sendCommand("bopqa finished");state=37;due=tick+20;}
                else {state=38;reconnect=true;disconnect(mc);due=tick+40;}
            } else if(state==37&&tick>=due) {
                state=20;disconnect(mc);due=tick+40;report.put("cleanSingleplayerDisconnect",true);
            } else if(state==38&&tick>=due&&mc.level==null) {state=20;due=tick+20;}
            else if(state==40&&mc.level!=null&&mc.level.getBlockState(ClientInteractions.MARKER).is(Blocks.DIAMOND_BLOCK)&&!capturing) {
                state=41;due=tick+20;report.put("serverConfirmedReconnect",true);
            } else if(state==41&&tick>=due&&!capturing) {
                state=42;capture(mc,"reconnect-complete",()->{state=43;});
            } else if(state==43) {
                mc.getConnection().sendCommand("bopqa finished");state=44;due=tick+20;
            } else if(state==44&&tick>=due) {
                state=45;disconnect(mc);due=tick+20;
            } else if(state==45&&tick>=due&&mc.level==null) {
                report.put("cleanDisconnect",true);report.put("phaseStatus","PASS");write(mc);state=99;requestedStop=true;mc.stop();
            }
        } catch(Throwable e) {
            e.printStackTrace();report.put("phaseStatus","FAIL");report.put("error",e.toString());
            try{write(mc);}catch(Exception ignored){}
            state=99;requestedStop=true;mc.stop();
        }
    }
    private static void disconnect(Minecraft mc) {
        int nextState=state;state=98;
        // Vanilla PauseScreen closes the connection before waiting for server save.
        // Minecraft.disconnect runs nested frames, so the controller stays inert.
        mc.level.disconnect();
        mc.disconnect(new GenericMessageScreen(Component.translatable("menu.savingLevel")));
        mc.setScreen(new TitleScreen());state=nextState;
    }
    private static void capture(Minecraft mc,String name,Runnable next) {
        capturing=true;
        String file="bop-qa-"+name+".png";
        Screenshot.grab(mc.gameDirectory,file,mc.getMainRenderTarget(),message->mc.execute(()->{
            try {
                Path path=mc.gameDirectory.toPath().resolve("screenshots").resolve(file);
                if(!Files.isRegularFile(path)||Files.size(path)<1000)throw new IllegalStateException("Screenshot write failed: "+message.getString());
                screenshots.add(Map.of("stage",name,"file",file,"size",Files.size(path),"sha256",PackagedRuntime.hash(path)));
                capturing=false;next.run();
            }catch(Exception e){report.put("phaseStatus","FAIL");report.put("error",e.toString());try{write(mc);}catch(Exception ignored){}state=99;requestedStop=true;mc.stop();}
        }));
    }
    private static void write(Minecraft mc)throws Exception{Files.writeString(mc.gameDirectory.toPath().resolve("bop-qa-client.json"),new GsonBuilder().setPrettyPrinting().create().toJson(report)+"\n");}
}
