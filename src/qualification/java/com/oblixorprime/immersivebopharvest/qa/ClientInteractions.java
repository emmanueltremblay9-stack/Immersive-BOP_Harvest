package com.oblixorprime.immersivebopharvest.qa;

import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import blusunrize.immersiveengineering.api.crafting.SawmillRecipe;
import blusunrize.immersiveengineering.api.multiblocks.blocks.registry.MultiblockBlockEntityMaster;
import blusunrize.immersiveengineering.api.multiblocks.blocks.util.RelativeBlockFace;
import blusunrize.immersiveengineering.common.blocks.multiblocks.logic.sawmill.SawmillLogic;
import blusunrize.immersiveengineering.common.config.IEServerConfig;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.MultifaceBlock;
import net.minecraft.tags.TagKey;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.phys.AABB;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;
import net.neoforged.neoforge.event.entity.player.ItemEntityPickupEvent;
import net.neoforged.neoforge.event.entity.EntityJoinLevelEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import net.neoforged.neoforge.event.level.BlockEvent;
import net.neoforged.neoforge.event.level.BlockDropsEvent;
import net.neoforged.neoforge.capabilities.Capabilities;
import vectorwing.farmersdelight.common.block.entity.CuttingBoardBlockEntity;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.UUID;

/** Real client packets compete for one board input. Results are measured on the server. */
final class ClientInteractions {
    static final BlockPos BOARD=new BlockPos(8,91,8), MARKER=new BlockPos(8,91,6);
    static final BlockPos SAW=new BlockPos(43,91,33), HARVEST=new BlockPos(8,91,9);
    private static final Map<String,UUID> ready=new LinkedHashMap<>();
    private static final Set<String> clicked=new HashSet<>(),observed=new HashSet<>(),finished=new HashSet<>(),clickPlayers=new HashSet<>();
    private static final List<Map<String,Object>> events=new ArrayList<>();
    private static List<Map<String,Object>> logoutInventory;
    private static MinecraftServer server;
    private static int ticks,due,maxOnline;
    private static boolean prepared,verified,reconnected,completion;
    private static int extraStage,energyBefore,bladeBefore;
    private static Map<String,Integer> expectedPrimary,expectedSecondary;
    private static final Map<String,Boolean> extraChecks=new LinkedHashMap<>();
    private static boolean sawPacket,harvestPacket;
    private static boolean interactionInspected,cleanupPending,retrievalPacket;
    private static final List<Map<String,Object>> harvestEvents=new ArrayList<>();
    private static final Map<UUID,Map<String,Object>> anchoredDrops=new LinkedHashMap<>();
    private static final Set<UUID> joinedDrops=new HashSet<>();
    private static int harvestSequence;
    private static Map<String,Object> harvestBaseline;

