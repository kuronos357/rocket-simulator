import matplotlib.pyplot as plt
import numpy as np
import json
import os

# 日本語フォント対応
plt.rcParams['font.sans-serif'] = ['Meiryo', 'Yu Gothic', 'MS Gothic', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

with open("scratch/massive_dense_sweep_results.json", "r", encoding="utf-8") as f:
    data = json.load(f)

b3 = data["best_asym_3fin"]
b4 = data["best_sym_4fin"]

# -------------------------------------------------------------------------
# Plot 1: Profile Comparison of the 150M Peak Candidates
# -------------------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6), sharey=True)

for ax, p, title, color in [
    (ax1, b3, f"新・設定A (1.5億パターン最良解): 3枚非対称 逆Y字35° (v_sc={b3['v_scale']:.2f})\n[高度 {b3['apogee_m']:.2f}m / 滞空 {b3['hang_time_s']:.2f}s / 翼重 {b3['fin_mass_g']:.2f}g / マージン +{b3['margin_cal']:.2f}cal]", "#1f77b4"),
    (ax2, b4, f"新・設定B (1.5億パターン最良解): 4枚対称 十字翼 (+)\n[高度 {b4['apogee_m']:.2f}m / 滞空 {b4['hang_time_s']:.2f}s / 翼重 {b4['fin_mass_g']:.2f}g / マージン +{b4['margin_cal']:.2f}cal]", "#ff7f0e"),
]:
    b = p["span_mm"]
    cr = p["cr_mm"]
    ct = p["ct_mm"]
    te_sweep = p["te_sweep_mm"]
    overhang = p["overhang_mm"]
    p_le = p["p_le"]
    p_te = p["p_te"]
    
    le_sweep = cr - ct + te_sweep
    eta = np.linspace(0, 1, 200)
    y = eta * b
    
    x_le = le_sweep * (eta ** p_le)
    x_te = cr + te_sweep * (eta ** p_te)
    
    x_tail = cr + te_sweep - overhang
    
    ax.fill_between(y, x_le, x_te, color=color, alpha=0.35)
    ax.plot(y, x_le, color=color, lw=2.5, label=f'前縁 ($p_{{le}}={p_le:.2f}$)')
    ax.plot(y, x_te, color=color, ls='--', lw=2.0, label=f'後縁 ($p_{{te}}={p_te:.2f}$)')
    ax.axhline(x_tail, color='black', ls=':', lw=2, label=f'機体後端ライン (突き出し={overhang:.1f}mm)')
    
    ax.invert_yaxis()
    ax.set_title(title, fontsize=10.5, fontweight='bold')
    ax.set_xlabel('スパン幅 y [mm] (機体外側へ)', fontsize=11)
    ax.set_ylabel('翼前縁基準位置 x [mm] (後方へ)', fontsize=11)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='lower left', fontsize=9)
    ax.set_aspect('equal')
    ax.set_xlim(-5, b + 8)
    
    specs_str = (
        f"スパン幅: {b:.1f} mm\n"
        f"翼根コード: {cr:.1f} mm\n"
        f"翼端コード: {ct:.1f} mm\n"
        f"後端突き出し: {overhang:.1f} mm\n"
        f"静安定マージン: +{p['margin_cal']:.2f} cal\n"
        f"翼合計質量: {p['fin_mass_g']:.2f} g"
    )
    ax.text(0.95, 0.95, specs_str, transform=ax.transAxes, ha='right', va='top', fontsize=9.5,
            bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.85))

plt.suptitle('【1.5億パターン超高密度全探索】新・設定A vs 新・設定B 最適非線形翼平面形', 
             fontsize=14, fontweight='bold', y=0.98)
plt.tight_layout()

os.makedirs('output', exist_ok=True)
plt.savefig('output/massive_dense_optimal_wings.png', dpi=300)
print('Successfully saved output/massive_dense_optimal_wings.png')

# -------------------------------------------------------------------------
# Plot 2: Pareto Front (Margin vs Hang Time / Apogee)
# -------------------------------------------------------------------------
pareto_3f = data["pareto_3fin"]
pareto_4f = data["pareto_4fin"]

m_3f = [row["margin_cal"] for row in pareto_3f if row["margin_cal"] >= 0.90]
t_3f = [row["hang_time_s"] for row in pareto_3f if row["margin_cal"] >= 0.90]
h_3f = [row["apogee_m"] for row in pareto_3f if row["margin_cal"] >= 0.90]

m_4f = [row["margin_cal"] for row in pareto_4f if row["margin_cal"] >= 0.90]
t_4f = [row["hang_time_s"] for row in pareto_4f if row["margin_cal"] >= 0.90]
h_4f = [row["apogee_m"] for row in pareto_4f if row["margin_cal"] >= 0.90]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5.5))

# Margin vs Hang time
ax1.plot(m_3f, t_3f, 'o-', color='#1f77b4', lw=2.5, markersize=5, label='3枚非対称 (逆Y字35°)')
ax1.plot(m_4f, t_4f, 's-', color='#ff7f0e', lw=2.5, markersize=5, label='4枚対称 (十字+)')
ax1.axvline(1.0, color='red', ls='--', alpha=0.7, label='推奨下限マージン (+1.0 cal)')
ax1.set_xlabel('静安定マージン [cal]', fontsize=11, fontweight='bold')
ax1.set_ylabel('最大総滞空時間 [秒]', fontsize=11, fontweight='bold')
ax1.set_title('静安定マージン vs 滞空時間 パレートフロンティア', fontsize=12, fontweight='bold')
ax1.grid(True, linestyle=':', alpha=0.6)
ax1.legend(loc='lower left', fontsize=10)

# Margin vs Apogee
ax2.plot(m_3f, h_3f, 'o-', color='#1f77b4', lw=2.5, markersize=5, label='3枚非対称 (逆Y字35°)')
ax2.plot(m_4f, h_4f, 's-', color='#ff7f0e', lw=2.5, markersize=5, label='4枚対称 (十字+)')
ax2.axvline(1.0, color='red', ls='--', alpha=0.7, label='推奨下限マージン (+1.0 cal)')
ax2.set_xlabel('静安定マージン [cal]', fontsize=11, fontweight='bold')
ax2.set_ylabel('最高到達高度 [m]', fontsize=11, fontweight='bold')
ax2.set_title('静安定マージン vs 最高高度 パレートフロンティア', fontsize=12, fontweight='bold')
ax2.grid(True, linestyle=':', alpha=0.6)
ax2.legend(loc='lower left', fontsize=10)

plt.suptitle('【1.5億パターン全探索結果】安定性マージンと性能の究極トレードオフ曲線', 
             fontsize=14, fontweight='bold', y=0.98)
plt.tight_layout()
plt.savefig('output/massive_dense_pareto_front.png', dpi=300)
print('Successfully saved output/massive_dense_pareto_front.png')
