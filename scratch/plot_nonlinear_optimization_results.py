import matplotlib.pyplot as plt
import numpy as np
import json
import os

# 日本語フォント対応
plt.rcParams['font.sans-serif'] = ['Meiryo', 'Yu Gothic', 'MS Gothic', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

with open("scratch/nonlinear_fin_optimization_full.json", "r", encoding="utf-8") as f:
    data = json.load(f)

best_3fin = data["best_asym_3fin"]
best_4fin = data["best_sym_4fin"]

# -------------------------------------------------------------------------
# Plot 1: Actual Optimized Fin Profiles (実機平面形状の比較)
# -------------------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), sharey=True)

for ax, p, title, color in [
    (ax1, best_3fin, f"新・設定A 本命: 3枚非対称 逆Y字35°\n(高度 {best_3fin['apogee_m']:.1f}m / 滞空 {best_3fin['hang_time_s']:.2f}s / 翼重 {best_3fin['fin_mass_g']:.2f}g)", "#1f77b4"),
    (ax2, best_4fin, f"新・設定B 本命: 4枚対称 十字翼 (+)\n(高度 {best_4fin['apogee_m']:.1f}m / 滞空 {best_4fin['hang_time_s']:.2f}s / 翼重 {best_4fin['fin_mass_g']:.2f}g)", "#ff7f0e"),
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
    
    # Coordinates where x=0 is tail end of fuselage (boat tail end)
    # Wing root starts at fuselage: root trailing edge is at x = -overhang + cr (wait, overhang is behind tail)
    # Root TE is at z = -overhang + cr - le_sweep ...
    # In our definition:
    # x_te(0) = cr, root is at (cr - overhang)
    # Let's align with fuselage tail: tail end is at X_fuselage = 0.
    # Overhang means tip trailing edge is at X_fuselage = +overhang (behind tail).
    # Since tip TE = cr + te_sweep, x_offset = overhang - (cr + te_sweep)?
    # Wait, in calc_nonlinear_fin_aero:
    # cp_fin = -overhang + (cr - xf_from_le)
    # So root TE is at +cr forward from tip TE's overhang?
    # Actually, tip TE is at -overhang (if overhang=20mm, it's 20mm behind fuselage tail).
    # Let's plot with root LE at x=0, and mark fuselage tail!
    
    x_le = le_sweep * (eta ** p_le)
    x_te = cr + te_sweep * (eta ** p_te)
    
    # In our coordinate, fuselage tail is at: x_tail = x_te(1) - overhang = cr + te_sweep - overhang
    x_tail = cr + te_sweep - overhang
    
    ax.fill_between(y, x_le, x_te, color=color, alpha=0.35)
    ax.plot(y, x_le, color=color, lw=2.5, label=f'前縁曲線 ($p_{{le}}={p_le:.1f}$)')
    ax.plot(y, x_te, color=color, ls='--', lw=2.0, label=f'後縁曲線 ($p_{{te}}={p_te:.1f}$)')
    
    # Draw Fuselage Tail line
    ax.axhline(x_tail, color='black', ls=':', lw=2, label=f'機体後端ライン (突き出し={overhang:.0f}mm)')
    
    ax.invert_yaxis()
    ax.set_title(title, fontsize=11, fontweight='bold')
    ax.set_xlabel('スパン幅 y [mm] (機体外側へ)', fontsize=11)
    ax.set_ylabel('翼前縁基準位置 x [mm] (後方へ)', fontsize=11)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='lower left', fontsize=9)
    ax.set_aspect('equal')
    ax.set_xlim(-5, b + 10)
    
    # Specs text
    specs_str = (
        f"スパン幅: {b:.0f} mm\n"
        f"翼根コード: {cr:.0f} mm\n"
        f"翼端コード: {ct:.1f} mm\n"
        f"後端突き出し: {overhang:.0f} mm\n"
        f"静安定マージン: +{p['margin_cal']:.2f} cal\n"
        f"翼合計質量: {p['fin_mass_g']:.2f} g"
    )
    ax.text(0.95, 0.95, specs_str, transform=ax.transAxes, ha='right', va='top', fontsize=9.5,
            bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.85))

