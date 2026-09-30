import matplotlib.pyplot as plt
import numpy as np
import os

# 日本語フォント対応
plt.rcParams['font.sans-serif'] = ['Meiryo', 'Yu Gothic', 'MS Gothic', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

fig, axes = plt.subplots(1, 4, figsize=(16, 5), sharey=True)

b = 65.0  # span mm
y = np.linspace(0, b, 200)

# 基準: 翼根 x=0〜c_root, 胴体接続部
# 1. オージー/ゴシック翼 (Ogive / Gothic)
c_root_1 = 30.0
c_tip_1 = 2.0
x_overhang = 20.0
# 後縁は直線後退
x_te_1 = c_root_1 + (y / b) * x_overhang
# 前縁は滑らかな凸曲線（オージー曲線）: 根元付近でコードが太く、外側で急激に絞られる
x_le_1 = (y / b)**2.2 * (c_root_1 + x_overhang - c_tip_1)

axes[0].fill_between(y, x_le_1, x_te_1, color='#1f77b4', alpha=0.35)
axes[0].plot(y, x_le_1, color='#1f77b4', lw=2.5, label='前縁: オージー曲線 (凸)')
axes[0].plot(y, x_te_1, color='#0d47a1', ls='--', lw=1.8, label='後縁: 直線テーパー')
axes[0].set_title('案1: オージー/ゴシック翼\n(Ogive / Gothic)\n【翼根強度最強・軽量・コンコルド風】', fontsize=11, fontweight='bold')

# 2. 放物線/冪乗前縁翼 (Parabolic Leading Edge)
c_root_2 = 25.0
c_tip_2 = 2.0
x_te_2 = c_root_2 + (y / b) * 20.0
x_le_2 = (y / b)**1.5 * (c_root_2 + 20.0 - c_tip_2)

axes[1].fill_between(y, x_le_2, x_te_2, color='#2ca02c', alpha=0.35)
axes[1].plot(y, x_le_2, color='#2ca02c', lw=2.5, label='前縁: 放物線 (y^1.5)')
axes[1].plot(y, x_te_2, color='#1b5e20', ls='--', lw=1.8, label='後縁: 直線テーパー')
axes[1].set_title('案2: 放物線前縁翼\n(Parabolic Leading Edge)\n【既存モデル拡張・応力集中ゼロ】', fontsize=11, fontweight='bold')

# 3. クレセント/三日月翼 (Crescent / Swept-Curved)
c_root_3 = 24.0
c_tip_3 = 2.5
x_le_3 = 24.0 * (y / b)**2.2
x_te_3 = c_root_3 + 22.0 * (y / b)**1.4

axes[2].fill_between(y, x_le_3, x_te_3, color='#9467bd', alpha=0.35)
axes[2].plot(y, x_le_3, color='#9467bd', lw=2.5, label='前縁: 後退曲線')
axes[2].plot(y, x_te_3, color='#4a148c', ls='--', lw=1.8, label='後縁: 前進/後退曲線')
axes[2].set_title('案3: クレセント/三日月翼\n(Crescent / Swept-Curved)\n【CP後退効果最大・翼端渦抑制】', fontsize=11, fontweight='bold')

# 4. スーパー楕円翼 (Super-Elliptic Wing)
c_root_4 = 22.0
c_y = (c_root_4 - 2.0) * np.maximum(0, 1 - (y / b)**2.5)**(1/2.5) + 2.0
x_mid = (y / b) * 20.0 + c_root_4 * 0.5
x_le_4 = x_mid - c_y * 0.5
x_te_4 = x_mid + c_y * 0.5

axes[3].fill_between(y, x_le_4, x_te_4, color='#ff7f0e', alpha=0.35)
axes[3].plot(y, x_le_4, color='#ff7f0e', lw=2.5, label='前縁: 楕円曲線')
axes[3].plot(y, x_te_4, color='#e65100', ls='--', lw=1.8, label='後縁: 楕円曲線')
axes[3].set_title('案4: スーパー楕円翼\n(Super-Elliptic Wing)\n【誘導抗力最小・揚力効率理論値】', fontsize=11, fontweight='bold')

for ax in axes:
    ax.invert_yaxis()
    ax.set_xlabel('スパン幅 y [mm] (機体外側へ)', fontsize=10)
    ax.set_ylabel('機軸方向位置 x [mm] (後方へ)', fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='lower left', fontsize=8)
    ax.set_aspect('equal')
    ax.set_xlim(-2, b + 5)
    ax.set_ylim(55, -5)

plt.tight_layout()
os.makedirs('output', exist_ok=True)
out_path = 'output/nonlinear_fin_concepts.png'
plt.savefig(out_path, dpi=300)
print(f'Successfully saved {out_path}')
