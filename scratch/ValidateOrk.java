
import java.io.File;
import java.lang.reflect.Method;
import info.openrocket.core.startup.OpenRocketCore;
import info.openrocket.core.file.GeneralRocketLoader;
import info.openrocket.core.document.OpenRocketDocument;
import info.openrocket.core.rocketcomponent.Rocket;
import info.openrocket.core.rocketcomponent.RocketComponent;

public class ValidateOrk {
    public static void main(String[] args) {
        if (args.length == 0) {
            System.out.println("Usage: ValidateOrk <path-to-ork>");
            return;
        }
        File orkFile = new File(args[0]);
        if (!orkFile.exists()) {
            System.err.println("File does not exist: " + orkFile.getAbsolutePath());
            System.exit(1);
        }
        try {
            System.out.println("Initializing OpenRocketCore...");
            OpenRocketCore.initialize();

            System.out.println("Validating OpenRocket file: " + orkFile.getName());
            GeneralRocketLoader loader = new GeneralRocketLoader(orkFile);
            OpenRocketDocument doc = loader.load();
            if (doc == null) {
                System.err.println("ERROR: doc is null!");
                System.exit(2);
            }
            Rocket rocket = doc.getRocket();
            System.out.println(">> SUCCESS! OpenRocket parsed the file successfully!");
            System.out.println("Rocket Name: " + rocket.getName());
            System.out.println("Stage count: " + rocket.getStageCount());
            System.out.printf("Total length: %.1f mm\n", rocket.getLength() * 1000.0);
            System.out.printf("Rocket dry mass: %.2f g\n", rocket.getMass() * 1000.0);
            for (RocketComponent comp : rocket) {
                System.out.printf(" - %s (%s): length=%.1f mm\n", 
                    comp.getName(), comp.getComponentName(), comp.getLength() * 1000.0);
            }
        } catch (Throwable t) {
            System.err.println("FAILED to load ORK file:");
            t.printStackTrace();
            System.exit(3);
        }
    }
}
