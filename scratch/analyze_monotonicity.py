"""
More detailed analysis of the non-monotonicity issue.
"""
import sys, os, math
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

sys.path.insert(0, r"d:\1_Stuff\0_programming\0_Project\ロケットシミュレーター")
from sim_engine.optimizer import RocketSpec, FinOptimizer

spec = RocketSpec(
    total_length_mm=190.0, body_diameter_mm=22.0, nose_length_mm=60.0,
    motor_type="1/2A6-2", dry_mass_override_g=11.5
)
opt = FinOptimizer(spec)
D = spec.body_diameter_mm

print("=== Non-monotonicity analysis: symmetric_3fin, ratio=0.8 ===")
print(f"{'span':>6} {'cr':>6} {'fin_mass':>9} {'CG':>7} {'CP':>7} {'margin':>8} {'cna_fins':>9} {'cna_eff':>8}")
for span in range(15, 85, 5):
    cr = span / 0.8
    res = opt.evaluate_fins(span_mm=span, cr_mm=cr, arrangement="symmetric_3fin")
    
    # Reconstruct internals for analysis
    R = D / 2.0
    ct = 0.0
    sweep = cr - ct
    mid_sweep = sweep / 2.0
    Lf = math.sqrt(mid_sweep**2 + span**2)
    k_body = 1.0 + R / (R + span)
    denom = 1.0 + math.sqrt(1.0 + (2.0 * Lf / (cr + ct))**2) if (cr + ct) > 0 else 2.0
    cna_1pair = k_body * (4.0 * 2.0 * (span / D)**2) / denom
    cna_fins = 1.5 * cna_1pair
    cna_eff = opt.cna_body_base + cna_fins
    
    print(f"{span:6d} {cr:6.1f} {res['fin_mass_g']:9.2f} {res['cg_mm']:7.1f} {res['cp_mm']:7.1f} {res['margin_cal']:+8.2f} {cna_fins:9.3f} {cna_eff:8.3f}")

print("\n=== Analysis ===")
print("The non-monotonicity is caused by fin mass pulling CG toward tail")
print("faster than fin CNα can pull CP toward tail, at large fin sizes.")
print("This is physical: very large fins are heavy and shift CG backward more")
print("than they shift CP backward.")
print("\nThe binary search assumes monotonicity which breaks here.")
print("Fix: use scipy.optimize or bounded search that handles non-monotonicity.")
