import java.io.File;
import java.util.List;
import info.openrocket.core.startup.OpenRocketCore;
import info.openrocket.core.file.GeneralRocketLoader;
import info.openrocket.core.document.OpenRocketDocument;
import info.openrocket.core.document.Simulation;
import info.openrocket.core.simulation.FlightData;
import info.openrocket.core.simulation.FlightDataBranch;
import info.openrocket.core.simulation.FlightDataType;
import info.openrocket.core.rocketcomponent.Rocket;
import info.openrocket.core.rocketcomponent.FlightConfiguration;
import info.openrocket.core.aerodynamics.BarrowmanCalculator;
import info.openrocket.core.aerodynamics.FlightConditions;
import info.openrocket.core.logging.WarningSet;
import info.openrocket.core.util.Coordinate;

public class RunDetailedOrkAnalysis {
    public static void main(String[] args) {
        if (args.length == 0) {
            System.out.println("Usage: RunDetailedOrkAnalysis <path-to-ork> [...]");
            return;
        }
        try {
            OpenRocketCore.initialize();
        } catch (Throwable t) {
            System.err.println("Init failed: " + t.getMessage());
        }

        for (String filePath : args) {
            File orkFile = new File(filePath);
            if (!orkFile.exists()) {
                System.err.println("File not found: " + filePath);
                continue;
            }
            analyzeFile(orkFile);
        }
    }

