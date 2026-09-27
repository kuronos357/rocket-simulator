import sys, os
sys.path.insert(0, ".")
from sim_engine.loader import RocketModel
from sim_engine.aero import AeroEngine
from sim_engine.flight_sim import FlightSimulator
import numpy as np

model = RocketModel('export/つくば＿ロケット v8_params.json', shell_thickness_mm=0.4, infill_ratio=0.02)

# ノーズ先端にストリーマ+金具 6g を追加配置 (Y=175mm)
model.parts.append({
    'name': 'Nose_Tip_Recovery_Hardware',
    'type': 'ballast',
    'mass_g': 6.0,
    'com_mm': np.array([0.0, 175.0, 0.0]),
    'moi_g_cm2': {'Ixx': 1.0, 'Iyy': 1.0, 'Izz': 1.0}
})
model._calculate_composite_properties()

aero = AeroEngine(model.stl_path, flight_axis='y', ref_diameter_mm=22.0)
aero_res = aero.compute_aerodynamics(40.0, alpha_deg=2.0, cg_z_mm=model.cg_mm[1])
sim = FlightSimulator(model, aero)
res = sim.run_simulation()

print(f"全備重量: {model.launch_mass_g:.1f} g")
print(f"新・重心(CG): {model.cg_mm[1]:.1f} mm")
print(f"空力中心(CP): {aero_res['CP_z_mm']:.1f} mm")
print(f"静安定性マージン: {aero_res['margin_cal']:.2f} cal (判定: {'[OK] 安定' if aero_res['is_stable'] else '[WARN] 不安定'})")
print(f"最高高度: {res['apogee_alt_m']:.1f} m")
print(f"着地終端速度: {res['terminal_velocity_m_s']:.1f} m/s")
print(f"総滞空時間: {res['total_flight_time_s']:.1f} 秒")
