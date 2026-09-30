import java.lang.reflect.Method;
import info.openrocket.core.rocketcomponent.Rocket;
import info.openrocket.core.rocketcomponent.FlightConfiguration;

public class TestCGCP {
    public static void main(String[] args) {
        try {
            System.out.println("=== FlightConfiguration Methods ===");
            for (Method m : FlightConfiguration.class.getMethods()) {
                if (m.getName().toLowerCase().contains("cp") || m.getName().toLowerCase().contains("cg") || m.getName().toLowerCase().contains("stability")) {
                    System.out.println("  " + m.getName() + " -> " + m.getReturnType().getSimpleName());
                }
            }
        } catch (Throwable t) { t.printStackTrace(); }
    }
}
