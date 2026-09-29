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
    recovery_mass_g=0.5,
    recovery_area_cm2=62.5,
    recovery_cd=0.25,
    descent_horizontal=True
)
opt = FinOptimizer(spec)

max_mar = -999
best_r = None
for span in range(20, 100, 5):
    for cr in range(20, 100, 5):
        r = evaluate_physically_correct_fins(opt, span, cr, 0.0, 30.0, 1.0, is_4fin=False)
        if r["margin_eff"] > max_mar:
            max_mar = r["margin_eff"]
            best_r = r

print(f"Max margin for 3-fin 30deg: {max_mar:.3f}")
print("Best r:", best_r)
