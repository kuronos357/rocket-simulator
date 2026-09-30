import java.lang.reflect.Method;
import info.openrocket.core.rocketcomponent.FlightConfiguration;

public class ListFC {
    public static void main(String[] args) {
        for (Method m : FlightConfiguration.class.getMethods()) {
            System.out.println(m.getName() + ' ' + m.getReturnType().getSimpleName());
        }
    }
}
