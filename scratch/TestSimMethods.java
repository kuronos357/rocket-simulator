import java.lang.reflect.Method;

public class TestSimMethods {
    public static void main(String[] args) {
        try {
            Class<?> cls = Class.forName("info.openrocket.core.document.Simulation");
            for (Method m : cls.getMethods()) {
                if (m.getDeclaringClass() == cls) {
                    System.out.println(m.getName() + " -> " + m.getReturnType().getSimpleName());
                }
            }
        } catch (Throwable t) { t.printStackTrace(); }
    }
}
