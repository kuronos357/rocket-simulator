import sys, time
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass
sys.path.insert(0, r"d:\1_Stuff\0_programming\0_Project\ロケットシミュレーター")
from sim_engine.optimizer import RocketSpec, FinOptimizer

configs = [
    ("tsukuba/sym3", dict(total_length_mm=190, body_diameter_mm=22, nose_length_mm=60, motor_type="1/2A6-2", dry_mass_override_g=11.5), "symmetric_3fin"),
    ("tsukuba/airplane", dict(total_length_mm=190, body_diameter_mm=22, nose_length_mm=60, motor_type="1/2A6-2", dry_mass_override_g=11.5), "airplane_3fin"),
    ("v9/sym3", dict(total_length_mm=363, body_diameter_mm=46.6, nose_length_mm=113, motor_type="C6-5", dry_mass_override_g=50, ballast_mass_g=35, ballast_z_mm=260), "symmetric_3fin"),
    ("v9/airplane", dict(total_length_mm=363, body_diameter_mm=46.6, nose_length_mm=113, motor_type="C6-5", dry_mass_override_g=50, ballast_mass_g=35, ballast_z_mm=260), "airplane_3fin"),
]

for name, kw, arr in configs:
    spec = RocketSpec(**kw)
    opt = FinOptimizer(spec)
    t0 = time.perf_counter()
    r = opt.optimize(target_margin_cal=1.0, arrangement=arr)
    dt = time.perf_counter() - t0
    if r:
        mk = "pitch_margin_cal" if arr == "airplane_3fin" else "margin_cal"
        print(f"{name:20s}  {dt:.3f}s  span={r['span_mm']:5.1f} cr={r['root_chord_mm']:5.1f}  mass={r['fin_mass_g']:.2f}g  {mk}={r[mk]:+.2f}")
    else:
        print(f"{name:20s}  {dt:.3f}s  NO SOLUTION")
