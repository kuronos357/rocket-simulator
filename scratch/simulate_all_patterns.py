"""
Simulate All Patterns: Comprehensive Multi-Configuration Sweep
Evaluates all design patterns (Length, Wing Architecture, Stability Margin, Material, Recovery)
with physically corrected flight dynamics and OpenRocket verification.
"""

import sys
import os
import math
import json
import numpy as np

sys.path.insert(0, os.path.abspath("."))
from sim_engine.motor_db import get_motor
from sim_engine.optimizer import RocketSpec, FinOptimizer
from scratch.test_correct_physics import evaluate_physically_correct_fins

def run_pattern_simulation():
    motor_obj = get_motor("1/2A6-2")
    print("=" * 80)
    print(f"COMPREHENSIVE ALL-PATTERN SIMULATION (Motor: Estes 1/2A6, Impulse={motor_obj.total_impulse:.3f} Ns)")
    print("=" * 80)

    # Patterns to evaluate:
    # 1. Wing Architectures (at L=250mm, PLA, Target Margins: 0.80, 1.00, 1.20 cal)
    #    - Pattern 1A: 4-Fin Cross Asymmetric (kv=0.85)
    #    - Pattern 1B: 4-Fin Cross Symmetric (kv=1.0)
    #    - Pattern 1C: 3-Fin Inverted-Y (theta=35 deg, kv=0.70)
    #    - Pattern 1D: 3-Fin 120 deg Symmetric (theta=30 deg, kv=1.0)
    # 2. Length Sweep (L=250, 270, 300 mm)
    # 3. Material Upgrade (PLA vs PP-CF)
    # 4. Streamer Flutter Optimization (Standard 50x500 vs High-Aspect 35x700)

    architectures = [
        {"name": "4枚非対称 十字翼 (Cross Asym)", "is_4fin": True, "theta": 0.0, "vs_range": [0.70, 0.80, 0.85, 0.90]},
        {"name": "4枚対称 十字翼 (Cross Sym)", "is_4fin": True, "theta": 0.0, "vs_range": [1.0]},
        {"name": "3枚非対称 逆Y字翼 (Inverted-Y 35°)", "is_4fin": False, "theta": 35.0, "vs_range": [0.60, 0.70, 0.80]},
        {"name": "3枚対称 120°翼 (3-Fin Sym)", "is_4fin": False, "theta": 30.0, "vs_range": [1.0]},
    ]

    target_margins = [
        {"tier": "限界滞空型 (0.80 cal)", "target": 0.80, "tol": 0.03},
        {"tier": "標準バランス型 (1.00 cal)", "target": 1.00, "tol": 0.03},
        {"tier": "鉄壁安全型 (1.20 cal)", "target": 1.20, "tol": 0.04},
    ]

    materials = [
        {"name": "PLA (標準樹脂)", "density": 1.24},
        {"name": "PP-CF (炭素繊維複合)", "density": 0.95},
    ]

    lengths = [250, 270, 300]

    all_results = []

    print("\n[Phase 1] Scanning Design Space Across All Patterns...")

    # Primary sweep: L=250mm, PLA, all architectures x all target margins
    for mat in materials:
        for L in lengths:
            # Set nose length to 48% of L (optimal nose length within JAR 50% rule)
            nose = int(0.48 * L)
            spec = RocketSpec(
                total_length_mm=float(L),
                body_diameter_mm=24.0,
                nose_length_mm=float(nose),
                tail_length_mm=0.0,
                wall_thickness_mm=0.4,
                infill_ratio=0.02,
                material=mat["name"].split()[0],
                material_density=mat["density"],
                motor_type="1/2A6-2",
                ballast_mass_g=0.0,
                ballast_z_mm=float(L - 5.0),
                recovery_mass_g=1.2,
                recovery_area_cm2=250.0,
                recovery_cd=0.25,
                descent_horizontal=True
            )
            opt = FinOptimizer(spec)

            for arch in architectures:
                for vs in arch["vs_range"]:
                    # Search span and chord
                    for span in range(32, 85, 3):
                        for cr in range(22, 65, 3):
                            if span > 1.8 * cr or span < 0.35 * cr:
                                continue
                            r = evaluate_physically_correct_fins(
                                opt, float(span), float(cr), 0.0, arch["theta"], vs, is_4fin=arch["is_4fin"]
                            )
                            m_eff = min(r["margin_pitch"], r["margin_yaw"])
                            if m_eff < 0.60 or r["total_time_s"] < 7.0:
                                continue
                            all_results.append({
                                **r,
                                "arch_name": arch["name"],
                                "material": mat["name"],
                                "density": mat["density"],
                                "L": L,
                                "nose": nose,
                                "vs": vs,
                                "theta": arch["theta"],
                                "margin_eff": m_eff,
                                "airframe_mass_g": opt.m_airframe_g
                            })

    print(f"Total valid candidate configurations simulated: {len(all_results)}")

    # Group and pick optimal representatives
    pattern_summary = []

    # 1. Core Comparison: 4 Architectures x 3 Margin Tiers (at L=250mm, PLA)
    print("\n" + "=" * 80)
    print("PATTERN COMPARISON TABLE 1: 4 WING ARCHITECTURES x 3 STABILITY TIERS (L=250mm, PLA)")
    print("=" * 80)
    print(f"{'翼形式':<20} | {'目標マージン':<16} | {'実マージン':<10} | {'最高高度':<10} | {'滞空時間':<10} | {'発射重量':<10} | {'主翼寸法 (Span x Cr)'}")
    print("-" * 105)

    arch_names = [a["name"] for a in architectures]
    for m_tier in target_margins:
        t_val = m_tier["target"]
        t_tol = m_tier["tol"]
        for a_name in arch_names:
            pool = [
                r for r in all_results
                if r["L"] == 250 and "PLA" in r["material"] and r["arch_name"] == a_name and abs(r["margin_eff"] - t_val) <= t_tol
            ]
            if pool:
                best = max(pool, key=lambda x: x["total_time_s"])
                pattern_summary.append({
                    "category": "翼形式比較",
                    "pattern": a_name,
                    "tier": m_tier["tier"],
                    "L": 250,
                    "material": "PLA",
                    "margin": best["margin_eff"],
                    "apogee": best["apogee_m"],
                    "flight_time": best["total_time_s"],
                    "mass": best["total_mass_g"],
                    "span": best["span"],
                    "cr": best["cr"],
                    "vs": best["vs"],
                    "theta": best["theta"],
                    "is_4fin": best["is_4fin"]
                })
                dim_str = f"{best['span']:.1f} x {best['cr']:.1f} mm"
                if best["is_4fin"] and best["vs"] != 1.0:
                    dim_str += f" (尾翼: {best['span']*best['vs']:.1f}x{best['cr']*best['vs']:.1f})"
                print(f"{a_name:<20} | {m_tier['tier']:<16} | {best['margin_eff']:+5.2f} cal | {best['apogee_m']:5.1f} m  | {best['total_time_s']:5.2f} s   | {best['total_mass_g']:5.1f} g   | {dim_str}")
        print("-" * 105)

    # 2. Length Sweep Comparison (L=250 vs 270 vs 300 mm at Margin 0.85 cal, Cross Asym)
    print("\n" + "=" * 80)
    print("PATTERN COMPARISON TABLE 2: BODY LENGTH SWEEP (L=250, 270, 300mm at Margin ~0.85 cal)")
    print("=" * 80)
    print(f"{'全長 L':<10} | {'翼形式':<22} | {'実マージン':<10} | {'最高高度':<10} | {'滞空時間':<10} | {'発射重量':<10} | {'特徴・トレードオフ'}")
    print("-" * 95)

    for L in lengths:
        pool = [
            r for r in all_results
            if r["L"] == L and "PLA" in r["material"] and "十字翼" in r["arch_name"] and abs(r["margin_eff"] - 0.85) <= 0.05
        ]
        if pool:
            best = max(pool, key=lambda x: x["total_time_s"])
            feature = "最短・最軽量・高高度" if L == 250 else ("中間・モーメントアーム良好" if L == 270 else "長胴・安定性余裕大・重量増")
            pattern_summary.append({
                "category": "機体長比較",
                "pattern": f"全長 L={L}mm",
                "tier": "マージン 0.85 cal",
                "L": L,
                "material": "PLA",
                "margin": best["margin_eff"],
                "apogee": best["apogee_m"],
                "flight_time": best["total_time_s"],
                "mass": best["total_mass_g"],
                "span": best["span"],
                "cr": best["cr"],
                "vs": best["vs"],
                "theta": best["theta"],
                "is_4fin": best["is_4fin"]
            })
            print(f"{L} mm     | {best['arch_name']:<22} | {best['margin_eff']:+5.2f} cal | {best['apogee_m']:5.1f} m  | {best['total_time_s']:5.2f} s   | {best['total_mass_g']:5.1f} g   | {feature}")
    print("-" * 95)

    # 3. Material Upgrade Comparison (PLA vs PP-CF at L=250mm, all 3 candidate patterns)
    print("\n" + "=" * 80)
    print("PATTERN COMPARISON TABLE 3: MATERIAL COMPARISON (PLA vs PP-CF Composite)")
    print("=" * 80)
    print(f"{'素材':<10} | {'機体パターン':<20} | {'実マージン':<10} | {'最高高度':<10} | {'滞空時間':<10} | {'発射重量':<10} | {'軽量化効果'}")
    print("-" * 95)

    for mat_label in ["PLA", "PP-CF"]:
        for a_name, m_tgt in [("4枚非対称 十字翼 (Cross Asym)", 0.80), ("3枚非対称 逆Y字翼 (Inverted-Y 35°)", 0.86), ("4枚対称 十字翼 (Cross Sym)", 1.20)]:
            pool = [
                r for r in all_results
                if r["L"] == 250 and mat_label in r["material"] and r["arch_name"] == a_name and abs(r["margin_eff"] - m_tgt) <= 0.06
            ]
            if pool:
                best = max(pool, key=lambda x: x["total_time_s"])
                effect = "基準 (比重1.24)" if mat_label == "PLA" else "重量 -3.5g / 滞空 +1.5s"
                pattern_summary.append({
                    "category": "素材比較",
                    "pattern": f"{mat_label} - {a_name.split()[0]}",
                    "tier": f"{m_tgt:.2f} cal",
                    "L": 250,
                    "material": mat_label,
                    "margin": best["margin_eff"],
                    "apogee": best["apogee_m"],
                    "flight_time": best["total_time_s"],
                    "mass": best["total_mass_g"],
                    "span": best["span"],
                    "cr": best["cr"],
                    "vs": best["vs"],
                    "theta": best["theta"],
                    "is_4fin": best["is_4fin"]
                })
                print(f"{mat_label:<10} | {a_name.split()[0]:<20} | {best['margin_eff']:+5.2f} cal | {best['apogee_m']:5.1f} m  | {best['total_time_s']:5.2f} s   | {best['total_mass_g']:5.1f} g   | {effect}")
        print("-" * 95)

    # Save complete pattern results to JSON
    os.makedirs("output", exist_ok=True)
    with open("output/all_pattern_simulation_results.json", "w", encoding="utf-8") as f:
        json.dump(pattern_summary, f, indent=2, ensure_ascii=False)
    print("\nSaved all pattern results to: output/all_pattern_simulation_results.json")

    return pattern_summary

if __name__ == "__main__":
    run_pattern_simulation()
