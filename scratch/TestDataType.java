import java.io.File;
import info.openrocket.core.startup.OpenRocketCore;
import info.openrocket.core.file.GeneralRocketLoader;
import info.openrocket.core.document.OpenRocketDocument;
import info.openrocket.core.document.Simulation;
import info.openrocket.core.simulation.FlightData;
import info.openrocket.core.simulation.FlightDataBranch;
import info.openrocket.core.simulation.FlightDataType;

public class TestDataType {
    public static void main(String[] args) throws Exception {
        OpenRocketCore.initialize();
        GeneralRocketLoader loader = new GeneralRocketLoader(new File(args[0]));
        OpenRocketDocument doc = loader.load();
        Simulation sim = doc.getSimulation(0);
        sim.simulate();
        FlightData data = sim.getSimulatedData();
        FlightDataBranch branch = data.getBranch(0);
        for (FlightDataType type : branch.getTypes()) {
            System.out.println("DATA_TYPE: " + type.getName());
        }
    }
}
