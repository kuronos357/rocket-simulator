import sys
import os
import numpy as np

sys.path.insert(0, os.path.abspath("."))
from sim_engine.optimizer import RocketSpec, FinOptimizer
from scratch.test_correct_physics import evaluate_physically_correct_fins

def run_investigation():
    print("=" * 80)
    print("INVESTIGATION: WHEN AND WHY DOES AN UNBALANCED FIN CONFIGURATION BECOME ADVANTAGEOUS?")
    print("=" * 80)

    # Base specification (JAR regulation compliant, 50x500mm streamer)
    spec_500 = RocketSpec(
        total_length_mm=280.0,
        body_diameter_mm=24.0,
        nose_length_mm=110.0,
        tail_length_mm=0.0,
        wall_thickness_mm=0.4,
        infill_ratio=0.02,
        material="PLA",
        material_density=1.24,
        motor_type="1/2A6-2",
        recovery_mass_g=1.2,
        recovery_area_cm2=250.0, # 50x500mm
        recovery_cd=0.25,
        descent_horizontal=True
    )
    opt_500 = FinOptimizer(spec_500)

    # -------------------------------------------------------------
    # 1. MATHEMATICAL PROOF FOR 3-FIN (Why 120 deg is optimal under symmetric constraint)
    # -------------------------------------------------------------
    print("\n--- 1. Mathematical Analysis of 3-Fin Geometry (Total Area Minimization) ---")
    print("For 3 fins (1 vertical fin Sv, 2 dihedral fins Sh at angle theta from horizontal):")
    print("Pitch restoring force ~ 2 * Sh * cos^2(theta)")
    print("Yaw restoring force   ~ Sv + 2 * Sh * sin^2(theta)")
    print("To satisfy Pitch >= Target (say 1.5 units) and Yaw >= Target (1.5 units):")
    print("Sh >= 1.5 / (2 * cos^2(theta))")
    print("Sv >= 1.5 - 2 * Sh * sin^2(theta) = 1.5 * (1 - tan^2(theta))  [if theta <= 45 deg, else Sv=0]")
    print("Total Area S_total = 2*Sh + Sv:")
    for th in [0, 10, 20, 30, 35, 45, 55]:
        rad = np.radians(th)
        cos2 = np.cos(rad)**2
        sin2 = np.sin(rad)**2
        # Required Sh to meet Pitch target = 1.5
        req_Sh = 1.5 / (2.0 * cos2)
        # Required Sv to meet Yaw target = 1.5
        req_Sv = max(0.0, 1.5 - 2.0 * req_Sh * sin2)
        total_S = 2.0 * req_Sh + req_Sv
        kv = (req_Sv / req_Sh) if req_Sh > 0 else 0
        print(f"  theta = {th:2d} deg: Sh = {req_Sh:5.3f}, Sv = {req_Sv:5.3f}, Total Fin Area = {total_S:5.3f}, Area Ratio Sv/Sh = {kv:5.3f}")

    # -------------------------------------------------------------
    # 2. SCENARIO A: ASYMMETRIC STABILITY REQUIREMENT (Airplane / Rocket-Plane Mode)
    # -------------------------------------------------------------
    print("\n--- 2. Scenario A: Asymmetric Stability Requirements (Pitch >= 1.20 cal, Yaw relaxed) ---")
    print("In vertical launch, rockets do not need 1.2 cal in Yaw if weathercocking in yaw is acceptable.")
    print("What if Yaw requirement is relaxed (1.20, 1.00, 0.80, 0.60 cal) while Pitch stays >= 1.20 cal?")

    yaw_targets = [1.20, 1.00, 0.80, 0.60]
    for target_yaw in yaw_targets:
        best = None
        for vs in [0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
            for span in range(35, 75, 2):
                for cr in range(25, 60, 2):
                    if span > 1.5 * cr or span < 0.3 * cr:
                        continue
                    r = evaluate_physically_correct_fins(opt_500, span, cr, 0.0, 0.0, vs, is_4fin=True)
                    if r["margin_pitch"] >= 1.20 and r["margin_yaw"] >= target_yaw:
                        if best is None or r["total_time_s"] > best["total_time_s"]:
                            best = r
                            best["vs"] = vs
        if best:
            print(f"  Target Yaw >= {target_yaw:.2f} cal: Optimal v_scale = {best['vs']:.2f} | Time: {best['total_time_s']:.2f}s | Apogee: {best['apogee_m']:.1f}m | Fin Mass: {best['fin_mass_g']:.2f}g | H_span={best['span']}mm, V_span={best['span']*best['vs']:.1f}mm | P_mar={best['margin_pitch']:+.2f}, Y_mar={best['margin_yaw']:+.2f}")

    # -------------------------------------------------------------
    # 3. SCENARIO B: STREAMER SIZE & CROSSFLOW DESCENT (Wing Braking)
    # -------------------------------------------------------------
    print("\n--- 3. Scenario B: Small Streamer vs Wing Braking (Can Oversized Wings Beat Symmetrical?) ---")
    print("Comparing Symmetrical 4-Fin (v_scale=1.0) vs Asymmetric Unbalanced 4-Fin (v_scale=0.6, huge horizontal wings):")

    for rec_area, label in [(250.0, "50x500mm (Standard)"), (62.5, "25x250mm (Small)"), (20.0, "Minimal (Tumble/Featherweight)")]:
        spec_custom = RocketSpec(
            total_length_mm=280.0,
            body_diameter_mm=24.0,
            nose_length_mm=110.0,
            tail_length_mm=0.0,
            wall_thickness_mm=0.4,
            infill_ratio=0.02,
            material="PLA",
            material_density=1.24,
            motor_type="1/2A6-2",
            recovery_mass_g=0.5 if rec_area < 100 else 1.2,
            recovery_area_cm2=rec_area,
            recovery_cd=0.25,
            descent_horizontal=True
        )
        opt_custom = FinOptimizer(spec_custom)

        # 1) Symmetric search (both margins >= 1.20)
        best_sym = None
        for span in range(35, 75, 2):
            for cr in range(25, 60, 2):
                if span > 1.5 * cr or span < 0.3 * cr:
                    continue
                r = evaluate_physically_correct_fins(opt_custom, span, cr, 0.0, 0.0, 1.0, is_4fin=True)
                if r["margin_pitch"] >= 1.20 and r["margin_yaw"] >= 1.20:
                    if best_sym is None or r["total_time_s"] > best_sym["total_time_s"]:
                        best_sym = r

        # 2) Unbalanced search (both margins >= 1.20, but v_scale <= 0.8 allowed with larger spans)
        best_asym = None
        for vs in [0.6, 0.7, 0.8]:
            for span in range(40, 110, 2):
                for cr in range(30, 80, 2):
                    if span > 2.0 * cr or span < 0.3 * cr:
                        continue
                    r = evaluate_physically_correct_fins(opt_custom, span, cr, 0.0, 0.0, vs, is_4fin=True)
                    if r["margin_pitch"] >= 1.20 and r["margin_yaw"] >= 1.20:
                        if best_asym is None or r["total_time_s"] > best_asym["total_time_s"]:
                            best_asym = r
                            best_asym["vs"] = vs

        print(f"\n  Recovery Area: {label}")
        if best_sym:
            print(f"    Symmetric (v=1.0): Time={best_sym['total_time_s']:.2f}s | Apogee={best_sym['apogee_m']:.1f}m | Descent={best_sym['v_descent']:.2f}m/s | FinMass={best_sym['fin_mass_g']:.2f}g | Span={best_sym['span']}x{best_sym['cr']}")
        if best_asym:
            print(f"    Asymmetric (v={best_asym['vs']:.1f}): Time={best_asym['total_time_s']:.2f}s | Apogee={best_asym['apogee_m']:.1f}m | Descent={best_asym['v_descent']:.2f}m/s | FinMass={best_asym['fin_mass_g']:.2f}g | H_span={best_asym['span']}x{best_asym['cr']}, V_span={best_asym['span']*best_asym['vs']:.1f}")

    # -------------------------------------------------------------
    # 4. SCENARIO C: 3-FIN CONFIGURATION (DIHEDRAL ANGLE & V-SCALE)
    # -------------------------------------------------------------
    print("\n--- 4. Scenario C: 3-Fin Dihedral Angle & Vertical Fin Scale Optimization ---")
    print("Testing 3-fin layouts with different dihedral angles theta and v_scale under Margin >= 1.20 cal:")
    for th in [0, 15, 30, 45]:
        best_3 = None
        for vs in [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.2, 1.5, 1.8, 2.0]:
            for span in range(35, 80, 2):
                for cr in range(25, 65, 2):
                    if span > 1.8 * cr or span < 0.3 * cr:
                        continue
                    r = evaluate_physically_correct_fins(opt_500, span, cr, 0.0, float(th), vs, is_4fin=False)
                    if r["margin_pitch"] >= 1.20 and r["margin_yaw"] >= 1.20:
                        if best_3 is None or r["total_time_s"] > best_3["total_time_s"]:
                            best_3 = r
                            best_3["vs"] = vs
        if best_3:
            print(f"  theta={th:2d} deg: Optimal v_scale={best_3['vs']:.2f} | Time: {best_3['total_time_s']:.2f}s | Apogee: {best_3['apogee_m']:.1f}m | Descent: {best_3['v_descent']:.2f}m/s | Fin Mass: {best_3['fin_mass_g']:.2f}g | H_span={best_3['span']}x{best_3['cr']}, V_span={best_3['span']*best_3['vs']:.1f} | P_mar={best_3['margin_pitch']:+.2f}, Y_mar={best_3['margin_yaw']:+.2f}")

if __name__ == "__main__":
    run_investigation()
