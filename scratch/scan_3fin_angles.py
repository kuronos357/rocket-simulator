import sys
import os
sys.path.insert(0, os.path.abspath("."))
from sim_engine.optimizer import RocketSpec, FinOptimizer
from scratch.test_correct_physics import evaluate_physically_correct_fins

spec = RocketSpec(
    total_length_mm=250.0,
    body_diameter_mm=24.0,
    nose_length_mm=105.0,
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

print("Testing 3-fin with different angles theta:")
for th in [0, 10, 15, 20, 25, 30, 35, 40]:
    best = None
    for vs in [0.5, 0.6, 0.7, 0.8, 1.0, 1.2, 1.4, 1.6]:
        for span in range(40, 95, 2):
            for cr in range(25, 65, 2):
                if span > 1.8 * cr or span < 0.35 * cr:
                    continue
                r = evaluate_physically_correct_fins(opt, float(span), float(cr), 0.0, float(th), vs, is_4fin=False)
                if r["margin_pitch"] >= 0.80 and r["margin_yaw"] >= 0.70:
                    if best is None or r["total_time_s"] > best["total_time_s"]:
                        best = {**r, "th": th, "vs": vs}
    if best:
        print(f"theta={th:2d} deg, vs={best['vs']:.2f} -> Time={best['total_time_s']:.2f}s | Apogee={best['apogee_m']:.1f}m | FinMass={best['fin_mass_g']:.2f}g | H={best['span']}x{best['cr']}mm, V={best['span']*best['vs']:.1f}mm | P_mar={best['margin_pitch']:+.2f}, Y_mar={best['margin_yaw']:+.2f}")
    else:
        print(f"theta={th:2d} deg -> No solution with Pitch>=0.80, Yaw>=0.70")
