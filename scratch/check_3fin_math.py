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

# Check theta=30, v_scale=1.0 with span=45.9, cr=30.6
r = evaluate_generalized_fins(opt, span_mm=45.9, cr_mm=30.6, taper_ratio=0.0, theta_deg=30.0, v_scale=1.0, is_4fin=False)
print("theta=30, v_scale=1.0 (span=45.9, cr=30.6):")
print(f"  margin_pitch = {r['margin_pitch']}")
print(f"  margin_yaw = {r['margin_yaw']}")
print(f"  margin_eff = {r['margin_eff']}")
