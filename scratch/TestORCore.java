
import java.lang.reflect.Method;
public class TestORCore {
    public static void main(String[] args) {
        try {
            Class<?> cls = Class.forName("info.openrocket.core.startup.OpenRocketCore");
            for (Method m : cls.getMethods()) {
                System.out.println("ORCore: " + m.getName() + " -> " + java.util.Arrays.toString(m.getParameterTypes()));
            }
        } catch (Throwable t) { t.printStackTrace(); }
    }
}
