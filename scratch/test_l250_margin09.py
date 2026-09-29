import sys
import os
sys.path.insert(0, os.path.abspath("."))
from sim_engine.optimizer import RocketSpec, FinOptimizer
from scratch.test_correct_physics import evaluate_physically_correct_fins

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
    recovery_mass_g=1.2,
    recovery_area_cm2=250.0,
    recovery_cd=0.25,
    descent_horizontal=True
)
opt = FinOptimizer(spec)
best = None
for span in range(40, 90, 2):
    for cr in range(30, 70, 2):
        if span > 1.5 * cr or span < 0.3 * cr:
            continue
        r = evaluate_physically_correct_fins(opt, span, cr, 0.0, 30.0, 1.0, is_4fin=False)
        if r["margin_pitch"] >= 0.90 and r["margin_yaw"] >= 0.90:
            if best is None or r["total_time_s"] > best["total_time_s"]:
                best = r

if best:
    print("Target Margin >= 0.90 cal for L=250mm:")
    print(f"Best Time: {best['total_time_s']:.2f}s | Apogee: {best['apogee_m']:.1f}m | Span: {best['span']}x{best['cr']}mm | FinMass: {best['fin_mass_g']:.2f}g | PitchMar: {best['margin_pitch']:+.2f}, YawMar: {best['margin_yaw']:+.2f}")
else:
    print("No solution found for margin >= 0.90 cal.")
