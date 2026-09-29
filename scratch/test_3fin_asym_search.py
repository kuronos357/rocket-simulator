import sys
import os
sys.path.insert(0, os.path.abspath("."))
from sim_engine.optimizer import RocketSpec, FinOptimizer
from scratch.test_correct_physics import evaluate_physically_correct_fins

def check_3fin_asymmetry():
    print("=" * 80)
    print("CHECKING 3-FIN ASYMMETRIC CONFIGURATIONS (T-tail, Inverted-Y, V-tail with kv != 1.0)")
    print("=" * 80)

    spec = RocketSpec(
        total_length_mm=250.0,
        body_diameter_mm=24.0,
        nose_length_mm=105.0,
        tail_length_mm=0.0,
        wall_thickness_mm=0.4,
        infill_ratio=0.02,
        material="PLA",
        material_density=1.24,
        motor_type="1/2A6-2",
        recovery_mass_g=1.2,
        recovery_area_cm2=250.0,
        recovery_cd=0.25,
        descent_horizontal=True
    )
    opt = FinOptimizer(spec)

    # 3-fin setup: 2 lower dihedral fins at angle theta from horizontal, 1 upper vertical fin scaled by kv
    # Scan theta in [0, 10, 20, 30, 40] and kv in [0.5, 0.6, 0.7, 0.8, 1.0, 1.2, 1.5]
    valid_3fin = []

    for th in [0.0, 10.0, 20.0, 30.0, 40.0]:
        for vs in [0.5, 0.6, 0.7, 0.8, 1.0, 1.2, 1.5]:
            for span in range(40, 95, 2):
                for cr in range(25, 65, 2):
                    if span > 1.8 * cr or span < 0.35 * cr:
                        continue
                    r = evaluate_physically_correct_fins(opt, float(span), float(cr), 0.0, th, vs, is_4fin=False)
                    # Check if it satisfies flyable stability (e.g. pitch >= 0.8 and yaw >= 0.7)
                    if r["margin_pitch"] >= 0.80 and r["margin_yaw"] >= 0.70:
                        valid_3fin.append({
                            **r,
                            "th": th,
                            "vs": vs,
                            "is_asym": (th != 30.0 or vs != 1.0)
                        })

    print(f"Total stable 3-fin designs found: {len(valid_3fin)}")
    asym_3fin = [c for c in valid_3fin if c["is_asym"]]
    sym_3fin = [c for c in valid_3fin if not c["is_asym"]]
    print(f"  - Symmetric (theta=30 deg, kv=1.0): {len(sym_3fin)}")
    print(f"  - Asymmetric (theta!=30 deg or kv!=1.0): {len(asym_3fin)}")

    # Sort asymmetric 3-fin by hang time
    asym_sorted = sorted(asym_3fin, key=lambda x: x["total_time_s"], reverse=True)
    sym_sorted = sorted(sym_3fin, key=lambda x: x["total_time_s"], reverse=True)

    print("\nTOP 5 SYMMETRIC 3-FIN (theta=30 deg, kv=1.0):")
    for i, c in enumerate(sym_sorted[:5]):
        print(f"  #{i+1}: Span={c['span']}x{c['cr']}mm | PitchMar={c['margin_pitch']:+.2f}, YawMar={c['margin_yaw']:+.2f} | Mass={c['total_mass_g']:.1f}g | Apogee={c['apogee_m']:.1f}m | Time={c['total_time_s']:.2f}s")

    print("\nTOP 5 ASYMMETRIC 3-FIN (theta!=30 deg or kv!=1.0):")
    for i, c in enumerate(asym_sorted[:5]):
        print(f"  #{i+1}: theta={c['th']:.0f}°, kv={c['vs']:.2f} | H-Span={c['span']}x{c['cr']}mm, V-Span={c['span']*c['vs']:.1f}mm | PitchMar={c['margin_pitch']:+.2f}, YawMar={c['margin_yaw']:+.2f} | Mass={c['total_mass_g']:.1f}g | Apogee={c['apogee_m']:.1f}m | Time={c['total_time_s']:.2f}s")

if __name__ == "__main__":
    check_3fin_asymmetry()
