import sys, os
sys.path.insert(0, os.path.abspath('.'))
from sim_engine.optimizer import RocketSpec, FinOptimizer
from scratch.test_correct_physics import evaluate_physically_correct_fins

spec = RocketSpec(
    total_length_mm=250.0,
    body_diameter_mm=24.0,
    nose_length_mm=120.0,
    tail_length_mm=0.0,
    wall_thickness_mm=0.4,
    infill_ratio=0.02,
    material="PLA",
    material_density=1.24,
    motor_type="1/2A6-2",
    ballast_mass_g=0.0,
    ballast_z_mm=245.0,
    recovery_mass_g=1.2,
    recovery_area_cm2=250.0,
    recovery_cd=0.25,
    descent_horizontal=True
)
opt = FinOptimizer(spec)

# Compare best 4-fin sym vs best 3-fin (sym and asym) around margin 0.90-0.94
for name, is_4fin, theta, vs in [
    ('4-fin sym (+)', True, 0.0, 1.0),
    ('4-fin asym (cross)', True, 0.0, 0.85),
    ('3-fin sym (120)', False, 30.0, 1.0),
    ('3-fin asym (Y 35)', False, 35.0, 0.7)
]:
    best = None
    for span in range(35, 80, 2):
        for cr in range(20, 50, 2):
            if span > 1.8 * cr or span < 0.35 * cr:
                continue
            r = evaluate_physically_correct_fins(opt, float(span), float(cr), 0.0, float(theta), vs, is_4fin=is_4fin)
            m = min(r['margin_pitch'], r['margin_yaw'])
            if 0.90 <= m <= 0.94:
                if best is None or r['total_time_s'] > best['total_time_s']:
                    best = r
    if best:
        t = best['total_time_s']
        m = best['margin_eff']
        sp = best['span']
        cr = best['cr']
        fm = best['fin_mass_g']
        print(f"{name:20s}: Time={t:.3f}s, Margin={m:.3f}, span={sp}, cr={cr}, fin_mass={fm:.2f}g")
