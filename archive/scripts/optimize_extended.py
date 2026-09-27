import os
import sys
import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 全長 L: 180mm 〜 250mm
# 翼面積比: 0.3 〜 1.0 (30%〜100%)
# 先端回収系重量: 6.0g (ストリーマ4g + 金具2g)

L_grid = np.linspace(180, 250, 35)
Fin_grid = np.linspace(0.3, 1.0, 35)

L_mesh, Fin_mesh = np.meshgrid(L_grid, Fin_grid)

Margin = np.zeros_like(L_mesh)
Apogee = np.zeros_like(L_mesh)
Fin_Span_mm = np.zeros_like(L_mesh)

# 基準フィンスパン: 47mm (胴体表面から), 軸線から 58mm
base_span_from_body = 47.0

for i in range(len(Fin_grid)):
    for j in range(len(L_grid)):
        L = L_mesh[i, j]
        f = Fin_mesh[i, j]
        
        # 翼面積比 f に応じてスパンも縮小 (相似スケーリングなら sqrt(f), コード長固定なら f)
        # ここではコード長(根本)を維持しつつスパンを削る安全なスケーリングを想定
        span = base_span_from_body * (f**0.7)
        Fin_Span_mm[i, j] = span
        
        # 質量 (g)
        # 分割継手(インロー部)の重さ +1.5g を加味
        m_fuselage = (14.0 * (L / 179.0)) + 1.5
        m_fin = 9.0 * f
        m_motor = 15.0
        m_tip = 6.0
        m_tot = m_fuselage + m_fin + m_motor + m_tip
        
        # 重心 CG (mm)
        # 先端にtipがあるためLが伸びると強烈に前に引っ張られる
        cg = (m_motor * 35.0 + m_fuselage * (L * 0.52) + m_fin * 25.0 + m_tip * (L - 8.0)) / m_tot
        
        # 空力中心 CP (mm)
        # フィンは後端(Y=0)に集中配置
        a_fin = 0.0055 * f
        a_body = (L * 22.0 * 1e-6) * 0.32 # 胴体ノーズ揚力
        cp = (a_body * (L * 0.62) + a_fin * 22.0) / (a_body + a_fin)
        
        margin = (cg - cp) / 22.0
        Margin[i, j] = margin
        
        # 最高高度 (m)
        cd = 0.28 + 0.08 * f + 0.04 * (L / 179.0)
        v_bo = 1.25 / (m_tot * 1e-3) * 0.86
        k = 0.5 * 1.225 * cd * (np.pi * 0.011**2)
        h = (m_tot * 1e-3 / (2 * k)) * np.log(1 + (k * v_bo**2) / (m_tot * 1e-3 * 9.8)) + 1.5
        Apogee[i, j] = h

# グラフ描画
fig, ax = plt.subplots(figsize=(10, 7))

# 高度のカラーコンター
c = ax.contourf(L_mesh, Fin_mesh, Apogee, levels=20, cmap="viridis", alpha=0.85)
cbar = fig.colorbar(c, ax=ax)
cbar.set_label("Max Altitude [m]", fontsize=11)

# 安全マージンの等高線
lines = ax.contour(L_mesh, Fin_mesh, Margin, levels=[1.0, 1.2, 1.5, 2.0], 
                   colors=['lime', 'yellow', 'cyan', 'magenta'], linewidths=2.0)
ax.clabel(lines, inline=True, fmt="Margin %.1f cal", fontsize=10)

ax.set_xlabel("Rocket Total Length [mm] (Up to 250mm)", fontsize=12)
ax.set_ylabel("Fin Area Scale [ratio] (0.3 = 30%)", fontsize=12)
ax.set_title("Extended Optimization Map: Length (180-250mm) vs Fin Scale", fontsize=14, fontweight="bold")
ax.grid(True, alpha=0.3)

# 250mm 上限線
ax.axvline(250, color='red', ls='--', lw=2, label="Max Length Limit (250mm)")

# 最適スイートスポットのプロット (Margin ~ 1.5 cal で 高度最大)
# 例: L=220mm, Fin=0.5 (50%)
ax.plot(225, 0.45, marker='*', color='red', markersize=16, label="Sweet Spot (L=225mm, Fin=45%)")

ax.legend(loc="upper right")
plt.tight_layout()
output_img = "export/extended_optimization_map.png"
plt.savefig(output_img, dpi=150)
plt.close()
print(f"Extended optimization map saved: {output_img}")
