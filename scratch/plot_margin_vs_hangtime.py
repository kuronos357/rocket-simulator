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

def run_simulation_and_plot():
    print("=" * 80)
    print("GENERATING 2D PLOT: SAFETY MARGIN vs HANG TIME (INFILL=2%, TIP BALLAST DOF)")
    print("=" * 80)

    streamer_area = 250.0  # 50x500mm
    streamer_mass = 1.2
    streamer_cd = 0.25

    results = []

    # Rocket length L=250mm (user's favorite short rocket) + L=270mm for high-stability comparison
    lengths = [250, 270]
    ballast_masses = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5]  # Tip ballast mass degrees of freedom

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
                    infill_ratio=0.02, # Fixed at 2% as requested
                    material="PLA",
                    material_density=1.24,
                    motor_type="1/2A6-2",
                    ballast_mass_g=m_bal,
                    ballast_z_mm=float(L - 5.0), # Near the very tip of the nose
                    recovery_mass_g=streamer_mass,
                    recovery_area_cm2=streamer_area,
                    recovery_cd=streamer_cd,
                    descent_horizontal=True
                )
                opt = FinOptimizer(spec)

                # 1. 3-Fin scan (theta and kv)
                for th in [20, 25, 30, 35, 40]:
                    for vs in [0.5, 0.6, 0.7, 0.8, 1.0]:
                        for span in range(35, 85, 3):
                            for cr in range(25, 55, 3):
                                if span > 1.8 * cr or span < 0.35 * cr:
                                    continue
                                r = evaluate_physically_correct_fins(opt, float(span), float(cr), 0.0, float(th), vs, is_4fin=False)
                                m_eff = min(r["margin_pitch"], r["margin_yaw"])
                                if 0.50 <= m_eff <= 1.80 and r["total_time_s"] >= 24.0:
                                    is_asym = (th != 30 or vs != 1.0)
                                    results.append({
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

                # 2. 4-Fin scan (+ shape, symmetric & asym)
                for vs in [0.7, 0.8, 1.0]:
                    for span in range(35, 80, 3):
                        for cr in range(25, 55, 3):
                            if span > 1.8 * cr or span < 0.35 * cr:
                                continue
                            r = evaluate_physically_correct_fins(opt, float(span), float(cr), 0.0, 0.0, vs, is_4fin=True)
                            m_eff = min(r["margin_pitch"], r["margin_yaw"])
                            if 0.50 <= m_eff <= 1.80 and r["total_time_s"] >= 24.0:
                                is_asym = (vs != 1.0)
                                results.append({
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

    print(f"Total valid configurations simulated: {len(results)}")

    # Plotting
    fig, ax = plt.subplots(figsize=(13, 8))

    # Separate by type
    data_3asym = [r for r in results if r["type"] == "3-fin-asym"]
    data_3sym = [r for r in results if r["type"] == "3-fin-sym"]
    data_4 = [r for r in results if "4-fin" in r["type"]]

    # Scatter plot
    ax.scatter([r["margin_eff"] for r in data_4], [r["time"] for r in data_4],
               c="lightgray", s=18, alpha=0.35, label="4枚翼 (+字 対称/アンバランス)")
    ax.scatter([r["margin_eff"] for r in data_3sym], [r["time"] for r in data_3sym],
               c="skyblue", s=25, alpha=0.5, label="3枚翼 (120° 対称)")
    ax.scatter([r["margin_eff"] for r in data_3asym], [r["time"] for r in data_3asym],
               c="forestgreen", s=35, alpha=0.65, label="3枚翼 アンバランス (本命: θ, kv自由度)")

    # Calculate Pareto Front (Envelop curve of best hang time at each margin)
    margin_bins = np.linspace(0.60, 1.60, 51)
    pareto_margins = []
    pareto_times = []
    pareto_best = []

    for i in range(len(margin_bins) - 1):
        m_low, m_high = margin_bins[i], margin_bins[i+1]
        bin_candidates = [r for r in results if m_low <= r["margin_eff"] < m_high]
        if bin_candidates:
            best_in_bin = max(bin_candidates, key=lambda x: x["time"])
            pareto_margins.append((m_low + m_high) / 2.0)
            pareto_times.append(best_in_bin["time"])
            pareto_best.append(best_in_bin)

    ax.plot(pareto_margins, pareto_times, color="crimson", lw=2.5, ls="-", label="パレート最適フロンティア (最高性能限界線)")

    # Annotate key target points: 0.7, 0.9, 1.2
    # 1. Target 0.9 cal (User's favorite 3-fin asymmetric)
    p09_candidates = [r for r in data_3asym if 0.88 <= r["margin_eff"] <= 0.92]
    if p09_candidates:
        best_p09 = max(p09_candidates, key=lambda x: x["time"])
        ax.scatter([best_p09["margin_eff"]], [best_p09["time"]], color="gold", edgecolor="black", s=140, zorder=5)
        ax.annotate(
            f"★【本命】0.9部門 3枚翼アンバランス\n"
            f"安全率: +{best_p09['margin_eff']:.2f} cal | 滞空: {best_p09['time']:.2f}秒\n"
            f"L={best_p09['L']}mm, 先端質点: {best_p09['ballast']:.1f}g\n"
            f"主翼 {best_p09['span']}x{best_p09['cr']}mm (θ={best_p09['th']}°, kv={best_p09['vs']:.2f})",
            xy=(best_p09["margin_eff"], best_p09["time"]),
            xytext=(best_p09["margin_eff"] + 0.05, best_p09["time"] + 0.6),
            arrowprops=dict(facecolor="black", shrink=0.08, width=1.5, headwidth=6),
            fontsize=9.5, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#fff9d6", edgecolor="goldenrod", lw=1.5)
        )

    # 2. Target 0.7 cal (Extreme performance point)
    p07_candidates = [r for r in data_3asym if 0.69 <= r["margin_eff"] <= 0.72]
    if p07_candidates:
        best_p07 = max(p07_candidates, key=lambda x: x["time"])
        ax.scatter([best_p07["margin_eff"]], [best_p07["time"]], color="lime", edgecolor="black", s=140, zorder=5)
        ax.annotate(
            f"【0.7部門】極限レコード機\n"
            f"安全率: +{best_p07['margin_eff']:.2f} cal | 滞空: {best_p07['time']:.2f}秒\n"
            f"θ={best_p07['th']:.0f}°, kv={best_p07['vs']:.2f}, 先端質点: {best_p07['ballast']:.1f}g",
            xy=(best_p07["margin_eff"], best_p07["time"]),
            xytext=(best_p07["margin_eff"] - 0.12, best_p07["time"] - 1.2),
            arrowprops=dict(facecolor="green", shrink=0.08, width=1.5, headwidth=6),
            fontsize=9,
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#eaffea", edgecolor="green", lw=1.2)
        )

    # 3. Target 1.2 cal (Safe / High stability point unlocked by ballast/length)
    p12_candidates = [r for r in results if 1.19 <= r["margin_eff"] <= 1.23]
    if p12_candidates:
        best_p12 = max(p12_candidates, key=lambda x: x["time"])
        ax.scatter([best_p12["margin_eff"]], [best_p12["time"]], color="blue", edgecolor="black", s=140, zorder=5)
        ax.annotate(
            f"【1.2部門】安全重視機\n"
            f"安全率: +{best_p12['margin_eff']:.2f} cal | 滞空: {best_p12['time']:.2f}秒\n"
            f"L={best_p12['L']}mm, 先端質点: {best_p12['ballast']:.1f}g",
            xy=(best_p12["margin_eff"], best_p12["time"]),
            xytext=(best_p12["margin_eff"] + 0.05, best_p12["time"] - 0.9),
            arrowprops=dict(facecolor="blue", shrink=0.08, width=1.5, headwidth=6),
            fontsize=9,
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#eef4ff", edgecolor="blue", lw=1.2)
        )

    # Shaded zones for safety levels
    ax.axvspan(0.6, 0.8, color="red", alpha=0.06, label="低マージン領域 (無風・競技レコード狙い)")
    ax.axvspan(0.8, 1.1, color="gold", alpha=0.08, label="本命領域 (0.9 cal: 性能と安定性の黄金バランス)")
    ax.axvspan(1.1, 1.6, color="blue", alpha=0.06, label="安全重視領域 (1.2 cal: 強風対応)")

    ax.set_title(r"モデルロケット 安全率（安定マージン）vs 滞空時間 2次元設計マップ" + "\n" + r"(インフィル2%統一・先端質点自由度 $m_{ballast} \in [0.0 \sim 2.5\mathrm{g}]$)", fontsize=13, fontweight='bold', pad=12)
    ax.set_xlabel("実効安全率（静的安定マージン） [cal = 口径倍率] (横軸: 右ほど安定・強風向き)", fontsize=11)
    ax.set_ylabel("合計滞空時間 [秒] (縦軸: 上ほど長く飛ぶ)", fontsize=11)
    ax.set_xlim(0.55, 1.55)
    ax.set_ylim(25.0, 31.2)
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(loc="lower left", fontsize=9.5, framealpha=0.95)

    plt.tight_layout()
    os.makedirs("output", exist_ok=True)
    out_file = os.path.join("output", "margin_vs_hangtime_tradeoff.png")
    plt.savefig(out_file, dpi=300)
    print(f"Saved plot to {out_file}")

    # Copy to artifact directory
    import shutil
    art_dir = r"C:\Users\kuron.HX99G\.gemini\antigravity\brain\f5d3bd8b-8307-472d-83e6-9bd725805a5f"
    shutil.copy(out_file, os.path.join(art_dir, "margin_vs_hangtime_tradeoff.png"))
    print("Copied to artifact directory.")

if __name__ == "__main__":
    run_simulation_and_plot()
