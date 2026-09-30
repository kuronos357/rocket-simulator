import java.lang.reflect.Method;

public class TestFlightDataMethods {
    public static void main(String[] args) {
        try {
            Class<?> cls = Class.forName("info.openrocket.core.simulation.FlightData");
            for (Method m : cls.getMethods()) {
                if (m.getDeclaringClass() == cls) {
                    System.out.println(m.getName() + " -> " + m.getReturnType().getSimpleName());
                }
            }
        } catch (Throwable t) { t.printStackTrace(); }
    }
}
