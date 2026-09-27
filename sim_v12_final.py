import os
from sim_engine.loader import RocketModel
from sim_engine.aero import AeroEngine
from sim_engine.flight_sim import FlightSimulator

json_path = "export/つくば＿ロケット v12_params.json"
clean_stl_path = "export/つくば＿ロケット v12_clean.stl"

base_model = RocketModel(json_path)
aero = AeroEngine(stl_path=clean_stl_path, flight_axis=base_model.flight_axis, ref_diameter_mm=22.0)

print(f"{'Streamer (g)':<12} | {'Dry Mass (g)':<12} | {'CG (mm)':<10} | {'CP (mm)':<10} | {'Margin (cal)':<12} | {'Apogee (m)':<10} | {'Flight Time (s)':<15}")
print("-" * 90)

for m_st in [1.5, 2.5, 3.5, 5.0]:
    model = RocketModel(json_path)
    for p in model.parts:
        if p.get("type") == "streamer":
            p["mass_g"] = m_st
            scale = m_st / 1.5
            p["moi_g_cm2"] = {k: v * scale for k, v in p["moi_g_cm2"].items()}
    model._calculate_composite_properties()
    
    cg_flight = model.cg_mm[1] if model.flight_axis == 'y' else model.cg_mm[2]
    aero_res = aero.compute_aerodynamics(velocity_m_s=40.0, alpha_deg=2.0, cg_z_mm=cg_flight)
    
    sim = FlightSimulator(rocket_model=model, aero_engine=aero)
    flight_res = sim.run_simulation()
    
    margin_cal = aero_res['margin_cal']
    dry_mass = model.dry_mass_g
    apo = flight_res['apogee_alt_m']
    ft = flight_res['total_flight_time_s']
    
    print(f"{m_st:<12.1f} | {dry_mass:<12.2f} | {cg_flight:<10.2f} | {aero_res['CP_z_mm']:<10.2f} | {margin_cal:<12.2f} | {apo:<10.1f} | {ft:<15.1f}")
