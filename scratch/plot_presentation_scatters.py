import sys
import os
import math
import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.abspath("."))
from sim_engine.optimizer import RocketSpec, FinOptimizer
from scratch.test_correct_physics import evaluate_physically_correct_fins

plt.rcParams['font.sans-serif'] = ['Yu Gothic', 'Meiryo', 'DejaVu Sans', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

def generate_presentation_scatters():
    print("=" * 80)
    print("GENERATING PRESENTATION-READY SCATTER PLOTS (TEXT-FREE & CLEAN EDITIONS)")
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
                    infill_ratio=0.02,
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
                                if 0.60 <= m_eff <= 1.50 and r["total_time_s"] >= 26.0:
                                    is_asym = (th != 30 or vs != 1.0)
                                    results.append({
                                        "margin_eff": m_eff,
                                        "time": r["total_time_s"],
                                        "apogee": r["apogee_m"],
                                        "L": L,
                                        "nose": nose,
                                        "ballast": m_bal,
                                        "span": span,
                                        "cr": cr,
                                        "th": th,
                                        "vs": vs,
                                        "type": "3-fin-asym" if is_asym else "3-fin-sym"
                                    })

                # 4-Fin scan
                for vs in [0.70, 0.80, 0.85, 0.90, 1.0]:
                    for span in range(35, 75, 2):
                        for cr in range(20, 48, 2):
                            if span > 1.8 * cr or span < 0.35 * cr:
                                continue
                            r = evaluate_physically_correct_fins(opt, float(span), float(cr), 0.0, 0.0, vs, is_4fin=True)
                            m_eff = min(r["margin_pitch"], r["margin_yaw"])
                            if 0.60 <= m_eff <= 1.50 and r["total_time_s"] >= 26.0:
                                results.append({
                                    "margin_eff": m_eff,
                                    "time": r["total_time_s"],
                                    "apogee": r["apogee_m"],
                                    "L": L,
                                    "nose": nose,
                                    "ballast": m_bal,
                                    "span": span,
                                    "cr": cr,
                                    "th": 0.0,
                                    "vs": vs,
                                    "type": "4-fin-sym" if vs == 1.0 else "4-fin-asym"
                                })

    print(f"Total simulated candidates: {len(results)}")

    # Calculate Pareto Frontier
    margin_bins = np.linspace(0.68, 1.35, 68)
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

    # Filter near-frontier points for crystal-clear presentation (within 1.2s of Pareto)
    near_points = []
    for r in results:
        m = r["margin_eff"]
        dists = [abs(pm - m) for pm in pareto_margins]
        if dists:
            min_idx = np.argmin(dists)
            if dists[min_idx] < 0.04 and (pareto_times[min_idx] - r["time"]) < 1.2:
                near_points.append(r)

    n_3asym = [r for r in near_points if r["type"] == "3-fin-asym"]
    n_3sym = [r for r in near_points if r["type"] == "3-fin-sym"]
    n_4sym = [r for r in near_points if r["type"] == "4-fin-sym"]
    n_4asym = [r for r in near_points if r["type"] == "4-fin-asym"]

    os.makedirs("output", exist_ok=True)
    art_dir = r"C:\Users\kuron.HX99G\.gemini\antigravity\brain\f5d3bd8b-8307-472d-83e6-9bd725805a5f"

    # =========================================================================
    # PLOT 1: Presentation Clean (16:9 Aspect Ratio, Minimal English Axis, No Text Callouts)
    # =========================================================================
    fig1, ax1 = plt.subplots(figsize=(16, 9), dpi=300)

    # Plot Scatter Points
    ax1.scatter([r["margin_eff"] for r in n_4sym], [r["time"] for r in n_4sym],
                color="#2b5c8f", marker="s", s=65, alpha=0.70, edgecolors="#122a47", linewidths=0.8, zorder=3, label="4-Fin Symmetric")
    ax1.scatter([r["margin_eff"] for r in n_4asym], [r["time"] for r in n_4asym],
                color="#7b4397", marker="D", s=55, alpha=0.70, edgecolors="#431c59", linewidths=0.8, zorder=3, label="4-Fin Asymmetric")
    ax1.scatter([r["margin_eff"] for r in n_3sym], [r["time"] for r in n_3sym],
                color="#00a896", marker="^", s=70, alpha=0.75, edgecolors="#025e54", linewidths=0.8, zorder=3, label="3-Fin Symmetric (120°)")
    ax1.scatter([r["margin_eff"] for r in n_3asym], [r["time"] for r in n_3asym],
                color="#2ec4b6", marker="o", s=75, alpha=0.85, edgecolors="#014f47", linewidths=0.8, zorder=4, label="3-Fin Inverted-Y Asymmetric")

    # Pareto Line
    ax1.plot(pareto_margins, pareto_times, color="#e63946", lw=3.5, ls="-", label="Pareto Frontier", zorder=5)

    # Highlight Optimal Candidate Dots without text balloons
    # Candidate 1 dot (0.80 cal)
    p1 = [r for r in pareto_best if 0.79 <= r["margin_eff"] <= 0.81]
    if p1:
        c1 = max(p1, key=lambda x: x["time"])
        ax1.scatter([c1["margin_eff"]], [c1["time"]], s=250, facecolor="#00f5d4", edgecolor="#111111", lw=2.5, zorder=6)

    # Candidate 2 dot (0.86 cal)
    p09 = [r for r in pareto_best if 0.85 <= r["margin_eff"] <= 0.88]
    if p09:
        c09 = max(p09, key=lambda x: x["time"])
        ax1.scatter([c09["margin_eff"]], [c09["time"]], s=280, facecolor="#ffd166", edgecolor="#111111", lw=2.5, zorder=6)

    # Candidate 3 dot (1.20-1.22 cal)
    p12 = [r for r in pareto_best if 1.20 <= r["margin_eff"] <= 1.23]
    if p12:
        c12 = max(p12, key=lambda x: x["time"])
        ax1.scatter([c12["margin_eff"]], [c12["time"]], s=250, facecolor="#118ab2", edgecolor="#111111", lw=2.5, zorder=6)

    ax1.set_xlim(0.68, 1.32)
    ax1.set_ylim(28.0, 31.1)
    ax1.set_xlabel("Static Stability Margin [cal]", fontsize=14, fontweight="bold", labelpad=10)
    ax1.set_ylabel("Total Flight Time [s]", fontsize=14, fontweight="bold", labelpad=10)
    ax1.tick_params(axis="both", which="major", labelsize=12)
    ax1.grid(True, linestyle="--", alpha=0.45)
    ax1.legend(loc="lower left", fontsize=12, framealpha=0.95, edgecolor="gray")

    plt.tight_layout()
    out_clean = os.path.join("output", "pareto_scatter_presentation_clean.png")
    fig1.savefig(out_clean, dpi=300)
    fig1.savefig(os.path.join(art_dir, "pareto_scatter_presentation_clean.png"), dpi=300)
    print(f"Saved: {out_clean}")

    # =========================================================================
    # PLOT 2: Pure Raw Scatter (Zero Text: No title, No labels, No legend, Just Data)
    # =========================================================================
    fig2, ax2 = plt.subplots(figsize=(16, 9), dpi=300)

    ax2.scatter([r["margin_eff"] for r in n_4sym], [r["time"] for r in n_4sym],
                color="#2b5c8f", marker="s", s=65, alpha=0.70, edgecolors="#122a47", linewidths=0.8, zorder=3)
    ax2.scatter([r["margin_eff"] for r in n_4asym], [r["time"] for r in n_4asym],
                color="#7b4397", marker="D", s=55, alpha=0.70, edgecolors="#431c59", linewidths=0.8, zorder=3)
    ax2.scatter([r["margin_eff"] for r in n_3sym], [r["time"] for r in n_3sym],
                color="#00a896", marker="^", s=70, alpha=0.75, edgecolors="#025e54", linewidths=0.8, zorder=3)
    ax2.scatter([r["margin_eff"] for r in n_3asym], [r["time"] for r in n_3asym],
                color="#2ec4b6", marker="o", s=75, alpha=0.85, edgecolors="#014f47", linewidths=0.8, zorder=4)

    ax2.plot(pareto_margins, pareto_times, color="#e63946", lw=3.5, ls="-", zorder=5)

    if p1:
        ax2.scatter([c1["margin_eff"]], [c1["time"]], s=260, facecolor="#00f5d4", edgecolor="#111111", lw=2.5, zorder=6)
    if p09:
        ax2.scatter([c09["margin_eff"]], [c09["time"]], s=290, facecolor="#ffd166", edgecolor="#111111", lw=2.5, zorder=6)
    if p12:
        ax2.scatter([c12["margin_eff"]], [c12["time"]], s=260, facecolor="#118ab2", edgecolor="#111111", lw=2.5, zorder=6)

    ax2.set_xlim(0.68, 1.32)
    ax2.set_ylim(28.0, 31.1)
    ax2.tick_params(axis="both", which="major", labelsize=11)
    ax2.grid(True, linestyle="--", alpha=0.40)

    plt.tight_layout()
    out_pure = os.path.join("output", "pareto_scatter_presentation_pure.png")
    fig2.savefig(out_pure, dpi=300)
    fig2.savefig(os.path.join(art_dir, "pareto_scatter_presentation_pure.png"), dpi=300)
    print(f"Saved: {out_pure}")

    # =========================================================================
    # PLOT 3: Pure Raw Scatter (Completely Naked, No Axis Ticks, Transparent Option)
    # =========================================================================
    fig3, ax3 = plt.subplots(figsize=(16, 9), dpi=300)

    ax3.scatter([r["margin_eff"] for r in n_4sym], [r["time"] for r in n_4sym],
                color="#2b5c8f", marker="s", s=70, alpha=0.70, edgecolors="#122a47", linewidths=0.8, zorder=3)
    ax3.scatter([r["margin_eff"] for r in n_4asym], [r["time"] for r in n_4asym],
                color="#7b4397", marker="D", s=60, alpha=0.70, edgecolors="#431c59", linewidths=0.8, zorder=3)
    ax3.scatter([r["margin_eff"] for r in n_3sym], [r["time"] for r in n_3sym],
                color="#00a896", marker="^", s=75, alpha=0.75, edgecolors="#025e54", linewidths=0.8, zorder=3)
    ax3.scatter([r["margin_eff"] for r in n_3asym], [r["time"] for r in n_3asym],
                color="#2ec4b6", marker="o", s=80, alpha=0.85, edgecolors="#014f47", linewidths=0.8, zorder=4)

    ax3.plot(pareto_margins, pareto_times, color="#e63946", lw=4.0, ls="-", zorder=5)

    if p1:
        ax3.scatter([c1["margin_eff"]], [c1["time"]], s=280, facecolor="#00f5d4", edgecolor="#111111", lw=2.5, zorder=6)
    if p09:
        ax3.scatter([c09["margin_eff"]], [c09["time"]], s=320, facecolor="#ffd166", edgecolor="#111111", lw=2.5, zorder=6)
    if p12:
        ax3.scatter([c12["margin_eff"]], [c12["time"]], s=280, facecolor="#118ab2", edgecolor="#111111", lw=2.5, zorder=6)

    ax3.set_xlim(0.68, 1.32)
    ax3.set_ylim(28.0, 31.1)
    ax3.set_xticks([])
    ax3.set_yticks([])
    ax3.grid(True, linestyle="--", alpha=0.30)
    for spine in ax3.spines.values():
        spine.set_color("#888888")
        spine.set_linewidth(1.0)

    plt.tight_layout()
    out_naked = os.path.join("output", "pareto_scatter_presentation_naked.png")
    fig3.savefig(out_naked, dpi=300)
    fig3.savefig(os.path.join(art_dir, "pareto_scatter_presentation_naked.png"), dpi=300)
    print(f"Saved: {out_naked}")

    print("All presentation scatter plots successfully generated!")

if __name__ == "__main__":
    generate_presentation_scatters()
