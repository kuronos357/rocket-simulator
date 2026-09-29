import sys
import os
import math

sys.path.insert(0, os.path.abspath("."))
from sim_engine.optimizer import RocketSpec, FinOptimizer
from scratch.test_correct_physics import evaluate_physically_correct_fins

def get_detailed_asym_top5():
    streamer_area = 250.0 # 50x500mm
    streamer_mass = 1.2
    streamer_cd = 0.25

    candidates = []

    for L in [250, 260, 270, 280, 290, 300]:
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

            # Test both kv < 1.0 (Pitch dominant) and kv > 1.0 (Yaw dominant)
            for vs in [0.5, 0.6, 0.7, 0.8, 1.2, 1.3, 1.4]:
                for span in range(35, 80, 2):
                    for cr in range(25, 55, 2):
                        if span > 1.6 * cr or span < 0.35 * cr:
                            continue
                        r = evaluate_physically_correct_fins(opt, float(span), float(cr), 0.0, 0.0, vs, is_4fin=True)
                        if r["margin_pitch"] >= 0.60 and r["margin_yaw"] >= 0.60:
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

    # Group 1: Pitch-Dominant (kv <= 0.8) sorted by total flight time while keeping Pitch >= 1.05 cal
    pitch_dominant = [c for c in candidates if c["vs"] <= 0.8 and c["margin_pitch"] >= 1.05 and c["margin_yaw"] >= 0.70]
    pitch_sorted = sorted(pitch_dominant, key=lambda x: x["total_time_s"], reverse=True)

    # Group 2: Yaw-Dominant (kv >= 1.2) sorted by total flight time while keeping Yaw >= 1.05 cal
    yaw_dominant = [c for c in candidates if c["vs"] >= 1.2 and c["margin_yaw"] >= 1.05 and c["margin_pitch"] >= 0.70]
    yaw_sorted = sorted(yaw_dominant, key=lambda x: x["total_time_s"], reverse=True)

    # Group 3: Best overall asymmetric (kv != 1.0) with Margin >= 0.80 both
    best_asym = [c for c in candidates if c["vs"] != 1.0 and c["margin_pitch"] >= 0.80 and c["margin_yaw"] >= 0.75]
    best_asym_sorted = sorted(best_asym, key=lambda x: x["total_time_s"], reverse=True)

    def print_table(title, items):
        print("\n" + "=" * 95)
        print(title)
        print("=" * 95)
        print(f"| Rank | 全長/ノーズ | ピッチマージン | ヨーマージン | 垂直比 kv | 水平主翼 (幅x弦) | 垂直尾翼 (幅x弦) | 打上質量 | 到達高度 | 滞空時間 |")
        print(f"|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")
        seen = set()
        count = 0
        for c in items:
            key = (c["L"], round(c["margin_pitch"], 1), round(c["margin_yaw"], 1), c["vs"])
            if key in seen:
                continue
            seen.add(key)
            count += 1
            print(f"| #{count} | {c['L']}/{c['nose']}mm | **{c['margin_pitch']:+.2f} cal** | **{c['margin_yaw']:+.2f} cal** | {c['vs']:.2f} | {c['span']:.0f}×{c['cr']:.0f}mm | {c['v_span']:.1f}×{c['v_cr']:.1f}mm | {c['total_mass_g']:.1f}g | {c['apogee_m']:.1f}m | **{c['total_time_s']:.2f}秒** |")
            if count >= 5:
                break

    print_table("【部門A】ピッチ安定率 優秀型アンバランス（主翼優位・飛行機型: kv <= 0.8）TOP 5", pitch_sorted)
    print_table("【部門B】ヨー安定率 優秀型アンバランス（尾翼優位・矢羽型: kv >= 1.2）TOP 5", yaw_sorted)
    print_table("【部門C】総合滞空時間 最優秀アンバランスアセンブリ TOP 5", best_asym_sorted)

if __name__ == "__main__":
    get_detailed_asym_top5()
