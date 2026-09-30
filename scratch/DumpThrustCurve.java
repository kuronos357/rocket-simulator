import java.io.File;
import info.openrocket.core.startup.OpenRocketCore;
import info.openrocket.core.file.GeneralRocketLoader;
import info.openrocket.core.document.OpenRocketDocument;
import info.openrocket.core.simulation.FlightData;
import info.openrocket.core.simulation.FlightDataBranch;
import info.openrocket.core.simulation.FlightDataType;
import java.util.List;

public class DumpThrustCurve {
    public static void main(String[] args) throws Exception {
        OpenRocketCore.initialize();
        GeneralRocketLoader loader = new GeneralRocketLoader(new File("output/ロケット_ベースライン.ork"));
        OpenRocketDocument doc = loader.load();
        info.openrocket.core.document.Simulation sim = doc.getSimulation(0);
        sim.simulate();
        FlightData data = sim.getSimulatedData();
        FlightDataBranch branch = data.getBranch(0);
        List<Double> times = branch.get(FlightDataType.TYPE_TIME);
        List<Double> thrusts = branch.get(FlightDataType.TYPE_THRUST_FORCE);
        System.out.println("TIME_THRUST_START");
        for (int i = 0; i < times.size(); i++) {
            if (thrusts.get(i) > 0.001 || (i > 0 && thrusts.get(i-1) > 0.001)) {
                System.out.printf("%.4f, %.4f\n", times.get(i), thrusts.get(i));
            }
        }
        System.out.println("TIME_THRUST_END");
    }
}
