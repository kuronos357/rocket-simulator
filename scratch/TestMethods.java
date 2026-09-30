
import java.io.File;
import java.lang.reflect.Method;

public class TestMethods {
    public static void main(String[] args) {
        try {
            Class<?> ctxCls = Class.forName("info.openrocket.core.file.DocumentLoadingContext");
            System.out.println("=== DocumentLoadingContext Methods ===");
            for (Method m : ctxCls.getMethods()) {
                if (m.getDeclaringClass() == ctxCls) {
                    System.out.println("  " + m.getName() + " -> " + m.getReturnType().getSimpleName());
                }
            }
            Class<?> loaderCls = Class.forName("info.openrocket.core.file.openrocket.importt.OpenRocketLoader");
            System.out.println("=== OpenRocketLoader Methods ===");
            for (Method m : loaderCls.getMethods()) {
                if (m.getDeclaringClass() == loaderCls) {
                    System.out.println("  " + m.getName() + " -> " + m.getReturnType().getSimpleName());
                }
            }
        } catch (Throwable t) {
            t.printStackTrace();
        }
    }
}
