import sys
import os
import math
import numpy as np

sys.path.insert(0, os.path.abspath("."))
from sim_engine.optimizer import RocketSpec, FinOptimizer
from scratch.test_correct_physics import evaluate_physically_correct_fins

def search_asymmetric_top5():
    print("=" * 80)
    print("SEARCHING TOP-5 ASYMMETRIC FIN CONFIGURATIONS")
    print("=" * 80)

    # Recovery spec (50x500mm streamer)
    streamer_area = 250.0
    streamer_mass = 1.2
    streamer_cd = 0.25

    candidates = []

    # Sweep rocket lengths and nose lengths (JAR compliant: L >= 250, N <= 0.48*L)
    for L in [250, 270, 290, 310, 330]:
        max_nose = int(0.48 * L)
        for nose in range(60, max_nose + 1, 20):
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

            # Asymmetric 4-fin: v_scale in [0.4, 0.5, 0.6, 0.7, 0.8] (clear asymmetry)
            for vs in [0.5, 0.6, 0.7, 0.8]:
                for span in range(40, 95, 3):
                    for cr in range(30, 70, 3):
                        if span > 1.8 * cr or span < 0.35 * cr:
                            continue
                        r = evaluate_physically_correct_fins(opt, float(span), float(cr), 0.0, 0.0, vs, is_4fin=True)
                        
                        # We only want flyable/stable configurations (at least pitch >= 0.7 and yaw >= 0.6)
                        if r["margin_pitch"] >= 0.70 and r["margin_yaw"] >= 0.60:
                            candidates.append({
                                **r,
                                "L": L,
                                "nose": nose,
                                "cyl": L - nose,
                                "vs": vs,
                                "v_span": span * vs,
                                "v_cr": cr * vs,
                                "airframe_mass_g": opt.m_airframe_g
                            })

    print(f"Total valid asymmetric candidates evaluated: {len(candidates)}")

    # 1. TOP 5 by Pitch Margin (high pitch stability) among competitive designs (Hang time >= 26s)
    # Or top 5 ranked by Pitch Margin directly
    sorted_by_pitch_margin = sorted(candidates, key=lambda x: x["margin_pitch"], reverse=True)
    
    # 2. TOP 5 by Yaw Margin directly
    sorted_by_yaw_margin = sorted(candidates, key=lambda x: x["margin_yaw"], reverse=True)

    # 3. TOP 5 by Flight Time with Pitch >= 1.0 (Pitch-favored)
    pitch_favored = [c for c in candidates if c["margin_pitch"] >= 1.0 and c["margin_yaw"] >= 0.7]
    sorted_pitch_favored = sorted(pitch_favored, key=lambda x: x["total_time_s"], reverse=True)

    # 4. TOP 5 by Flight Time with Yaw >= 1.0 (Yaw-favored)
    yaw_favored = [c for c in candidates if c["margin_yaw"] >= 1.0 and c["margin_pitch"] >= 0.7]
    sorted_yaw_favored = sorted(yaw_favored, key=lambda x: x["total_time_s"], reverse=True)

    # 5. Pareto / Overall Best Asymmetric configurations ranked by flight time (with pitch >= 0.8, yaw >= 0.7)
    balanced_asym = [c for c in candidates if c["margin_pitch"] >= 0.8 and c["margin_yaw"] >= 0.7]
    sorted_best_time = sorted(balanced_asym, key=lambda x: x["total_time_s"], reverse=True)

    def print_top(title, c_list, top_n=5):
        print("\n" + "=" * 90)
        print(f" {title} (TOP {top_n})")
        print("=" * 90)
        header = f"{'Rank':4s} | {'L/Nose':10s} | {'PitchMar':8s} | {'YawMar':8s} | {'kv':5s} | {'H-Wing (bxCr)':15s} | {'V-Fin (bxCr)':15s} | {'Mass':6s} | {'Apogee':7s} | {'Time':6s}"
        print(header)
        print("-" * 90)
        
        seen = set()
        count = 0
        for c in c_list:
            # Key to avoid near-duplicate outputs
            key = (c["L"], round(c["margin_pitch"], 1), round(c["margin_yaw"], 1), c["vs"])
            if key in seen:
                continue
            seen.add(key)
            count += 1
            h_str = f"{c['span']:.0f}x{c['cr']:.0f}mm"
            v_str = f"{c['v_span']:.0f}x{c['v_cr']:.0f}mm"
            ln_str = f"{c['L']}/{c['nose']}mm"
            print(f"#{count:<3d} | {ln_str:10s} | {c['margin_pitch']:+6.2f}cal | {c['margin_yaw']:+6.2f}cal | {c['vs']:4.2f} | {h_str:15s} | {v_str:15s} | {c['total_mass_g']:5.1f}g | {c['apogee_m']:6.1f}m | {c['total_time_s']:5.2f}s")
            if count >= top_n:
                break

    print_top("CATEGORY 1: ピッチ安定率（Pitch Margin）重視型 アンバランス TOP 5", sorted_by_pitch_margin, 5)
    print_top("CATEGORY 2: ヨー安定率（Yaw Margin）重視型 アンバランス TOP 5", sorted_by_yaw_margin, 5)
    print_top("CATEGORY 3: ピッチ安定確保（Pitch>=1.0, Yaw>=0.7）での最高滞空時間 TOP 5", sorted_pitch_favored, 5)
    print_top("CATEGORY 4: 全アンバランス設定における滞空時間ランキング TOP 5 (Pitch>=0.8, Yaw>=0.7)", sorted_best_time, 5)

if __name__ == "__main__":
    search_asymmetric_top5()
