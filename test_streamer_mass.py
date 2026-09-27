import os
import numpy as np
from sim_engine.loader import RocketModel
from sim_engine.aero import AeroEngine
from sim_engine.flight_sim import FlightSimulator

json_path = "export/つくば＿ロケット v8_params.json"

print(f"{'Streamer (g)':<12} | {'Dry Mass (g)':<12} | {'CG (mm)':<10} | {'CP (mm)':<10} | {'Margin (cal)':<12} | {'Apo (m)':<8} | {'V_desc (m/s)':<12} | {'Flight Time (s)':<15}")
print("-" * 105)

# Load base model to get aero
base_model = RocketModel(json_path)
aero = AeroEngine(stl_path=base_model.stl_path, flight_axis=base_model.flight_axis, ref_diameter_mm=22.0)

for m_streamer in [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0]:
    model = RocketModel(json_path)
    
    # Override streamer mass
    for part in model.parts:
        if part.get("type") == "streamer":
            part["mass_g"] = m_streamer
            scale = m_streamer / 1.5
            part["moi_g_cm2"] = {k: v * scale for k, v in part["moi_g_cm2"].items()}
            
    # recalculate composite properties
    model._calculate_composite_properties()
    
    cg_flight = model.cg_mm[1] if model.flight_axis == 'y' else model.cg_mm[2]
    aero_res = aero.compute_aerodynamics(velocity_m_s=40.0, alpha_deg=2.0, cg_z_mm=cg_flight)
    
    sim = FlightSimulator(rocket_model=model, aero_engine=aero)
    flight_res = sim.run_simulation()
    
    margin_cal = aero_res['margin_cal']
    dry_mass = model.dry_mass_g
    apo = flight_res['apogee_alt_m']
    ft = flight_res['total_flight_time_s']
    v_desc = flight_res['terminal_velocity_m_s']
    
    print(f"{m_streamer:<12.1f} | {dry_mass:<12.2f} | {cg_flight:<10.2f} | {aero_res['CP_z_mm']:<10.2f} | {margin_cal:<12.2f} | {apo:<8.1f} | {v_desc:<12.2f} | {ft:<15.1f}")
