import os
from sim_engine.loader import RocketModel
from sim_engine.aero import AeroEngine
from sim_engine.flight_sim import FlightSimulator

json_path = "export/つくば＿ロケット v12_params.json"
clean_stl_path = "export/つくば＿ロケット v12_clean.stl"

model = RocketModel(json_path)

# 構造体パーツの現在の合計質量
struct_parts = [p for p in model.parts if p.get("type") == "structure"]
current_struct_mass = sum(p["mass_g"] for p in struct_parts)
target_struct_mass = 11.07 # スライサーの正味機体重量

scale = target_struct_mass / current_struct_mass
print(f"Scaling structure mass: {current_struct_mass:.3f}g -> {target_struct_mass:.3f}g (scale={scale:.4f})")

for p in struct_parts:
    p["mass_g"] *= scale
    p["moi_g_cm2"] = {k: v * scale for k, v in p["moi_g_cm2"].items()}

model._calculate_composite_properties()

print(f"\n=== Actual Flight Configuration (Slicer Airframe = 11.07g) ===")
print(f"Airframe Dry Mass (with 1.5g streamer): {model.dry_mass_g:.2f} g")
print(f"Total Launch Gross Mass (at Ignition) : {model.launch_mass_g:.2f} g")
cg_flight = model.cg_mm[1] if model.flight_axis == 'y' else model.cg_mm[2]
print(f"Center of Gravity (CG from tail)      : {cg_flight:.2f} mm")

aero = AeroEngine(stl_path=clean_stl_path, flight_axis=model.flight_axis, ref_diameter_mm=22.0)
aero_res = aero.compute_aerodynamics(velocity_m_s=40.0, alpha_deg=2.0, cg_z_mm=cg_flight)

print(f"Center of Pressure (CP from tail)     : {aero_res['CP_z_mm']:.2f} mm")
print(f"Static Stability Margin               : {aero_res['margin_cal']:.2f} cal")

sim = FlightSimulator(rocket_model=model, aero_engine=aero)
flight_res = sim.run_simulation()

print(f"\n=== Flight Dynamics Results ===")
print(f"Apogee Altitude                 : {flight_res['apogee_alt_m']:.1f} m")
print(f"Max Velocity                    : {flight_res['max_velocity_km_h']:.1f} km/h ({flight_res['max_velocity_m_s']:.1f} m/s)")
print(f"Max Acceleration                : {flight_res['max_accel_G']:.1f} G")
print(f"Launch Rod Clear Speed (0.9m)   : {flight_res['rod_clear_speed_m_s']:.1f} m/s")
print(f"Ejection Timing & Alt           : T+{flight_res['ejection_time_s']:.2f}s (Alt: {flight_res['ejection_alt_m']:.1f} m)")
print(f"Terminal Descent Velocity       : {flight_res['terminal_velocity_m_s']:.1f} m/s")
print(f"Total Flight Time (to landing)  : {flight_res['total_flight_time_s']:.1f} s")
