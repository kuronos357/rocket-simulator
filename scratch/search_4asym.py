import sys, os
sys.path.insert(0, os.path.abspath('.'))
from sim_engine.optimizer import RocketSpec, FinOptimizer
from scratch.test_correct_physics import evaluate_physically_correct_fins

spec = RocketSpec(total_length_mm=250.0, body_diameter_mm=24.0, nose_length_mm=120.0,
                  tail_length_mm=0.0, wall_thickness_mm=0.4, infill_ratio=0.02,
                  material='PLA', material_density=1.24, motor_type='1/2A6-2',
                  ballast_mass_g=0.0, ballast_z_mm=245.0, recovery_mass_g=1.2,
                  recovery_area_cm2=250.0, recovery_cd=0.25, descent_horizontal=True)
opt = FinOptimizer(spec)

matches = []
for vs in [0.6, 0.7, 0.75, 0.8, 0.85, 0.9]:
    for span in range(35, 85):
        for cr in range(25, 60):
            if span > 1.8 * cr or span < 0.35 * cr:
                continue
            r = evaluate_physically_correct_fins(opt, float(span), float(cr), 0.0, 0.0, vs, is_4fin=True)
            m_eff = min(r['margin_pitch'], r['margin_yaw'])
            if 0.78 <= m_eff <= 0.82 and r['total_time_s'] >= 30.2:
                matches.append({**r, 'margin_eff': m_eff, 'span': span, 'cr': cr, 'vs': vs})

matches.sort(key=lambda x: abs(x['margin_eff'] - 0.80)*2 + abs(x['total_time_s'] - 30.48))
print(f"Total 4-fin-asym matches: {len(matches)}")
for m in matches[:10]:
    print(f"m_eff={m['margin_eff']:.3f}, pitch={m['margin_pitch']:.3f}, yaw={m['margin_yaw']:.3f}, time={m['total_time_s']:.2f}s, span={m['span']}, cr={m['cr']}, vs={m['vs']}, apogee={m['apogee_m']:.1f}m")
