import sys
import os
sys.path.insert(0, os.path.abspath("."))
from sim_engine.optimizer import RocketSpec, FinOptimizer

# Test with tsukuba rocket spec
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
print("Running opt.optimize with arrangement='auto', target_margin_cal=1.20:")
res = opt.optimize(target_margin_cal=1.20, arrangement="auto")
print("Result auto:", res)

print("\nRunning opt.optimize with arrangement='symmetric_3fin', target_margin_cal=1.20:")
res3 = opt.optimize(target_margin_cal=1.20, arrangement="symmetric_3fin")
print("Result 3fin:", res3)
