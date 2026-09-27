import numpy as np
from sim_engine.loader import RocketModel
from sim_engine.aero import AeroEngine

json_path = "export/つくば＿ロケット v12_params.json"
clean_stl_path = "export/つくば＿ロケット v12_clean.stl"

base_model = RocketModel(json_path, airframe_mass_override_g=11.07)
L = base_model.total_length_mm
D = 22.0
cp_tail = 67.61

print(f"=== Ignition vs Burnout Stability (Default: Streamer 1.5g) ===")

# Ignition
cg_ign = base_model.cg_mm[1]
margin_ign = (cg_ign - cp_tail) / D

# Burnout (propellant 1.56g burned from motor tail around Y=15mm)
prop_mass = 1.56
prop_y = 15.0
total_ign_mass = base_model.launch_mass_g
burnout_mass = total_ign_mass - prop_mass

# New CG
burnout_cg = (total_ign_mass * cg_ign - prop_mass * prop_y) / burnout_mass
margin_bo = (burnout_cg - cp_tail) / D

print(f"Ignition: CG = {cg_ign:.2f} mm, Margin = {margin_ign:.2f} cal ({(margin_ign*100):.1f}%)")
print(f"Burnout : CG = {burnout_cg:.2f} mm, Margin = {margin_bo:.2f} cal ({(margin_bo*100):.1f}%)")
print(f"CG shift during boost: +{burnout_cg - cg_ign:.2f} mm forward")
