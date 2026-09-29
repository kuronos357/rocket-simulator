import sys
import os
sys.path.insert(0, os.path.abspath("."))
from sim_engine.optimizer import RocketSpec, FinOptimizer

# Compare 3-fin vs 4-fin on the optimal 280mm body
spec = RocketSpec(
    total_length_mm=280.0,
    body_diameter_mm=24.0,
    nose_length_mm=110.0,
    tail_length_mm=0.0,
    wall_thickness_mm=0.4,
    infill_ratio=0.02,
    material="PLA",
    material_density=1.24,
    motor_type="1/2A6-2",
    recovery_mass_g=0.5,
    recovery_area_cm2=62.5,
    recovery_cd=0.25,
    descent_horizontal=True
)
opt = FinOptimizer(spec)

print("Comparison on L=280mm, Nose=110mm body (Target Margin = +1.20 cal):")

for arr in ["auto", "airplane_3fin", "symmetric_3fin", "symmetric_4fin"]:
    res = opt.optimize(target_margin_cal=1.20, arrangement=arr)
    if res:
        th = res['theta_deg']
        vs = res['v_scale']
        is4 = res['is_4fin']
        print(f"\nConfiguration: {arr}")
        print(f"  Type: {'4-fin' if is4 else '3-fin'}, theta={th:.1f}°, v_scale={vs:.2f}")
        print(f"  Main Fin: span={res['span_mm']}mm, cr={res['root_chord_mm']}mm (Fin mass: {res['fin_mass_g']:.2f}g)")
        if res.get('v_span_mm'):
            print(f"  Vert Fin: span={res['v_span_mm']}mm, cr={res['v_cr_mm']}mm")
        print(f"  Mass: {res['total_mass_g']:.1f}g | CG: {res['cg_mm']:.1f}mm, CP: {res['cp_mm']:.1f}mm")
        print(f"  Pitch Margin: {res['pitch_margin_cal']:+.2f}cal, Yaw Margin: {res['yaw_margin_cal']:+.2f}cal")
        print(f"  Apogee: {res['apogee_m']:.1f}m, Hang Time: {res['total_flight_time_s']:.2f}s, Descent V: {res['v_descent_m_s']:.2f}m/s")
    else:
        print(f"\nConfiguration: {arr} -> No solution")
