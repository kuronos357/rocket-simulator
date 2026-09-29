import sys
import os
sys.path.insert(0, os.path.abspath("."))
from sim_engine.optimizer import RocketSpec, FinOptimizer
from scratch.test_generalized_fins import evaluate_generalized_fins

spec = RocketSpec(
    total_length_mm=250.0,
    body_diameter_mm=24.0,
    nose_length_mm=60.0,
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

print("--- Testing 3-fin (theta variable, v_scale variable) ---")
# 3 fins: 2 side fins at angle theta from horizontal, 1 vertical fin
for th in [0.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0]:
    for vs in [0.6, 0.8, 1.0, 1.2, 1.4]:
        best = None
        for span in range(20, 75, 1):
            for cr in range(20, 75, 1):
                if span > 1.5 * cr or span < 0.3 * cr:
                    continue
                r = evaluate_generalized_fins(opt, span, cr, 0.0, th, vs, is_4fin=False)
                if r["margin_pitch"] >= 1.20 and r["margin_yaw"] >= 1.20:
                    if best is None or r["fin_mass_g"] < best["fin_mass_g"]:
                        best = r
        if best:
            print(f"3-fin theta={th:4.1f}°, v_scale={vs:3.1f} -> MinMass: {best['fin_mass_g']:.2f}g (span={best['span']}, cr={best['cr']}) | Apogee: {best['apogee_m']:.1f}m, Time: {best['total_time_s']:.2f}s | P_mar={best['margin_pitch']:+.2f}, Y_mar={best['margin_yaw']:+.2f}")

print("\n--- Testing 4-fin (+ shape, theta=0, v_scale variable) ---")
# 4 fins: 2 horizontal wings at theta=0, 2 vertical fins at v_scale
for vs in [0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
    best = None
    for span in range(20, 75, 1):
        for cr in range(20, 75, 1):
            if span > 1.5 * cr or span < 0.3 * cr:
                continue
            r = evaluate_generalized_fins(opt, span, cr, 0.0, vs, is_4fin=True)
            if r["margin_pitch"] >= 1.20 and r["margin_yaw"] >= 1.20:
                if best is None or r["fin_mass_g"] < best["fin_mass_g"]:
                    best = r
    if best:
        print(f"4-fin (+) v_scale={vs:3.1f} -> MinMass: {best['fin_mass_g']:.2f}g (h_span={best['span']}, h_cr={best['cr']}, v_span={best['span']*vs:.1f}) | Apogee: {best['apogee_m']:.1f}m, Time: {best['total_time_s']:.2f}s | P_mar={best['margin_pitch']:+.2f}, Y_mar={best['margin_yaw']:+.2f}")
