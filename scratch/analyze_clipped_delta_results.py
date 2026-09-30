"""
Analyze and summarize the Clipped Delta & Nose Length sweep results
"""

import json
import os
import numpy as np

def analyze():
    results_path = os.path.join("scratch", "clipped_delta_optimization_results.json")
    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Loaded {len(data):,} valid simulation points.\n")

    # 1. Overall Absolute Maximum Hang Time across ALL configurations (Margin >= 0.80 cal)
    stable_080 = [d for d in data if d["margin_eff"] >= 0.80]
    stable_100 = [d for d in data if d["margin_eff"] >= 1.00]
    stable_120 = [d for d in data if d["margin_eff"] >= 1.20]

    # Best for Horizontal Descent (Horizontal Attitude Descent)
    top_horiz_080 = sorted(stable_080, key=lambda x: x["total_time_horiz_s"], reverse=True)[:5]
    top_horiz_100 = sorted(stable_100, key=lambda x: x["total_time_horiz_s"], reverse=True)[:5]
    top_horiz_120 = sorted(stable_120, key=lambda x: x["total_time_horiz_s"], reverse=True)[:5]

    print("=" * 90)
    print("TOP CANDIDATES FOR HORIZONTAL DESCENT (機体水平降下ギミック有効)")
    print("=" * 90)
    
    print("\n【 1. 限界滞空型 (Margin >= +0.80 cal) TOP 3 】")
    for i, p in enumerate(top_horiz_080[:3], 1):
        print(f"  Rank {i}: 滞空時間 = {p['total_time_horiz_s']:.2f} s (高度 {p['apogee_m']:.1f} m, 降下速度 {p['v_desc_horiz']:.2f} m/s)")
        print(f"    - ノーズ長: {p['nose_mm']} mm (全長比 {p['nose_mm']/250*100:.1f}%)")
        print(f"    - 翼構成: {p['arch_name']}")
        print(f"    - クリプトデルタ諸元: スパン = {p['span_mm']} mm, 根元コード cr = {p['cr_mm']} mm, 翼端コード ct = {p['ct_mm']} mm (テーパー比 lambda = {p['taper_ratio']:.2f})")
        print(f"    - 質量: フィン質量 = {p['fin_mass_g']:.2f} g, 全備質量 = {p['total_mass_g']:.2f} g")
        print(f"    - 安定性: マージン = {p['margin_eff']:+.2f} cal (Pitch: {p['margin_pitch']:+.2f}, Yaw: {p['margin_yaw']:+.2f})\n")

    print("\n【 2. 標準バランス型 (Margin >= +1.00 cal) TOP 3 】")
    for i, p in enumerate(top_horiz_100[:3], 1):
        print(f"  Rank {i}: 滞空時間 = {p['total_time_horiz_s']:.2f} s (高度 {p['apogee_m']:.1f} m, 降下速度 {p['v_desc_horiz']:.2f} m/s)")
        print(f"    - ノーズ長: {p['nose_mm']} mm (全長比 {p['nose_mm']/250*100:.1f}%)")
        print(f"    - 翼構成: {p['arch_name']}")
        print(f"    - クリプトデルタ諸元: スパン = {p['span_mm']} mm, 根元コード cr = {p['cr_mm']} mm, 翼端コード ct = {p['ct_mm']} mm (テーパー比 lambda = {p['taper_ratio']:.2f})")
        print(f"    - 質量: フィン質量 = {p['fin_mass_g']:.2f} g, 全備質量 = {p['total_mass_g']:.2f} g")
        print(f"    - 安定性: マージン = {p['margin_eff']:+.2f} cal (Pitch: {p['margin_pitch']:+.2f}, Yaw: {p['margin_yaw']:+.2f})\n")

    print("\n【 3. 鉄壁安全型 (Margin >= +1.20 cal) TOP 3 】")
    for i, p in enumerate(top_horiz_120[:3], 1):
        print(f"  Rank {i}: 滞空時間 = {p['total_time_horiz_s']:.2f} s (高度 {p['apogee_m']:.1f} m, 降下速度 {p['v_desc_horiz']:.2f} m/s)")
        print(f"    - ノーズ長: {p['nose_mm']} mm (全長比 {p['nose_mm']/250*100:.1f}%)")
        print(f"    - 翼構成: {p['arch_name']}")
        print(f"    - クリプトデルタ諸元: スパン = {p['span_mm']} mm, 根元コード cr = {p['cr_mm']} mm, 翼端コード ct = {p['ct_mm']} mm (テーパー比 lambda = {p['taper_ratio']:.2f})")
        print(f"    - 質量: フィン質量 = {p['fin_mass_g']:.2f} g, 全備質量 = {p['total_mass_g']:.2f} g")
        print(f"    - 安定性: マージン = {p['margin_eff']:+.2f} cal (Pitch: {p['margin_pitch']:+.2f}, Yaw: {p['margin_yaw']:+.2f})\n")

    # 2. Nose Length Sensitivity Analysis
    print("=" * 90)
    print("NOSE LENGTH SENSITIVITY (ノーズ長さによる最大滞空時間の推移: Margin >= 0.80 cal)")
    print("=" * 90)
    nose_vals = sorted(list(set(d["nose_mm"] for d in stable_080)))
    for n in nose_vals:
        sub = [d for d in stable_080 if d["nose_mm"] == n]
        best_n = max(sub, key=lambda x: x["total_time_horiz_s"])
        print(f"  ノーズ長 = {n:3d} mm (胴体長 {250-n:3d} mm): 最大滞空時間 = {best_n['total_time_horiz_s']:.2f} s | 高度 = {best_n['apogee_m']:.1f} m, 全備質量 = {best_n['total_mass_g']:.1f} g, 翼 = {best_n['arch_name']}, Span={best_n['span_mm']}, Cr={best_n['cr_mm']}, Ct={best_n['ct_mm']} (tr={best_n['taper_ratio']:.2f})")

    # 3. Taper Ratio (lambda = ct / cr) Effect
    print("\n" + "=" * 90)
    print("CLIPPED DELTA TAPER RATIO SENSITIVITY (テーパー比による影響: ノーズ最適時)")
    print("=" * 90)
    best_overall_nose = top_horiz_080[0]["nose_mm"]
    sub_nose = [d for d in stable_080 if d["nose_mm"] == best_overall_nose]
    tr_vals = sorted(list(set(d["taper_ratio"] for d in sub_nose)))
    for tr in tr_vals:
        sub_tr = [d for d in sub_nose if abs(d["taper_ratio"] - tr) < 1e-4]
        best_tr = max(sub_tr, key=lambda x: x["total_time_horiz_s"])
        print(f"  テーパー比 lambda = {tr:4.2f}: 最大滞空時間 = {best_tr['total_time_horiz_s']:.2f} s | Span = {best_tr['span_mm']:2d} mm, Cr = {best_tr['cr_mm']:2d} mm, Ct = {best_tr['ct_mm']:4.1f} mm, フィン質量 = {best_tr['fin_mass_g']:.2f} g, Margin = {best_tr['margin_eff']:+.2f}")

    # 4. Pure Streamer Descent Analysis (Non-horizontal)
    top_pure_080 = sorted(stable_080, key=lambda x: x["total_time_pure_s"], reverse=True)[:3]
    print("\n" + "=" * 90)
    print("FOR COMPARISON: PURE STREAMER VERTICAL DESCENT (通常ストリーマ垂直降下時)")
    print("=" * 90)
    for i, p in enumerate(top_pure_080, 1):
        print(f"  Rank {i}: 滞空時間 = {p['total_time_pure_s']:.2f} s (高度 {p['apogee_m']:.1f} m, 降下速度 {p['v_desc_pure']:.2f} m/s)")
        print(f"    - ノーズ長: {p['nose_mm']} mm, 翼構成: {p['arch_name']}")
        print(f"    - クリプトデルタ諸元: Span = {p['span_mm']} mm, Cr = {p['cr_mm']} mm, Ct = {p['ct_mm']} mm (lambda = {p['taper_ratio']:.2f})")
        print(f"    - 全備質量 = {p['total_mass_g']:.2f} g, マージン = {p['margin_eff']:+.2f} cal\n")

if __name__ == "__main__":
    analyze()
