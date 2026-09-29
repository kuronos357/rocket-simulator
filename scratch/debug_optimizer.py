import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from sim_engine.optimizer import RocketSpec, FinOptimizer

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

spec = RocketSpec(
    total_length_mm=190.0,
    body_diameter_mm=22.0,
    nose_length_mm=60.0,
    motor_type='1/2A6-2',
    dry_mass_override_g=11.5
)
opt = FinOptimizer(spec)
print(f"Base launch mass: {opt.m_base_launch:.1f}g, CG: {opt.z_base_cg:.1f}mm")

for s in [30.0, 40.0, 50.0, 60.0, 70.0]:
    cr = s
    eval_res = opt.evaluate_fins(s, cr, arrangement='airplane_3fin', shape_type='trapezoid', taper_ratio=0.0)
    print(f"s={s:4.1f}mm, cr={cr:4.1f}mm -> Pitch margin: {eval_res['pitch_margin_cal']:+.2f} cal, Total margin: {eval_res['margin_cal']:+.2f} cal, CG: {eval_res['cg_mm']:.1f}mm, CP: {eval_res['cp_mm']:.1f}mm")

# optimize を実行して内部トレース
res = opt.optimize(target_margin_cal=1.0, arrangement='airplane_3fin', shape_type='trapezoid', taper_ratio=0.0)
print("Optimizer result:", res)