    static void install() {
        NeoForge.EVENT_BUS.addListener(ClientInteractions::commands);
        NeoForge.EVENT_BUS.addListener(ClientInteractions::click);
        NeoForge.EVENT_BUS.addListener(ClientInteractions::logout);
        NeoForge.EVENT_BUS.addListener(ClientInteractions::tick);
        NeoForge.EVENT_BUS.addListener(ClientInteractions::broken);
        NeoForge.EVENT_BUS.addListener(ClientInteractions::drops);
        NeoForge.EVENT_BUS.addListener(ClientInteractions::join);
        NeoForge.EVENT_BUS.addListener(ClientInteractions::pickup);
    }
    private static void commands(RegisterCommandsEvent event) {
        var root=Commands.literal("bopqa").requires(source->source.getEntity() instanceof ServerPlayer player&&Set.of("BopQaOne","BopQaTwo").contains(player.getGameProfile().getName()));
        for(String action:List.of("ready","clicked","cleared","observed","extras","saw-clicked","harvest-ready","harvested","rejoined","finished"))
            root.then(Commands.literal(action).executes(context->{handle(context.getSource().getPlayerOrException(),action);return 1;}));
        event.getDispatcher().register(root);
    }
    private static void handle(ServerPlayer player,String action) {
        server=player.getServer();String name=player.getGameProfile().getName();
        events.add(Map.of("event",action,"player",name,"uuid",player.getUUID().toString(),"tick",ticks));
        switch(action) {
            case "ready" -> {
                if(ready.containsKey(name))throw new IllegalStateException("Duplicate initial client ready");
                ready.put(name,player.getUUID());
                if(ready.size()==1)prepare(server.overworld());
                player.setGameMode(GameType.SURVIVAL);player.getInventory().clearContent();
                player.getInventory().setItem(0,new ItemStack(Items.IRON_AXE));player.getInventory().selected=0;
                player.teleportTo(server.overworld(),name.equals("BopQaOne")?6.5:10.5,91,10.5,name.equals("BopQaOne")?-45:45,40);
                if(ready.size()==requiredPlayers())server.overworld().setBlockAndUpdate(MARKER,Blocks.GOLD_BLOCK.defaultBlockState());
            }
            case "clicked" -> {clicked.add(name);if(clicked.size()==requiredPlayers())due=ticks+20;}
            case "cleared" -> {
                PackagedRuntime.equal("real client retrieved parked tool",true,name.equals("BopQaOne")&&cleanupPending&&retrievalPacket);
                cleanupPending=false;due=ticks+10;
            }
            case "observed" -> {PackagedRuntime.equal("client observed server result "+name,true,verified);observed.add(name);}
            case "extras" -> {
                PackagedRuntime.equal("additional interactions use observed client-one",true,name.equals("BopQaOne")&&observed.contains(name)&&extraStage==0);
                var helper=sawMaster().getHelper();var state=(SawmillLogic.State)helper.getState();
                PackagedRuntime.equal("client saw fixture starts idle",true,state.sawmillProcessQueue.isEmpty());
                events.add(Map.of("event","fixture-blade-removed","player",name,"tick",ticks,"item",state.sawblade.getItem().toString(),"damage",state.sawblade.getDamageValue()));
                state.sawblade=ItemStack.EMPTY;helper.getContext().markDirtyAndSync();
                player.getInventory().clearContent();player.getInventory().setItem(0,PackagedRuntime.stack("immersiveengineering:sawblade"));player.getInventory().selected=0;
                player.teleportTo(server.overworld(),41.5,91,35.5,-30,30);
                extraStage=1;server.overworld().setBlockAndUpdate(MARKER,Blocks.COPPER_BLOCK.defaultBlockState());
            }
            case "saw-clicked" -> {
                PackagedRuntime.equal("real client saw interaction packet",true,sawPacket&&name.equals("BopQaOne")&&extraStage==1);
                var helper=sawMaster().getHelper();var state=(SawmillLogic.State)helper.getState();var mb=helper.getContext().getLevel();
                PackagedRuntime.equal("client installed real sawblade","immersiveengineering:sawblade",BuiltInRegistries.ITEM.getKey(state.sawblade.getItem()).toString());
                PackagedRuntime.equal("client blade consumed from inventory",true,player.getMainHandItem().isEmpty());
                var recipe=SawmillRecipe.findRecipe(server.overworld(),PackagedRuntime.stack("biomesoplenty:fir_log"));
                expectedPrimary=new TreeMap<>(FormedSawmills.contents(server.overworld(),mb.toAbsolute(new BlockPos(5,1,1))));expectedPrimary.merge("biomesoplenty:fir_planks",6,Integer::sum);
                expectedSecondary=new TreeMap<>(FormedSawmills.contents(server.overworld(),mb.toAbsolute(new BlockPos(3,0,3))));expectedSecondary.merge(BuiltInRegistries.ITEM.getKey(recipe.secondaryOutputs.get().getFirst().getItem()).toString(),2,Integer::sum);
                energyBefore=state.getEnergy().getEnergyStored();bladeBefore=state.sawblade.getDamageValue();
                var input=server.overworld().getCapability(Capabilities.ItemHandler.BLOCK,mb.toAbsolute(new BlockPos(0,1,1)),mb.toAbsolute(RelativeBlockFace.RIGHT));
                PackagedRuntime.equal("client installed blade machine accepts real input",true,input.insertItem(0,PackagedRuntime.stack("biomesoplenty:fir_log"),false).isEmpty());
                extraStage=2;
            }
            case "harvest-ready" -> {
                PackagedRuntime.equal("client harvest follows observed saw result",true,name.equals("BopQaOne")&&extraStage==3);
                player.getInventory().clearContent();player.getInventory().setItem(0,PackagedRuntime.stack("farmersdelight:iron_knife"));
                player.teleportTo(server.overworld(),6.5,91,10.5,-45,40);
                server.overworld().getEntitiesOfClass(ItemEntity.class,new AABB(BOARD).inflate(7)).forEach(ItemEntity::discard);
                var web=BuiltInRegistries.BLOCK.get(ResourceLocation.parse("biomesoplenty:webbing")).defaultBlockState().setValue(MultifaceBlock.getFaceProperty(Direction.DOWN),true);
                PackagedRuntime.equal("client webbing fixture is supported",true,web.canSurvive(server.overworld(),HARVEST));
                server.overworld().setBlockAndUpdate(HARVEST,web);extraStage=4;captureHarvestBaseline();
                server.overworld().setBlockAndUpdate(MARKER,Blocks.REDSTONE_BLOCK.defaultBlockState());
            }
            case "harvested" -> {PackagedRuntime.equal("client harvest stage",4,extraStage);extraStage=5;due=ticks+20;}
            case "rejoined" -> {
                PackagedRuntime.equal("reconnected original identity",ready.get("BopQaOne"),player.getUUID());
                PackagedRuntime.equal("reconnected saved inventory",logoutInventory,inventory(player));
                PackagedRuntime.equal("client reconnect after observed result",true,observed.contains(name));
                reconnected=true;server.overworld().setBlockAndUpdate(MARKER,Blocks.DIAMOND_BLOCK.defaultBlockState());
            }
            case "finished" -> {PackagedRuntime.equal("finished client observed output "+name,true,observed.contains(name));finished.add(name);}
            default -> throw new IllegalArgumentException(action);
        }
    }
    private static int requiredPlayers(){return server.isSingleplayer()?1:2;}
    private static void prepare(ServerLevel level) {
        for(BlockPos pos:BlockPos.betweenClosed(BOARD.offset(-5,-1,-5),BOARD.offset(5,3,5)))
            level.setBlockAndUpdate(pos,pos.getY()==90?Blocks.STONE.defaultBlockState():Blocks.AIR.defaultBlockState());
        level.getEntitiesOfClass(ItemEntity.class,new AABB(BOARD).inflate(7)).forEach(ItemEntity::discard);
        level.setBlockAndUpdate(BOARD,BuiltInRegistries.BLOCK.get(ResourceLocation.parse("farmersdelight:cutting_board")).defaultBlockState());
        var board=(CuttingBoardBlockEntity)level.getBlockEntity(BOARD);
        PackagedRuntime.equal("client board single input",true,board.addItem(PackagedRuntime.stack("biomesoplenty:fir_log")).isEmpty());
        level.setBlockAndUpdate(MARKER,Blocks.IRON_BLOCK.defaultBlockState());prepared=true;
    }
    private static void click(PlayerInteractEvent.RightClickBlock event) {
        if(server!=null&&!event.getLevel().isClientSide()&&event.getPos().equals(SAW)&&event.getEntity() instanceof ServerPlayer player&&player.getGameProfile().getName().equals("BopQaOne")) {
            sawPacket=true;events.add(Map.of("event","actual-sawmill-use-item-packet","player","BopQaOne","tick",ticks));
        }
        if(server!=null&&!event.getLevel().isClientSide()&&event.getPos().equals(BOARD)&&event.getEntity() instanceof ServerPlayer player) {
            String name=player.getGameProfile().getName();clickPlayers.add(name);
            if(cleanupPending){PackagedRuntime.equal("parked tool retrieval uses empty hand",true,name.equals("BopQaOne")&&event.getItemStack().isEmpty());retrievalPacket=true;}
            events.add(Map.of("event",cleanupPending?"actual-board-retrieve-packet":"actual-use-item-packet","player",name,"tick",ticks,"item",BuiltInRegistries.ITEM.getKey(event.getItemStack().getItem()).toString()));
        }
    }
    private static MultiblockBlockEntityMaster<?> sawMaster(){return (MultiblockBlockEntityMaster<?>)server.overworld().getBlockEntity(SAW);}
    private static void broken(BlockEvent.BreakEvent event) {
        if(server!=null&&event.getPos().equals(HARVEST)&&event.getPlayer() instanceof ServerPlayer player&&player.getGameProfile().getName().equals("BopQaOne")) {
            PackagedRuntime.equal("real client harvest uses knife tag",true,player.getMainHandItem().is(TagKey.create(Registries.ITEM,ResourceLocation.parse("c:tools/knife"))));
            harvestPacket=true;events.add(Map.of("event","actual-harvest-break-packet","player","BopQaOne","tick",ticks,"block",BuiltInRegistries.BLOCK.getKey(event.getState().getBlock()).toString()));
        }
    }
    private static void drops(BlockDropsEvent event) {
        if(server==null||extraStage!=4||!event.getPos().equals(HARVEST)||!event.getState().is(BuiltInRegistries.BLOCK.get(ResourceLocation.parse("biomesoplenty:webbing"))))return;
        if(!(event.getBreaker() instanceof ServerPlayer player)||!player.getUUID().equals(ready.get("BopQaOne"))||!event.getTool().is(TagKey.create(Registries.ITEM,ResourceLocation.parse("c:tools/knife"))))return;
        for(ItemEntity entity:event.getDrops()) {
            ItemStack stack=entity.getItem();String item=BuiltInRegistries.ITEM.getKey(stack.getItem()).toString();UUID uuid=entity.getUUID();
            var drop=new LinkedHashMap<String,Object>();drop.put("entityUuid",uuid.toString());drop.put("item",item);drop.put("count",stack.getCount());
            anchoredDrops.put(uuid,drop);harvestEvent("drop",uuid,item,stack.getCount(),null);
        }
    }
    private static void join(EntityJoinLevelEvent event) {
        if(server==null||event.getLevel().isClientSide()||!(event.getEntity() instanceof ItemEntity entity)||!anchoredDrops.containsKey(entity.getUUID()))return;
        ItemStack stack=entity.getItem();joinedDrops.add(entity.getUUID());harvestEvent("join",entity.getUUID(),BuiltInRegistries.ITEM.getKey(stack.getItem()).toString(),stack.getCount(),null);
    }
    private static void pickup(ItemEntityPickupEvent.Post event) {
        if(server==null||!anchoredDrops.containsKey(event.getItemEntity().getUUID()))return;
        {
            ItemStack original=event.getOriginalStack();int count=original.getCount()-event.getCurrentStack().getCount();
            if(count>0)harvestEvent("pickup",event.getItemEntity().getUUID(),BuiltInRegistries.ITEM.getKey(original.getItem()).toString(),count,event.getPlayer());
        }
    }
    private static void logout(PlayerEvent.PlayerLoggedOutEvent event) {
        if(server!=null&&event.getEntity() instanceof ServerPlayer player) {
            String name=player.getGameProfile().getName();events.add(Map.of("event","logout","player",name,"tick",ticks));
            if(name.equals("BopQaOne")&&observed.contains(name)&&!reconnected)logoutInventory=inventory(player);
        }
    }
    private static void tick(ServerTickEvent.Post event) {
        if(server==null||server!=event.getServer()||completion)return;
        try {
            ticks++;maxOnline=Math.max(maxOnline,server.getPlayerCount());
            if(ticks>6000)throw new IllegalStateException("Multiplayer 6000-tick budget exhausted");
            if(extraStage==2) {
                var helper=sawMaster().getHelper();var state=(SawmillLogic.State)helper.getState();var mb=helper.getContext().getLevel();
                if(state.sawmillProcessQueue.isEmpty()) {
                    PackagedRuntime.equal("client saw primary port delta",expectedPrimary,FormedSawmills.contents(server.overworld(),mb.toAbsolute(new BlockPos(5,1,1))));
                    PackagedRuntime.equal("client saw secondary port delta",expectedSecondary,FormedSawmills.contents(server.overworld(),mb.toAbsolute(new BlockPos(3,0,3))));
                    var recipe=SawmillRecipe.findRecipe(server.overworld(),PackagedRuntime.stack("biomesoplenty:fir_log"));
                    PackagedRuntime.equal("client saw energy consumed",recipe.getTotalProcessTime()*(recipe.getTotalProcessEnergy()/recipe.getTotalProcessTime()),energyBefore-state.getEnergy().getEnergyStored());
                    PackagedRuntime.equal("client saw blade wear",IEServerConfig.MACHINES.sawmill_bladeDamage.get(),state.sawblade.getDamageValue()-bladeBefore);
                    extraChecks.put("sawmill",true);extraStage=3;server.overworld().setBlockAndUpdate(MARKER,Blocks.LAPIS_BLOCK.defaultBlockState());
                }
            }
            if(extraStage==5&&ticks>=due) {
                PackagedRuntime.equal("actual client broke supported webbing",true,harvestPacket&&server.overworld().getBlockState(HARVEST).isAir());
                Map<String,Object> observation=harvestObservation();
                @SuppressWarnings("unchecked") Map<String,Integer> drops=(Map<String,Integer>)((Map<String,Object>)observation.get("final")).get("aggregate");
                @SuppressWarnings("unchecked") Map<String,Integer> anchored=(Map<String,Integer>)observation.get("anchoredDropAggregate");
                PackagedRuntime.interactionReport(interactionReport(observation,false));
                PackagedRuntime.equal("anchored harvest lifecycle joined",anchoredDrops.keySet(),joinedDrops);
                PackagedRuntime.equal("anchored client harvest output",anchored,drops);
                PackagedRuntime.equal("actual client harvest output",Map.of("minecraft:string",1),drops);
                extraChecks.put("harvest",true);extraStage=6;server.overworld().setBlockAndUpdate(MARKER,Blocks.NETHERITE_BLOCK.defaultBlockState());
            }
            if(prepared&&!verified&&clicked.size()==requiredPlayers()&&ticks>=due) {
                var level=server.overworld();var board=(CuttingBoardBlockEntity)level.getBlockEntity(BOARD);
                if(!interactionInspected) {
                    PackagedRuntime.equal("all real clients sent board interactions",ready.keySet(),clickPlayers);
                    PackagedRuntime.equal("concurrent board original input consumed",true,board.isEmpty()||board.getStoredItem().is(Items.IRON_AXE));
                    Totals before=totals(level,board);
                    PackagedRuntime.equal("concurrent output before tool retrieval",Map.of("biomesoplenty:stripped_fir_log",1,"farmersdelight:tree_bark",1),before.outputs);
                    PackagedRuntime.equal("concurrent tools conserved including board",requiredPlayers(),before.tools);
                    PackagedRuntime.equal("concurrent durability before tool retrieval",1,before.damage);
                    interactionInspected=true;
                    if(!board.isEmpty()){cleanupPending=true;level.setBlockAndUpdate(MARKER,Blocks.QUARTZ_BLOCK.defaultBlockState());}
                }
                if(cleanupPending)return;
                PackagedRuntime.equal("concurrent board input consumed",true,board.isEmpty());
                Totals after=totals(level,board);
                PackagedRuntime.equal("authoritative combined client and ground outputs",Map.of("biomesoplenty:stripped_fir_log",1,"farmersdelight:tree_bark",1),after.outputs);
                PackagedRuntime.equal("all client tools conserved after retrieval",requiredPlayers(),after.tools);
                int inventoryTools=0;for(ServerPlayer player:server.getPlayerList().getPlayers())for(ItemStack item:player.getInventory().items)if(item.is(Items.IRON_AXE))inventoryTools+=item.getCount();
                PackagedRuntime.equal("all tools returned to client inventories",requiredPlayers(),inventoryTools);
                PackagedRuntime.equal("only one actual tool use consumes durability",1,after.damage);
                verified=true;level.setBlockAndUpdate(MARKER,Blocks.EMERALD_BLOCK.defaultBlockState());
                PackagedRuntime.interactionReport(interactionReport(harvestObservation(),false));
            }
            if(verified&&finished.size()==requiredPlayers()&&(server.isSingleplayer()||server.getPlayerCount()==0)) {
                PackagedRuntime.equal("real client IE and harvest completed",Map.of("sawmill",true,"harvest",true),extraChecks);
                if(!server.isSingleplayer()){PackagedRuntime.equal("two concurrent real clients",2,maxOnline);PackagedRuntime.equal("real client reconnect",true,reconnected);}
                completion=true;PackagedRuntime.interactionReport(interactionReport(harvestObservation(),true));
                if(!server.isSingleplayer())PackagedRuntime.finishMultiplayer(server);
            }
        } catch(Throwable e){completion=true;PackagedRuntime.failInteraction(server,e);}
    }
    private record Totals(Map<String,Integer> outputs,int tools,int damage) {}
    private static Totals totals(ServerLevel level,CuttingBoardBlockEntity board) {
        List<ItemStack> stacks=new ArrayList<>();
        for(ServerPlayer player:server.getPlayerList().getPlayers())stacks.addAll(player.getInventory().items);
        for(ItemEntity item:level.getEntitiesOfClass(ItemEntity.class,new AABB(BOARD).inflate(7)))stacks.add(item.getItem());
        stacks.add(board.getStoredItem());Map<String,Integer> outputs=new TreeMap<>();int tools=0,damage=0;
        for(ItemStack item:stacks) {
            if(item.is(Items.IRON_AXE)){tools+=item.getCount();damage+=item.getDamageValue();}
            else if(!item.isEmpty())outputs.merge(BuiltInRegistries.ITEM.getKey(item.getItem()).toString(),item.getCount(),Integer::sum);
        }
        return new Totals(outputs,tools,damage);
    }
    private static List<Map<String,Object>> inventory(ServerPlayer player) {
        List<Map<String,Object>> result=new ArrayList<>();int slot=0;
        for(ItemStack stack:player.getInventory().items)result.add(Map.of("slot",slot++,"item",BuiltInRegistries.ITEM.getKey(stack.getItem()).toString(),"count",stack.getCount(),"damage",stack.getDamageValue()));
        return result;
    }
    private static void captureHarvestBaseline() {
        harvestEvents.clear();anchoredDrops.clear();joinedDrops.clear();harvestSequence=0;
        var baseline=new LinkedHashMap<String,Object>();baseline.put("tick",ticks);baseline.put("extraStage",extraStage);baseline.put("players",harvestPlayers());baseline.put("nearbyItemEntities",nearbyItems());harvestBaseline=baseline;
    }
    private static List<Map<String,Object>> harvestPlayers() {
        List<Map<String,Object>> players=new ArrayList<>();
        for(String name:List.of("BopQaOne","BopQaTwo"))if(ready.containsKey(name)) {
            ServerPlayer player=server.getPlayerList().getPlayer(ready.get(name));if(player==null)throw new IllegalStateException("Missing ready-bound QA player "+name);
            var row=new LinkedHashMap<String,Object>();row.put("player",name);row.put("uuid",player.getUUID().toString());row.put("position",position(player.blockPosition()));row.put("inventory",inventory(player));players.add(row);
        }
        return players;
    }
    private static List<Map<String,Object>> nearbyItems() {
        List<Map<String,Object>> result=new ArrayList<>();
        for(ItemEntity entity:server.overworld().getEntitiesOfClass(ItemEntity.class,new AABB(HARVEST).inflate(7))) {
            ItemStack item=entity.getItem();var row=new LinkedHashMap<String,Object>();row.put("uuid",entity.getUUID().toString());row.put("item",BuiltInRegistries.ITEM.getKey(item.getItem()).toString());row.put("count",item.getCount());row.put("position",position(entity.blockPosition()));result.add(row);
        }
        result.sort((left,right)->String.valueOf(left.get("uuid")).compareTo(String.valueOf(right.get("uuid"))));return result;
    }
    private static Map<String,Object> position(BlockPos value) {return Map.of("x",value.getX(),"y",value.getY(),"z",value.getZ());}
    private static void harvestEvent(String kind,UUID entity,String item,int count,net.minecraft.world.entity.player.Player destination) {
        var row=new LinkedHashMap<String,Object>();row.put("sequence",++harvestSequence);row.put("tick",ticks);row.put("kind",kind);row.put("entityUuid",entity.toString());row.put("item",item);row.put("count",count);
        if(destination!=null) {var to=new LinkedHashMap<String,Object>();to.put("player",destination.getGameProfile().getName());to.put("uuid",destination.getUUID().toString());row.put("destination",to);}harvestEvents.add(row);
    }
    private static Map<String,Object> harvestObservation() {
        var fixture=new LinkedHashMap<String,Object>();fixture.put("dimension","minecraft:overworld");fixture.put("block","biomesoplenty:webbing");fixture.put("position",position(HARVEST));fixture.put("observationBounds",Map.of("center",position(HARVEST),"inflate",7));
        List<Map<String,Object>> identities=new ArrayList<>();for(String name:List.of("BopQaOne","BopQaTwo"))if(ready.containsKey(name))identities.add(Map.of("player",name,"uuid",ready.get(name).toString()));
        Map<String,Object> baseline=harvestBaseline==null?Map.of("tick",ticks,"extraStage",extraStage,"players",List.of(),"nearbyItemEntities",List.of()):harvestBaseline;
        List<Map<String,Object>> players=harvestPlayers(),ground=nearbyItems();Map<String,Integer> aggregate=positiveDeltas(players,ground),anchored=new TreeMap<>();
        for(Map<String,Object> drop:anchoredDrops.values())anchored.merge((String)drop.get("item"),(Integer)drop.get("count"),Integer::sum);
        List<Map<String,Object>> destinations=new ArrayList<>();for(Map<String,Object> event:harvestEvents)if(event.get("kind").equals("pickup")) {var row=new LinkedHashMap<>(event);row.remove("sequence");row.remove("tick");row.remove("destination");row.put("destination",event.get("destination"));destinations.add(row);}for(Map<String,Object> item:ground)if(anchoredDrops.containsKey(UUID.fromString((String)item.get("uuid"))))destinations.add(Map.of("kind","ground","entityUuid",item.get("uuid"),"item",item.get("item"),"count",item.get("count")));
        var finalSample=new LinkedHashMap<String,Object>();finalSample.put("tick",ticks);finalSample.put("extraStage",extraStage);finalSample.put("players",players);finalSample.put("nearbyItemEntities",ground);finalSample.put("destinations",destinations);finalSample.put("aggregate",aggregate);
        var result=new LinkedHashMap<String,Object>();result.put("schemaVersion",1);result.put("fixture",fixture);result.put("expectedAggregate",Map.of("minecraft:string",1));result.put("qaIdentities",identities);result.put("baseline",baseline);result.put("events",new ArrayList<>(harvestEvents));result.put("anchoredDropAggregate",anchored);result.put("final",finalSample);return result;
    }
    private static Map<String,Integer> positiveDeltas(List<Map<String,Object>> players,List<Map<String,Object>> ground) {
        Map<String,Integer> baseline=new TreeMap<>(),current=new TreeMap<>(),result=new TreeMap<>();if(harvestBaseline!=null)for(Map<String,Object> player:(List<Map<String,Object>>)harvestBaseline.get("players"))totals((List<Map<String,Object>>)player.get("inventory"),baseline);for(Map<String,Object> player:players)totals((List<Map<String,Object>>)player.get("inventory"),current);for(var entry:current.entrySet())if(entry.getValue()>baseline.getOrDefault(entry.getKey(),0))result.put(entry.getKey(),entry.getValue()-baseline.getOrDefault(entry.getKey(),0));for(Map<String,Object> item:ground)result.merge((String)item.get("item"),(Integer)item.get("count"),Integer::sum);return result;
    }
    private static void totals(List<Map<String,Object>> inventory,Map<String,Integer> result) {for(Map<String,Object> item:inventory)if((Integer)item.get("count")>0&&!item.get("item").equals("minecraft:air"))result.merge((String)item.get("item"),(Integer)item.get("count"),Integer::sum);}
    private static Map<String,Object> interactionReport(Map<String,Object> observation,boolean finishedReport) {var result=new LinkedHashMap<String,Object>();result.put("events",events);result.put("verified",true);result.put("maxConcurrentPlayers",maxOnline);result.put("extraChecks",extraChecks);result.put("harvestObservation",observation);if(finishedReport){result.put("reconnected",reconnected);result.put("finishedClients",finished.size());}return result;}
}
