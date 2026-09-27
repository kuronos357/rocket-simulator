"""
Main CLI Runner for Rocket Simulator
Automatically finds latest exported params.json, runs physical/aero/flight simulation,
and outputs report & flight profile graph.
"""

import os
import glob
import sys

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

from sim_engine.loader import RocketModel
from sim_engine.aero import AeroEngine
from sim_engine.flight_sim import FlightSimulator
from sim_engine.report import print_summary_report, plot_flight_profile

def main():
    export_dir = os.path.join(os.path.dirname(__file__), "export")
    
    # 1. JSONファイルの検索
    if len(sys.argv) > 1:
        target_arg = sys.argv[1]
        if target_arg.endswith(".stl") or target_arg.endswith(".step"):
            base = os.path.splitext(target_arg)[0]
            candidate = f"{base}_params.json"
            json_path = candidate if os.path.exists(candidate) else target_arg
        else:
            json_path = target_arg
    else:
        json_files = glob.glob(os.path.join(export_dir, "*_params.json"))
        if not json_files:
            print("❌ エクスポートされた JSON ファイルが export/ 内に見つかりません。")
            return
        # 最新のファイルを選択
        json_path = max(json_files, key=os.path.getmtime)

    print(f"Loading: {os.path.basename(json_path)}")
    
    # 2. モデルのロード (スライサー実測値 11.07g を適用)
    model = RocketModel(
        json_path=json_path,
        shell_thickness_mm=0.4,
        infill_ratio=0.02,
        default_material="PLA",
        airframe_mass_override_g=11.07 # スライサー実測値 (1層 2%)
    )
    
    # 3. 3Dメッシュ空力計算 (内部パーツを除外した _clean.stl があれば優先)
    clean_stl = model.stl_path.replace(".stl", "_clean.stl")
    actual_stl_path = clean_stl if os.path.exists(clean_stl) else model.stl_path
    
    print(f"Analyzing STL aerodynamic mesh ({os.path.basename(actual_stl_path)})...")
    aero = AeroEngine(
        stl_path=actual_stl_path,
        flight_axis=model.flight_axis,
        ref_diameter_mm=22.0 # 胴体直径 ~22mm
    )
    
    # 飛行速度 40m/s, 迎角2度での静安定性・空力
    cg_flight_axis = model.cg_mm[1] if model.flight_axis == "y" else model.cg_mm[2]
    aero_res = aero.compute_aerodynamics(velocity_m_s=40.0, alpha_deg=2.0, cg_z_mm=cg_flight_axis)
    
    # 4. 飛翔ダイナミクス計算
    print("Running flight dynamics & descent simulation...")
    sim = FlightSimulator(rocket_model=model, aero_engine=aero)
    flight_res = sim.run_simulation()
    
    # 5. レポート出力 & グラフ保存
    print_summary_report(model, aero_res, flight_res)
    
    graph_path = os.path.join(export_dir, f"{model.design_name}_flight_profile.png")
    plot_flight_profile(flight_res, output_path=graph_path)

if __name__ == "__main__":
    main()
