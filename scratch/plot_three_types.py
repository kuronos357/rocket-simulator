import sys
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Set fonts
plt.rcParams['font.sans-serif'] = ['Yu Gothic', 'Meiryo', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def plot_three_designs():
    fig, axes = plt.subplots(1, 3, figsize=(15, 8.5))

    types = [
        {
            "name": "タイプ1：安全重視 (1.2 cal)",
            "margin_label": "Pitch: +1.21 cal / Yaw: +1.21 cal",
            "L": 280.0, "N": 125.0, "D": 24.0,
            "h_span": 63.0, "h_cr": 41.0,
            "v_span": 63.0, "v_cr": 41.0,
            "fin_mass": 2.56, "total_mass": 33.3,
            "apogee": 124.9, "hang_time": 27.00, "v_desc": 5.64,
            "color": "tab:blue",
            "desc": "【特徴】強風対応・直進安定性重視\n胴体を280mmに伸ばし確実に復元\nどのような天候でも安全に飛ぶ鉄板機"
        },
        {
            "name": "タイプ2：競技攻め最短 (0.9 cal)",
            "margin_label": "Pitch: +0.92 cal / Yaw: +0.92 cal",
            "L": 250.0, "N": 110.0, "D": 24.0,
            "h_span": 55.0, "h_cr": 35.0,
            "v_span": 55.0, "v_cr": 35.0,
            "fin_mass": 1.91, "total_mass": 31.1,
            "apogee": 140.0, "hang_time": 29.54, "v_desc": 5.74,
            "color": "tab:orange",
            "desc": "【特徴】レギュレーション下限最短250mm\n極小フィンで打上総質量31.1g！\n最高高度140m＆滞空29.5秒の最速機"
        },
        {
            "name": "タイプ3：アンバランス飛行機型 (0.7 cal)",
            "margin_label": "Pitch: +1.10 cal / Yaw: +0.78 cal",
            "L": 250.0, "N": 95.0, "D": 24.0,
            "h_span": 71.0, "h_cr": 45.0,
            "v_span": 49.7, "v_cr": 31.5,
            "fin_mass": 2.36, "total_mass": 31.9,
            "apogee": 133.4, "hang_time": 29.28, "v_desc": 5.50,
            "color": "tab:green",
            "desc": "【特徴】大型水平主翼(71mm)＋小型尾翼(50mm)\n主翼が横風降下時の強力エアブレーキに！\n降下速度5.50m/sで粘り滞空29.3秒"
        }
    ]

    for i, t in enumerate(types):
        ax = axes[i]
        ax.set_title(f"{t['name']}\n[{t['margin_label']}]", fontsize=12, fontweight='bold', color=t['color'], pad=12)
        ax.set_xlim(-110, 110)
        ax.set_ylim(-130, 310)
        ax.grid(True, linestyle=":", alpha=0.5)
        ax.set_xlabel("機体幅方向 [mm]", fontsize=10)
        if i == 0:
            ax.set_ylabel("テールからの距離 Z [mm]", fontsize=10)

        # Draw Rocket Airframe
        L = t["L"]
        N = t["N"]
        D = t["D"]
        R = D / 2.0
        cyl_len = L - N

        # Cylinder
        cyl = patches.Rectangle((-R, 0), D, cyl_len, facecolor="#e0e0e0", edgecolor="black", lw=1.5)
        ax.add_patch(cyl)

        # Nose cone (parabolic/ogive representation)
        nose_xs = [-R, 0, R]
        nose_ys = [cyl_len, L, cyl_len]
        nose = patches.Polygon(list(zip(nose_xs, nose_ys)), facecolor="#b0b0b0", edgecolor="black", lw=1.5)
        ax.add_patch(nose)

        # Motor (inside at bottom)
        motor = patches.Rectangle((-9, 0), 18, 70, facecolor="#ffccaa", edgecolor="#d95f02", lw=1.2, ls="--", alpha=0.7)
        ax.add_patch(motor)
        ax.text(0, 35, "Motor 1/2A", ha='center', va='center', fontsize=7, color="#d95f02", rotation=90)

        # Horizontal Fins (Left & Right)
        h_s = t["h_span"]
        h_cr = t["h_cr"]
        # Right fin
        rf_xs = [R, R + h_s, R]
        rf_ys = [0, 0, h_cr]
        ax.add_patch(patches.Polygon(list(zip(rf_xs, rf_ys)), facecolor=t["color"], edgecolor="black", lw=1.2, alpha=0.85))
        # Left fin
        lf_xs = [-R, -R - h_s, -R]
        lf_ys = [0, 0, h_cr]
        ax.add_patch(patches.Polygon(list(zip(lf_xs, lf_ys)), facecolor=t["color"], edgecolor="black", lw=1.2, alpha=0.85))

        # Vertical Fin marker
        v_s = t["v_span"]
        v_cr = t["v_cr"]
        ax.plot([0, 0], [0, v_cr], color="crimson", lw=3, label="垂直尾翼根元")
        ax.plot([0, 0], [0, v_s], color="crimson", lw=1.8, ls="--")
        ax.text(3, v_s*0.5, f"V-Fin {v_s:.1f}mm", color="crimson", fontsize=8, va='center')

        # Dimension markers
        ax.text(R + h_s*0.5, -8, f"主翼 {h_s:.1f}mm", ha='center', fontsize=8, color=t["color"], fontweight='bold')

        # Center line
        ax.axvline(0, color="gray", lw=0.8, ls="-.")

        # Spec text box in the bottom half
        spec_text = (
            f"【幾何寸法】\n"
            f"・全長 L: {L:.0f} mm (ノーズ: {N:.0f} mm)\n"
            f"・平行胴体長: {cyl_len:.0f} mm\n"
            f"・水平主翼: {h_s:.1f} × {h_cr:.1f} mm\n"
            f"・垂直尾翼: {v_s:.1f} × {v_cr:.1f} mm\n"
            f"・機体乾燥質量: {t['total_mass']-16.2:.1f} g (打上: {t['total_mass']:.1f} g)\n"
            f"------------------------------------\n"
            f"★ 最高到達高度: {t['apogee']:.1f} m\n"
            f"★ 降下終末速度: {t['v_desc']:.2f} m/s\n"
            f"★ 合計滞空時間: {t['hang_time']:.2f} 秒\n\n"
            f"{t['desc']}"
        )
        ax.text(0, -25, spec_text, ha='center', va='top', fontsize=8.5,
                bbox=dict(boxstyle="round,pad=0.5", facecolor="#fcfcfc", edgecolor=t["color"], lw=1.5))

    plt.suptitle("モデルロケット 3大最適化モデル外観＆性能比較 (1.2 cal / 0.9 cal / 0.7 cal)", fontsize=14, fontweight='bold', y=0.98)
    plt.tight_layout(rect=[0.02, 0.02, 0.98, 0.95])

    os.makedirs("output", exist_ok=True)
    out_file = os.path.join("output", "three_types_comparison.png")
    plt.savefig(out_file, dpi=300)
    print(f"Saved {out_file}")

    # Copy to artifact
    import shutil
    art_dir = r"C:\Users\kuron.HX99G\.gemini\antigravity\brain\f5d3bd8b-8307-472d-83e6-9bd725805a5f"
    shutil.copy(out_file, os.path.join(art_dir, "three_types_comparison.png"))
    print("Copied to artifact directory.")

if __name__ == "__main__":
    plot_three_designs()
