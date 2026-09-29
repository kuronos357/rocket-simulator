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

def generate_comparison_plots():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # --- Plot 1: Scenario A (Yaw target relaxation) ---
    spec_500 = RocketSpec(
        total_length_mm=280.0,
        body_diameter_mm=24.0,
        nose_length_mm=110.0,
        tail_length_mm=0.0,
        wall_thickness_mm=0.4,
        infill_ratio=0.02,
        material="PLA",
        material_density=1.24,
        motor_type="1/2A6-2",
        recovery_mass_g=1.2,
        recovery_area_cm2=250.0,
        recovery_cd=0.25,
        descent_horizontal=True
    )
    opt_500 = FinOptimizer(spec_500)

    yaw_targets = np.linspace(0.6, 1.2, 7)
    opt_kvs = []
    opt_times = []
    opt_apogees = []
    opt_masses = []

    for target_yaw in yaw_targets:
        best = None
        for vs in np.linspace(0.5, 1.0, 11):
            for span in range(35, 75, 2):
                for cr in range(25, 60, 2):
                    if span > 1.5 * cr or span < 0.3 * cr:
                        continue
                    r = evaluate_physically_correct_fins(opt_500, span, cr, 0.0, 0.0, vs, is_4fin=True)
                    if r["margin_pitch"] >= 1.20 and r["margin_yaw"] >= target_yaw:
                        if best is None or r["total_time_s"] > best["total_time_s"]:
                            best = r
                            best["vs"] = vs
        if best:
            opt_kvs.append(best["vs"])
            opt_times.append(best["total_time_s"])
            opt_apogees.append(best["apogee_m"])
            opt_masses.append(best["fin_mass_g"])

    color1 = 'tab:blue'
    ax1.set_title("【条件1】ヨー安定要求の緩和によるアンバランス化\n(ピッチ≧1.20cal 維持, ストリーマー50x500mm)", fontsize=11, fontweight='bold')
    ax1.set_xlabel("要求ヨー安定マージン [cal]", fontsize=10)
    ax1.set_ylabel("最適垂直比率 kv = bv / bh", color=color1, fontsize=10)
    line1 = ax1.plot(yaw_targets, opt_kvs, 'o-', color=color1, lw=2, label="最適垂直比率 kv")
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.grid(True, linestyle="--", alpha=0.6)
    ax1.set_ylim(0.4, 1.1)

    ax1_twin = ax1.twinx()
    color2 = 'tab:red'
    ax1_twin.set_ylabel("滞空時間 [秒]", color=color2, fontsize=10)
    line2 = ax1_twin.plot(yaw_targets, opt_times, 's--', color=color2, lw=2, label="滞空時間 [s]")
    ax1_twin.tick_params(axis='y', labelcolor=color2)

    # Annotations
    ax1.annotate("対称4枚翼 (kv=1.0)\n26.71s / 123.6m", xy=(1.2, 1.0), xytext=(1.05, 0.92),
                 arrowprops=dict(facecolor='black', shrink=0.08, width=1, headwidth=5), fontsize=9)
    ax1.annotate("アンバランス飛行機尾翼 (kv=0.7)\n27.85s / 129.4m (+1.14s)", xy=(0.6, 0.7), xytext=(0.65, 0.55),
                 arrowprops=dict(facecolor='red', shrink=0.08, width=1, headwidth=5), fontsize=9, color='red', fontweight='bold')

    # --- Plot 2: Scenario B (Streamer Area vs Advantage of Asymmetry) ---
    streamer_areas = [20.0, 40.0, 62.5, 100.0, 150.0, 200.0, 250.0]
    times_sym = []
    times_asym = []

    for s_area in streamer_areas:
        rec_m = 0.5 if s_area < 100 else 1.2
        spec_c = RocketSpec(
            total_length_mm=280.0,
            body_diameter_mm=24.0,
            nose_length_mm=110.0,
            tail_length_mm=0.0,
            wall_thickness_mm=0.4,
            infill_ratio=0.02,
            material="PLA",
            material_density=1.24,
            motor_type="1/2A6-2",
            recovery_mass_g=rec_m,
            recovery_area_cm2=s_area,
            recovery_cd=0.25,
            descent_horizontal=True
        )
        opt_c = FinOptimizer(spec_c)

        # Symmetric (v=1.0)
        best_s = None
        for span in range(35, 75, 2):
            for cr in range(25, 60, 2):
                if span > 1.5 * cr or span < 0.3 * cr:
                    continue
                r = evaluate_physically_correct_fins(opt_c, span, cr, 0.0, 0.0, 1.0, is_4fin=True)
                if r["margin_pitch"] >= 1.20 and r["margin_yaw"] >= 1.20:
                    if best_s is None or r["total_time_s"] > best_s["total_time_s"]:
                        best_s = r

        # Asymmetric (v <= 0.8, larger spans allowed)
        best_a = None
        for vs in [0.6, 0.7, 0.8]:
            for span in range(40, 110, 3):
                for cr in range(30, 80, 3):
                    if span > 2.0 * cr or span < 0.3 * cr:
                        continue
                    r = evaluate_physically_correct_fins(opt_c, span, cr, 0.0, 0.0, vs, is_4fin=True)
                    if r["margin_pitch"] >= 1.20 and r["margin_yaw"] >= 1.20:
                        if best_a is None or r["total_time_s"] > best_a["total_time_s"]:
                            best_a = r

        times_sym.append(best_s["total_time_s"] if best_s else 0.0)
        times_asym.append(best_a["total_time_s"] if best_a else 0.0)

    time_diff = np.array(times_asym) - np.array(times_sym)

    ax2.set_title("【条件2】ストリーマー面積とアンバランス翼の勝敗\n(巨大水平主翼による水平降下ブレーキ効果)", fontsize=11, fontweight='bold')
    ax2.set_xlabel("ストリーマー面積 [cm²] (横軸)", fontsize=10)
    ax2.set_ylabel("アンバランス翼の滞空時間優位性 Δt [秒]\n(正ならアンバランス勝利 / 負なら対称勝利)", fontsize=10)

    bar_colors = ['green' if d > 0 else 'gray' for d in time_diff]
    bars = ax2.bar([str(int(a)) for a in streamer_areas], time_diff, color=bar_colors, width=0.55, edgecolor='black', alpha=0.85)
    ax2.axhline(0, color='black', lw=1.2, ls='--')
    ax2.grid(True, linestyle="--", alpha=0.5, axis='y')

    for bar, d in zip(bars, time_diff):
        yval = bar.get_height()
        va = 'bottom' if yval >= 0 else 'top'
        ax2.text(bar.get_x() + bar.get_width()/2.0, yval + (0.02 if yval>=0 else -0.05), f"{yval:+.2f}s", ha='center', va=va, fontsize=9, fontweight='bold')

    ax2.annotate("ストリーマー極小クラス(25x250mm以下):\n巨大水平翼のエアブレーキが効き\nアンバランス配置が+0.6〜0.7秒勝利！", xy=(1, 0.63), xytext=(1.5, 0.40),
                 arrowprops=dict(facecolor='green', shrink=0.08, width=1, headwidth=5), fontsize=9, color='green', fontweight='bold')
    ax2.annotate("ストリーマー大型クラス(50x500mm):\nストリーマーの抗力が圧倒的になり\n軽量な対称4枚翼が有利に近づく", xy=(6, 0.49), xytext=(3.5, 0.15),
                 arrowprops=dict(facecolor='black', shrink=0.08, width=1, headwidth=5), fontsize=9)

    plt.tight_layout()
    os.makedirs("output", exist_ok=True)
    out_path = os.path.join("output", "unbalanced_fin_conditions.png")
    plt.savefig(out_path, dpi=300)
    print(f"Graph saved to {out_path}")

    # Copy to artifact directory
    import shutil
    artifact_dir = r"C:\Users\kuron.HX99G\.gemini\antigravity\brain\f5d3bd8b-8307-472d-83e6-9bd725805a5f"
    shutil.copy(out_path, os.path.join(artifact_dir, "unbalanced_fin_conditions.png"))
    print("Copied to artifact directory.")

if __name__ == "__main__":
    generate_comparison_plots()
