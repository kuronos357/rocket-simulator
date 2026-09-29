import sys
import os
sys.path.insert(0, os.path.abspath("."))
import matplotlib.pyplot as plt
import numpy as np

from sim_engine.optimizer import RocketSpec, FinOptimizer
from sim_engine.mdo import FullRocketOptimizer

def main():
    # Define streamer sizes (Aspect ratio 10:1, length >= 10 * width as per JAR rules)
    streamer_configs = [
        {"name": "25x250mm (JAR最小)", "w_mm": 25, "l_mm": 250, "area_cm2": 62.5, "mass_g": 0.5},
        {"name": "30x300mm", "w_mm": 30, "l_mm": 300, "area_cm2": 90.0, "mass_g": 0.6},
        {"name": "40x400mm", "w_mm": 40, "l_mm": 400, "area_cm2": 160.0, "mass_g": 0.9},
        {"name": "50x500mm (代表値)", "w_mm": 50, "l_mm": 500, "area_cm2": 250.0, "mass_g": 1.2},
        {"name": "60x600mm", "w_mm": 60, "l_mm": 600, "area_cm2": 360.0, "mass_g": 1.6},
        {"name": "75x750mm", "w_mm": 75, "l_mm": 750, "area_cm2": 562.5, "mass_g": 2.2},
        {"name": "100x1000mm", "w_mm": 100, "l_mm": 1000, "area_cm2": 1000.0, "mass_g": 3.5},
    ]

    results = []

    print("=== Running Streamer Size Sweep for JAR Competition ===")
    print("Motor: 1/2A6-2, Diameter: 24mm, Wall: 0.4mm, Infill: 2%, Stability Margin >= +1.20 cal\n")

    for sc in streamer_configs:
        area = sc["area_cm2"]
        mass = sc["mass_g"]
        
        spec = RocketSpec(
            total_length_mm=280.0,
            body_diameter_mm=24.0,
            nose_length_mm=100.0,
            tail_length_mm=0.0,
            wall_thickness_mm=0.4,
            infill_ratio=0.02,
            material="PLA",
            material_density=1.24,
            motor_type="1/2A6-2",
            ballast_mass_g=0.0,
            recovery_mass_g=mass,
            recovery_area_cm2=area,
            recovery_cd=0.25,
            descent_horizontal=True
        )
        
        mdo = FullRocketOptimizer(spec)
        mdo_res = mdo.optimize_design(
            length_range=[260.0, 270.0, 280.0, 290.0, 300.0],
            nose_range=[80.0, 90.0, 100.0, 110.0],
            tail_range=[0.0],
            shape_n_range=[0.75],
            target_margin_cal=1.20,
            arrangement="auto",
            shape_type="trapezoid",
            taper_ratios=[0.0],
            fin_thickness_mm=0.4,
            optimize_for="time"
        )
        
        if mdo_res:
            time_sorted = sorted(mdo_res, key=lambda x: x["fins"]["total_flight_time_s"], reverse=True)
            best = time_sorted[0]
            f = best["fins"]
            b = best["body"]
            entry = {
                "name": sc["name"],
                "w_mm": sc["w_mm"],
                "l_mm": sc["l_mm"],
                "area_cm2": area,
                "mass_g": mass,
                "best_time_s": f["total_flight_time_s"],
                "apogee_m": f["apogee_m"],
                "v_descent_m_s": f["v_descent_m_s"],
                "total_mass_g": f["total_mass_g"],
                "length_mm": b["total_length_mm"],
                "nose_mm": b["nose_length_mm"],
                "span_mm": f["span_mm"],
                "cr_mm": f["root_chord_mm"],
                "margin_cal": f["margin_cal"],
                "is_4fin": f["is_4fin"],
                "theta_deg": f["theta_deg"],
                "full_fin": f
            }
            results.append(entry)
            print(f"[{sc['name']}] Area={area:6.1f}cm2, Mass={mass:.1f}g -> HangTime={entry['best_time_s']:5.2f}s | Apogee={entry['apogee_m']:5.1f}m | V_descent={entry['v_descent_m_s']:4.2f}m/s | Body L={entry['length_mm']}mm, Fin Span={entry['span_mm']}mm")
        else:
            print(f"[{sc['name']}] No solution found.")

    # Plot the graph
    areas = [r["area_cm2"] for r in results]
    times = [r["best_time_s"] for r in results]
    apogees = [r["apogee_m"] for r in results]
    v_descents = [r["v_descent_m_s"] for r in results]
    labels = [f"{r['w_mm']}x{r['l_mm']}" for r in results]

    fig, ax1 = plt.subplots(figsize=(10, 6))

    color = 'tab:blue'
    ax1.set_xlabel('Streamer Area [cm²] (Length = 10 x Width)', fontsize=12)
    ax1.set_ylabel('Max Hang Time [s]', color=color, fontsize=12)
    line1 = ax1.plot(areas, times, marker='o', color=color, linewidth=2.5, markersize=8, label='Hang Time [s]')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True, linestyle='--', alpha=0.6)

    # Annotate points
    for i, txt in enumerate(labels):
        ax1.annotate(f"{txt}\n{times[i]:.1f}s", (areas[i], times[i]), 
                     textcoords="offset points", xytext=(0, 10), ha='center', fontsize=9, fontweight='bold', color=color)

    # Highlight 50x500mm
    target_50 = next((r for r in results if r["w_mm"] == 50), None)
    if target_50:
        ax1.scatter([target_50["area_cm2"]], [target_50["best_time_s"]], color='red', s=150, zorder=5, label='Target: 50x500mm')
        ax1.annotate(f"Target: 50x500mm\nHang Time: {target_50['best_time_s']:.1f}s\n(Descent: {target_50['v_descent_m_s']:.2f} m/s)", 
                     (target_50["area_cm2"], target_50["best_time_s"]),
                     textcoords="offset points", xytext=(25, -45), fontsize=10, fontweight='bold', color='red',
                     bbox=dict(boxstyle="round,pad=0.4", fc="#fff9db", ec="red", lw=1.5, alpha=0.9),
                     arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.2", color='red', lw=1.8))

    ax2 = ax1.twinx()
    color = 'tab:green'
    ax2.set_ylabel('Apogee [m] & Descent Speed [m/s]', color=color, fontsize=12)
    line2 = ax2.plot(areas, apogees, marker='s', color=color, linestyle='--', linewidth=1.5, markersize=6, label='Apogee [m]')
    line3 = ax2.plot(areas, [v * 10 for v in v_descents], marker='^', color='tab:orange', linestyle=':', linewidth=1.5, markersize=6, label='Descent V x10 [dm/s]')
    ax2.tick_params(axis='y', labelcolor=color)

    # Combine legends
    lines = line1 + line2 + line3
    labs = [l.get_label() for l in lines]
    ax1.legend(lines, labs, loc='center right', framealpha=0.9)

    plt.title('Streamer Size vs Max Hang Time (1/2A6-2 Motor, JAR Rules)', fontsize=14, pad=15)
    fig.tight_layout()

    os.makedirs("output", exist_ok=True)
    out_path = os.path.join("output", "streamer_vs_hang_time.png")
    plt.savefig(out_path, dpi=150)
    print(f"\n[Graph Saved] {os.path.abspath(out_path)}")

    # Output detailed card for 50x500mm
    print("\n" + "="*70)
    print("             ★★★ 50x500mm 代表値 詳細設計カード ★★★")
    print("="*70)
    if target_50:
        f = target_50["full_fin"]
        b = target_50
        print(f"【 1. 機体寸法 (JAR競技規則適合) 】")
        print(f"  - 全長        : {b['length_mm']} mm (50%ルール: 円筒部 {(b['length_mm']-b['nose_mm']):.1f}mm / {((b['length_mm']-b['nose_mm'])/b['length_mm']*100):.1f}%)")
        print(f"  - ノーズ長さ  : {b['nose_mm']} mm")
        print(f"  - 胴体直径    : 24.0 mm")
        print(f"  - ストリーマー: 50 mm x 500 mm (面積: 250 cm2, 重量: {b['mass_g']}g)")
        print(f"\n【 2. フィン寸法 (4枚十字翼 +型) 】")
        print(f"  - 主翼 スパン (張り出し) : {f['span_mm']:5.1f} mm  (機体全幅: {f['total_width_mm']:.1f} mm)")
        print(f"  - 主翼 根元コード長 (高) : {f['root_chord_mm']:5.1f} mm")
        print(f"  - 主翼 翼端コード長       : {f['tip_chord_mm']:5.1f} mm (デルタ翼)")
        print(f"  - フィン単体重量 (4枚)    : {f['fin_mass_g']:5.2f} g")
        print(f"\n【 3. 安定性と性能 】")
        print(f"  - 全備質量                : {f['total_mass_g']:5.1f} g")
        print(f"  - 静安定マージン          : {f['margin_cal']:+5.2f} cal (Pitch: {f['pitch_margin_cal']:+.2f}, Yaw: {f['yaw_margin_cal']:+.2f})")
        print(f"  - 最高到達高度            : {f['apogee_m']:5.1f} m")
        print(f"  - 終端降下速度            : {f['v_descent_m_s']:5.2f} m/s")
        print(f"  - 総滞空時間 (Hang Time)  : {f['total_flight_time_s']:5.2f} 秒")
    print("="*70)

if __name__ == "__main__":
    main()
