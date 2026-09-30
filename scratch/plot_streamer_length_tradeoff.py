"""
Generate Scatter Plot: Stability Margin vs Hang Time
with Streamer Length (L_streamer) as a Degree of Freedom alongside
Nose Length and Clipped Delta Wing Geometries.
"""

import sys
import os
import math
import json
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['Yu Gothic', 'Meiryo', 'MS Gothic', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def create_plot():
    json_path = os.path.join("scratch", "streamer_length_sweep_results.json")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Loaded {len(data):,} simulation points.")

    fig, ax = plt.subplots(figsize=(14.5, 9), dpi=300)

    # Architectures styling
    arch_styles = {
        "4-fin-asym": {"name": "4枚非対称 十字翼 (Cross-Asym)", "color": "#1f77b4", "size": 24, "alpha": 0.45},
        "4-fin-sym": {"name": "4枚対称 十字翼 (+)", "color": "#7f7f7f", "size": 18, "alpha": 0.35},
        "3-fin-asym": {"name": "3枚非対称 逆Y字翼 (Inv-Y 35°)", "color": "#2ca02c", "size": 30, "alpha": 0.55},
        "3-fin-sym": {"name": "3枚対称 120°翼 (Y)", "color": "#17becf", "size": 20, "alpha": 0.40},
        "3-fin-t": {"name": "3枚T字型 飛行機翼 (T-shape)", "color": "#ff7f0e", "size": 22, "alpha": 0.45},
    }

    # 1. Plot all scatter points colored by wing architecture
    for key, style in arch_styles.items():
        subset = [d for d in data if d["type_key"] == key]
        if subset:
            ax.scatter(
                [d["margin"] for d in subset],
                [d["time"] for d in subset],
                c=style["color"],
                s=style["size"],
                alpha=style["alpha"],
                edgecolors="none",
                label=style["name"],
                zorder=2
            )

    # 2. Plot Pareto Frontiers for key Streamer Lengths (200, 600, 1200, 1800 mm)
    frontier_configs = [
        {"L": 200, "label": "L=200mm (240 cm², 小型・アンバランス有利)", "color": "#8c564b", "lw": 2.0, "ls": ":"},
        {"L": 600, "label": "L=600mm (720 cm², 中型標準)", "color": "#9467bd", "lw": 2.2, "ls": "--"},
        {"L": 1200, "label": "L=1200mm (1440 cm², 基準・高滞空)", "color": "#d62728", "lw": 3.2, "ls": "-"},
        {"L": 1800, "label": "L=1800mm (2160 cm², 超大型・重量飽和限界)", "color": "#e377c2", "lw": 2.2, "ls": "-."},
    ]

    margin_bins = np.linspace(0.60, 1.50, 46)

    for fc in frontier_configs:
        sub_L = [d for d in data if d["streamer_L"] == fc["L"]]
        p_m, p_t = [], []
        for i in range(len(margin_bins) - 1):
            m_l, m_h = margin_bins[i], margin_bins[i+1]
            bin_pts = [d for d in sub_L if m_l <= d["margin"] < m_h]
            if bin_pts:
                best = max(bin_pts, key=lambda x: x["time"])
                p_m.append((m_l + m_h) / 2.0)
                p_t.append(best["time"])
        if p_m:
            ax.plot(p_m, p_t, color=fc["color"], lw=fc["lw"], ls=fc["ls"], label=f"パレート限界線: {fc['label']}", zorder=4)

    # 3. Overall Pareto frontier across ALL streamer lengths
    overall_p_m, overall_p_t, overall_best = [], [], []
    for i in range(len(margin_bins) - 1):
        m_l, m_h = margin_bins[i], margin_bins[i+1]
        bin_pts = [d for d in data if m_l <= d["margin"] < m_h]
        if bin_pts:
            best = max(bin_pts, key=lambda x: x["time"])
            overall_p_m.append((m_l + m_h) / 2.0)
            overall_p_t.append(best["time"])
            overall_best.append(best)

    # 4. Highlight & Annotate Top Representative Points (Global Optimal at L=1200~1800mm)
    # Point 1: 0.8 cal
    cands_08 = [d for d in data if 0.79 <= d["margin"] <= 0.82]
    best_08 = max(cands_08, key=lambda x: x["time"])
    ax.scatter([best_08["margin"]], [best_08["time"]], color="lime", edgecolor="black", s=180, zorder=7)
    ax.annotate(
        f"★【限界滞空型】0.8 cal 最適解\n"
        f"滞空時間: {best_08['time']:.2f} 秒 (高度 {best_08['apogee']:.1f}m, 降下 {best_08['v_desc']:.2f}m/s)\n"
        f"ストリーマー: 120 x {best_08['streamer_L']}mm (重量 {best_08['streamer_mass']}g)\n"
        f"翼構成: {best_08['arch_name']}\n"
        f"クリプトデルタ: {best_08['span']}x{best_08['cr']}mm (ct={best_08['ct']}mm, λ={best_08['tr']:.2f})",
        xy=(best_08["margin"], best_08["time"]),
        xytext=(best_08["margin"] - 0.22, best_08["time"] + 1.2),
        arrowprops=dict(facecolor="black", shrink=0.08, width=1.5, headwidth=6),
        fontsize=9.2, fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.6", facecolor="#eaffea", edgecolor="#2ca02c", lw=1.5)
    )

    # Point 2: 1.0 cal
    cands_10 = [d for d in data if 0.98 <= d["margin"] <= 1.02]
    best_10 = max(cands_10, key=lambda x: x["time"])
    ax.scatter([best_10["margin"]], [best_10["time"]], color="gold", edgecolor="black", s=180, zorder=7)
    ax.annotate(
        f"★【本命・高バランス型】1.0 cal 最適解\n"
        f"滞空時間: {best_10['time']:.2f} 秒 (高度 {best_10['apogee']:.1f}m, 降下 {best_10['v_desc']:.2f}m/s)\n"
        f"ストリーマー: 120 x {best_10['streamer_L']}mm (重量 {best_10['streamer_mass']}g)\n"
        f"翼構成: {best_10['arch_name']}\n"
        f"クリプトデルタ: {best_10['span']}x{best_10['cr']}mm (ct={best_10['ct']}mm, λ={best_10['tr']:.2f})",
        xy=(best_10["margin"], best_10["time"]),
        xytext=(best_10["margin"] - 0.08, best_10["time"] + 1.25),
        arrowprops=dict(facecolor="black", shrink=0.08, width=1.5, headwidth=6),
        fontsize=9.2, fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.6", facecolor="#fff9d6", edgecolor="goldenrod", lw=1.5)
    )

    # Point 3: Small streamer champion (L=200mm, where Asymmetric dominates)
    cands_200 = [d for d in data if d["streamer_L"] == 200 and 0.80 <= d["margin"] <= 0.85]
    best_200 = max(cands_200, key=lambda x: x["time"])
    ax.scatter([best_200["margin"]], [best_200["time"]], color="#ff3366", edgecolor="black", s=150, zorder=7)
    ax.annotate(
        f"◆【小型ストリーマー最適解】L=200mm (240 cm²)\n"
        f"滞空時間: {best_200['time']:.2f} 秒 (高度 {best_200['apogee']:.1f}m)\n"
        f"勝者: {best_200['arch_name']} (アンバランス独壇場)\n"
        f"クリプトデルタ: {best_200['span']}x{best_200['cr']}mm (λ={best_200['tr']:.2f})",
        xy=(best_200["margin"], best_200["time"]),
        xytext=(best_200["margin"] + 0.10, best_200["time"] - 0.35),
        arrowprops=dict(facecolor="black", shrink=0.08, width=1.5, headwidth=6),
        fontsize=8.8, fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#ffeef2", edgecolor="#ff3366", lw=1.3)
    )

    # 5. Background Safety Zone Bands
    ax.axvspan(0.60, 0.80, color="#d62728", alpha=0.05, label="低マージン領域 (無風・記録狙い)")
    ax.axvspan(0.80, 1.10, color="#ff7f0e", alpha=0.07, label="本命黄金領域 (0.8~1.1 cal: 性能と安定性の両立)")
    ax.axvspan(1.10, 1.55, color="#1f77b4", alpha=0.05, label="高安定安全領域 (1.2 cal〜: 強風対応・失格防止)")

    # 6. Titles & Labels
    ax.set_title(
        "モデルロケット 安定率 vs 滞空時間 設計マップ\n"
        "【自由度：ストリーマー長 L=200~1800mm × ノーズ長 × クリプトデルタ翼 全パラメータ解析】",
        fontsize=13.5,
        fontweight="bold",
        pad=14
    )
    ax.set_xlabel("実効安全率（静的安定マージン） [cal = 口径倍率] (横軸: 右ほど安定・風に強い)", fontsize=11.5, labelpad=8)
    ax.set_ylabel("合計滞空時間 [秒] (縦軸: 上ほど長く滞空)", fontsize=11.5, labelpad=8)

    ax.set_xlim(0.55, 1.55)
    ax.set_ylim(10.0, 20.5)

    ax.grid(True, linestyle="--", alpha=0.55, zorder=1)
    ax.legend(loc="lower left", fontsize=8.8, framealpha=0.95, facecolor="white", edgecolor="#cccccc", ncol=2)

    plt.tight_layout()

    out_file = os.path.join("output", "margin_vs_hangtime_streamer_sweep.png")
    plt.savefig(out_file, dpi=300)
    print(f"Saved plot to {out_file}")

    # Copy to artifacts directory
    art_dir = r"C:\Users\kuron.HX99G\.gemini\antigravity\brain\07d75649-5831-48d4-9417-33296222f683"
    import shutil
    shutil.copy(out_file, os.path.join(art_dir, "margin_vs_hangtime_streamer_sweep.png"))
    print(f"Copied to artifact directory.")

if __name__ == "__main__":
    create_plot()
