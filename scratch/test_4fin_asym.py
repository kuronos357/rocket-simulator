import sys
import os
sys.path.insert(0, os.path.abspath("."))
from sim_engine.optimizer import RocketSpec, FinOptimizer
from scratch.test_correct_physics import evaluate_physically_correct_fins

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

print("Testing 4-fin (+) with various vertical fin scale ratios (v_scale):")
for vs in [0.6, 0.7, 0.8, 0.9, 1.0]:
    best = None
    for span in range(35, 75, 1):
        for cr in range(25, 60, 1):
            if span > 1.5 * cr or span < 0.3 * cr:
                continue
            r = evaluate_physically_correct_fins(opt, span, cr, 0.0, 0.0, vs, is_4fin=True)
            if r["margin_pitch"] >= 1.20 and r["margin_yaw"] >= 1.20:
                if best is None or r["total_time_s"] > best["total_time_s"]:
                    best = r
    if best:
        print(f"v_scale={vs:3.1f} -> Best Time: {best['total_time_s']:.2f}s | Apogee: {best['apogee_m']:.1f}m | H_span={best['span']}mm, H_cr={best['cr']}mm, V_span={best['span']*vs:.1f}mm | Fin Mass: {best['fin_mass_g']:.2f}g | P_mar={best['margin_pitch']:+.2f}, Y_mar={best['margin_yaw']:+.2f}")
