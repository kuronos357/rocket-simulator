import sys
import os
sys.path.insert(0, os.path.abspath("."))
from sim_engine.optimizer import RocketSpec, FinOptimizer

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
res = opt.optimize(target_margin_cal=1.2, arrangement="symmetric_3fin")
print("optimize result symmetric_3fin:", res)
res4 = opt.optimize(target_margin_cal=1.2, arrangement="symmetric_4fin")
print("optimize result symmetric_4fin:", res4)
res_air = opt.optimize(target_margin_cal=1.2, arrangement="airplane_3fin")
print("optimize result airplane_3fin:", res_air)
