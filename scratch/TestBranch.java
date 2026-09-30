import java.lang.reflect.Method;
import info.openrocket.core.simulation.FlightDataBranch;

public class TestBranch {
    public static void main(String[] args) {
        for (Method m : FlightDataBranch.class.getMethods()) {
            System.out.println(m.getName() + ' ' + m.getReturnType().getSimpleName());
        }
    }
}
