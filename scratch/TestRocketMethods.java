import java.lang.reflect.Method;
import info.openrocket.core.rocketcomponent.Rocket;

public class TestRocketMethods {
    public static void main(String[] args) {
        for (Method m : Rocket.class.getMethods()) {
            String n = m.getName().toLowerCase();
            if (n.contains("mass") || n.contains("cg") || n.contains("length") || n.contains("diameter") || n.contains("stability") || n.contains("cp")) {
                System.out.println(m.getName() + " -> " + m.getReturnType().getSimpleName());
            }
        }
    }
}
