import subprocess

java_code = """
import java.io.File;
import info.openrocket.core.startup.OpenRocketCore;
import info.openrocket.core.file.GeneralRocketLoader;
import info.openrocket.core.document.OpenRocketDocument;
import info.openrocket.core.document.Simulation;
import info.openrocket.core.simulation.FlightData;
import info.openrocket.core.rocketcomponent.Rocket;
import info.openrocket.core.rocketcomponent.RocketComponent;

public class CheckMass {
    public static void main(String[] args) {
        try {
            OpenRocketCore.initialize();
            GeneralRocketLoader loader = new GeneralRocketLoader(new File("output/ロケット_ベースライン.ork"));
            OpenRocketDocument doc = loader.load();
            Rocket rocket = doc.getRocket();
            System.out.printf("Rocket getMass: %.2f g\\n", rocket.getMass() * 1000.0);
            for (RocketComponent comp : rocket) {
                System.out.printf(" - %s: mass=%.2f g, len=%.1f mm\\n", 
                    comp.getName(), comp.getMass() * 1000.0, comp.getLength() * 1000.0);
            }
            Simulation sim = doc.getSimulation(0);
            System.out.println("Simulation name: " + sim.getName());
            sim.simulate();
            FlightData data = sim.getSimulatedData();
            System.out.printf("Sim apogee: %.2f m\\n", data.getMaxAltitude());
            System.out.printf("Sim max vel: %.2f m/s\\n", data.getMaxVelocity());
            System.out.printf("Sim flight time: %.2f s\\n", data.getFlightTime());
        } catch (Throwable t) { t.printStackTrace(); }
    }
}
"""

with open("scratch/CheckMass.java", "w", encoding="utf-8") as f:
    f.write(java_code)

res = subprocess.run([
    "java",
    "-cp", "C:\\Program Files\\OpenRocket\\jar\\OpenRocket-24.12.jar;scratch",
    "scratch/CheckMass.java"
], capture_output=True, text=True)
print("STDOUT:\n", res.stdout)
if res.stderr:
    print("STDERR:\n", res.stderr)
