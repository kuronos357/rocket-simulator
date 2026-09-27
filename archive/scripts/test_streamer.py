import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

from sim_engine.loader import RocketModel
from sim_engine.aero import AeroEngine
from sim_engine.flight_sim import FlightSimulator

json_path = "export/つくば＿ロケット v6_params.json"
model = RocketModel(json_path, shell_thickness_mm=0.4, infill_ratio=0.02)

print("\n--- [シミュレーション比較: ストリーマ大型化 & 先端配置] ---")
print(f"【現状 (1.5g / Y=99mm)】: CG={model.cg_mm[1]:.1f}mm, 全備重量={model.launch_mass_g:.1f}g")

# パターンA: 6g（幅8cm x 長さ150cm 程度の厚手フィルム/リップストップナイロン）
# パターンB: 8g（幅10cm x 長さ200cm + ショックコード）
# パターンC: 10g（超大型ストリーマまたは小型クロスパラシュート）

for target_mass, pos_y in [(5.0, 130.0), (8.0, 140.0), (10.0, 150.0)]:
    for p in model.parts:
        if p["type"] == "streamer":
            p["mass_g"] = target_mass
            p["com_mm"][1] = pos_y
            
    model._calculate_composite_properties()
    cg_y = model.cg_mm[1]
    
    aero = AeroEngine(model.stl_path, flight_axis="y", ref_diameter_mm=22.0)
    aero_res = aero.compute_aerodynamics(40.0, alpha_deg=2.0, cg_z_mm=cg_y)
    
    sim = FlightSimulator(model, aero)
    # ストリーマ面積を質量に比例して拡大
    # 8g なら 0.15 m2
    streamer_area = 0.05 * (target_mass / 1.5)
    descent_CdS = 0.22 * streamer_area
    
    res = sim.run_simulation()
    
    print(f"\n▶ ストリーマ {target_mass}g (先端Y={pos_y}mm配置):")
    print(f"  ・全備重量: {model.launch_mass_g:.1f} g")
    print(f"  ・新 重心 (CG): {cg_y:.1f} mm (後端から)")
    print(f"  ・空力中心 (CP): {aero_res['CP_z_mm']:.1f} mm")
    print(f"  ・静安定性マージン: {aero_res['margin_cal']:.2f} cal (判定: {'[OK] 安定' if aero_res['is_stable'] else '[WARN] 不安定'})")
    print(f"  ・最高到達高度: {res['apogee_alt_m']:.1f} m")
    print(f"  ・着地終端速度: {res['terminal_velocity_m_s']:.1f} m/s")
    print(f"  ・総滞空時間: {res['total_flight_time_s']:.1f} 秒")

# パターンD: 先端金具(アイボルト・ネジ 4g @ 165mm) + ストリーマ(4g @ 135mm)
model_d = RocketModel(json_path, shell_thickness_mm=0.4, infill_ratio=0.02)
for p in model_d.parts:
    if p["type"] == "streamer":
        p["mass_g"] = 4.0
        p["com_mm"][1] = 135.0

import numpy as np
model_d.parts.append({
    "name": "Nose_Tip_Hardware",
    "type": "ballast",
    "mass_g": 5.0,
    "com_mm": np.array([0.0, 168.0, 0.0]),
    "moi_g_cm2": {"Ixx": 1.0, "Iyy": 1.0, "Izz": 1.0}
})
model_d._calculate_composite_properties()
cg_y_d = model_d.cg_mm[1]
aero_d = AeroEngine(model_d.stl_path, flight_axis="y", ref_diameter_mm=22.0)
aero_res_d = aero_d.compute_aerodynamics(40.0, alpha_deg=2.0, cg_z_mm=cg_y_d)
sim_d = FlightSimulator(model_d, aero_d)
res_d = sim_d.run_simulation()

print(f"\n▶ 【機能付随の理想案】先端金具・ショックコード固定部(5g @ Y=168mm) + 大型ストリーマ(4g @ Y=135mm):")
print(f"  ・全備重量: {model_d.launch_mass_g:.1f} g")
print(f"  ・新 重心 (CG): {cg_y_d:.1f} mm (後端から)")
print(f"  ・空力中心 (CP): {aero_res_d['CP_z_mm']:.1f} mm")
print(f"  ・静安定性マージン: {aero_res_d['margin_cal']:.2f} cal (判定: {'[OK] 安定' if aero_res_d['is_stable'] else '[WARN] 不安定'})")
print(f"  ・最高到達高度: {res_d['apogee_alt_m']:.1f} m")
print(f"  ・着地終端速度: {res_d['terminal_velocity_m_s']:.1f} m/s")
print(f"  ・総滞空時間: {res_d['total_flight_time_s']:.1f} 秒")
