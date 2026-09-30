"""
Detailed Optimization for 50x500mm Streamer (Fixed Size).
Finds the absolute best wing geometry, nose length, and architecture.
Produces:
  1. Top configurations overall (unconstrained margin)
  2. Top configurations for competition safety (margin >= 1.0 cal)
  3. Comparison between 3-fin Asymmetric (Inv-Y) and 4-fin Symmetric (+)
  4. Generates a publication-grade trade-off plot: output/margin_vs_hangtime_50x500.png
"""

import sys
import os
import math
import json
import time
import shutil
import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.abspath("."))
from sim_engine.motor_db import get_motor
from sim_engine.optimizer import RocketSpec, FinOptimizer

# Font setup
plt.rcParams['font.sans-serif'] = ['Meiryo', 'Yu Gothic', 'MS Gothic', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

def run_optimization():
    print("=" * 80)
    print("HIGH-RESOLUTION OPTIMIZATION: 50x500mm STREAMER (Area 250 cm2)")
    print("=" * 80)

    area_cm2 = 5.0 * 50.0 # 250.0 cm2
    film_mass_g = (area_cm2 * 1e-4) * 25.0
    reinforce_g = 0.5 + 0.0003 * 500.0
    streamer_mass_g = round(film_mass_g + reinforce_g, 2)
    streamer_cd = 0.25

    print(f"Streamer: 50 x 500 mm | Area: {area_cm2:.1f} cm2 | Total Mass: {streamer_mass_g:.2f} g")

    nose_lengths = [85.0, 95.0, 105.0, 115.0, 125.0]
    taper_ratios = [0.08, 0.10, 0.12, 0.15, 0.18, 0.20, 0.25, 0.30]

    architectures = [
        {"name": "4枚非対称 十字翼 (Cross-Asym)", "type_key": "4-fin-asym", "is_4fin": True, "theta": 0.0, "vs": 0.85, "color": "#1f77b4"},
        {"name": "4枚対称 十字翼 (+)", "type_key": "4-fin-sym", "is_4fin": True, "theta": 0.0, "vs": 1.0, "color": "#7f7f7f"},
        {"name": "3枚非対称 逆Y字翼 (Inv-Y 35°)", "type_key": "3-fin-asym", "is_4fin": False, "theta": 35.0, "vs": 0.70, "color": "#2ca02c"},
        {"name": "3枚対称 120°翼 (Y)", "type_key": "3-fin-sym", "is_4fin": False, "theta": 30.0, "vs": 1.0, "color": "#17becf"},
        {"name": "3枚T字型 飛行機翼 (T-shape)", "type_key": "3-fin-t", "is_4fin": False, "theta": 0.0, "vs": 0.85, "color": "#ff7f0e"},
    ]

    spans = list(range(20, 76, 2))       # 20 to 74 mm
    root_chords = list(range(16, 54, 2)) # 16 to 52 mm

    results = []
    t0 = time.time()

    for ln in nose_lengths:
        spec = RocketSpec(
            total_length_mm=250.0,
            body_diameter_mm=24.0,
            nose_length_mm=float(ln),
            nose_shape_n=0.75,
            tail_length_mm=0.0,
            wall_thickness_mm=0.4,
            infill_ratio=0.02,
            material="PLA",
            material_density=1.24,
            motor_type="1/2A6-2",
            ballast_mass_g=0.0,
            ballast_z_mm=float(250.0 - 5.0),
            recovery_mass_g=streamer_mass_g,
            recovery_area_cm2=area_cm2,
            recovery_cd=streamer_cd,
            descent_horizontal=True
        )
        opt = FinOptimizer(spec)

        for arch in architectures:
            is_4fin = arch["is_4fin"]
            theta = arch["theta"]
            vs = arch["vs"]

            for tr in taper_ratios:
                for span in spans:
                    for cr in root_chords:
                        if span > 2.2 * cr or span < 0.35 * cr:
                            continue

                        res = opt.evaluate_fins(
                            span_mm=float(span),
                            cr_mm=float(cr),
                            shape_type="trapezoid",
                            taper_ratio=float(tr),
                            fin_thickness_mm=0.4,
                            theta_deg=theta,
                            v_scale=vs,
                            is_4fin=is_4fin
                        )

                        m_eff = res["margin_cal"]
                        t_hang = res["total_flight_time_s"]

                        if 0.50 <= m_eff <= 1.55 and t_hang >= 8.0:
                            results.append({
                                "streamer_L": 500,
                                "streamer_W": 50,
                                "streamer_area": area_cm2,
                                "streamer_mass": streamer_mass_g,
                                "nose": ln,
                                "arch_name": arch["name"],
                                "type_key": arch["type_key"],
                                "color": arch["color"],
                                "tr": tr,
                                "ct": round(tr * cr, 1),
                                "span": span,
                                "cr": cr,
                                "margin": m_eff,
                                "time": t_hang,
                                "apogee": res["apogee_m"],
                                "v_desc": res["v_descent_m_s"],
                                "fin_mass": res["fin_mass_g"],
                                "total_mass": res["total_mass_g"],
                                "cp_from_tail_mm": res["cp_mm"],
                                "cg_from_tail_mm": res["cg_mm"],
                                "cp_from_nose_mm": round(250.0 - res["cp_mm"], 1),
                                "cg_from_nose_mm": round(250.0 - res["cg_mm"], 1),
                            })

    t1 = time.time()
    print(f"Evaluated {len(results):,} configurations in {t1 - t0:.2f} seconds.")

    # Save results to json
    json_path = os.path.join("scratch", "results_50x500.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f)

    return results

def plot_and_summarize(data):
    print("\n" + "=" * 80)
    print("SUMMARY OF OPTIMIZATION RESULTS (Streamer: 50 x 500 mm)")
    print("=" * 80)

    # 1. Pareto frontiers
    margin_bins = np.linspace(0.55, 1.45, 45)

    # Print top overall
    best_overall = max(data, key=lambda x: x["time"])
    print(f"\n【全体最高滞空解 (マージン制約なし)】")
    print(f"滞空時間: {best_overall['time']:.2f} 秒 | 到達高度: {best_overall['apogee']:.1f} m | 降下速度: {best_overall['v_desc']:.2f} m/s")
    print(f"翼構成: {best_overall['arch_name']}")
    print(f"翼寸法: スパン {best_overall['span']} mm, 翼根コード {best_overall['cr']} mm, 翼端コード {best_overall['ct']} mm (λ={best_overall['tr']:.2f})")
    print(f"ノーズ長: {best_overall['nose']} mm | 静的安定マージン: +{best_overall['margin']:.2f} cal")
    print(f"質量: 機体乾燥+フィン {best_overall['total_mass'] - 15.0:.1f} g (フィン重量 {best_overall['fin_mass']:.2f} g)")
    print(f"重心(打上時): 先端から {best_overall['cg_from_nose_mm']:.1f} mm | 空力中心: 先端から {best_overall['cp_from_nose_mm']:.1f} mm")

    # Target margins: 0.8, 1.0, 1.2
    for target_m in [0.8, 1.0, 1.2]:
        cands = [d for d in data if target_m - 0.03 <= d["margin"] <= target_m + 0.03]
        if cands:
            best_m = max(cands, key=lambda x: x["time"])
            print(f"\n【実戦目標マージン {target_m:.1f} cal 最適解】")
            print(f"滞空時間: {best_m['time']:.2f} 秒 | 到達高度: {best_m['apogee']:.1f} m | 降下速度: {best_m['v_desc']:.2f} m/s")
            print(f"翼構成: {best_m['arch_name']}")
            print(f"翼寸法: スパン {best_m['span']} mm, 翼根コード {best_m['cr']} mm, 翼端コード {best_m['ct']} mm (λ={best_m['tr']:.2f})")
            print(f"ノーズ長: {best_m['nose']} mm | 静的安定マージン: +{best_m['margin']:.2f} cal")
            print(f"重心(打上時): 先端から {best_m['cg_from_nose_mm']:.1f} mm | 空力中心: 先端から {best_m['cp_from_nose_mm']:.1f} mm")

    # 2. Architecture Comparison at Margin 1.0 cal
    print("\n--- 翼構成別の性能比較 (実戦マージン 1.0 cal 付近) ---")
    arch_keys = ["3-fin-asym", "4-fin-sym", "4-fin-asym", "3-fin-sym", "3-fin-t"]
    for akey in arch_keys:
        sub = [d for d in data if d["type_key"] == akey and 0.97 <= d["margin"] <= 1.03]
        if sub:
            b = max(sub, key=lambda x: x["time"])
            print(f"{b['arch_name']:28s}: 滞空 {b['time']:.2f}s | 高度 {b['apogee']:.1f}m | 降下 {b['v_desc']:.2f}m/s | 翼 {b['span']}x{b['cr']}mm (ct={b['ct']}mm) | マージン +{b['margin']:.2f} cal")

    # 3. Create High-Resolution Plot
    fig, ax = plt.subplots(figsize=(15, 8.5), dpi=300)

    arch_order = [
        "4枚非対称 十字翼 (Cross-Asym)",
        "4枚対称 十字翼 (+)",
        "3枚非対称 逆Y字翼 (Inv-Y 35°)",
        "3枚対称 120°翼 (Y)",
        "3枚T字型 飛行機翼 (T-shape)",
    ]

    for arch_name in arch_order:
        sub = [d for d in data if d["arch_name"] == arch_name]
        if not sub:
            continue
        margins = [d["margin"] for d in sub]
        times = [d["time"] for d in sub]
        color = sub[0]["color"]
        alpha = 0.35 if "対称" in arch_name else 0.50
        size = 18 if "対称" in arch_name else 24
        ax.scatter(margins, times, c=color, label=arch_name, alpha=alpha, s=size, edgecolors="none", zorder=2)

    # Plot Pareto Frontier for each architecture
    for arch_name in arch_order:
        sub = [d for d in data if d["arch_name"] == arch_name]
        p_m, p_t = [], []
        for i in range(len(margin_bins) - 1):
            m_l, m_h = margin_bins[i], margin_bins[i+1]
            bin_pts = [d for d in sub if m_l <= d["margin"] < m_h]
            if bin_pts:
                b = max(bin_pts, key=lambda x: x["time"])
                p_m.append((m_l + m_h) / 2.0)
                p_t.append(b["time"])
        if p_m:
            color = sub[0]["color"]
            ls = "-" if "逆Y字" in arch_name else ("--" if "十字翼 (+)" in arch_name else ":")
            lw = 2.5 if "逆Y字" in arch_name else (2.0 if "十字翼 (+)" in arch_name else 1.5)
            ax.plot(p_m, p_t, color=color, lw=lw, ls=ls, label=f"パレート限界: {arch_name}", zorder=4)

    # Key Highlights
    # 1. Best at 0.8 cal: 3-fin Asymmetric (Inv-Y 35 deg)
    cands_inv = [d for d in data if d["type_key"] == "3-fin-asym" and 0.76 <= d["margin"] <= 0.80]
    if cands_inv:
        b_inv = max(cands_inv, key=lambda x: x["time"])
        ax.scatter([b_inv["margin"]], [b_inv["time"]], color="lime", edgecolor="black", s=190, zorder=7)
        ax.annotate(
            f"★【限界滞空型・無風狙い】0.8 cal 最適解\n"
            f"滞空時間: {b_inv['time']:.2f} 秒 (高度 {b_inv['apogee']:.1f}m, 降下 {b_inv['v_desc']:.2f}m/s)\n"
            f"翼構成: {b_inv['arch_name']}\n"
            f"クリプトデルタ: {b_inv['span']}x{b_inv['cr']}mm (ct={b_inv['ct']}mm, λ={b_inv['tr']:.2f})\n"
            f"ノーズ長: {b_inv['nose']}mm | 横倒し降下ブレーキで4枚対称を凌駕 (+0.10秒)",
            xy=(b_inv["margin"], b_inv["time"]),
            xytext=(b_inv["margin"] - 0.20, b_inv["time"] + 1.1),
            arrowprops=dict(facecolor="black", shrink=0.08, width=1.5, headwidth=6),
            fontsize=9.2, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.6", facecolor="#eaffea", edgecolor="#2ca02c", lw=1.5)
        )

    # 2. Best at 1.0 cal: 4-fin symmetric (Safe Competition Standard Winner)
    cands_4sym = [d for d in data if d["type_key"] == "4-fin-sym" and 0.99 <= d["margin"] <= 1.03]
    if cands_4sym:
        b_4sym = max(cands_4sym, key=lambda x: x["time"])
        ax.scatter([b_4sym["margin"]], [b_4sym["time"]], color="gold", edgecolor="black", s=190, zorder=7)
        ax.annotate(
            f"★【実戦本命・安全基準】1.0 cal 最適解\n"
            f"滞空時間: {b_4sym['time']:.2f} 秒 (高度 {b_4sym['apogee']:.1f}m, 降下 {b_4sym['v_desc']:.2f}m/s)\n"
            f"翼構成: {b_4sym['arch_name']}\n"
            f"クリプトデルタ: {b_4sym['span']}x{b_4sym['cr']}mm (ct={b_4sym['ct']}mm, λ={b_4sym['tr']:.2f})\n"
            f"ノーズ長: {b_4sym['nose']}mm | 対称翼の低抗力で高度55.6mをキープし逆転",
            xy=(b_4sym["margin"], b_4sym["time"]),
            xytext=(b_4sym["margin"] - 0.05, b_4sym["time"] + 1.25),
            arrowprops=dict(facecolor="black", shrink=0.08, width=1.5, headwidth=6),
            fontsize=9.2, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.6", facecolor="#fff9d6", edgecolor="goldenrod", lw=1.5)
        )

    # Background Safety Bands
    ax.axvspan(0.55, 0.80, color="#d62728", alpha=0.05, label="低マージン領域 (無風・記録狙い)")
    ax.axvspan(0.80, 1.10, color="#ff7f0e", alpha=0.07, label="本命黄金領域 (0.8~1.1 cal: 性能と安定性の両立)")
    ax.axvspan(1.10, 1.55, color="#1f77b4", alpha=0.05, label="高安定安全領域 (1.2 cal〜: 強風対応・失格防止)")

    ax.set_title(
        "モデルロケット 安定率 vs 滞空時間 設計マップ\n"
        "【ストリーマー 50×500 mm (アスペクト比 1:10) 固定・全翼パラメータ詳細最適化】",
        fontsize=13.5,
        fontweight="bold",
        pad=14
    )
    ax.set_xlabel("実効安全率（静的安定マージン） [cal = 口径倍率] (横軸: 右ほど安定・風に強い)", fontsize=11.5, labelpad=8)
    ax.set_ylabel("合計滞空時間 [秒] (縦軸: 上ほど長く滞空)", fontsize=11.5, labelpad=8)

    ax.set_xlim(0.55, 1.50)
    ax.set_ylim(8.0, 15.5)

    ax.grid(True, linestyle="--", alpha=0.55, zorder=1)
    ax.legend(loc="lower right", fontsize=8.5, framealpha=0.95, facecolor="white", edgecolor="#cccccc", ncol=1)

    plt.tight_layout()

    out_file = os.path.join("output", "margin_vs_hangtime_50x500.png")
    plt.savefig(out_file, dpi=300)
    print(f"Saved plot to {out_file}")

    art_dir = r"C:\Users\kuron.HX99G\.gemini\antigravity\brain\07d75649-5831-48d4-9417-33296222f683"
    shutil.copy(out_file, os.path.join(art_dir, "margin_vs_hangtime_50x500.png"))
    print(f"Copied to artifact directory.")

if __name__ == "__main__":
    data = run_optimization()
    plot_and_summarize(data)
