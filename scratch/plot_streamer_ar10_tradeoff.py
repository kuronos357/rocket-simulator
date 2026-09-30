"""
Plot margin vs hangtime tradeoff with Streamer AR 1:10 Fixed.
Follows design of output/失敗版/margin_vs_hangtime_tradeoff.png
"""

import json
import os
import shutil
import matplotlib.pyplot as plt
import numpy as np

# Font setup for Japanese
plt.rcParams['font.sans-serif'] = ['Meiryo', 'Yu Gothic', 'MS Gothic', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

def create_plot():
    json_path = os.path.join("scratch", "streamer_ar10_sweep_results.json")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Loaded {len(data):,} simulation points with AR 1:10 fixed.")

    fig, ax = plt.subplots(figsize=(15, 8.5), dpi=300)

    # 1. Scatter points for each wing architecture
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
        alpha = 0.28 if "対称" in arch_name else 0.45
        size = 14 if "対称" in arch_name else 20
        ax.scatter(margins, times, c=color, label=arch_name, alpha=alpha, s=size, edgecolors="none", zorder=2)

    # 2. Pareto Frontiers for key AR 1:10 sizes
    margin_bins = np.linspace(0.55, 1.45, 45)
    frontier_configs = [
        {"L": 250, "W": 25, "color": "#8c564b", "ls": ":", "lw": 2.2, "label": "25x250mm (62.5cm², 規則最小・流失防止)"},
        {"L": 600, "W": 60, "color": "#9467bd", "ls": "--", "lw": 2.2, "label": "60x600mm (360cm², 中型)"},
        {"L": 1200, "W": 120, "color": "#d62728", "ls": "-", "lw": 2.8, "label": "120x1200mm (1440cm², 本命・高バランス)"},
        {"L": 1600, "W": 160, "color": "#e377c2", "ls": "-.", "lw": 2.5, "label": "160x1600mm (2560cm², 物理限界ピーク)"},
    ]

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

    # 3. Key Point Highlights & Annotations
    # Point 1: Global Maximum Peak (L=1600mm, 0.8 cal)
    cands_1600 = [d for d in data if d["streamer_L"] == 1600 and 0.78 <= d["margin"] <= 0.83]
    best_peak = max(cands_1600, key=lambda x: x["time"])
    ax.scatter([best_peak["margin"]], [best_peak["time"]], color="lime", edgecolor="black", s=180, zorder=7)
    ax.annotate(
        f"★【物理限界ピーク】L=1600mm (160x1600mm, 重量 7.38g)\n"
        f"滞空時間: {best_peak['time']:.2f} 秒 (高度 {best_peak['apogee']:.1f}m, 降下 {best_peak['v_desc']:.2f}m/s)\n"
        f"※これ以上大型化(1800mm)すると重量増で高度が落ち逆に滞空時間低下\n"
        f"翼構成: {best_peak['arch_name']} | 56x28mm (ct=2.8mm, λ=0.10)",
        xy=(best_peak["margin"], best_peak["time"]),
        xytext=(best_peak["margin"] - 0.22, best_peak["time"] + 1.2),
        arrowprops=dict(facecolor="black", shrink=0.08, width=1.5, headwidth=6),
        fontsize=9.2, fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.6", facecolor="#eaffea", edgecolor="#2ca02c", lw=1.5)
    )

    # Point 2: 120x1200mm at 1.0 cal (Recommended Competition Standard)
    cands_1200 = [d for d in data if d["streamer_L"] == 1200 and 0.98 <= d["margin"] <= 1.02]
    best_10 = max(cands_1200, key=lambda x: x["time"])
    ax.scatter([best_10["margin"]], [best_10["time"]], color="gold", edgecolor="black", s=180, zorder=7)
    ax.annotate(
        f"★【本命・実戦推奨】120x1200mm (マージン 1.0 cal)\n"
        f"滞空時間: {best_10['time']:.2f} 秒 (高度 {best_10['apogee']:.1f}m, 降下 {best_10['v_desc']:.2f}m/s)\n"
        f"翼構成: {best_10['arch_name']}\n"
        f"クリプトデルタ: {best_10['span']}x{best_10['cr']}mm (ct={best_10['ct']}mm, λ={best_10['tr']:.2f})\n"
        f"収納性・放出信頼性・強風耐性の総合バランス最高",
        xy=(best_10["margin"], best_10["time"]),
        xytext=(best_10["margin"] - 0.08, best_10["time"] + 1.3),
        arrowprops=dict(facecolor="black", shrink=0.08, width=1.5, headwidth=6),
        fontsize=9.2, fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.6", facecolor="#fff9d6", edgecolor="goldenrod", lw=1.5)
    )

    # Point 3: Small streamer (25x250mm, Rule minimum)
    cands_250 = [d for d in data if d["streamer_L"] == 250 and 0.70 <= d["margin"] <= 0.85]
    best_250 = max(cands_250, key=lambda x: x["time"])
    ax.scatter([best_250["margin"]], [best_250["time"]], color="#ff3366", edgecolor="black", s=150, zorder=7)
    ax.annotate(
        f"◆【流失防止・規則最小】25x250mm (AR 1:10 下限)\n"
        f"滞空時間: {best_250['time']:.2f} 秒 (高度 {best_250['apogee']:.1f}m, 降下 {best_250['v_desc']:.2f}m/s)\n"
        f"勝者: {best_250['arch_name']} (アンバランス独壇場)\n"
        f"クリプトデルタ: {best_250['span']}x{best_250['cr']}mm (λ={best_250['tr']:.2f})\n"
        f"強風時や狭い射場で確実に流失・ロストを防ぐ構成",
        xy=(best_250["margin"], best_250["time"]),
        xytext=(best_250["margin"] + 0.08, best_250["time"] - 1.8),
        arrowprops=dict(facecolor="black", shrink=0.08, width=1.5, headwidth=6),
        fontsize=8.8, fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#ffeef2", edgecolor="#ff3366", lw=1.3)
    )

    # 4. Background Safety Zone Bands
    ax.axvspan(0.55, 0.80, color="#d62728", alpha=0.05, label="低マージン領域 (無風・記録狙い)")
    ax.axvspan(0.80, 1.10, color="#ff7f0e", alpha=0.07, label="本命黄金領域 (0.8~1.1 cal: 性能と安定性の両立)")
    ax.axvspan(1.10, 1.55, color="#1f77b4", alpha=0.05, label="高安定安全領域 (1.2 cal〜: 強風対応・失格防止)")

    # 5. Titles & Labels
    ax.set_title(
        "モデルロケット 安定率 vs 滞空時間 設計マップ\n"
        "【アスペクト比 1:10 固定 (W=0.1L, W≧25mm) × ノーズ長 × クリプトデルタ翼 全パラメータ解析】",
        fontsize=13.5,
        fontweight="bold",
        pad=14
    )
    ax.set_xlabel("実効安全率（静的安定マージン） [cal = 口径倍率] (横軸: 右ほど安定・風に強い)", fontsize=11.5, labelpad=8)
    ax.set_ylabel("合計滞空時間 [秒] (縦軸: 上ほど長く滞空)", fontsize=11.5, labelpad=8)

    ax.set_xlim(0.55, 1.50)
    ax.set_ylim(8.0, 21.0)

    ax.grid(True, linestyle="--", alpha=0.55, zorder=1)
    ax.legend(loc="lower right", fontsize=8.8, framealpha=0.95, facecolor="white", edgecolor="#cccccc", ncol=1)

    plt.tight_layout()

    out_file = os.path.join("output", "margin_vs_hangtime_ar10.png")
    plt.savefig(out_file, dpi=300)
    print(f"Saved plot to {out_file}")

    art_dir = r"C:\Users\kuron.HX99G\.gemini\antigravity\brain\07d75649-5831-48d4-9417-33296222f683"
    shutil.copy(out_file, os.path.join(art_dir, "margin_vs_hangtime_ar10.png"))
    print(f"Copied to artifact directory.")

if __name__ == "__main__":
    create_plot()