plt.suptitle('【非線形パラメトリック翼 最適解】新・設定A（3枚逆Y字） vs 新・設定B（4枚十字）', 
             fontsize=14, fontweight='bold', y=0.98)
plt.tight_layout()

os.makedirs('output', exist_ok=True)
plt.savefig('output/best_nonlinear_wings_profile.png', dpi=300)
print('Successfully saved output/best_nonlinear_wings_profile.png')

# -------------------------------------------------------------------------
# Plot 2: Category Comparison (直線 vs 各種非線形)
# -------------------------------------------------------------------------
cats = data["summary_records"]
cat_names = [c["category"].split("(")[0].strip() for c in cats]
apo_3fin = [c["best_3fin"]["apogee_m"] for c in cats]
time_3fin = [c["best_3fin"]["hang_time_s"] for c in cats]
mass_3fin = [c["best_3fin"]["fin_mass_g"] for c in cats]

apo_4fin = [c["best_4fin"]["apogee_m"] for c in cats]
time_4fin = [c["best_4fin"]["hang_time_s"] for c in cats]
mass_4fin = [c["best_4fin"]["fin_mass_g"] for c in cats]

x = np.arange(len(cat_names))
width = 0.35

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5.5))

# Apogee comparison
rects1 = ax1.bar(x - width/2, apo_3fin, width, label='3枚非対称 (逆Y字35°)', color='#1f77b4', alpha=0.85)
rects2 = ax1.bar(x + width/2, apo_4fin, width, label='4枚対称 (十字+)', color='#ff7f0e', alpha=0.85)
ax1.set_ylabel('最高到達高度 [m]', fontsize=11, fontweight='bold')
ax1.set_title('翼形状カテゴリー別 最高到達高度の比較', fontsize=12, fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels(cat_names, rotation=20, ha='right', fontsize=9.5)
ax1.set_ylim(55, 65)
ax1.grid(True, axis='y', linestyle=':', alpha=0.6)
ax1.legend(loc='upper right')

for r in rects1:
    h = r.get_height()
    ax1.annotate(f'{h:.1f}m', xy=(r.get_x() + r.get_width()/2, h), xytext=(0, 3),
                 textcoords="offset points", ha='center', va='bottom', fontsize=8.5, fontweight='bold')
for r in rects2:
    h = r.get_height()
    ax1.annotate(f'{h:.1f}m', xy=(r.get_x() + r.get_width()/2, h), xytext=(0, 3),
                 textcoords="offset points", ha='center', va='bottom', fontsize=8.5, fontweight='bold')

# Hang time comparison
rects3 = ax2.bar(x - width/2, time_3fin, width, label='3枚非対称 (逆Y字35°)', color='#2ca02c', alpha=0.85)
rects4 = ax2.bar(x + width/2, time_4fin, width, label='4枚対称 (十字+)', color='#9467bd', alpha=0.85)
ax2.set_ylabel('総滞空時間 [秒]', fontsize=11, fontweight='bold')
ax2.set_title('翼形状カテゴリー別 滞空時間の比較', fontsize=12, fontweight='bold')
ax2.set_xticks(x)
ax2.set_xticklabels(cat_names, rotation=20, ha='right', fontsize=9.5)
ax2.set_ylim(13.5, 14.3)
ax2.grid(True, axis='y', linestyle=':', alpha=0.6)
ax2.legend(loc='upper right')

for r in rects3:
    h = r.get_height()
    ax2.annotate(f'{h:.2f}s', xy=(r.get_x() + r.get_width()/2, h), xytext=(0, 3),
                 textcoords="offset points", ha='center', va='bottom', fontsize=8.5, fontweight='bold')
for r in rects4:
    h = r.get_height()
    ax2.annotate(f'{h:.2f}s', xy=(r.get_x() + r.get_width()/2, h), xytext=(0, 3),
                 textcoords="offset points", ha='center', va='bottom', fontsize=8.5, fontweight='bold')

plt.suptitle('【直線翼 vs 各種非線形翼】性能ベンチマーク比較 (静安定マージン >= +1.0 cal)', 
             fontsize=14, fontweight='bold', y=0.98)
plt.tight_layout()
plt.savefig('output/nonlinear_category_benchmark.png', dpi=300)
print('Successfully saved output/nonlinear_category_benchmark.png')
