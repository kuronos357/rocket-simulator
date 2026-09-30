import java.io.File;
import java.lang.reflect.Method;
import info.openrocket.core.startup.OpenRocketCore;
import info.openrocket.core.file.GeneralRocketLoader;
import info.openrocket.core.document.OpenRocketDocument;
import info.openrocket.core.rocketcomponent.Rocket;
import info.openrocket.core.aerodynamics.BarrowmanCalculator;
import info.openrocket.core.util.Coordinate;

public class TestBarrowmanCP {
    public static void main(String[] args) {
        if (args.length == 0) return;
        try {
            OpenRocketCore.initialize();
            GeneralRocketLoader loader = new GeneralRocketLoader(new File(args[0]));
            OpenRocketDocument doc = loader.load();
            Rocket rocket = doc.getRocket();
            
            System.out.println("Rocket length: " + rocket.getLength() * 1000 + " mm");
            Coordinate cg = rocket.getCG();
            System.out.println("CG: " + (cg != null ? (cg.x * 1000 + " mm") : "null"));
            
            BarrowmanCalculator calc = new BarrowmanCalculator();
            // check calc methods
            for (Method m : BarrowmanCalculator.class.getMethods()) {
                if (m.getName().equals("getCP")) {
                    System.out.println("getCP params: " + java.util.Arrays.toString(m.getParameterTypes()));
                }
            }
        } catch (Throwable t) {
            t.printStackTrace();
        }
    }
}
