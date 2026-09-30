"""
Generate All-Pattern Comprehensive Scatter Plots
Produces 3 high-resolution presentation plots:
1. all_patterns_scatter_detailed.png : Full annotated plot (PLA vs PP-CF, Lengths, Baseline comparison)
2. all_patterns_scatter_pure.png     : Textless / Naked presentation scatter plot
3. all_patterns_scatter_by_wing.png  : Colored by wing architecture (4-asym, 4-sym, 3-Y, 3-sym)
"""

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

def run_all_patterns_scatter():
    print("=" * 80)
    print("GENERATING ALL-PATTERNS SCATTER PLOTS (PLA, PP-CF, LENGTHS, WING TYPES)")
    print("=" * 80)

    streamer_area = 250.0
    streamer_mass = 1.2
    streamer_cd = 0.25

    results = []

    # Sweep configurations
    configs = [
        # (Material, Density, Lengths, Noses, Ballasts)
        ("PLA", 1.24, [250, 270, 300], [100, 120], [0.0, 1.0]),
        ("PP-CF", 0.95, [250], [100, 120], [0.0, 1.0]),
    ]

    for mat_name, mat_rho, lengths, noses, ballasts in configs:
        for L in lengths:
            for nose in noses:
                for m_bal in ballasts:
                    spec = RocketSpec(
                        total_length_mm=float(L),
                        body_diameter_mm=24.0,
                        nose_length_mm=float(nose),
                        tail_length_mm=0.0,
                        wall_thickness_mm=0.4,
                        infill_ratio=0.02,
                        material=mat_name,
                        material_density=mat_rho,
                        motor_type="1/2A6-2",
                        ballast_mass_g=m_bal,
                        ballast_z_mm=float(L - 5.0),
                        recovery_mass_g=streamer_mass,
                        recovery_area_cm2=streamer_area,
                        recovery_cd=streamer_cd,
                        descent_horizontal=True
                    )
                    opt = FinOptimizer(spec)

                    # 3-Fin scan (theta 25, 30, 35 deg)
                    for th in [25, 30, 35]:
                        for vs in [0.6, 0.7, 0.8, 1.0]:
                            for span in range(35, 85, 4):
                                for cr in range(25, 55, 4):
                                    if span > 1.8 * cr or span < 0.35 * cr:
                                        continue
                                    r = evaluate_physically_correct_fins(opt, float(span), float(cr), 0.0, float(th), vs, is_4fin=False)
                                    m_eff = min(r["margin_pitch"], r["margin_yaw"])
                                    if 0.65 <= m_eff <= 1.35 and r["total_time_s"] >= 7.5:
                                        is_asym = (th != 30 or vs != 1.0)
                                        results.append({
                                            "margin_eff": m_eff,
                                            "time": r["total_time_s"],
                                            "apogee": r["apogee_m"],
                                            "L": L,
                                            "material": mat_name,
                                            "type": "3枚非対称 (逆Y字)" if is_asym else "3枚対称 (120°)",
                                            "is_ppcf": (mat_name == "PP-CF")
                                        })

                    # 4-Fin scan
                    for vs in [0.70, 0.80, 0.85, 0.90, 1.0]:
                        for span in range(35, 75, 4):
                            for cr in range(20, 48, 4):
                                if span > 1.8 * cr or span < 0.35 * cr:
                                    continue
                                r = evaluate_physically_correct_fins(opt, float(span), float(cr), 0.0, 0.0, vs, is_4fin=True)
                                m_eff = min(r["margin_pitch"], r["margin_yaw"])
                                if 0.65 <= m_eff <= 1.35 and r["total_time_s"] >= 7.5:
                                    results.append({
                                        "margin_eff": m_eff,
                                        "time": r["total_time_s"],
                                        "apogee": r["apogee_m"],
                                        "L": L,
                                        "material": mat_name,
                                        "type": "4枚対称 (+字)" if vs == 1.0 else "4枚非対称 (十字)",
                                        "is_ppcf": (mat_name == "PP-CF")
                                    })

    print(f"Total simulated data points: {len(results)}")

    # Separate PLA and PP-CF
    pla_pts = [r for r in results if r["material"] == "PLA"]
    ppcf_pts = [r for r in results if r["material"] == "PP-CF"]

    # Calculate Pareto frontier for PLA (L=250mm)
    pla_250 = [r for r in pla_pts if r["L"] == 250]
    bins = np.linspace(0.68, 1.32, 45)
    pareto_pla = []
    for i in range(len(bins) - 1):
        cands = [r for r in pla_250 if bins[i] <= r["margin_eff"] < bins[i+1]]
        if cands:
            pareto_pla.append(max(cands, key=lambda x: x["time"]))

    # Calculate Pareto frontier for PP-CF (L=250mm)
    pareto_ppcf = []
    for i in range(len(bins) - 1):
        cands = [r for r in ppcf_pts if bins[i] <= r["margin_eff"] < bins[i+1]]
        if cands:
            pareto_ppcf.append(max(cands, key=lambda x: x["time"]))

    # Key Candidates
    c1 = {"margin": 0.79, "time": 9.59, "name": "機体①: 限界滞空型 (+0.79 cal, 9.6s)"}
    c2 = {"margin": 0.86, "time": 9.25, "name": "機体②: 超高安定型 (+0.86 cal, 9.3s)"}
    c3 = {"margin": 1.22, "time": 8.84, "name": "機体③: 鉄壁安全型 (+1.22 cal, 8.8s)"}
    c_base = {"margin": 1.15, "time": 10.23, "name": "ベースライン機 (つくば 190mm / 違反)"}

    os.makedirs("output", exist_ok=True)
    art_dir = r"C:\Users\kuron.HX99G\.gemini\antigravity\brain\f5d3bd8b-8307-472d-83e6-9bd725805a5f"

    # =========================================================================
    # PLOT 1: Comprehensive Annotated Scatter Plot (Detailed)
    # =========================================================================
    fig1, ax1 = plt.subplots(figsize=(16, 9), dpi=300)
    fig1.patch.set_facecolor('#ffffff')
    ax1.set_facecolor('#fafbfc')
    ax1.grid(True, linestyle="--", alpha=0.35, color="#b0bec5", zorder=1)

    # 1. Background cloud for PLA (L=270, 300)
    pla_long = [r for r in pla_pts if r["L"] > 250]
    ax1.scatter([r["margin_eff"] for r in pla_long], [r["time"] for r in pla_long],
                color="#b0bec5", s=25, alpha=0.30, edgecolor="none", zorder=2, label="PLA 長胴型 (L=270/300mm)")

    # 2. Main PLA L=250 points
    ax1.scatter([r["margin_eff"] for r in pla_250], [r["time"] for r in pla_250],
                color="#457b9d", s=35, alpha=0.55, edgecolor="none", zorder=3, label="PLA 標準機 (L=250mm 全探索)")

    # 3. PP-CF points cloud
    if ppcf_pts:
        ax1.scatter([r["margin_eff"] for r in ppcf_pts], [r["time"] for r in ppcf_pts],
                    color="#b5179e", s=35, alpha=0.55, edgecolor="none", zorder=3, label="PP-CF 炭素繊維複合 (L=250mm 全探索)")

    # 4. Pareto Frontier Lines
    if pareto_pla:
        ax1.plot([p["margin_eff"] for p in pareto_pla], [p["time"] for p in pareto_pla],
                 color="#e63946", lw=4.0, ls="-", zorder=5, label="PLA パレート最適フロンティア線")
    if pareto_ppcf:
        ax1.plot([p["margin_eff"] for p in pareto_ppcf], [p["time"] for p in pareto_ppcf],
                 color="#7209b7", lw=3.5, ls="--", zorder=5, label="PP-CF 最適フロンティア線 (+1.6秒向上)")

    # 5. Highlight 3 Main Candidates + Baseline
    ax1.scatter([c1["margin"]], [c1["time"]], s=420, facecolor="#00f5d4", edgecolor="#111111", lw=3.0, zorder=7, label=c1["name"])
    ax1.scatter([c2["margin"]], [c2["time"]], s=420, facecolor="#ffd166", edgecolor="#111111", lw=3.0, zorder=7, label=c2["name"])
    ax1.scatter([c3["margin"]], [c3["time"]], s=420, facecolor="#ef476f", edgecolor="#111111", lw=3.0, zorder=7, label=c3["name"])
    ax1.scatter([c_base["margin"]], [c_base["time"]], s=450, facecolor="#ffffff", edgecolor="#e63946", lw=3.5, marker="*", zorder=7, label=c_base["name"])

    # Labels and Legend
    ax1.set_xlim(0.68, 1.32)
    ax1.set_ylim(7.8, 12.0)
    ax1.set_xlabel("Static Stability Margin [cal]  (静的安定マージン)", fontsize=18, fontweight="bold", labelpad=12)
    ax1.set_ylabel("Total Flight Time [s]  (総滞空時間)", fontsize=18, fontweight="bold", labelpad=12)
    ax1.set_title("全設計パターン網羅 飛行時間 vs 安定性 パレートフロンティア散布図", fontsize=20, fontweight="bold", pad=16)
    ax1.tick_params(axis="both", labelsize=14)
    ax1.legend(loc="upper right", fontsize=11, framealpha=0.95, facecolor="#ffffff", edgecolor="#cfd8dc")

    plt.tight_layout()
    p1 = "output/all_patterns_scatter_detailed.png"
    fig1.savefig(p1, dpi=300)
    fig1.savefig(os.path.join(art_dir, "all_patterns_scatter_detailed.png"), dpi=300)
    plt.close(fig1)

    # =========================================================================
    # PLOT 2: Pure Naked Presentation Scatter Plot (文字・注釈一切なし)
    # =========================================================================
    fig2, ax2 = plt.subplots(figsize=(16, 9), dpi=300)
    fig2.patch.set_facecolor('#ffffff')
    ax2.set_facecolor('#fafbfc')
    ax2.grid(True, linestyle="--", alpha=0.35, color="#b0bec5", zorder=1)

    # Background cloud (PLA)
    ax2.scatter([r["margin_eff"] for r in pla_pts], [r["time"] for r in pla_pts],
                color="#cfd8dc", s=22, alpha=0.45, edgecolor="none", zorder=2)

    # PP-CF cloud
    if ppcf_pts:
        ax2.scatter([r["margin_eff"] for r in ppcf_pts], [r["time"] for r in ppcf_pts],
                    color="#e0aaff", s=22, alpha=0.40, edgecolor="none", zorder=3)

    # Pareto lines
    if pareto_pla:
        ax2.plot([p["margin_eff"] for p in pareto_pla], [p["time"] for p in pareto_pla],
                 color="#e63946", lw=4.5, ls="-", zorder=4)
        ax2.scatter([p["margin_eff"] for p in pareto_pla], [p["time"] for p in pareto_pla],
                    color="#e63946", s=80, edgecolor="#ffffff", lw=1.2, zorder=5)

    if pareto_ppcf:
        ax2.plot([p["margin_eff"] for p in pareto_ppcf], [p["time"] for p in pareto_ppcf],
                 color="#7209b7", lw=4.0, ls="--", zorder=4)

    # 3 Candidate Dots + Baseline (No text labels)
    ax2.scatter([c1["margin"]], [c1["time"]], s=500, facecolor="#00f5d4", edgecolor="#111111", lw=3.5, zorder=6)
    ax2.scatter([c2["margin"]], [c2["time"]], s=500, facecolor="#ffd166", edgecolor="#111111", lw=3.5, zorder=6)
    ax2.scatter([c3["margin"]], [c3["time"]], s=500, facecolor="#ef476f", edgecolor="#111111", lw=3.5, zorder=6)
    ax2.scatter([c_base["margin"]], [c_base["time"]], s=550, facecolor="#ffffff", edgecolor="#e63946", lw=4.0, marker="*", zorder=6)

    ax2.set_xlim(0.68, 1.32)
    ax2.set_ylim(7.8, 12.0)
    ax2.set_xlabel("Static Stability Margin [cal]", fontsize=18, fontweight="bold", labelpad=12)
    ax2.set_ylabel("Total Flight Time [s]", fontsize=18, fontweight="bold", labelpad=12)
    ax2.tick_params(axis="both", labelsize=14)

    plt.tight_layout()
    p2 = "output/all_patterns_scatter_pure.png"
    fig2.savefig(p2, dpi=300)
    fig2.savefig(os.path.join(art_dir, "all_patterns_scatter_pure.png"), dpi=300)
    plt.close(fig2)

    # =========================================================================
    # PLOT 3: Architecture-Colored Scatter Plot (4枚非対称/4枚対称/逆Y字/120°)
    # =========================================================================
    fig3, ax3 = plt.subplots(figsize=(16, 9), dpi=300)
    fig3.patch.set_facecolor('#ffffff')
    ax3.set_facecolor('#fafbfc')
    ax3.grid(True, linestyle="--", alpha=0.35, color="#b0bec5", zorder=1)

    arch_styles = {
        "4枚非対称 (十字)": {"color": "#e63946", "marker": "D", "size": 65, "label": "4枚非対称 十字翼 (Cross Asym)"},
        "4枚対称 (+字)": {"color": "#1d3557", "marker": "s", "size": 65, "label": "4枚対称 十字翼 (Cross Sym)"},
        "3枚非対称 (逆Y字)": {"color": "#f4a261", "marker": "o", "size": 75, "label": "3枚非対称 逆Y字翼 (Inverted-Y 35°)"},
        "3枚対称 (120°)": {"color": "#2a9d8f", "marker": "^", "size": 75, "label": "3枚対称 120°翼 (3-Fin Sym)"},
    }

    for a_type, st in arch_styles.items():
        sub = [r for r in pla_250 if r["type"] == a_type]
        if sub:
            ax3.scatter([r["margin_eff"] for r in sub], [r["time"] for r in sub],
                        color=st["color"], marker=st["marker"], s=st["size"], alpha=0.75,
                        edgecolor="#ffffff", lw=0.8, zorder=3, label=st["label"])

    if pareto_pla:
        ax3.plot([p["margin_eff"] for p in pareto_pla], [p["time"] for p in pareto_pla],
                 color="#111111", lw=3.5, ls="-", zorder=4, label="パレート最適限界線 (Pareto Frontier)")

    # Highlight Candidates
    ax3.scatter([c1["margin"]], [c1["time"]], s=450, facecolor="#00f5d4", edgecolor="#111111", lw=3.0, zorder=6, label=c1["name"])
    ax3.scatter([c2["margin"]], [c2["time"]], s=450, facecolor="#ffd166", edgecolor="#111111", lw=3.0, zorder=6, label=c2["name"])
    ax3.scatter([c3["margin"]], [c3["time"]], s=450, facecolor="#ef476f", edgecolor="#111111", lw=3.0, zorder=6, label=c3["name"])

    ax3.set_xlim(0.68, 1.32)
    ax3.set_ylim(8.0, 10.2)
    ax3.set_xlabel("Static Stability Margin [cal]  (静的安定マージン)", fontsize=18, fontweight="bold", labelpad=12)
    ax3.set_ylabel("Total Flight Time [s]  (総滞空時間)", fontsize=18, fontweight="bold", labelpad=12)
    ax3.set_title("4大翼形式別 全探索散布図とパレートフロンティア (L=250mm, PLA)", fontsize=20, fontweight="bold", pad=16)
    ax3.tick_params(axis="both", labelsize=14)
    ax3.legend(loc="upper right", fontsize=12, framealpha=0.95, facecolor="#ffffff", edgecolor="#cfd8dc")

    plt.tight_layout()
    p3 = "output/all_patterns_scatter_by_wing.png"
    fig3.savefig(p3, dpi=300)
    fig3.savefig(os.path.join(art_dir, "all_patterns_scatter_by_wing.png"), dpi=300)
    plt.close(fig3)

    print("ALL SCATTER PLOTS GENERATED AND SAVED SUCCESSFULLY!")

if __name__ == "__main__":
    run_all_patterns_scatter()
