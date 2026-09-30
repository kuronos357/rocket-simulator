
import java.io.File;
import info.openrocket.core.startup.OpenRocketCore;
import info.openrocket.core.file.GeneralRocketLoader;
import info.openrocket.core.document.OpenRocketDocument;
import info.openrocket.core.document.Simulation;
import info.openrocket.core.simulation.FlightData;
import info.openrocket.core.rocketcomponent.Rocket;

public class RunOrkSim {
    public static void main(String[] args) {
        if (args.length == 0) {
            System.out.println("Usage: RunOrkSim <path-to-ork>");
            return;
        }
        File orkFile = new File(args[0]);
        try {
            OpenRocketCore.initialize();
            GeneralRocketLoader loader = new GeneralRocketLoader(orkFile);
            OpenRocketDocument doc = loader.load();
            Rocket rocket = doc.getRocket();
            
            if (doc.getSimulationCount() == 0) {
                Simulation sim = new Simulation(rocket);
                doc.addSimulation(sim);
            }
            Simulation sim = doc.getSimulation(0);
            sim.simulate();
            FlightData data = sim.getSimulatedData();

            System.out.println("RESULT_START");
            System.out.println("ROCKET_NAME=" + rocket.getName());
            System.out.printf("APOGEE_M=%.2f\n", data.getMaxAltitude());
            System.out.printf("MAX_VEL_MS=%.2f\n", data.getMaxVelocity());
            System.out.printf("TIME_TO_APOGEE_S=%.2f\n", data.getTimeToApogee());
            System.out.printf("FLIGHT_TIME_S=%.2f\n", data.getFlightTime());
            System.out.printf("DESCENT_VEL_MS=%.2f\n", data.getGroundHitVelocity());
            System.out.println("RESULT_END");
        } catch (Throwable t) {
            System.err.println("ERROR: " + t.getMessage());
            t.printStackTrace();
        }
    }
}
