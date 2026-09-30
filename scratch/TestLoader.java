
import java.io.File;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;

public class TestLoader {
    public static void main(String[] args) {
        try {
            Class<?> cls = Class.forName("info.openrocket.core.file.openrocket.importt.OpenRocketLoader");
            System.out.println("Loaded OpenRocketLoader class: " + cls.getName());
            for (Method m : cls.getMethods()) {
                if (Modifier.isPublic(m.getModifiers())) {
                    System.out.println("Method: " + m.getName() + " -> " + java.util.Arrays.toString(m.getParameterTypes()));
                }
            }
        } catch (Throwable e) {
            e.printStackTrace();
        }
    }
}
