package nil.simplegameutils;

import java.net.URI;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;

import org.java_websocket.client.WebSocketClient;
import org.java_websocket.drafts.Draft;
import org.java_websocket.handshake.ServerHandshake;

import com.google.gson.JsonObject;

import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.network.chat.Component;
import net.minecraft.util.GsonHelper;

public class SGUWebSocketClient extends WebSocketClient  {
    public SGUWebSocketClient(URI serverUri, Draft draft) {
        super(serverUri, draft);
    }

    public SGUWebSocketClient(URI serverUri) {
        super(serverUri);
    }

    @Override
    public void onOpen(ServerHandshake handshakedata) {
        JsonObject auth = new JsonObject();

        auth.addProperty("type", "auth-login");
        auth.addProperty("username", SimpleGameUtilsClient.CONFIG.username);
        auth.addProperty("password", SimpleGameUtilsClient.CONFIG.password);

        send(StandardCharsets.UTF_8.encode(auth.toString()));
        System.out.println("Connection opened.");
    }

    @Override
    public void onClose(int code, String reason, boolean remote) {
        System.out.println("Closed with exit code " + code + " \nAdditional info: " + reason);
    }

    @Override
    public void onMessage(String message) {
        System.out.println("Recieved message: " + message);
        JsonObject obj = GsonHelper.parse(message);
        LocalPlayer p = Minecraft.getInstance().player;
        if (p != null) {
            p.displayClientMessage(Component.literal("New message!"), false);
            p.displayClientMessage(Component.literal("Message type: " + obj.get("type").getAsString()), false);
            for (String key : obj.keySet()) {
                if (key.equals("type")) continue;
                p.displayClientMessage(Component.literal("Field " + key + ": " + obj.get(key).toString()), false);
            }
        }

        if (obj.get("type").getAsString().equals("project-info-single")) {
            JsonObject prog = obj.get("progress").getAsJsonObject();
            for (String itemID : prog.keySet()) {
                p.displayClientMessage(Component.literal("Progress towards " + itemID + ":"), false);
                int goal = prog.get(itemID).getAsJsonObject().get("goal").getAsInt();
                int gathered = prog.get(itemID).getAsJsonObject().get("gathered").getAsInt();
                p.displayClientMessage(Component.literal(gathered + "/" + goal), false);
            }
        }
    }

    @Override
    public void onMessage(ByteBuffer message) {
        System.out.println("Recieved ByteBuffer");
    }

    @Override
    public void onError(Exception ex) {
        System.err.println("An error occurred: " + ex);
    }

    @Override
    public void send(String message) {
        super.send(StandardCharsets.UTF_8.encode(message));
    }
}
