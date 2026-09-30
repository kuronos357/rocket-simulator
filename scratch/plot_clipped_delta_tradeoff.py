"""
Plot Margin vs Hang Time Trade-off Scatter Plot for Clipped Delta Wings & Nose Lengths
Streamer: 120mm x 1200mm (Area: 1440 cm2)
Material: PLA (1.24 g/cm3), Nozzle: 0.4mm, Wall: 0.4mm, Infill: 2%
Style matched to output/失敗版/margin_vs_hangtime_tradeoff.png
"""

import sys
import os
import math
import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.abspath("."))
from sim_engine.motor_db import get_motor
from sim_engine.optimizer import RocketSpec, FinOptimizer

# Configure font for Japanese support
plt.rcParams['font.sans-serif'] = ['Yu Gothic', 'Meiryo', 'MS Gothic', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def run_simulation_and_generate_plot():
    print("=" * 80)
    print("RUNNING SIMULATION: STREAMER 120mm x 1200mm (1440 cm2)")
    print("Generating 'Margin vs Hang Time' Scatter Plot by Wing Architecture")
    print("=" * 80)

    # 1. Physical Specifications
    streamer_area_cm2 = 1440.0   # 120mm x 1200mm
    streamer_mass_g = 3.5        # Mylar/Polyethylene film ~25g/m2 (0.144m2 -> 3.6g)
    streamer_cd = 0.25           # Standard streamer drag coefficient

    # Nose lengths to scan: 70mm to 125mm (JAR 50% limit is 125mm for L=250mm)
    nose_lengths = [70, 85, 100, 115, 125]
    
    # Clipped delta taper ratios (ct / cr)
    taper_ratios = [0.0, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40]

    # Wing architectures
    architectures = [
        {"name": "4枚非対称 十字翼 (Cross-Asym)", "type_key": "4-fin-asym", "is_4fin": True, "theta": 0.0, "vs": 0.85, "color": "#1f77b4", "size": 36, "alpha": 0.65},
        {"name": "4枚対称 十字翼 (+)", "type_key": "4-fin-sym", "is_4fin": True, "theta": 0.0, "vs": 1.0, "color": "#7f7f7f", "size": 22, "alpha": 0.40},
        {"name": "3枚非対称 逆Y字翼 (Inv-Y 35°)", "type_key": "3-fin-asym", "is_4fin": False, "theta": 35.0, "vs": 0.70, "color": "#2ca02c", "size": 42, "alpha": 0.75},
        {"name": "3枚対称 120°翼 (Y)", "type_key": "3-fin-sym", "is_4fin": False, "theta": 30.0, "vs": 1.0, "color": "#17becf", "size": 26, "alpha": 0.50},
        {"name": "3枚T字型 飛行機翼 (T-shape)", "type_key": "3-fin-t", "is_4fin": False, "theta": 0.0, "vs": 0.85, "color": "#ff7f0e", "size": 30, "alpha": 0.55},
    ]

    spans = list(range(26, 76, 2))      # 26 to 74 mm
    root_chords = list(range(18, 56, 2))# 18 to 54 mm

    results = []
    print("Sweeping parameter combinations across all wing types...")

    for nose in nose_lengths:
        spec = RocketSpec(
            total_length_mm=250.0,
            body_diameter_mm=24.0,
            nose_length_mm=float(nose),
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
            recovery_area_cm2=streamer_area_cm2,
            recovery_cd=streamer_cd,
            descent_horizontal=True # Horizontal descent
        )
        opt = FinOptimizer(spec)

        for arch in architectures:
            is_4fin = arch["is_4fin"]
            theta = arch["theta"]
            vs = arch["vs"]

            for tr in taper_ratios:
                for span in spans:
                    for cr in root_chords:
                        if span > 2.0 * cr or span < 0.35 * cr:
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

                        # Filter reasonable margins
                        if 0.55 <= m_eff <= 1.65 and t_hang >= 12.0:
                            results.append({
                                "margin": m_eff,
                                "time": t_hang,
                                "apogee": res["apogee_m"],
                                "v_desc": res["v_descent_m_s"],
                                "nose": nose,
                                "tr": tr,
                                "ct": round(tr * cr, 1),
                                "span": span,
                                "cr": cr,
                                "arch_name": arch["name"],
                                "type_key": arch["type_key"],
                                "fin_mass": res["fin_mass_g"],
                                "total_mass": res["total_mass_g"]
                            })

    print(f"Total valid configurations found: {len(results):,}")

    # 2. Plotting Setup
    fig, ax = plt.subplots(figsize=(14, 8.5), dpi=300)

    # Plot scatters by wing architecture
    for arch in architectures:
        subset = [r for r in results if r["type_key"] == arch["type_key"]]
        if subset:
            ax.scatter(
                [r["margin"] for r in subset],
                [r["time"] for r in subset],
                c=arch["color"],
                s=arch["size"],
                alpha=arch["alpha"],
                edgecolors="none",
                label=arch["name"],
                zorder=2
            )

    # 3. Pareto Frontier Calculation (Envelope curve of max hang time)
    margin_bins = np.linspace(0.60, 1.50, 46)
    pareto_margins = []
    pareto_times = []
    pareto_best = []

    for i in range(len(margin_bins) - 1):
        m_low, m_high = margin_bins[i], margin_bins[i+1]
        bin_pts = [r for r in results if m_low <= r["margin"] < m_high]
        if bin_pts:
            best = max(bin_pts, key=lambda x: x["time"])
            pareto_margins.append((m_low + m_high) / 2.0)
            pareto_times.append(best["time"])
            pareto_best.append(best)

    if pareto_margins:
        ax.plot(
            pareto_margins,
            pareto_times,
            color="#d62728", # Crimson Red
            lw=3.0,
            ls="-",
            label="パレート最適フロンティア (最高性能限界線)",
            zorder=4
        )

    # 4. Highlight & Annotate Top 3 Representative Points
    # A. 0.8 cal Tier (限界滞空型)
    cands_08 = [r for r in results if 0.79 <= r["margin"] <= 0.82]
    if cands_08:
        best_08 = max(cands_08, key=lambda x: x["time"])
        ax.scatter([best_08["margin"]], [best_08["time"]], color="lime", edgecolor="black", s=180, zorder=6)
        ax.annotate(
            f"★【限界滞空型】0.8 cal 部門\n"
            f"滞空時間: {best_08['time']:.2f} 秒 (高度 {best_08['apogee']:.1f}m)\n"
            f"安定率: +{best_08['margin']:.2f} cal | {best_08['arch_name']}\n"
            f"ノーズ長: {best_08['nose']}mm (50%上限)\n"
            f"クリプトデルタ: {best_08['span']}x{best_08['cr']}mm (ct={best_08['ct']}mm, λ={best_08['tr']:.2f})",
            xy=(best_08["margin"], best_08["time"]),
            xytext=(best_08["margin"] - 0.22, best_08["time"] + 1.1),
            arrowprops=dict(facecolor="black", shrink=0.08, width=1.5, headwidth=6),
            fontsize=9.5, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.6", facecolor="#eaffea", edgecolor="#2ca02c", lw=1.5)
        )

    # B. 1.0 cal Tier (標準バランス型 / 本命)
    cands_10 = [r for r in results if 0.98 <= r["margin"] <= 1.02]
    if cands_10:
        best_10 = max(cands_10, key=lambda x: x["time"])
        ax.scatter([best_10["margin"]], [best_10["time"]], color="gold", edgecolor="black", s=180, zorder=6)
        ax.annotate(
            f"★【本命・高バランス】1.0 cal 部門\n"
            f"滞空時間: {best_10['time']:.2f} 秒 (高度 {best_10['apogee']:.1f}m)\n"
            f"安定率: +{best_10['margin']:.2f} cal | {best_10['arch_name']}\n"
            f"ノーズ長: {best_10['nose']}mm (50%上限)\n"
            f"クリプトデルタ: {best_10['span']}x{best_10['cr']}mm (ct={best_10['ct']}mm, λ={best_10['tr']:.2f})",
            xy=(best_10["margin"], best_10["time"]),
            xytext=(best_10["margin"] - 0.08, best_10["time"] + 1.2),
            arrowprops=dict(facecolor="black", shrink=0.08, width=1.5, headwidth=6),
            fontsize=9.5, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.6", facecolor="#fff9d6", edgecolor="goldenrod", lw=1.5)
        )

    # C. 1.2 cal Tier (鉄壁安全型)
    cands_12 = [r for r in results if 1.18 <= r["margin"] <= 1.22]
    if cands_12:
        best_12 = max(cands_12, key=lambda x: x["time"])
        ax.scatter([best_12["margin"]], [best_12["time"]], color="#00bcd4", edgecolor="black", s=180, zorder=6)
        ax.annotate(
            f"★【鉄壁安全型】1.2 cal 部門 (強風対応)\n"
            f"滞空時間: {best_12['time']:.2f} 秒 (高度 {best_12['apogee']:.1f}m)\n"
            f"安定率: +{best_12['margin']:.2f} cal | {best_12['arch_name']}\n"
            f"ノーズ長: {best_12['nose']}mm\n"
            f"クリプトデルタ: {best_12['span']}x{best_12['cr']}mm (ct={best_12['ct']}mm, λ={best_12['tr']:.2f})",
            xy=(best_12["margin"], best_12["time"]),
            xytext=(best_12["margin"] + 0.06, best_12["time"] + 0.3),
            arrowprops=dict(facecolor="black", shrink=0.08, width=1.5, headwidth=6),
            fontsize=9.5, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.6", facecolor="#eef4ff", edgecolor="#1f77b4", lw=1.5)
        )

    # 5. Background Safety Zone Bands
    ax.axvspan(0.60, 0.80, color="#d62728", alpha=0.06, label="低マージン領域 (無風・記録狙い)")
    ax.axvspan(0.80, 1.10, color="#ff7f0e", alpha=0.08, label="本命黄金領域 (0.8~1.1 cal: 性能と安定性の両立)")
    ax.axvspan(1.10, 1.60, color="#1f77b4", alpha=0.06, label="高安定安全領域 (1.2 cal〜: 強風対応・失格防止)")

    # 6. Titles & Labels
    ax.set_title(
        "モデルロケット 安定率（静的安定マージン）vs 滞空時間 設計マップ\n"
        "【大型ストリーマー 120mm x 1200mm (1440 cm²) / PLA 0.4mm外壁1層・インフィル2% / クリプトデルタ翼全翼種比較】",
        fontsize=13.5,
        fontweight="bold",
        pad=14
    )
    ax.set_xlabel("実効安全率（静的安定マージン） [cal = 口径倍率] (横軸: 右ほど安定・風に強い)", fontsize=11.5, labelpad=8)
    ax.set_ylabel("合計滞空時間 [秒] (縦軸: 上ほど長く滞空)", fontsize=11.5, labelpad=8)

    y_min = math.floor(min(r["time"] for r in results)) - 1
    y_max = math.ceil(max(r["time"] for r in results)) + 2
    ax.set_xlim(0.55, 1.55)
    ax.set_ylim(y_min, y_max)

    ax.grid(True, linestyle="--", alpha=0.55, zorder=1)
    ax.legend(loc="lower left", fontsize=9.5, framealpha=0.95, facecolor="white", edgecolor="#cccccc")

    plt.tight_layout()

    # Save to multiple locations
    os.makedirs("output", exist_ok=True)
    out_file1 = os.path.join("output", "margin_vs_hangtime_tradeoff.png")
    out_file2 = os.path.join("output", "margin_vs_hangtime_clipped_delta_120x1200.png")
    
    plt.savefig(out_file1, dpi=300)
    plt.savefig(out_file2, dpi=300)
    print(f"Plot successfully saved to:")
    print(f"  1. {out_file1}")
    print(f"  2. {out_file2}")

    # Copy to artifacts directory
    art_dir = r"C:\Users\kuron.HX99G\.gemini\antigravity\brain\07d75649-5831-48d4-9417-33296222f683"
    import shutil
    shutil.copy(out_file1, os.path.join(art_dir, "margin_vs_hangtime_tradeoff.png"))
    print(f"Copied to artifact directory: {art_dir}")

    return best_08, best_10, best_12

if __name__ == "__main__":
    run_simulation_and_generate_plot()
