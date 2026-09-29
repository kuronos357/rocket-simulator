import sys
import os
sys.path.insert(0, os.path.abspath("."))
from sim_engine.optimizer import RocketSpec, FinOptimizer

# Test with L=330mm (JAR legal, 50% rule satisfied)
spec = RocketSpec(
    total_length_mm=330.0,
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
print("Running opt.optimize with arrangement='auto', target_margin_cal=1.20 for L=330mm:")
res = opt.optimize(target_margin_cal=1.20, arrangement="auto")
print("Result auto for L=330mm:")
if res:
    for k, v in res.items():
        print(f"  {k}: {v}")
else:
    print("None")
