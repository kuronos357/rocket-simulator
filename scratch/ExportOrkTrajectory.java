import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.List;
import info.openrocket.core.startup.OpenRocketCore;
import info.openrocket.core.file.GeneralRocketLoader;
import info.openrocket.core.document.OpenRocketDocument;
import info.openrocket.core.document.Simulation;
import info.openrocket.core.simulation.FlightData;
import info.openrocket.core.simulation.FlightDataBranch;
import info.openrocket.core.simulation.FlightDataType;

public class ExportOrkTrajectory {
    public static void main(String[] args) throws Exception {
        if (args.length < 2) {
            System.out.println("Usage: ExportOrkTrajectory <input-ork> <output-csv>");
            return;
        }
        OpenRocketCore.initialize();
        GeneralRocketLoader loader = new GeneralRocketLoader(new File(args[0]));
        OpenRocketDocument doc = loader.load();
        Simulation sim = doc.getSimulation(0);
        sim.simulate();
        FlightData data = sim.getSimulatedData();
        FlightDataBranch branch = data.getBranch(0);

        List<Double> time = null;
        List<Double> alt = null;
        List<Double> vel = null;

        for (FlightDataType type : branch.getTypes()) {
            String name = type.getName();
            if (name.equalsIgnoreCase("Time") || name.equals("時間")) {
                time = branch.get(type);
            } else if (name.equalsIgnoreCase("Altitude") || name.equals("高度")) {
                alt = branch.get(type);
            } else if (name.equalsIgnoreCase("Total velocity") || name.equalsIgnoreCase("Velocity") || name.equals("速度")) {
                if (vel == null) vel = branch.get(type);
            }
        }

        PrintWriter pw = new PrintWriter(new FileWriter(args[1]));
        pw.println("time_s,altitude_m,velocity_ms");
        if (time != null && alt != null) {
            for (int i = 0; i < time.size(); i++) {
                double t = time.get(i);
                double a = alt.get(i);
                double v = (vel != null && i < vel.size()) ? vel.get(i) : 0.0;
                pw.printf("%.4f,%.4f,%.4f\n", t, a, v);
            }
        }
        pw.close();
        System.out.println("Exported trajectory to: " + args[1]);
    }
}
