import subprocess

java_code = """
import java.lang.reflect.*;
import info.openrocket.core.aerodynamics.barrowman.FinSetCalc;

public class TestFinCalc {
    public static void main(String[] args) {
        System.out.println("Methods in FinSetCalc:");
        for (Method m : FinSetCalc.class.getDeclaredMethods()) {
            System.out.println(m.getName() + " -> " + m.getReturnType().getSimpleName());
        }
    }
}
"""
with open('scratch/TestFinCalc.java', 'w', encoding='utf-8') as f:
    f.write(java_code)

res = subprocess.run([
    'java', 
    '-cp', 'C:\\Program Files\\OpenRocket\\jar\\OpenRocket-24.12.jar;scratch', 
    'scratch/TestFinCalc.java'
], capture_output=True, text=True)
print("STDOUT:\n", res.stdout)
print("STDERR:\n", res.stderr)
