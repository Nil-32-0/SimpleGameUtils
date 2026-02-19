package nil.simplegameutils.commands;

import static net.fabricmc.fabric.api.client.command.v2.ClientCommandManager.argument;
import static net.fabricmc.fabric.api.client.command.v2.ClientCommandManager.literal;

import java.net.URI;
import java.nio.charset.StandardCharsets;

import com.google.gson.JsonObject;
import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;

import net.fabricmc.fabric.api.client.command.v2.FabricClientCommandSource;
import net.minecraft.client.Minecraft;
import net.minecraft.network.chat.Component;
import nil.simplegameutils.SGUWebSocketClient;
import nil.simplegameutils.SimpleGameUtilsClient;


public final class SGUCommand {
    private static String cachedAddress;
    private static SGUWebSocketClient client;

    public static void register(CommandDispatcher<FabricClientCommandSource> dispatcher) {
        try{
            cachedAddress = SimpleGameUtilsClient.CONFIG.address;
            client = new SGUWebSocketClient(new URI(cachedAddress));
        } catch (Exception e) {
            System.out.println(e);
        }

        dispatcher.register(literal("sgu")
            .then(literal("connect").executes(SGUCommand::connectToServer))
            .then(literal("group")
                .then(literal("create").then(argument("group_name", StringArgumentType.string()).executes(ctx -> {
                    connectToServer(ctx);
                    JsonRequestBuilder req = new JsonRequestBuilder("group-create").addFromStringParam("group_name", ctx);
                    client.send(req.build().toString());
                    return 0;
                })))
                .then(literal("list").executes(ctx -> {
                    connectToServer(ctx);
                    JsonRequestBuilder req = new JsonRequestBuilder("group-list");
                    client.send(req.build().toString());
                    return 0;
                }))
                .then(argument("group_id", IntegerArgumentType.integer(0))
                .then(literal("info").executes(ctx -> {
                    connectToServer(ctx);
                    JsonRequestBuilder req = new JsonRequestBuilder("group-info-req");
                    client.send(req.addFromIntParam("group_id", ctx).build().toString());
                    return 0;
                }))
                .then(literal("delete").executes(ctx -> {
                    connectToServer(ctx);
                    JsonRequestBuilder req = new JsonRequestBuilder("group-delete");
                    client.send(req.addFromIntParam("group_id", ctx).build().toString());
                    return 0;
                }))
                .then(literal("transfer").then(argument("new_owner_username", StringArgumentType.string()).executes(ctx -> {
                    connectToServer(ctx);
                    JsonRequestBuilder req = new JsonRequestBuilder("group-transfer");
                    req.addFromIntParam("group_id", ctx).addFromStringParam("new_owner_username", ctx);
                    client.send(req.build().toString());
                    return 0;
                })))
                .then(literal("add").then(argument("new_member_username", StringArgumentType.string()).executes(ctx -> {
                    connectToServer(ctx);
                    JsonRequestBuilder req = new JsonRequestBuilder("group-add");
                    req.addFromIntParam("group_id", ctx).addFromStringParam("new_member_username", ctx);
                    client.send(req.build().toString());
                    return 0;
                })))
                .then(literal("remove").then(argument("member_username", StringArgumentType.string()).executes(ctx -> {
                    connectToServer(ctx);
                    JsonRequestBuilder req = new JsonRequestBuilder("group-remove");
                    req.addFromIntParam("group_id", ctx).addFromStringParam("member_username", ctx);
                    client.send(req.build().toString());
                    return 0;
                })))
                .then(literal("leave").executes(ctx -> {
                    connectToServer(ctx);
                    JsonRequestBuilder req = new JsonRequestBuilder("group-leave");
                    client.send(req.addFromIntParam("group_id", ctx).build().toString());
                    return 0;
                }))
            ))
            .then(literal("inventory")
                .then(literal("add").then(argument("inv_id", StringArgumentType.string()).executes(ctx -> {
                    connectToServer(ctx);
                    JsonObject req = new JsonObject();
                    req.addProperty("type", "inventory-add");
                    req.addProperty("external_id", StringArgumentType.getString(ctx, "inv_id"));
                    client.send(StandardCharsets.UTF_8.encode(req.toString()));
                    return 0;
                })))
                .then(literal("remove").then(argument("inv_id", StringArgumentType.string()).executes(ctx -> {
                    connectToServer(ctx);
                    JsonObject req = new JsonObject();
                    req.addProperty("type", "inventory-remove");
                    req.addProperty("external_id", StringArgumentType.getString(ctx, "inv_id"));
                    client.send(StandardCharsets.UTF_8.encode(req.toString()));
                    return 0;
                })))
            )
            .then(literal("items")
                .then(literal("get").then(argument("inv_id", StringArgumentType.string()).executes(ctx -> {
                    connectToServer(ctx);
                    JsonObject req = new JsonObject();
                    req.addProperty("type", "item-get");
                    req.addProperty("external_id", StringArgumentType.getString(ctx, "inv_id"));
                    client.send(StandardCharsets.UTF_8.encode(req.toString()));
                    return 0;
                })))
                .then(literal("add").then(argument("inv_id", StringArgumentType.string())
                    .then(argument("item_id", StringArgumentType.string())
                        .then(argument("item_qty", IntegerArgumentType.integer(0))
                            .executes(ctx -> changeItems(ctx, true))))))
                .then(literal("remove").then(argument("inv_id", StringArgumentType.string())
                    .then(argument("item_id", StringArgumentType.string())
                        .then(argument("item_qty", IntegerArgumentType.integer(0))
                            .executes(ctx -> changeItems(ctx, false))))))
                .then(literal("delete").then(argument("inv_id", StringArgumentType.string())
                    .then(argument("item_id", StringArgumentType.string()).executes(ctx -> {
                        if (client == null || !client.isOpen()) {
                            connectToServer(ctx);
                        }
                        JsonObject req = new JsonObject();
                        req.addProperty("type", "item-delete");
                        req.addProperty("external_id", StringArgumentType.getString(ctx, "inv_id"));
                        
                        String item_id = StringArgumentType.getString(ctx, "item_id");
                        if (item_id == "hand") {
                            item_id = Minecraft.getInstance().player.getMainHandItem().getItem().toString();
                        }
                        req.addProperty("item_id", item_id);

                        client.send(StandardCharsets.UTF_8.encode(req.toString()));
                        return 0;
                    }))))
                .then(literal("transfer").then(argument("item_id", StringArgumentType.string())
                    .then(argument("item_qty", IntegerArgumentType.integer(0))
                        .then(argument("source_id", StringArgumentType.string())
                            .then(argument("target_id", StringArgumentType.string()).executes(ctx -> {
                                if (client == null || !client.isOpen()) {
                                    connectToServer(ctx);
                                }
                                JsonObject req = new JsonObject();
                                req.addProperty("type", "item-transfer");
                                req.addProperty("source_id", StringArgumentType.getString(ctx, "source_id"));
                                req.addProperty("target_id", StringArgumentType.getString(ctx, "target_id"));
                                
                                String item_id = StringArgumentType.getString(ctx, "item_id");
                                int item_qty = IntegerArgumentType.getInteger(ctx, "item_qty");
                                if (item_id == "hand") {
                                    item_id = Minecraft.getInstance().player.getMainHandItem().getItem().toString();
                                    item_qty = Minecraft.getInstance().player.getMainHandItem().getCount();
                                }
                                req.addProperty("item_id", item_id);
                                req.addProperty("item_qty", item_qty);
                                
                                client.send(StandardCharsets.UTF_8.encode(req.toString()));
                                return 0;
                    }))))))
            )
            .then(literal("projects")
                .then(literal("view")
                    .then(literal("all").executes(SGUCommand::viewProjects))
                    .then(literal("one").then(argument("project_id", IntegerArgumentType.integer(0)).executes(SGUCommand::viewProject)))
                )
                .then(literal("create").then(argument("name", StringArgumentType.string())
                    .then(literal("PUBLIC").executes(ctx -> createProject(ctx, "PUBLIC", ""))
                        .then(argument("desc", StringArgumentType.string()).executes(ctx ->
                            createProject(ctx, "PUBLIC", StringArgumentType.getString(ctx, "desc"))
                        ))
                    )
                    .then(literal("PRIVATE").executes(ctx -> createProject(ctx, "PRIVATE", ""))
                        .then(argument("desc", StringArgumentType.string()).executes(ctx ->
                            createProject(ctx, "PRIVATE", StringArgumentType.getString(ctx, "desc"))
                        ))
                    )
                    .then(literal("GROUP").then(argument("group_id", IntegerArgumentType.integer(0))
                        .executes(ctx -> createProject(ctx, "GROUP", ""))
                        .then(argument("desc", StringArgumentType.string()).executes(ctx ->
                            createProject(ctx, "GROUP", StringArgumentType.getString(ctx, "desc"))
                        ))
                    ))
                ))
                .then(argument("project_id", IntegerArgumentType.integer(0))
                .then(literal("delete")
                    .executes(ctx -> {
                        connectToServer(ctx);
                        JsonRequestBuilder req = new JsonRequestBuilder("project-delete");
                        client.send(req.addFromIntParam("project_id", ctx).build().toString());
                        return 0;
                    })
                )
                .then(literal("transfer")
                    .then(argument("new_owner_username", StringArgumentType.string()).executes(ctx -> {
                        connectToServer(ctx);
                        JsonRequestBuilder req = new JsonRequestBuilder("project-transfer");
                        client.send(req.addFromIntParam("project_id", ctx).addFromStringParam("new_owner_username", ctx).build().toString());
                        return 0;
                    }))
                )
                .then(literal("scope")
                    .then(literal("PUBLIC").executes(ctx -> {
                        connectToServer(ctx);
                        JsonRequestBuilder req = new JsonRequestBuilder("project-scope");
                        req.add("group_id", -1).addFromIntParam("project_id", ctx);
                        client.send(req.add("scope", "PUBLIC").build().toString());
                        return 0;
                    }))
                    .then(literal("PRIVATE").executes(ctx -> {
                        connectToServer(ctx);
                        JsonRequestBuilder req = new JsonRequestBuilder("project-scope");
                        req.add("group_id", -1).addFromIntParam("project_id", ctx);
                        client.send(req.add("scope", "PRIVATE").build().toString());
                        return 0;
                    }))
                    .then(literal("GROUP").then(argument("group_id", IntegerArgumentType.integer(0)).executes(ctx -> {
                        connectToServer(ctx);
                        JsonRequestBuilder req = new JsonRequestBuilder("project-scope");
                        req.addFromIntParam("group_id", ctx).addFromIntParam("project_id", ctx);
                        client.send(req.add("scope", "GROUP").build().toString());
                        return 0;
                    })))
                )
                .then(literal("item").then(argument("item_id", StringArgumentType.string())
                    .then(literal("track")
                            .then(argument("item_qty", IntegerArgumentType.integer(1)).executes(ctx -> {
                                connectToServer(ctx);
                                JsonRequestBuilder req = new JsonRequestBuilder("project-item-track");
                                req.addFromStringParam("item_id", ctx).addFromIntParam("item_qty", ctx);
                                client.send(req.addFromIntParam("project_id", ctx).build().toString());
                                return 0;
                    })))
                    .then(literal("delete").executes(ctx -> {
                            connectToServer(ctx);
                            JsonRequestBuilder req = new JsonRequestBuilder("project-item-delete");
                            req.addFromIntParam("project_id", ctx).addFromStringParam("item_id", ctx);
                            client.send(req.build().toString());
                            return 0;
                    }))
                    .then(literal("add").then(argument("item_qty", IntegerArgumentType.integer(0))
                        .then(argument("external_id", StringArgumentType.string()).executes(ctx -> {
                            connectToServer(ctx);
                            JsonRequestBuilder req = new JsonRequestBuilder("project-item-add");
                            req.addFromIntParam("project_id", ctx).addFromStringParam("item_id", ctx);
                            req.addFromIntParam("item_qty", ctx).addFromStringParam("external_id", ctx);
                            client.send(req.build().toString());
                            return 0;
                    }))))
                    .then(literal("remove").then(argument("item_qty", IntegerArgumentType.integer(0))
                        .then(argument("external_id", StringArgumentType.string()).executes(ctx -> {
                            connectToServer(ctx);
                            JsonRequestBuilder req = new JsonRequestBuilder("project-item-remove");
                            req.addFromIntParam("project_id", ctx).addFromStringParam("item_id", ctx);
                            req.addFromIntParam("item_qty", ctx).addFromStringParam("external_id", ctx);
                            client.send(req.build().toString());
                            return 0;
                    }))))
                    .then(literal("reserve").then(argument("item_qty", IntegerArgumentType.integer(0))
                        .then(argument("external_id", StringArgumentType.string()).executes(ctx -> {
                            connectToServer(ctx);
                            JsonRequestBuilder req = new JsonRequestBuilder("project-item-reserve");
                            req.add("target_project_id", IntegerArgumentType.getInteger(ctx, "project_id"));
                            req.addFromIntParam("item_id", ctx).addFromIntParam("item_qty", ctx);
                            req.addFromStringParam("external_id", ctx).add("source_project_id", -1);
                            client.send(req.build().toString());
                            return 0;
                        })
                        .then(argument("source_project_id", IntegerArgumentType.integer(0)).executes(ctx -> {
                            connectToServer(ctx);
                            JsonRequestBuilder req = new JsonRequestBuilder("project-item-reserve");
                            req.add("target_project_id", IntegerArgumentType.getInteger(ctx, "project_id"));
                            req.addFromIntParam("item_id", ctx).addFromIntParam("item_qty", ctx);
                            req.addFromStringParam("external_id", ctx).addFromIntParam("source_project_id", ctx);
                            client.send(req.build().toString());
                            return 0;
                        }))
                    )))
                    .then(literal("release").then(argument("item_qty", IntegerArgumentType.integer(0))
                        .then(argument("external_id", StringArgumentType.string()).executes(ctx -> {
                            connectToServer(ctx);
                            JsonRequestBuilder req = new JsonRequestBuilder("project-item-release");
                            req.addFromIntParam("project_id", ctx).addFromStringParam("item_id", ctx);
                            req.addFromIntParam("item_qty", ctx).addFromStringParam("external_id", ctx);
                            client.send(req.build().toString());
                            return 0;
                    }))))
            ))))
            .then(literal("disconnect").executes(ctx -> {
                if (client.isOpen()) {
                    client.close(1000, "closing");
                }
                return 0;
            }))
        );
    }

