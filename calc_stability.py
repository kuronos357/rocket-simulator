import numpy as np
from sim_engine.loader import RocketModel
from sim_engine.aero import AeroEngine

json_path = "export/つくば＿ロケット v12_params.json"
clean_stl_path = "export/つくば＿ロケット v12_clean.stl"

base_model = RocketModel(json_path, airframe_mass_override_g=11.07)
aero = AeroEngine(stl_path=clean_stl_path, flight_axis=base_model.flight_axis, ref_diameter_mm=22.0)

L = base_model.total_length_mm # 180.0 mm
D = 22.0 # mm

# 迎角2度でのCP
cp_from_tail = 67.61
cp_from_nose = L - cp_from_tail

print(f"Rocket Total Length: {L:.1f} mm, Body Diameter: {D:.1f} mm")
print(f"CP (Center of Pressure): {cp_from_tail:.2f} mm from tail ({cp_from_nose:.2f} mm from nose)\n")

print(f"{'Condition':<25} | {'Launch Mass':<11} | {'CG from Tail':<12} | {'CG from Nose':<12} | {'Margin (mm)':<11} | {'Margin (cal)':<12} | {'Margin (%D)':<11}")
print("-" * 105)

conditions = [
    ("Default (Streamer 1.5g)", 1.5, 0.0),
    ("Streamer 2.5g", 2.5, 0.0),
    ("Streamer 3.5g", 3.5, 0.0),
    ("+1.0g Nose Ballast (St 1.5g)", 1.5, 1.0),
    ("+2.0g Nose Ballast (St 1.5g)", 1.5, 2.0),
    ("+3.0g Nose Ballast (St 1.5g)", 1.5, 3.0),
    ("+2.0g Ballast + St 3.0g", 3.0, 2.0),
]

for name, m_st, m_ballast in conditions:
    model = RocketModel(json_path, airframe_mass_override_g=11.07)
    
    # Update streamer mass
    for p in model.parts:
        if p.get("type") == "streamer":
            p["mass_g"] = m_st
            scale = m_st / 1.5
            p["moi_g_cm2"] = {k: v * scale for k, v in p["moi_g_cm2"].items()}
            
    # Add nose ballast if any (located near nose tip Y=175mm)
    if m_ballast > 0:
        ballast_part = {
            "name": "Nose_Ballast",
            "type": "ballast",
            "mass_g": m_ballast,
            "com_mm": np.array([0.0, 175.0, 0.0]),
            "moi_g_cm2": {"Ixx": 0.1, "Iyy": 0.1, "Izz": 0.1}
        }
        model.parts.append(ballast_part)
        
    model._calculate_composite_properties()
    
    cg_tail = model.cg_mm[1]
    cg_nose = L - cg_tail
    
    # Margin in mm: (cg_tail - cp_from_tail)
    # Positive means CG is in front of CP (closer to nose) -> STABLE
    margin_mm = cg_tail - cp_from_tail
    margin_cal = margin_mm / D
    margin_pct = (margin_mm / D) * 100.0
    
    print(f"{name:<25} | {model.launch_mass_g:<10.2f}g | {cg_tail:<10.2f}mm | {cg_nose:<10.2f}mm | {margin_mm:<9.2f}mm | {margin_cal:<10.2f}cal | {margin_pct:<10.1f}%")
