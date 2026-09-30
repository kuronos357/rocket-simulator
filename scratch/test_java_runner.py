import subprocess
import os

code = """
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
"""
with open('scratch/TestLoader.java', 'w', encoding='utf-8') as f:
    f.write(code)

res = subprocess.run([
    'java',
    '-cp', 'C:\\Program Files\\OpenRocket\\jar\\OpenRocket-24.12.jar;scratch',
    'scratch/TestLoader.java'
], capture_output=True, text=True)
print("STDOUT:\n", res.stdout)
print("STDERR:\n", res.stderr)
