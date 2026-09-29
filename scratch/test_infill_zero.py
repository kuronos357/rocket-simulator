import sys
import os
import math
import numpy as np

sys.path.insert(0, os.path.abspath("."))
from sim_engine.optimizer import RocketSpec, FinOptimizer
from scratch.test_correct_physics import evaluate_physically_correct_fins

def run_infill_zero_search():
    print("=" * 80)
    print("RUNNING 4-DIVISION SEARCH WITH INFILL = 0.0% (COMPLETELY HOLLOW)")
    print("=" * 80)

    streamer_area = 250.0  # 50x500mm
    streamer_mass = 1.2
    streamer_cd = 0.25

    all_candidates = []
    lengths = [250, 260, 270, 280, 300, 320]

    for L in lengths:
        max_nose = int(0.48 * L)
        for nose in range(60, max_nose + 1, 15):
            spec = RocketSpec(
                total_length_mm=float(L),
                body_diameter_mm=24.0,
                nose_length_mm=float(nose),
                tail_length_mm=0.0,
                wall_thickness_mm=0.4,
                infill_ratio=0.0, # 0% INFILL! Completely hollow shell
                material="PLA",
                material_density=1.24,
                motor_type="1/2A6-2",
                recovery_mass_g=streamer_mass,
                recovery_area_cm2=streamer_area,
                recovery_cd=streamer_cd,
                descent_horizontal=True
            )
            opt = FinOptimizer(spec)

            # A. 3-Fin
            for th in [0, 15, 20, 25, 30, 35, 40]:
                for vs in [0.5, 0.6, 0.7, 0.8, 1.0, 1.2, 1.4, 1.6]:
                    for span in range(35, 90, 2):
                        for cr in range(25, 60, 2):
                            if span > 1.8 * cr or span < 0.35 * cr:
                                continue
                            r = evaluate_physically_correct_fins(opt, float(span), float(cr), 0.0, float(th), vs, is_4fin=False)
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
                                    "config_type": f"3-fin (th={th}°, kv={vs:.2f})" if is_asym else "3-fin (120° symmetric)",
                                    "airframe_mass_g": opt.m_airframe_g
                                })

            # B. 4-Fin
            for vs in [0.5, 0.6, 0.7, 0.8, 1.0, 1.2, 1.4]:
                for span in range(35, 90, 2):
                    for cr in range(25, 60, 2):
                        if span > 1.8 * cr or span < 0.35 * cr:
                            continue
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
                                "config_type": f"4-fin (+ shape, kv={vs:.2f})" if is_asym else "4-fin (+ shape symmetric)",
                                "airframe_mass_g": opt.m_airframe_g
                            })

    print(f"Total valid candidate designs: {len(all_candidates)}")

    divisions = [
        ("【1.2部門】高安定・安全重視 (Pitch >= 1.20 cal, Yaw >= 1.20 cal)", lambda c: c["margin_pitch"] >= 1.20 and c["margin_yaw"] >= 1.20),
        ("【0.9部門】競技攻め・最短軽量 (Pitch >= 0.90 cal, Yaw >= 0.90 cal)", lambda c: c["margin_pitch"] >= 0.90 and c["margin_yaw"] >= 0.90),
        ("【0.7部門】極限軽量・低マージン (Pitch >= 0.70 cal, Yaw >= 0.70 cal)", lambda c: c["margin_pitch"] >= 0.70 and c["margin_yaw"] >= 0.70),
        ("【アンバランス設定部門】(is_asym == True / Pitch >= 0.80, Yaw >= 0.70)", lambda c: c["is_asym"] and c["margin_pitch"] >= 0.80 and c["margin_yaw"] >= 0.70)
    ]

    for title, flt in divisions:
        sub = [c for c in all_candidates if flt(c)]
        sorted_sub = sorted(sub, key=lambda x: x["total_time_s"], reverse=True)
        print("\n" + "=" * 105)
        print(f"  {title} (INFILL = 0%)")
        print("=" * 105)
        print(f"| Rank | 構成タイプ | 枚数 | 全長/ノーズ | ピッチ | ヨー | 主翼 (幅x弦) | 尾翼 (幅x弦) | フィン質量 | 最高高度 | 滞空時間 |")
        print(f"|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")
        seen = set()
        count = 0
        for c in sorted_sub:
            key = (c["num_fins"], c["L"], round(c["margin_pitch"], 1), round(c["margin_yaw"], 1), c["vs"], c["th"])
            if key in seen:
                continue
            seen.add(key)
            count += 1
            h_str = f"{c['span']:.0f}×{c['cr']:.0f}mm"
            v_str = f"{c['v_span']:.1f}×{c['v_cr']:.1f}mm"
            ln_str = f"{c['L']}/{c['nose']}mm"
            print(f"| #{count} | {c['config_type']:<24s} | {c['num_fins']}枚 | {ln_str:10s} | {c['margin_pitch']:+5.2f}cal | {c['margin_yaw']:+5.2f}cal | {h_str:12s} | {v_str:14s} | {c['fin_mass_g']:4.2f}g | {c['apogee_m']:5.1f}m | **{c['total_time_s']:5.2f}秒** |")
            if count >= 5:
                break

if __name__ == "__main__":
    run_infill_zero_search()
