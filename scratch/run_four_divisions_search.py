import sys
import os
import math
import numpy as np

sys.path.insert(0, os.path.abspath("."))
from sim_engine.optimizer import RocketSpec, FinOptimizer
from scratch.test_correct_physics import evaluate_physically_correct_fins

def run_four_divisions_search():
    print("=" * 80)
    print("RUNNING COMPREHENSIVE 4-DIVISION SEARCH (3-FIN & 4-FIN ALL INCLUDED)")
    print("=" * 80)

    # Recovery parameters
    streamer_area = 250.0  # 50x500mm
    streamer_mass = 1.2
    streamer_cd = 0.25

    all_candidates = []

    # Rocket length & nose length grid
    lengths = [250, 260, 270, 280, 300, 320]

    total_evals = 0

    for L in lengths:
        max_nose = int(0.48 * L)
        for nose in range(60, max_nose + 1, 15):
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

            # -------------------------------------------------------------
            # A. 3-Fin configurations: theta in [0..40], kv in [0.5..1.6]
            # -------------------------------------------------------------
            for th in [0, 15, 20, 25, 30, 35, 40]:
                for vs in [0.5, 0.6, 0.7, 0.8, 1.0, 1.2, 1.4, 1.6]:
                    for span in range(35, 90, 2):
                        for cr in range(25, 60, 2):
                            if span > 1.8 * cr or span < 0.35 * cr:
                                continue
                            total_evals += 1
                            r = evaluate_physically_correct_fins(opt, float(span), float(cr), 0.0, float(th), vs, is_4fin=False)
                            # Basic stability filter
                            if r["margin_pitch"] >= 0.50 and r["margin_yaw"] >= 0.50:
                                is_asym = (th != 30 or vs != 1.0)
                                all_candidates.append({
                                    **r,
                                    "L": L,
                                    "nose": nose,
                                    "cyl": L - nose,
                                    "num_fins": 3,
                                    "th": float(th),
                                    "vs": vs,
                                    "is_4fin": False,
                                    "is_asym": is_asym,
                                    "v_span": span * vs,
                                    "v_cr": cr * vs,
                                    "config_type": f"3-fin (th={th}°, kv={vs:.2f})" if is_asym else "3-fin (120° symmetric)"
                                })

            # -------------------------------------------------------------
            # B. 4-Fin configurations (+ shape): theta=0, kv in [0.5..1.4]
            # -------------------------------------------------------------
            for vs in [0.5, 0.6, 0.7, 0.8, 1.0, 1.2, 1.4]:
                for span in range(35, 90, 2):
                    for cr in range(25, 60, 2):
                        if span > 1.8 * cr or span < 0.35 * cr:
                            continue
                        total_evals += 1
                        r = evaluate_physically_correct_fins(opt, float(span), float(cr), 0.0, 0.0, vs, is_4fin=True)
                        if r["margin_pitch"] >= 0.50 and r["margin_yaw"] >= 0.50:
                            is_asym = (vs != 1.0)
                            all_candidates.append({
                                **r,
                                "L": L,
                                "nose": nose,
                                "cyl": L - nose,
                                "num_fins": 4,
                                "th": 0.0,
                                "vs": vs,
                                "is_4fin": True,
                                "is_asym": is_asym,
                                "v_span": span * vs,
                                "v_cr": cr * vs,
                                "config_type": f"4-fin (+ shape, kv={vs:.2f})" if is_asym else "4-fin (+ shape symmetric)"
                            })

    print(f"Total evaluations performed: {total_evals}")
    print(f"Total valid candidate designs: {len(all_candidates)}")

    # -------------------------------------------------------------------------
    # DIVISION 1: 1.2 CAL DIVISION (Pitch >= 1.20 and Yaw >= 1.20)
    # -------------------------------------------------------------------------
    c_12 = [c for c in all_candidates if c["margin_pitch"] >= 1.20 and c["margin_yaw"] >= 1.20]
    sorted_12 = sorted(c_12, key=lambda x: x["total_time_s"], reverse=True)

    # -------------------------------------------------------------------------
    # DIVISION 2: 0.9 CAL DIVISION (Pitch >= 0.90 and Yaw >= 0.90)
    # -------------------------------------------------------------------------
    c_09 = [c for c in all_candidates if c["margin_pitch"] >= 0.90 and c["margin_yaw"] >= 0.90]
    sorted_09 = sorted(c_09, key=lambda x: x["total_time_s"], reverse=True)

    # -------------------------------------------------------------------------
    # DIVISION 3: 0.7 CAL DIVISION (Pitch >= 0.70 and Yaw >= 0.70)
    # -------------------------------------------------------------------------
    c_07 = [c for c in all_candidates if c["margin_pitch"] >= 0.70 and c["margin_yaw"] >= 0.70]
    sorted_07 = sorted(c_07, key=lambda x: x["total_time_s"], reverse=True)

    # -------------------------------------------------------------------------
    # DIVISION 4: ASYMMETRIC SETTING DIVISION (is_asym == True, Pitch >= 0.80, Yaw >= 0.70)
    # -------------------------------------------------------------------------
    c_asym = [c for c in all_candidates if c["is_asym"] and c["margin_pitch"] >= 0.80 and c["margin_yaw"] >= 0.70]
    sorted_asym = sorted(c_asym, key=lambda x: x["total_time_s"], reverse=True)

    def print_division(div_name, sorted_list, top_n=5):
        print("\n" + "=" * 105)
        print(f"  {div_name} (TOP {top_n})")
        print("=" * 105)
        print(f"| Rank | 構成タイプ | 枚数 | 全長/ノーズ | ピッチ | ヨー | 主翼 (幅x弦) | 尾翼 (幅x弦) | フィン質量 | 最高高度 | 滞空時間 |")
        print(f"|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")
        seen = set()
        count = 0
        for c in sorted_list:
            key = (c["num_fins"], c["L"], round(c["margin_pitch"], 1), round(c["margin_yaw"], 1), c["vs"], c["th"])
            if key in seen:
                continue
            seen.add(key)
            count += 1
            h_str = f"{c['span']:.0f}×{c['cr']:.0f}mm"
            v_str = f"{c['v_span']:.1f}×{c['v_cr']:.1f}mm"
            ln_str = f"{c['L']}/{c['nose']}mm"
            print(f"| #{count} | {c['config_type']:<24s} | {c['num_fins']}枚 | {ln_str:10s} | {c['margin_pitch']:+5.2f}cal | {c['margin_yaw']:+5.2f}cal | {h_str:12s} | {v_str:14s} | {c['fin_mass_g']:4.2f}g | {c['apogee_m']:5.1f}m | **{c['total_time_s']:5.2f}秒** |")
            if count >= top_n:
                break

    print_division("【1.2部門】高安定・安全重視 (Pitch >= 1.20 cal, Yaw >= 1.20 cal)", sorted_12)
    print_division("【0.9部門】競技攻め・最短軽量 (Pitch >= 0.90 cal, Yaw >= 0.90 cal)", sorted_09)
    print_division("【0.7部門】極限軽量・低マージン (Pitch >= 0.70 cal, Yaw >= 0.70 cal)", sorted_07)
    print_division("【アンバランス設定部門】(kv != 1.0 または theta != 30° / Pitch >= 0.80, Yaw >= 0.70)", sorted_asym)

if __name__ == "__main__":
    run_four_divisions_search()
