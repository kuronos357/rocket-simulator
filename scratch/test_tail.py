import sys
import os
sys.path.insert(0, os.path.abspath("."))
from sim_engine.optimizer import RocketSpec, FinOptimizer
from scratch.test_correct_physics import evaluate_physically_correct_fins

print("Testing Boat Tail (tail_length_mm = 20mm):")
for L in [250.0, 280.0, 300.0]:
    for tail_len in [0.0, 15.0, 25.0]:
        # Check JAR 50% rule: (L - N - T) >= 0.50 * L
        nose_len = 60.0
        if (L - nose_len - tail_len) < 0.50 * L:
            continue
        spec = RocketSpec(
            total_length_mm=L,
            body_diameter_mm=24.0,
            nose_length_mm=nose_len,
            tail_length_mm=tail_len,
            wall_thickness_mm=0.4,
            infill_ratio=0.02,
            material="PLA",
            material_density=1.24,
            motor_type="1/2A6-2",
            ballast_mass_g=0.0,
            recovery_mass_g=0.5,
            recovery_area_cm2=62.5,
            recovery_cd=0.25,
            descent_horizontal=True
        )
        opt = FinOptimizer(spec)
        best = None
        for span in range(15, 65, 2):
            for cr in range(20, 65, 2):
                if span > 1.5 * cr or span < 0.3 * cr:
                    continue
                r = evaluate_physically_correct_fins(opt, span, cr, 0.0, 30.0, 1.0, is_4fin=False)
                if r["margin_eff"] >= 1.20:
                    if best is None or r["fin_mass_g"] < best["fin_mass_g"]:
                        best = r
        if best:
            print(f"L={L:3.0f}mm, Tail={tail_len:2.0f}mm -> CG={opt.z_base_cg:5.1f}mm, cna_body={opt.cna_body_base:.2f} | Best Fin: span={best['span']}, cr={best['cr']} (mass={best['fin_mass_g']:.2f}g) | Apogee={best['apogee_m']:.1f}m, Time={best['total_time_s']:.2f}s")
        else:
            print(f"L={L:3.0f}mm, Tail={tail_len:2.0f}mm -> CG={opt.z_base_cg:5.1f}mm, cna_body={opt.cna_body_base:.2f} | No solution in span<=65mm")
