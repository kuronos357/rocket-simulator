import sys
import os
import math
import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.abspath("."))
from sim_engine.optimizer import RocketSpec, FinOptimizer
from scratch.test_correct_physics import evaluate_physically_correct_fins

# Set font
plt.rcParams['font.sans-serif'] = ['Yu Gothic', 'Meiryo', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def run_zoomed_pareto_plot():
    print("=" * 80)
    print("GENERATING ZOOMED PARETO-FOCUSED PLOT")
    print("=" * 80)

    streamer_area = 250.0  # 50x500mm
    streamer_mass = 1.2
    streamer_cd = 0.25

    results = []

    lengths = [250, 270]
    ballast_masses = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5]

    for L in lengths:
        max_nose = int(0.48 * L)
        for nose in [80, 100, 115, max_nose]:
            for m_bal in ballast_masses:
                spec = RocketSpec(
                    total_length_mm=float(L),
                    body_diameter_mm=24.0,
                    nose_length_mm=float(nose),
                    tail_length_mm=0.0,
                    wall_thickness_mm=0.4,
                    infill_ratio=0.02, # 2% unified
                    material="PLA",
                    material_density=1.24,
                    motor_type="1/2A6-2",
                    ballast_mass_g=m_bal,
                    ballast_z_mm=float(L - 5.0),
                    recovery_mass_g=streamer_mass,
                    recovery_area_cm2=streamer_area,
                    recovery_cd=streamer_cd,
                    descent_horizontal=True
                )
                opt = FinOptimizer(spec)

                # 3-Fin scan
                for th in [20, 25, 30, 35, 40]:
                    for vs in [0.5, 0.6, 0.7, 0.8, 1.0]:
                        for span in range(35, 85, 2):
                            for cr in range(25, 55, 2):
                                if span > 1.8 * cr or span < 0.35 * cr:
                                    continue
                                r = evaluate_physically_correct_fins(opt, float(span), float(cr), 0.0, float(th), vs, is_4fin=False)
                                m_eff = min(r["margin_pitch"], r["margin_yaw"])
                                if 0.65 <= m_eff <= 1.35 and r["total_time_s"] >= 27.5:
                                    is_asym = (th != 30 or vs != 1.0)
                                    results.append({
                                        **r,
                                        "margin_eff": m_eff,
                                        "time": r["total_time_s"],
                                        "apogee": r["apogee_m"],
                                        "L": L,
                                        "nose": nose,
                                        "ballast": m_bal,
                                        "type": "3-fin-asym" if is_asym else "3-fin-sym",
                                        "span": span,
                                        "cr": cr,
                                        "th": th,
                                        "vs": vs
                                    })

                # 4-Fin scan
                for vs in [0.7, 0.8, 1.0]:
                    for span in range(35, 80, 2):
                        for cr in range(25, 55, 2):
                            if span > 1.8 * cr or span < 0.35 * cr:
                                continue
                            r = evaluate_physically_correct_fins(opt, float(span), float(cr), 0.0, 0.0, vs, is_4fin=True)
                            m_eff = min(r["margin_pitch"], r["margin_yaw"])
                            if 0.65 <= m_eff <= 1.35 and r["total_time_s"] >= 27.5:
                                is_asym = (vs != 1.0)
                                results.append({
                                    **r,
                                    "margin_eff": m_eff,
                                    "time": r["total_time_s"],
                                    "apogee": r["apogee_m"],
                                    "L": L,
                                    "nose": nose,
                                    "ballast": m_bal,
                                    "type": "4-fin-asym" if is_asym else "4-fin-sym",
                                    "span": span,
                                    "cr": cr,
                                    "th": 0,
                                    "vs": vs
                                })

    print(f"Total candidate points in high-performance zone: {len(results)}")

    # Calculate Pareto frontier
    margin_bins = np.linspace(0.66, 1.34, 40)
    pareto_margins = []
    pareto_times = []
    pareto_best = []

    for i in range(len(margin_bins) - 1):
        m_low, m_high = margin_bins[i], margin_bins[i+1]
        bin_cands = [r for r in results if m_low <= r["margin_eff"] < m_high]
        if bin_cands:
            best = max(bin_cands, key=lambda x: x["time"])
            pareto_margins.append((m_low + m_high) / 2.0)
            pareto_times.append(best["time"])
            pareto_best.append(best)

    # Filter points to only those CLOSE to the red line (within 0.35s of the frontier)
    near_frontier_points = []
    for r in results:
        # find closest pareto time
        idx = np.argmin(np.abs(np.array(pareto_margins) - r["margin_eff"]))
        p_time = pareto_times[idx]
        if r["time"] >= p_time - 0.35: # within 0.35s of maximum
            near_frontier_points.append(r)

    print(f"Points selected near Pareto frontier: {len(near_frontier_points)}")

    # Create clean, high-resolution figure
    fig, ax = plt.subplots(figsize=(14, 8.5))

    # Separate near-frontier points by configuration type
    n_3asym = [r for r in near_frontier_points if r["type"] == "3-fin-asym"]
    n_3sym = [r for r in near_frontier_points if r["type"] == "3-fin-sym"]
    n_4sym = [r for r in near_frontier_points if r["type"] == "4-fin-sym"]
    n_4asym = [r for r in near_frontier_points if r["type"] == "4-fin-asym"]

    # Scatter with distinct markers and colors
    ax.scatter([r["margin_eff"] for r in n_4sym], [r["time"] for r in n_4sym],
               color="royalblue", marker="s", s=55, alpha=0.75, label="4枚翼 (+字 対称)", edgecolors="navy", zorder=3)
    ax.scatter([r["margin_eff"] for r in n_4asym], [r["time"] for r in n_4asym],
               color="mediumpurple", marker="D", s=50, alpha=0.75, label="4枚翼 (+字 アンバランス)", edgecolors="purple", zorder=3)
    ax.scatter([r["margin_eff"] for r in n_3sym], [r["time"] for r in n_3sym],
               color="cyan", marker="^", s=65, alpha=0.75, label="3枚翼 (120° 対称)", edgecolors="teal", zorder=3)
    ax.scatter([r["margin_eff"] for r in n_3asym], [r["time"] for r in n_3asym],
               color="limegreen", marker="o", s=60, alpha=0.85, label="3枚翼 (逆Y字 アンバランス: 本命)", edgecolors="darkgreen", zorder=4)

    # Plot Pareto line
    ax.plot(pareto_margins, pareto_times, color="crimson", lw=3.0, ls="-", label="パレート最適フロンティア (理論最高性能線)", zorder=5)

    # Key highlight annotations with clean callouts
    # 1. Peak 1 (0.80 cal)
    p1 = [r for r in pareto_best if 0.79 <= r["margin_eff"] <= 0.82]
    if p1:
        c1 = max(p1, key=lambda x: x["time"])
        ax.scatter([c1["margin_eff"]], [c1["time"]], s=180, facecolor="lime", edgecolor="black", lw=2, zorder=6)
        ax.annotate(
            f"【極大点①】3枚翼アンバランス (主翼ブレーキ効果)\n"
            f"・安全率: +{c1['margin_eff']:.2f} cal | 滞空: {c1['time']:.2f} 秒\n"
            f"・主翼: {c1['span']}×{c1['cr']} mm (θ={c1['th']}°, kv={c1['vs']:.2f})\n"
            f"・尾翼: {c1['span']*c1['vs']:.1f} mm | 高度: {c1['apogee']:.1f} m\n"
            f"・先端質点: 0.0 g (オモリ不要)",
            xy=(c1["margin_eff"], c1["time"]),
            xytext=(c1["margin_eff"] - 0.09, c1["time"] + 0.32),
            arrowprops=dict(facecolor="black", shrink=0.08, width=1.5, headwidth=6),
            fontsize=9.5, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#f0fff0", edgecolor="green", lw=1.5)
        )

    # 2. Main Choice (0.89 cal)
    p09 = [r for r in pareto_best if 0.88 <= r["margin_eff"] <= 0.91]
    if p09:
        c09 = max(p09, key=lambda x: x["time"])
        ax.scatter([c09["margin_eff"]], [c09["time"]], s=200, facecolor="gold", edgecolor="black", lw=2, zorder=6)
        ax.annotate(
            f"★【本命】0.9部門 3枚翼アンバランス (黄金スイートスポット)\n"
            f"・安全率: +{c09['margin_eff']:.2f} cal | 滞空: {c09['time']:.2f} 秒\n"
            f"・主翼: {c09['span']}×{c09['cr']} mm (θ={c09['th']}°, kv={c09['vs']:.2f})\n"
            f"・尾翼: {c09['span']*c09['vs']:.1f} mm | 高度: {c09['apogee']:.1f} m\n"
            f"・先端質点: 0.0 g (オモリ不要)",
            xy=(c09["margin_eff"], c09["time"]),
            xytext=(c09["margin_eff"] + 0.04, c09["time"] + 0.45),
            arrowprops=dict(facecolor="black", shrink=0.08, width=1.5, headwidth=6),
            fontsize=9.5, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#fffde6", edgecolor="goldenrod", lw=2.0)
        )

    # 3. Peak 2 (0.95 cal)
    p2 = [r for r in pareto_best if 0.94 <= r["margin_eff"] <= 0.96]
    if p2:
        c2 = max(p2, key=lambda x: x["time"])
        ax.scatter([c2["margin_eff"]], [c2["time"]], s=180, facecolor="cyan", edgecolor="black", lw=2, zorder=6)
        ax.annotate(
            f"【極大点②】4枚翼対称 (幾何学的対称の黄金解)\n"
            f"・安全率: +{c2['margin_eff']:.2f} cal | 滞空: {c2['time']:.2f} 秒\n"
            f"・翼(4枚同形): {c2['span']}×{c2['cr']} mm (十字型)\n"
            f"・高度: {c2['apogee']:.1f} m | 先端質点: 0.0 g",
            xy=(c2["margin_eff"], c2["time"]),
            xytext=(1.01, 30.15),
            arrowprops=dict(facecolor="royalblue", shrink=0.08, width=1.5, headwidth=6),
            fontsize=9.5, fontweight="bold", zorder=10,
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#eef8ff", edgecolor="royalblue", lw=1.5)
        )

    # 4. High Stability Point (1.20~1.22 cal)
    p12 = [r for r in pareto_best if 1.20 <= r["margin_eff"] <= 1.23]
    if p12:
        c12 = max(p12, key=lambda x: x["time"])
        ax.scatter([c12["margin_eff"]], [c12["time"]], s=180, facecolor="blue", edgecolor="black", lw=2, zorder=6)
        ax.annotate(
            f"【1.2部門】安全重視機 (先端質点で解禁)\n"
            f"・安全率: +{c12['margin_eff']:.2f} cal | 滞空: {c12['time']:.2f} 秒\n"
            f"・L={c12['L']} mm | 先端質点: {c12['ballast']:.1f} g\n"
            f"・強風でも矢のように直進する鉄壁仕様",
            xy=(c12["margin_eff"], c12["time"]),
            xytext=(1.16, 29.35),
            arrowprops=dict(facecolor="blue", shrink=0.08, width=1.5, headwidth=6),
            fontsize=9.5, fontweight="bold", zorder=10,
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#f0f4ff", edgecolor="blue", lw=1.5)
        )

    # Grid and axis limits (Zoomed into high-performance region)
    ax.set_xlim(0.68, 1.32)
    ax.set_ylim(27.8, 31.2)
    ax.set_xlabel("実効安全率（静的安定マージン） [cal = 口径倍率] (横軸)", fontsize=11, fontweight="bold")
    ax.set_ylabel("合計滞空時間 [秒] (縦軸: ズーム表示 27.8s 〜 31.2s)", fontsize=11, fontweight="bold")
    ax.set_title("モデルロケット 最高性能限界（パレートフロンティア）周辺データ拡大図\n(インフィル2%統一・先端質点自由度 $m_{ballast} \in [0.0 \sim 2.5\mathrm{g}]$)", fontsize=13, fontweight="bold", pad=12)

    ax.grid(True, linestyle="--", alpha=0.55)
    ax.legend(loc="lower left", fontsize=10, framealpha=0.95, edgecolor="gray")

    plt.tight_layout()
    os.makedirs("output", exist_ok=True)
    out_file = os.path.join("output", "pareto_frontier_zoomed.png")
    plt.savefig(out_file, dpi=300)
    print(f"Saved zoomed plot to {out_file}")

    # Copy to artifact
    import shutil
    art_dir = r"C:\Users\kuron.HX99G\.gemini\antigravity\brain\f5d3bd8b-8307-472d-83e6-9bd725805a5f"
    shutil.copy(out_file, os.path.join(art_dir, "pareto_frontier_zoomed.png"))
    print("Copied to artifact directory.")

if __name__ == "__main__":
    run_zoomed_pareto_plot()
