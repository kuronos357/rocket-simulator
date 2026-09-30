import subprocess

java_code = """
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
"""

with open("scratch/TestORCore.java", "w", encoding="utf-8") as f:
    f.write(java_code)

res = subprocess.run([
    "java",
    "-cp", "C:\\Program Files\\OpenRocket\\jar\\OpenRocket-24.12.jar;scratch",
    "scratch/TestORCore.java"
], capture_output=True, text=True)
print("STDOUT:\n", res.stdout)
print("STDERR:\n", res.stderr)
