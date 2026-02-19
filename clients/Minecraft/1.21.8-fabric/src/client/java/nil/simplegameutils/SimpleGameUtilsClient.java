package nil.simplegameutils;

import me.shedaniel.autoconfig.AutoConfig;
import me.shedaniel.autoconfig.serializer.GsonConfigSerializer;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.command.v2.ClientCommandRegistrationCallback;

import nil.simplegameutils.commands.SGUCommand;
import nil.simplegameutils.config.SGUConfig;

public class SimpleGameUtilsClient implements ClientModInitializer {
	public static final String MODID = "simplegameutils";

	public static SGUConfig CONFIG;

	@Override
	public void onInitializeClient() {
		// This entrypoint is suitable for setting up client-specific logic, such as rendering.
		AutoConfig.register(SGUConfig.class, GsonConfigSerializer::new);
		CONFIG = AutoConfig.getConfigHolder(SGUConfig.class).getConfig();
		ClientCommandRegistrationCallback.EVENT.register((dispatcher, registryAccess) -> SGUCommand.register(dispatcher));
	}
}