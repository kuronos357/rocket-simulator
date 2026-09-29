import sys
import os
import math
import numpy as np

sys.path.insert(0, os.path.abspath("."))
from sim_engine.optimizer import RocketSpec, FinOptimizer
from scratch.test_correct_physics import evaluate_physically_correct_fins

def run_three_tier_search():
    print("=" * 80)
    print("RUNNING THREE-TIER OPTIMIZATION SEARCH (MARGIN TARGETS: 1.20, 0.90, 0.70 cal)")
    print("=" * 80)

    # Common parameters
    streamer_area = 250.0  # 50x500mm
    streamer_mass = 1.2
    streamer_cd = 0.25

    # Target specifications to search:
    # 1. Target 1.20 cal (Safe, high-stability model)
    # 2. Target 0.90 cal (Competitive, lightweight model)
    # 3. Target 0.70 cal (Unbalanced / relaxed yaw airplane model: Pitch >= 1.0, Yaw >= 0.70, or Both >= 0.70)

    targets = [
        {"name": "Type 1 (Safe / High Stability)", "pitch_min": 1.20, "yaw_min": 1.20, "label": "1.2 cal"},
        {"name": "Type 2 (Competitive / Short & Light)", "pitch_min": 0.90, "yaw_min": 0.90, "label": "0.9 cal"},
        {"name": "Type 3 (Unbalanced Airplane Wing)", "pitch_min": 1.10, "yaw_min": 0.70, "label": "0.7 cal (Unbalanced)"},
        {"name": "Type 3B (Extreme Relaxed 0.70)", "pitch_min": 0.70, "yaw_min": 0.70, "label": "0.7 cal (Symmetric/All)"}
    ]

    results = {}

    for tgt in targets:
        p_min = tgt["pitch_min"]
        y_min = tgt["yaw_min"]
        print(f"\n>>> Searching optimal configuration for {tgt['name']} (Req: Pitch >= {p_min:.2f} cal, Yaw >= {y_min:.2f} cal) <<<")
        
        best_overall = None

        # Search over lengths: 250 to 330 mm
        for L in range(250, 335, 10):
            # Nose length: 50 to 0.48*L (JAR 50% rule requires L - N >= 0.50*L => N <= 0.50*L)
            max_nose = int(0.48 * L)
            min_nose = 50
            for nose in range(min_nose, max_nose + 1, 15):
                spec = RocketSpec(
                    total_length_mm=float(L),
                    body_diameter_mm=24.0,
                    nose_length_mm=float(nose),
                    tail_length_mm=0.0,
                    wall_thickness_mm=0.4,
                    infill_ratio=0.02,
                    material="PLA",
                    material_density=1.24,
                    motor_type="1/2A6-2",
                    recovery_mass_g=streamer_mass,
                    recovery_area_cm2=streamer_area,
                    recovery_cd=streamer_cd,
                    descent_horizontal=True
                )
                opt = FinOptimizer(spec)

                # Search fin configurations:
                # 4-fin (+), 4-fin (asym kv in 0.6~1.0), 3-fin (120 deg)
                # 1) 4-fin scan
                for vs in [0.6, 0.7, 0.8, 1.0]:
                    for span in range(35, 85, 2):
                        for cr in range(25, 65, 2):
                            if span > 1.6 * cr or span < 0.35 * cr:
                                continue
                            r = evaluate_physically_correct_fins(opt, float(span), float(cr), 0.0, 0.0, vs, is_4fin=True)
                            if r["margin_pitch"] >= p_min and r["margin_yaw"] >= y_min:
                                if best_overall is None or r["total_time_s"] > best_overall["total_time_s"]:
                                    best_overall = {
                                        **r,
                                        "L": L,
                                        "nose": nose,
                                        "config_name": f"4-fin (+) with kv={vs:.2f}",
                                        "vs": vs,
                                        "airframe_mass_g": opt.m_airframe_g
                                    }

                # 2) 3-fin scan (theta=30 deg, kv=1.0)
                for span in range(40, 90, 2):
                    for cr in range(25, 65, 2):
                        if span > 1.6 * cr or span < 0.35 * cr:
                            continue
                        r = evaluate_physically_correct_fins(opt, float(span), float(cr), 0.0, 30.0, 1.0, is_4fin=False)
                        if r["margin_pitch"] >= p_min and r["margin_yaw"] >= y_min:
                            if best_overall is None or r["total_time_s"] > best_overall["total_time_s"]:
                                best_overall = {
                                    **r,
                                    "L": L,
                                    "nose": nose,
                                    "config_name": "3-fin (120 deg)",
                                    "vs": 1.0,
                                    "airframe_mass_g": opt.m_airframe_g
                                }

        results[tgt["label"]] = best_overall
        if best_overall:
            b = best_overall
            print(f"  FOUND OPTIMAL for {tgt['label']}:")
            print(f"    Total Length L: {b['L']} mm | Nose Length: {b['nose']} mm | Airframe Dry: {b['airframe_mass_g']:.1f} g")
            print(f"    Fin Config: {b['config_name']}")
            print(f"    Horizontal Wing: Span = {b['span']:.1f} mm, Root Chord = {b['cr']:.1f} mm")
            if b['is_4fin']:
                print(f"    Vertical Fin:    Span = {b['span']*b['vs']:.1f} mm, Root Chord = {b['cr']*b['vs']:.1f} mm (Ratio kv={b['vs']:.2f})")
            print(f"    Fin Mass: {b['fin_mass_g']:.2f} g | Total Launch Mass: {b['total_mass_g']:.1f} g")
            print(f"    Stability Margins: Pitch = {b['margin_pitch']:+.2f} cal, Yaw = {b['margin_yaw']:+.2f} cal")
            print(f"    Flight Performance: Apogee = {b['apogee_m']:.1f} m, Hang Time = {b['total_time_s']:.2f} s, Descent V = {b['v_descent']:.2f} m/s")

if __name__ == "__main__":
    run_three_tier_search()
