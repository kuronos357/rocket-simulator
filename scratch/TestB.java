
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
