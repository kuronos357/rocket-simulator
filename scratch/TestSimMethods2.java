import java.lang.reflect.Method;
import info.openrocket.core.document.Simulation;

public class TestSimMethods2 {
    public static void main(String[] args) {
        for (Method m : Simulation.class.getMethods()) {
            if (m.getName().toLowerCase().contains("config") || m.getName().toLowerCase().contains("option")) {
                System.out.println(m.getName() + " -> " + m.getReturnType().getSimpleName());
            }
        }
    }
}
