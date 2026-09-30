import subprocess
import os
import json

java_code = """
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
            System.out.printf("APOGEE_M=%.2f\\n", data.getMaxAltitude());
            System.out.printf("MAX_VEL_MS=%.2f\\n", data.getMaxVelocity());
            System.out.printf("TIME_TO_APOGEE_S=%.2f\\n", data.getTimeToApogee());
            System.out.printf("FLIGHT_TIME_S=%.2f\\n", data.getFlightTime());
            System.out.printf("DESCENT_VEL_MS=%.2f\\n", data.getGroundHitVelocity());
            System.out.println("RESULT_END");
        } catch (Throwable t) {
            System.err.println("ERROR: " + t.getMessage());
            t.printStackTrace();
        }
    }
}
"""

with open("scratch/RunOrkSim.java", "w", encoding="utf-8") as f:
    f.write(java_code)

def run_openrocket_file(filepath):
    res = subprocess.run([
        "java",
        "-cp", "C:\\Program Files\\OpenRocket\\jar\\OpenRocket-24.12.jar;scratch",
        "scratch/RunOrkSim.java",
        filepath
    ], capture_output=True, text=True)
    
    out = res.stdout
    results = {}
    if "RESULT_START" in out and "RESULT_END" in out:
        part = out.split("RESULT_START")[1].split("RESULT_END")[0]
        for line in part.strip().splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                try:
                    results[k] = float(v)
                except ValueError:
                    results[k] = v
    return results

if __name__ == "__main__":
    targets = [
        ("ベースライン機 (Baseline)", "output/ロケット_ベースライン.ork", 59.35, 10.23),
        ("機体① 限界滞空型 (Candidate 1)", "output/ロケット_機体1_限界滞空型.ork", 56.06, 9.59),
        ("機体② 超高安定型 (Candidate 2)", "output/ロケット_機体2_超高安定型.ork", 54.03, 9.25),
        ("機体③ 鉄壁安全型 (Candidate 3)", "output/ロケット_機体3_鉄壁安全型.ork", 51.55, 8.84),
    ]

    print("=" * 78)
    print(f"{'モデル名':<25} | {'項目':<10} | {'自作シミュ':<10} | {'OpenRocket':<10} | {'一致度/誤差'}")
    print("=" * 78)

    for label, path, my_apo, my_time in targets:
        ork_res = run_openrocket_file(path)
        if ork_res:
            ork_apo = ork_res.get('APOGEE_M', 0.0)
            ork_time = ork_res.get('FLIGHT_TIME_S', 0.0)
            apo_diff = abs(my_apo - ork_apo) / my_apo * 100
            time_diff = abs(my_time - ork_time) / my_time * 100
            print(f"{label:<25} | 最高高度   | {my_apo:6.1f} m  | {ork_apo:6.1f} m  | 差 {apo_diff:4.1f}%")
            print(f"{'':<25} | 滞空時間   | {my_time:6.1f} s  | {ork_time:6.1f} s  | 差 {time_diff:4.1f}%")
            print("-" * 78)
        else:
            print(f"{label}: Error running OpenRocket")
