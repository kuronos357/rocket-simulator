import java.io.File;
import info.openrocket.core.startup.OpenRocketCore;
import info.openrocket.core.file.GeneralRocketLoader;
import info.openrocket.core.document.OpenRocketDocument;
import info.openrocket.core.rocketcomponent.RocketComponent;
import info.openrocket.core.rocketcomponent.MotorMount;
import info.openrocket.core.motor.Motor;

public class CheckMotor {
    public static void main(String[] args) throws Exception {
        OpenRocketCore.initialize();
        File f = new File("output/ロケット_ベースライン.ork");
        GeneralRocketLoader loader = new GeneralRocketLoader(f);
        OpenRocketDocument doc = loader.load();
        for (RocketComponent c : doc.getRocket()) {
            if (c instanceof MotorMount) {
                MotorMount mm = (MotorMount) c;
                Motor m = mm.getMotor(doc.getDefaultConfiguration());
                if (m != null) {
                    System.out.println("Motor designation: " + m.getDesignation());
                    System.out.println("Motor total impulse: " + m.getTotalImpulse());
                    System.out.println("Motor burn time: " + m.getBurnTimeDuration());
                    System.out.println("Motor launch mass: " + m.getLaunchMass());
                    System.out.println("Motor empty mass: " + m.getEmptyMass());
                }
            }
        }
    }
}
