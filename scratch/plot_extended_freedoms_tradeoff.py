"""
Plot Trade-off Analysis with Extended Freedoms:
Boat Tail + Trailing Edge Taper + Rear Overhang + Extended Span.
Comparison with previous baseline (50x500mm straight body).
"""

import os
import json
import numpy as np
import matplotlib.pyplot as plt
import shutil

plt.rcParams['font.sans-serif'] = ['Meiryo', 'Yu Gothic', 'MS Gothic', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

def main():
    with open("scratch/massive_extended_sweep_results.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # Separate by architecture
    data_a = [d for d in data if d["type_key"] == "3-fin-asym"]
    data_b = [d for d in data if d["type_key"] == "4-fin-sym"]

    fig, ax = plt.subplots(figsize=(13, 7.5))

    # Scatter points (subsample for rendering performance)
    np.random.seed(42)
    sample_a = np.random.choice(data_a, min(len(data_a), 6000), replace=False)
    sample_b = np.random.choice(data_b, min(len(data_b), 6000), replace=False)

    ax.scatter([d["margin"] for d in sample_b], [d["time"] for d in sample_b],
               c='#7f7f7f', alpha=0.25, s=18, label=f'設定B系: 4枚対称 十字翼+ (有効解 {len(data_b):,}件)')
    ax.scatter([d["margin"] for d in sample_a], [d["time"] for d in sample_a],
               c='#2ca02c', alpha=0.35, s=20, label=f'設定A系: 3枚非対称 逆Y字35° (有効解 {len(data_a):,}件)')

    # Previous best points (without tail/overhang/TE taper)
    # Old Setting A: margin 0.77, time 13.30s
    # Old Setting B: margin 0.99, time 13.03s
    ax.scatter([0.77], [13.30], c='#d62728', marker='X', s=200, edgecolors='black', linewidth=1.5, zorder=6,
               label='【前回最良】設定A (直円筒/直角後縁/面一): 13.30s (+0.77 cal)')
    ax.scatter([0.99], [13.03], c='#1f77b4', marker='s', s=160, edgecolors='black', linewidth=1.5, zorder=6,
               label='【前回最良】設定B (直円筒/直角後縁/面一): 13.03s (+0.99 cal)')

    # New champions
    # Best Setting A with Margin >= 1.00: 14.21s (+1.01 cal)
    # Best Setting B with Margin >= 1.00: 14.10s (+1.00 cal)
    # Best Overall: 14.31s (+0.52 cal)
    ax.scatter([1.01], [14.21], c='#00e676', marker='*', s=350, edgecolors='black', linewidth=2.0, zorder=7,
               label='【新・設定A本命】ボートテール20mm + 後縁後退20° + 後端突出20mm: 14.21s (+1.01 cal)')
    ax.scatter([1.00], [14.10], c='#ff9100', marker='D', s=220, edgecolors='black', linewidth=1.8, zorder=7,
               label='【新・設定B本命】ボートテール20mm + 後縁後退10° + 後端突出20mm: 14.10s (+1.00 cal)')

    # Reference lines
    ax.axvline(1.0, color='#d62728', linestyle='--', linewidth=1.5, alpha=0.7)
    ax.text(1.01, 8.5, '大会安全基準 (Margin ≧ +1.0 cal)', color='#d62728', fontsize=11, fontweight='bold', rotation=90)

    ax.axhline(13.30, color='gray', linestyle=':', linewidth=1.2, alpha=0.6)

    # Annotations
    ax.annotate('【新・設定A本命】\n滞空 14.21s (+0.91s 更新!)\n高度 61.5m (ベース抗力半減)\n翼重 1.08g (30%軽量化)\nスパン 65mm / 後縁+20° / 突出20mm',
                xy=(1.01, 14.21), xytext=(1.10, 12.8),
                arrowprops=dict(facecolor='black', arrowstyle='->', lw=1.5),
                fontsize=10, fontweight='bold', backgroundcolor='#e8f5e9',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='#e8f5e9', edgecolor='#2ca02c', lw=1.5))

    ax.annotate('【新・設定B本命】\n滞空 14.10s (+1.07s 更新!)\n高度 61.7m\n翼重 1.00g (38%軽量化)\nスパン 45mm / 後縁+10° / 突出20mm',
                xy=(1.00, 14.10), xytext=(0.60, 10.2),
                arrowprops=dict(facecolor='black', arrowstyle='->', lw=1.5),
                fontsize=10, fontweight='bold', backgroundcolor='#fff3e0',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='#fff3e0', edgecolor='#ff9100', lw=1.5))

    ax.annotate('前回設定A (13.30s)\nここから +0.91秒 延伸！',
                xy=(0.77, 13.30), xytext=(0.58, 12.0),
                arrowprops=dict(facecolor='black', arrowstyle='->', lw=1.2),
                fontsize=9.5, backgroundcolor='white')

    ax.set_title('新自由度（ボートテール・翼下テーパー角・後端オーバーハング・スパン100mm）導入による滞空性能の飛躍',
                 fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('静的安定マージン [caliber] (打上時)', fontsize=12)
    ax.set_ylabel('総滞空時間 [秒] (横倒し降下モデル)', fontsize=12)
    ax.set_xlim(0.45, 1.55)
    ax.set_ylim(8.0, 14.8)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='lower left', fontsize=10, framealpha=0.95)

    plt.tight_layout()
    out_png = "output/margin_vs_hangtime_extended_freedoms.png"
    plt.savefig(out_png, dpi=300)
    print(f"Saved plot to: {out_png}")

    artifact_dir = r"C:\Users\kuron.HX99G\.gemini\antigravity\brain\07d75649-5831-48d4-9417-33296222f683"
    dest = os.path.join(artifact_dir, "margin_vs_hangtime_extended_freedoms.png")
    shutil.copyfile(out_png, dest)
    print(f"Copied to artifact: {dest}")

if __name__ == '__main__':
    main()
