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

r = evaluate_generalized_fins(opt, span_mm=30.0, cr_mm=40.0, taper_ratio=0.0, theta_deg=0.0, v_scale=0.8)
print("Span=30, Cr=40, Theta=0, v_scale=0.8:")
for k, v in r.items():
    print(f"  {k}: {v}")
