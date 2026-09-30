"""
Comprehensive Investigation:
1. Tip Chord (ct) and Taper Ratio (lambda = ct / cr) Effect on Performance & Stability
2. Conditions Under Which Asymmetric / Unbalanced Configurations Hold an Advantage
"""

import sys
import os
import math
import numpy as np

sys.path.insert(0, os.path.abspath("."))
from sim_engine.optimizer import RocketSpec, FinOptimizer
from scratch.test_correct_physics import evaluate_physically_correct_fins

def analyze_tip_chord():
    print("=" * 80)
    print("PART 1: TIP CHORD (ct) & TAPER RATIO (lambda = ct / cr) ANALYSIS")
    print("=" * 80)
    
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
    
    # Let's compare fin geometries that achieve the SAME target margin (~0.80 cal, ~0.92 cal, ~1.20 cal)
    # with different taper ratios lambda = ct / cr in [0.0, 0.15, 0.30, 0.50, 0.70, 1.0]
    # For 4-fin symmetric
    target_margins = [0.80, 0.92, 1.20]
    taper_ratios = [0.0, 0.15, 0.30, 0.50, 0.70, 1.0]
    
    for tm in target_margins:
        print(f"\n--- Target Margin >= {tm:.2f} cal (4-Fin Symmetric) ---")
        print(f"{'Taper (ct/cr)':15s} | {'Span [mm]':9s} | {'Cr [mm]':7s} | {'Ct [mm]':7s} | {'Fin Mass':8s} | {'Margin':7s} | {'Apogee':7s} | {'Time':7s}")
        print("-" * 80)
        
        for tr in taper_ratios:
            best = None
            # Scan span and cr
            for span in range(30, 80, 2):
                for cr in range(18, 60, 2):
                    ct = tr * cr
                    if span > 2.0 * cr or span < 0.3 * cr:
                        continue
                    # Evaluate
                    bal = 1.0 if tm >= 1.15 else 0.0
                    spec.ballast_mass_g = bal
                    opt_cur = FinOptimizer(spec)
                    
                    r = evaluate_physically_correct_fins(
                        opt_cur, float(span), float(cr), tr, 0.0, 1.0, is_4fin=True
                    )
                    m = min(r["margin_pitch"], r["margin_yaw"])
                    if m >= tm:
                        if best is None or r["total_time_s"] > best["total_time_s"]:
                            best = r
                            best["tr"] = tr
                            best["ct"] = ct
            if best:
                ct_val = best["tr"] * best["cr"]
                print(f"lambda = {best['tr']:4.2f}    | {best['span']:7.1f}mm | {best['cr']:5.1f}mm | {ct_val:5.1f}mm | {best['fin_mass_g']:6.2f}g | {best['margin_eff']:+6.2f} | {best['apogee_m']:5.1f}m | {best['total_time_s']:5.2f}s")

def analyze_unbalance_conditions():
    print("\n" + "=" * 80)
    print("PART 2: WHEN DOES AN UNBALANCED (ASYMMETRIC) CONFIGURATION WIN?")
    print("=" * 80)
    
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
    
    # Case 1: Crosswind Sensitivity & Pitch-Yaw Decoupling
    # Pitch stability Margin_pitch >= 1.0 cal (gravity-turn resistance)
    # Yaw stability Margin_yaw varied from 0.50 cal to 1.0 cal (weathercocking reduction)
    print("\n[Condition 1: Pitch-Yaw Decoupling under Horizontal Crosswind]")
    print("Requirement: Pitch Margin >= 1.00 cal, Yaw Margin >= Target")
    print(f"{'Target Yaw Margin':18s} | {'Optimal Form':18s} | {'v_scale':8s} | {'Fin Mass':8s} | {'Apogee':7s} | {'Flight Time':11s} | {'Advantage vs Sym'}")
    print("-" * 105)
    
    for target_yaw in [1.00, 0.85, 0.70, 0.55]:
        # Symmetric baseline (must satisfy both >= 1.00)
        best_sym = None
        for span in range(35, 75, 2):
            for cr in range(20, 50, 2):
                if span > 1.8 * cr or span < 0.35 * cr: continue
                r = evaluate_physically_correct_fins(opt, float(span), float(cr), 0.0, 0.0, 1.0, is_4fin=True)
                if r["margin_pitch"] >= 1.00 and r["margin_yaw"] >= 1.00:
                    if best_sym is None or r["total_time_s"] > best_sym["total_time_s"]:
                        best_sym = r

        # Asymmetric (Pitch >= 1.00, Yaw >= target_yaw)
        best_asym = None
        for vs in [0.50, 0.60, 0.70, 0.80, 0.90, 1.0]:
            for span in range(35, 75, 2):
                for cr in range(20, 50, 2):
                    if span > 1.8 * cr or span < 0.35 * cr: continue
                    r = evaluate_physically_correct_fins(opt, float(span), float(cr), 0.0, 0.0, vs, is_4fin=True)
                    if r["margin_pitch"] >= 1.00 and r["margin_yaw"] >= target_yaw:
                        if best_asym is None or r["total_time_s"] > best_asym["total_time_s"]:
                            best_asym = r
                            best_asym["vs"] = vs
        
        diff_time = best_asym["total_time_s"] - best_sym["total_time_s"]
        diff_mass = best_asym["fin_mass_g"] - best_sym["fin_mass_g"]
        print(f"Yaw >= {target_yaw:4.2f} cal      | {'4-Fin Asym' if best_asym['vs'] < 1.0 else '4-Fin Sym':18s} | vs={best_asym['vs']:4.2f}  | {best_asym['fin_mass_g']:6.2f}g | {best_asym['apogee_m']:5.1f}m | {best_asym['total_time_s']:5.2f}s       | +{diff_time:+.2f}s ({diff_mass:+.2f}g mass)")

    # Case 2: 3-Fin Inverted-Y (Landing shock absorption vs Dorsal fin protection)
    print("\n[Condition 2: 3-Fin Inverted-Y Geometry & Landing Protection]")
    print("Inverted-Y (theta=35 deg down, 1 dorsal fin up):")
    for th in [0, 20, 30, 35, 40]:
        best_3y = None
        for vs in [0.5, 0.6, 0.7, 0.8, 1.0]:
            for span in range(40, 85, 2):
                for cr in range(25, 55, 2):
                    if span > 1.8 * cr or span < 0.35 * cr: continue
                    r = evaluate_physically_correct_fins(opt, float(span), float(cr), 0.0, float(th), vs, is_4fin=False)
                    if r["margin_pitch"] >= 0.90 and r["margin_yaw"] >= 0.90:
                        if best_3y is None or r["total_time_s"] > best_3y["total_time_s"]:
                            best_3y = r
                            best_3y["vs"] = vs
        if best_3y:
            print(f"  theta={th:2d} deg: Best vs={best_3y['vs']:4.2f} | Time: {best_3y['total_time_s']:5.2f}s | Apogee: {best_3y['apogee_m']:5.1f}m | Fin Mass: {best_3y['fin_mass_g']:5.2f}g | H_span={best_3y['span']}x{best_3y['cr']}, V_span={best_3y['span']*best_3y['vs']:.1f}")

if __name__ == "__main__":
    analyze_tip_chord()
    analyze_unbalance_conditions()
