import java.lang.reflect.Method;
import info.openrocket.core.document.OpenRocketDocument;

public class TestDocMethods {
    public static void main(String[] args) {
        try {
            Class<?> cls = OpenRocketDocument.class;
            for (Method m : cls.getMethods()) {
                if (m.getName().toLowerCase().contains("sim")) {
                    System.out.println(m.getName() + " -> " + m.getReturnType().getName());
                }
            }
        } catch (Throwable t) { t.printStackTrace(); }
    }
}
