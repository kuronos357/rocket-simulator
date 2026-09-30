import sys, os
sys.path.insert(0, os.path.abspath("."))
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

# Let's finely sweep span and cr for 4-fin symmetric (vs=1.0)
pts = []
for span in range(35, 75, 2):
    for cr in range(20, 50, 2):
        if span > 1.8 * cr or span < 0.35 * cr:
            continue
        r = evaluate_physically_correct_fins(opt, float(span), float(cr), 0.0, 0.0, 1.0, is_4fin=True)
        m = min(r["margin_pitch"], r["margin_yaw"])
        pts.append((m, r["total_time_s"], span, cr, r["apogee_m"], r["total_mass_g"]))

pts.sort(key=lambda x: x[0])
print("Margin, Time, Span, Cr, Apogee, Mass")
for p in pts:
    if 0.70 <= p[0] <= 1.00:
        print(f"Margin={p[0]:.3f}, Time={p[1]:.3f}s, span={p[2]}, cr={p[3]}, apo={p[4]:.1f}m, mass={p[5]:.2f}g")
