import subprocess

java_code = """
import java.io.File;
import java.util.List;
import info.openrocket.core.startup.OpenRocketCore;
import info.openrocket.core.file.GeneralRocketLoader;
import info.openrocket.core.document.OpenRocketDocument;
import info.openrocket.core.document.Simulation;
import info.openrocket.core.simulation.FlightData;
import info.openrocket.core.simulation.FlightDataBranch;
import info.openrocket.core.simulation.FlightDataType;

public class PrintTrajectory {
    public static void main(String[] args) {
        try {
            OpenRocketCore.initialize();
            GeneralRocketLoader loader = new GeneralRocketLoader(new File("scratch/test_c1_correct_mass.ork"));
            OpenRocketDocument doc = loader.load();
            Simulation sim = doc.getSimulation(0);
            sim.simulate();
            FlightData data = sim.getSimulatedData();
            FlightDataBranch branch = data.getBranch(0);
            
            List<Double> times = branch.get(FlightDataType.TYPE_TIME);
            List<Double> alts = branch.get(FlightDataType.TYPE_ALTITUDE);
            List<Double> vels = branch.get(FlightDataType.TYPE_VELOCITY_Z);
            List<Double> accs = branch.get(FlightDataType.TYPE_ACCELERATION_Z);
            
            System.out.println("Points count: " + times.size());
            System.out.println("Time [s], Alt [m], Vel [m/s], Acc [m/s2]");
            int step = Math.max(1, times.size() / 25);
            for (int i = 0; i < times.size(); i += step) {
                System.out.printf("%.3f, %.2f, %.2f, %.2f\\n", times.get(i), alts.get(i), vels.get(i), accs.get(i));
            }
            System.out.printf("APOGEE: %.2f m at t=%.2f s\\n", data.getMaxAltitude(), data.getTimeToApogee());
            System.out.printf("MAX VEL: %.2f m/s\\n", data.getMaxVelocity());
        } catch (Throwable t) { t.printStackTrace(); }
    }
}
"""

with open("scratch/PrintTrajectory.java", "w", encoding="utf-8") as f:
    f.write(java_code)

res = subprocess.run([
    "java",
    "-cp", "C:\\Program Files\\OpenRocket\\jar\\OpenRocket-24.12.jar;scratch",
    "scratch/PrintTrajectory.java"
], capture_output=True, text=True)

print("STDOUT:\n", res.stdout)
if res.stderr:
    print("STDERR:\n", res.stderr)