    private static int createProject(CommandContext<FabricClientCommandSource> ctx, String scope, String desc) {
        connectToServer(ctx);
        JsonRequestBuilder req = new JsonRequestBuilder("project-create").addFromStringParam("name", ctx);
        req.add("scope", scope).add("desc", desc);
        if (scope == "GROUP") {
            req.addFromIntParam("group_id", ctx);
        } else {
            req.add("group_id", -1);
        }
        client.send(req.build().toString());
        return 0;
    }

    private static int connectToServer(CommandContext<FabricClientCommandSource> ctx) {
        if (client != null && client.isOpen()) {
            return 0;
        }
        if (!SimpleGameUtilsClient.CONFIG.address.equals(cachedAddress) || client == null) {
            cachedAddress = SimpleGameUtilsClient.CONFIG.address;
            try {
                client = new SGUWebSocketClient(new URI(cachedAddress));
            } catch (Exception e) {
                System.out.println(e);
            }
        }
        ctx.getSource().sendFeedback(Component.literal("Connecting to address: " + client.getURI().toString()));
        try {
            if (client.isClosed()) {
                client.reconnectBlocking();
            } else {
                client.connectBlocking();
            }
        } catch (Exception e) {
            System.out.println(e);
        }
        return 0;
    }

    private static int viewProjects(CommandContext<FabricClientCommandSource> ctx) {
        connectToServer(ctx);
        client.send(new JsonRequestBuilder("project-view-all").build().toString());
        return 0;
    }

