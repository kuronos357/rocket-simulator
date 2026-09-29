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
print(f"cna_body_base = {opt.cna_body_base}, cp_body_base = {opt.cp_body_base}")
print(f"m_base_launch = {opt.m_base_launch}, z_base_cg = {opt.z_base_cg}")

# Let's inspect evaluate_fins in optimizer.py
res_opt = opt.evaluate_fins(span_mm=30.0, cr_mm=40.0, arrangement="airplane_3fin")
print("\noptimizer.py evaluate_fins:")
print(f"  cg = {res_opt['cg_mm']}, cp = {res_opt['cp_mm']}, margin = {res_opt['margin_cal']}")
print(f"  pitch_margin = {res_opt['pitch_margin_cal']}, yaw_margin = {res_opt['yaw_margin_cal']}")