    private static void analyzeFile(File orkFile) {
        try {
            GeneralRocketLoader loader = new GeneralRocketLoader(orkFile);
            OpenRocketDocument doc = loader.load();
            Rocket rocket = doc.getRocket();
            
            if (doc.getSimulationCount() == 0) {
                Simulation sim = new Simulation(rocket);
                doc.addSimulation(sim);
            }
            Simulation sim = doc.getSimulation(0);
            sim.simulate();
            FlightConfiguration fc = sim.getActiveConfiguration();
            FlightData data = sim.getSimulatedData();
            FlightDataBranch branch = data.getBranch(0);

            // Find data series
            List<Double> times = null;
            List<Double> cgs = null;
            List<Double> cps = null;
            List<Double> margins = null;
            List<Double> masses = null;
            List<Double> vels = null;
            List<Double> alts = null;

            for (FlightDataType type : branch.getTypes()) {
                String name = type.getName();
                List<Double> vals = branch.get(type);
                if (vals == null || vals.isEmpty()) continue;
                
                if (name.equalsIgnoreCase("Time")) {
                    times = vals;
                } else if (name.equalsIgnoreCase("CG location")) {
                    cgs = vals;
                } else if (name.equalsIgnoreCase("CP location")) {
                    cps = vals;
                } else if (name.equalsIgnoreCase("Stability margin calibers")) {
                    margins = vals;
                } else if (name.equalsIgnoreCase("Mass")) {
                    if (masses == null) masses = vals;
                } else if (name.equalsIgnoreCase("Vertical velocity") || name.equalsIgnoreCase("Total velocity")) {
                    if (vels == null) vels = vals;
                } else if (name.equalsIgnoreCase("Altitude")) {
                    if (alts == null) alts = vals;
                }
            }

            // Find first valid CP and Margin (when velocity > 5 m/s, e.g. off launch rod)
            Double rodCp = null;
            Double rodCg = null;
            Double rodMargin = null;
            Double launchMass = (masses != null && !masses.isEmpty()) ? masses.get(0) : rocket.getMass();
            Double launchCg = (cgs != null && !cgs.isEmpty()) ? cgs.get(0) : (rocket.getCG() != null ? rocket.getCG().x : null);

            if (cps != null && margins != null) {
                for (int i = 0; i < cps.size(); i++) {
                    Double cpVal = cps.get(i);
                    Double mVal = margins.get(i);
                    if (cpVal != null && !Double.isNaN(cpVal) && !Double.isInfinite(cpVal)) {
                        rodCp = cpVal;
                        rodCg = (cgs != null && i < cgs.size()) ? cgs.get(i) : launchCg;
                        rodMargin = mVal;
                        break;
                    }
                }
            }

            // Direct calculation via BarrowmanCalculator
            Double barrowmanCp = null;
            try {
                if (fc != null) {
                    BarrowmanCalculator calc = new BarrowmanCalculator();
                    FlightConditions cond = new FlightConditions(fc);
                    cond.setMach(0.1);
                    cond.setAOA(0.0);
                    Coordinate cpCoord = calc.getCP(fc, cond, new WarningSet());
                    if (cpCoord != null) {
                        barrowmanCp = cpCoord.x;
                    }
                }
            } catch (Throwable t) {
                // ignore
            }

            System.out.println("ANALYSIS_START");
            System.out.println("FILE=" + orkFile.getName());
            System.out.println("ROCKET_NAME=" + rocket.getName());
            System.out.printf("TOTAL_LENGTH_MM=%.2f\n", rocket.getLength() * 1000.0);
            System.out.printf("LAUNCH_MASS_G=%.2f\n", launchMass * 1000.0);
            if (launchCg != null) {
                System.out.printf("LAUNCH_CG_FROM_NOSE_MM=%.2f\n", launchCg * 1000.0);
            }
            if (rodCp != null) {
                System.out.printf("FLIGHT_CP_FROM_NOSE_MM=%.2f\n", rodCp * 1000.0);
            }
            if (rodCg != null) {
                System.out.printf("FLIGHT_CG_FROM_NOSE_MM=%.2f\n", rodCg * 1000.0);
            }
            if (rodMargin != null) {
                System.out.printf("FLIGHT_MARGIN_CAL=%.2f\n", rodMargin);
            }
            if (barrowmanCp != null) {
                System.out.printf("BARROWMAN_CP_FROM_NOSE_MM=%.2f\n", barrowmanCp * 1000.0);
                if (launchCg != null) {
                    double bMargin = (barrowmanCp - launchCg) / 0.024;
                    System.out.printf("BARROWMAN_STATIC_MARGIN_CAL=%.2f\n", bMargin);
                }
            }
            System.out.printf("APOGEE_M=%.2f\n", data.getMaxAltitude());
            System.out.printf("MAX_VEL_MS=%.2f\n", data.getMaxVelocity());
            System.out.printf("TIME_TO_APOGEE_S=%.2f\n", data.getTimeToApogee());
            System.out.printf("FLIGHT_TIME_S=%.2f\n", data.getFlightTime());
            System.out.printf("GROUND_HIT_VEL_MS=%.2f\n", data.getGroundHitVelocity());
            System.out.printf("LAUNCH_ROD_VEL_MS=%.2f\n", data.getLaunchRodVelocity());

            if (times != null && alts != null) {
                String csvName = "output/" + orkFile.getName().replace(".ork", "_traj.csv");
                try (java.io.PrintWriter pw = new java.io.PrintWriter(new java.io.FileWriter(csvName))) {
                    pw.println("time_s,altitude_m,velocity_ms");
                    for (int i = 0; i < times.size(); i++) {
                        double t = times.get(i);
                        double a = (alts != null && i < alts.size()) ? alts.get(i) : 0.0;
                        double v = (vels != null && i < vels.size()) ? vels.get(i) : 0.0;
                        pw.printf(java.util.Locale.US, "%.4f,%.4f,%.4f\n", t, a, v);
                    }
                    System.out.println("SAVED_CSV=" + csvName);
                } catch (Exception ex) {
                    System.err.println("Failed to write CSV: " + ex.getMessage());
                }
            }
            System.out.println("ANALYSIS_END");

        } catch (Throwable t) {
            System.err.println("ERROR processing " + orkFile.getName() + ": " + t.getMessage());
            t.printStackTrace();
        }
    }
}
