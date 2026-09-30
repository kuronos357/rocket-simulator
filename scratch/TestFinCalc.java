
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
