package nil.simplegameutils.config;

import me.shedaniel.autoconfig.ConfigData;
import me.shedaniel.autoconfig.annotation.Config;
import nil.simplegameutils.SimpleGameUtilsClient;

@Config(name = SimpleGameUtilsClient.MODID)
public class SGUConfig implements ConfigData {
    public String address = "ws://127.0.0.1:9001";
    public String accessKey;
}
