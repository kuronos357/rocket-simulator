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
    recovery_mass_g=1.2,
    recovery_area_cm2=250.0,
    recovery_cd=0.25,
    descent_horizontal=True
)
opt = FinOptimizer(spec)

print("3-fin sweep:")
for th in [0, 10, 20, 30, 40]:
    for vs in [0.5, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0]:
        r = evaluate_physically_correct_fins(opt, 75, 45, 0.0, float(th), vs, is_4fin=False)
        print(f"th={th:2d} deg, vs={vs:3.1f} -> Pitch_mar={r['margin_pitch']:+.2f}, Yaw_mar={r['margin_yaw']:+.2f}, FinMass={r['fin_mass_g']:.2f}g, Time={r['total_time_s']:.2f}s")
