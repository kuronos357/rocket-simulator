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

span = 45.9
cr = 30.6
res_opt = opt.evaluate_fins(span, cr, arrangement="symmetric_3fin")
print("res_opt (optimizer.py):")
print(f"  cg = {res_opt['cg_mm']}, cp = {res_opt['cp_mm']}, margin = {res_opt['margin_cal']}")

# Now let's trace evaluate_generalized_fins
ct = 0.0
sweep = cr - ct
mid_sweep = sweep + (ct - cr) / 2.0
Lf = (mid_sweep**2 + span**2)**0.5
D = 24.0
R = 12.0
k_body = 1.0 + R / (R + span)
denom = 1.0 + (1.0 + (2.0 * Lf / cr)**2)**0.5
cna_1pair = k_body * (4.0 * 2.0 * (span / D)**2) / denom
print(f"  cna_1pair = {cna_1pair}")
print(f"  cna_fins in opt = {1.5 * cna_1pair}")
cna_pitch_fins = (0.5**2 + (3**0.5 / 2)**2) # wait! What was cos^2(30 deg)?
print(f"  cos^2(30 deg) = {(3**0.5 / 2)**2}")
print(f"  cna_pitch_fins in gen = {(3**0.5 / 2)**2 * cna_1pair}")
