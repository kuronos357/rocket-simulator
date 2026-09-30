import subprocess

java_code = """
import java.lang.reflect.*;
import info.openrocket.core.aerodynamics.BarrowmanCalculator;

public class TestB {
    public static void main(String[] args) {
        System.out.println("Methods in BarrowmanCalculator:");
        for (Method m : BarrowmanCalculator.class.getDeclaredMethods()) {
            System.out.println(m.getName());
        }
    }
}
"""
with open('scratch/TestB.java', 'w', encoding='utf-8') as f:
    f.write(java_code)

res = subprocess.run([
    'java', 
    '-cp', 'C:\\Program Files\\OpenRocket\\jar\\OpenRocket-24.12.jar;scratch', 
    'scratch/TestB.java'
], capture_output=True, text=True)
print("STDOUT:\n", res.stdout)
