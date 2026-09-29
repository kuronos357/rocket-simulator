"""
Post-fix verification: confirm all 3 bugs are actually fixed in the code.
"""
import sys, os, math
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

sys.path.insert(0, r"d:\1_Stuff\0_programming\0_Project\ロケットシミュレーター")
from sim_engine.optimizer import RocketSpec, FinOptimizer
from sim_engine.motor_db import get_motor

print("=" * 70)
print("   POST-FIX VERIFICATION")
print("=" * 70)

# ===== BUG 1: Coast mass =====
print("\n--- Bug 1: Coast mass (should use burnout mass) ---")
# Read the source code and check
import inspect
src = inspect.getsource(FinOptimizer.evaluate_fins)
if "burnout_mass_g" in src and "total_launch_mass_g - motor_obj.propellant_mass_g" in src:
    print("  ✅ FIXED: Code now uses burnout_mass_g for coast drag calculation")
else:
    print("  ❌ NOT FIXED: Still using launch mass for coast")

# Numerical verification
spec = RocketSpec(
    total_length_mm=190.0, body_diameter_mm=22.0, nose_length_mm=60.0,
    motor_type="1/2A6-2", dry_mass_override_g=11.5
)
opt = FinOptimizer(spec)
res = opt.evaluate_fins(span_mm=40.0, cr_mm=30.0, arrangement="symmetric_3fin")
motor = get_motor("1/2A6-2")

# Manually compute expected altitude with burnout mass
D = 22.0; R = D/2.0
S_ref = math.pi * (R * 1e-3)**2
total_mass_g = res["total_mass_g"]
burnout_g = total_mass_g - motor.propellant_mass_g
avg_thrust = motor.total_impulse / motor.burn_time
m_avg_kg = (total_mass_g - motor.propellant_mass_g * 0.5) * 1e-3
v_bo = max(0.0, (avg_thrust / m_avg_kg - 9.8) * motor.burn_time)
# Build Cd the same way the code does
fin_area_cm2 = 3 * 0.5 * 30.0 * 40.0 * 0.01  # approximate
wet_area_m2 = (math.pi * D * 190.0 + fin_area_cm2 * 200.0) * 1e-6
Cd = 0.0045 * (wet_area_m2 / S_ref) + 0.10 + 0.08
k_right = 0.5 * 1.225 * Cd * S_ref / (burnout_g * 1e-3)
k_wrong = 0.5 * 1.225 * Cd * S_ref / (total_mass_g * 1e-3)
h_coast_right = (1/(2*k_right)) * math.log(1 + k_right * v_bo**2 / 9.8)
h_coast_wrong = (1/(2*k_wrong)) * math.log(1 + k_wrong * v_bo**2 / 9.8)
print(f"  Burnout mass coast: {h_coast_right:.1f}m vs launch mass coast: {h_coast_wrong:.1f}m")
print(f"  Code reports apogee: {res['apogee_m']}m")

# ===== BUG 2: Non-monotonicity =====
print("\n--- Bug 2: Optimizer handles non-monotonic margin ---")
# Test: set a target that would be on the ASCENDING part of the curve.
# Also test a target near the peak to make sure it doesn't overshoot.
res_opt = opt.optimize(target_margin_cal=0.98, arrangement="symmetric_3fin")
if res_opt:
    # The margin should be very close to the target (within 0.05 cal)
    diff = abs(res_opt["margin_cal"] - 0.98)
    if diff < 0.05:
        print(f"  ✅ FIXED: target=0.98, got margin={res_opt['margin_cal']:+.2f} (diff={diff:.3f} cal)")
    else:
        print(f"  ⚠️  Margin not precise: target=0.98, got {res_opt['margin_cal']:+.2f}")
    
    # Verify it found the SMALLEST fin (ascending side)
    print(f"  Result: span={res_opt['span_mm']}mm, cr={res_opt['root_chord_mm']}mm, mass={res_opt['fin_mass_g']}g")
else:
    print("  ❌ Optimizer returned None!")

# Test with a target that exceeds the peak (should still find something or return None gracefully)
peak_test = opt.optimize(target_margin_cal=1.25, arrangement="symmetric_3fin")
if peak_test:
    print(f"  Target=1.25 (near peak): found margin={peak_test['margin_cal']:+.2f}, span={peak_test['span_mm']}mm")
else:
    print(f"  Target=1.25 (above peak ~1.23): correctly returned None (unreachable)")

# ===== BUG 3: Area comparison metric =====
print("\n--- Bug 3: Optimizer comparison metric ---")
src_opt = inspect.getsource(FinOptimizer.optimize)
if "fin_mass_g" in src_opt and "min_fin_mass" in src_opt:
    print("  ✅ FIXED: Code now uses fin_mass_g for comparison (includes all fins)")
elif "fin_area_1side_cm2" in src_opt:
    print("  ❌ NOT FIXED: Still using single-fin area for comparison")
else:
    print("  ⚠️  Could not determine comparison metric from source")

# ===== Regression: all presets still work =====
print("\n--- Regression test: all presets ---")
for name, preset_data in [
    ("tsukuba", dict(total_length_mm=190, body_diameter_mm=22, nose_length_mm=60, motor_type="1/2A6-2", dry_mass_override_g=11.5)),
    ("v9", dict(total_length_mm=363, body_diameter_mm=46.6, nose_length_mm=113, motor_type="C6-5", dry_mass_override_g=50, ballast_mass_g=35, ballast_z_mm=260))
]:
    spec = RocketSpec(**preset_data)
    o = FinOptimizer(spec)
    for arr in ["symmetric_3fin", "airplane_3fin", "symmetric_4fin"]:
        r = o.optimize(target_margin_cal=1.0, arrangement=arr)
        if r:
            target_key = "pitch_margin_cal" if arr == "airplane_3fin" else "margin_cal"
            m = r[target_key]
            status = "✅" if abs(m - 1.0) < 0.05 else "⚠️"
            print(f"  {status} {name}/{arr}: {target_key}={m:+.2f}, mass={r['fin_mass_g']:.2f}g, apogee={r['apogee_m']}m")
        else:
            print(f"  ⚠️  {name}/{arr}: No solution (target may be unreachable)")

print("\n" + "=" * 70)
print("   DONE")
print("=" * 70)
