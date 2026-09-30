import java.lang.reflect.Method;
import info.openrocket.core.rocketcomponent.Rocket;
import info.openrocket.core.aerodynamics.BarrowmanCalculator;

public class TestCGCP2 {
    public static void main(String[] args) {
        try {
            System.out.println("=== Rocket Methods ===");
            for (Method m : Rocket.class.getMethods()) {
                String n = m.getName().toLowerCase();
                if (n.contains("cp") || n.contains("cg") || n.contains("center") || n.contains("stability") || n.contains("margin")) {
                    System.out.println("  Rocket." + m.getName() + " -> " + m.getReturnType().getSimpleName());
                }
            }
            System.out.println("=== BarrowmanCalculator Methods ===");
            for (Method m : BarrowmanCalculator.class.getMethods()) {
                System.out.println("  Barrowman." + m.getName() + " -> " + m.getReturnType().getSimpleName());
            }
        } catch (Throwable t) { t.printStackTrace(); }
    }
}
