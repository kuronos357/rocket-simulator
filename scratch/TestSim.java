import java.io.File;
import info.openrocket.core.startup.OpenRocketCore;
import info.openrocket.core.file.GeneralRocketLoader;
import info.openrocket.core.document.OpenRocketDocument;
import info.openrocket.core.rocketcomponent.Rocket;
import info.openrocket.core.simulation.Simulation;
import info.openrocket.core.simulation.FlightData;

public class TestSim {
    public static void main(String[] args) {
        try {
            OpenRocketCore.initialize();
            GeneralRocketLoader loader = new GeneralRocketLoader(new File("scratch/sample_example.ork"));
            OpenRocketDocument doc = loader.load();
            System.out.println("Simulations count: " + doc.getSimulationCount());
            if (doc.getSimulationCount() > 0) {
                Simulation sim = doc.getSimulation(0);
                System.out.println("Running simulation: " + sim.getName());
                sim.simulate();
                FlightData data = sim.getSimulatedData();
                System.out.printf("Max Altitude: %.2f m\n", data.getMaxAltitude());
                System.out.printf("Max Velocity: %.2f m/s\n", data.getMaxVelocity());
                System.out.printf("Flight Time: %.2f s\n", data.getFlightTime());
                System.out.printf("Time to Apogee: %.2f s\n", data.getTimeToApogee());
            }
        } catch (Throwable t) {
            t.printStackTrace();
        }
    }
}
