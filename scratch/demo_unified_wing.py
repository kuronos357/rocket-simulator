import matplotlib.pyplot as plt
import numpy as np
import os

# 日本語フォント対応
plt.rcParams['font.sans-serif'] = ['Meiryo', 'Yu Gothic', 'MS Gothic', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# パラメトリック翼の統一関数:
# η = y / b ∈ [0, 1]
# x_le(η) = sweep_tip * η^p_le
# x_te(η) = c_root + (sweep_tip + c_tip - c_root) * η^p_te

b = 65.0       # スパン [mm]
c_root = 25.0  # 翼根コード [mm]
c_tip = 2.0    # 翼端コード [mm]
overhang = 20.0 # 後端オーバーハング [mm]
# 後端オーバーハング = x_te(1) - c_root = sweep_tip + c_tip - c_root
# したがって sweep_tip = overhang + c_root - c_tip = 20 + 25 - 2 = 43 mm
sweep_tip = overhang + c_root - c_tip

eta = np.linspace(0, 1.0, 200)
y = eta * b

fig, axes = plt.subplots(2, 3, figsize=(15, 9), sharey=True, sharex=True)

# 変化させる定数の組み合わせ
configs = [
    (1.0, 1.0, "p_le = 1.0, p_te = 1.0\n【標準クリップトデルタ（直線）】", "#4575b4"),
    (1.5, 1.0, "p_le = 1.5, p_te = 1.0\n【放物線前縁（マイルドな凸）】", "#74add1"),
    (2.5, 1.0, "p_le = 2.5, p_te = 1.0\n【オージー/ゴシック翼（強烈な凸）】", "#313695"),
    (2.5, 1.8, "p_le = 2.5, p_te = 1.8\n【クレセント/三日月翼（前縁凸・後縁後退）】", "#7b2cbf"),
    (0.5, 1.0, "p_le = 0.5, p_te = 1.0\n【フィレット翼（前縁凹・根元急拡大）】", "#d73027"),
    (2.0, 0.5, "p_le = 2.0, p_te = 0.5\n【バイオミメティック（膨らみ翼）】", "#f46d43"),
]

for idx, (p_le, p_te, title, col) in enumerate(configs):
    ax = axes[idx // 3, idx % 3]
    
    x_le = sweep_tip * (eta ** p_le)
    x_te = c_root + (sweep_tip + c_tip - c_root) * (eta ** p_te)
    
    # 面積と重心の計算
    area = np.trapezoid(x_te - x_le, y)
    cg_x = np.trapezoid((x_te**2 - x_le**2) / 2.0, y) / area
    cg_y = np.trapezoid((x_te - x_le) * y, y) / area
    
    ax.fill_between(y, x_le, x_te, color=col, alpha=0.35)
    ax.plot(y, x_le, color=col, lw=2.5, label='前縁 (LE)')
    ax.plot(y, x_te, color=col, ls='--', lw=2.0, label='後縁 (TE)')
    ax.plot(cg_y, cg_x, 'ro', markersize=6, label=f'図心 (X={cg_x:.1f}mm)')
    
    ax.invert_yaxis()
    ax.set_title(title, fontsize=10.5, fontweight='bold')
    ax.set_xlabel('スパン幅 y [mm]')
    ax.set_ylabel('機軸方向位置 x [mm]')
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='lower left', fontsize=8)
    ax.set_aspect('equal')
    ax.set_xlim(-2, b + 5)
    ax.set_ylim(55, -5)
    
    # 諸元アノテーション
    ax.text(0.95, 0.92, f'面積: {area:.0f} mm²\n翼重量: {area*0.000624:.2f} g', 
            transform=ax.transAxes, ha='right', va='top', fontsize=9,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

plt.suptitle('【統一パラメトリック翼関数】定数 (p_le, p_te) を変えるだけで生み出される多様な翼形状', 
             fontsize=14, fontweight='bold', y=0.99)
plt.tight_layout()

os.makedirs('output', exist_ok=True)
plt.savefig('output/unified_parametric_wing_demo.png', dpi=300)
print('Successfully saved output/unified_parametric_wing_demo.png')
