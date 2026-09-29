import sys, time
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

sys.path.insert(0, r"d:\1_Stuff\0_programming\0_Project\ロケットシミュレーター")
from sim_engine.optimizer import RocketSpec, FinOptimizer

def test_taper():
    print("=== Taper Ratio Optimization Test ===")
    spec = RocketSpec(
        total_length_mm=190.0, body_diameter_mm=22.0, nose_length_mm=60.0,
        motor_type="1/2A6-2", dry_mass_override_g=11.5
    )
    opt = FinOptimizer(spec)
    
    taper_candidates = [0.0, 0.25, 0.5, 0.75, 1.0]
    
    print("1. Testing individual tapers...")
    for tr in taper_candidates:
        r = opt.optimize(target_margin_cal=1.0, arrangement="symmetric_3fin", taper_ratio=tr)
        if r:
            print(f"  Taper={tr:4.2f} -> Span={r['span_mm']:5.1f}, Cr={r['root_chord_mm']:5.1f}, Ct={r['tip_chord_mm']:5.1f}, Mass={r['fin_mass_g']:.3f}g")
        else:
            print(f"  Taper={tr:4.2f} -> NO SOLUTION")
            
    print("\n2. Testing combined 3D search...")
    t0 = time.perf_counter()
    best = opt.optimize(target_margin_cal=1.0, arrangement="symmetric_3fin", taper_ratio=taper_candidates)
    t1 = time.perf_counter()
    
    if best:
        print(f"  Best found in {t1-t0:.3f}s:")
        print(f"  Taper={best['tip_chord_mm']/best['root_chord_mm'] if best['root_chord_mm']>0 else 0:4.2f}")
        print(f"  Span={best['span_mm']:5.1f}, Cr={best['root_chord_mm']:5.1f}, Ct={best['tip_chord_mm']:5.1f}, Mass={best['fin_mass_g']:.3f}g")
    else:
        print("  NO SOLUTION IN COMBINED")

if __name__ == "__main__":
    test_taper()