    private static int viewProject(CommandContext<FabricClientCommandSource> ctx) {
        connectToServer(ctx);
        client.send(new JsonRequestBuilder("project-view-one").addFromIntParam("project_id", ctx).build().toString());
        return 0;
    }

    private static int changeItems(CommandContext<FabricClientCommandSource> ctx, boolean countIncrease) {
        if (client == null || !client.isOpen()) {
            connectToServer(ctx);
        }
        JsonObject req = new JsonObject();
        req.addProperty("type", countIncrease ? "item-add" : "item-remove");
        req.addProperty("external_id", StringArgumentType.getString(ctx, "inv_id"));
        
        String item_id = StringArgumentType.getString(ctx, "item_id");
        int item_qty = IntegerArgumentType.getInteger(ctx, "item_qty");
        if (item_id == "hand") {
            item_id = Minecraft.getInstance().player.getMainHandItem().getItem().toString();
            item_qty = Minecraft.getInstance().player.getMainHandItem().getCount();
        }
        req.addProperty("item_id", item_id);
        req.addProperty("item_qty", item_qty);

        client.send(req.toString());
        return 0;
    }

    private static class JsonRequestBuilder {
        private JsonObject obj;

        public JsonRequestBuilder(String requestType) {
            this.obj = new JsonObject();
            this.obj.addProperty("type", requestType);
        }

        public JsonRequestBuilder add(String field, String value) {
            this.obj.addProperty(field, value);
            return this;
        }

        public JsonRequestBuilder add(String field, Integer value) {
            this.obj.addProperty(field, value);
            return this;
        }

        public JsonRequestBuilder addFromIntParam(String field, CommandContext<FabricClientCommandSource> ctx) {
            this.obj.addProperty(field, IntegerArgumentType.getInteger(ctx, field));
            return this;
        }

        public JsonRequestBuilder addFromStringParam(String field, CommandContext<FabricClientCommandSource> ctx) {
            this.obj.addProperty(field, StringArgumentType.getString(ctx, field));
            return this;
        }

        public JsonObject build() {
            return obj;
        }
    }
}
