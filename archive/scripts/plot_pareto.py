import os
import sys
import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 全長 L: 160mm 〜 220mm
# 翼スパン/面積比: 0.5 〜 1.2
# 翼形状: 前削り(後退型) vs 全体縮小

L_grid = np.linspace(160, 220, 30)
Fin_grid = np.linspace(0.4, 1.1, 30)

L_mesh, Fin_mesh = np.meshgrid(L_grid, Fin_grid)

# 各グリッドでのマージンと最高高度の計算
# 先端にストリーマ+金具 7g
Margin = np.zeros_like(L_mesh)
Apogee = np.zeros_like(L_mesh)

for i in range(len(Fin_grid)):
    for j in range(len(L_grid)):
        L = L_mesh[i, j]
        f = Fin_mesh[i, j]
        
        # 質量 (g)
        m_fuselage = 13.0 * (L / 179.0)
        m_fin = 9.0 * f
        m_motor = 15.0
        m_tip = 7.0
        m_tot = m_fuselage + m_fin + m_motor + m_tip
        
        # 重心 CG (mm)
        # 先端にtipがあるためLが伸びるとCGは大きく前に引っ張られる
        cg = (m_motor * 35.0 + m_fuselage * (L * 0.50) + m_fin * 25.0 + m_tip * (L - 8.0)) / m_tot
        
        # 空力中心 CP (mm)
        # フィンを後ろ寄りに設計した場合: フィンCPは後端から約 22mm
        # 胴体ノーズCPは 約 L * 0.60
        # 面積比率
        a_fin = 0.0055 * f
        a_body = (L * 22.0 * 1e-6) * 0.35 # 胴体実効揚力面積
        cp = (a_body * (L * 0.60) + a_fin * 22.0) / (a_body + a_fin)
        
        margin = (cg - cp) / 22.0
        Margin[i, j] = margin
        
        # 最高高度 (m)
        cd = 0.30 + 0.08 * f + 0.03 * (L / 179.0)
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
lines = ax.contour(L_mesh, Fin_mesh, Margin, levels=[0.5, 1.0, 1.5, 2.0], colors=['white', 'lime', 'yellow', 'red'], linewidths=2.0)
ax.clabel(lines, inline=True, fmt="Margin %.1f cal", fontsize=10)

ax.set_xlabel("Rocket Total Length [mm]", fontsize=12)
ax.set_ylabel("Fin Area Scale [ratio]", fontsize=12)
ax.set_title("Optimization Map: Total Length vs Fin Area Scale", fontsize=14, fontweight="bold")
ax.grid(True, alpha=0.3)

# 1発プリント限界線 (180mm / 200mm)
ax.axvline(180, color='magenta', ls='--', lw=2, label="1-Piece Print Limit (180mm)")
ax.axvline(200, color='orange', ls=':', lw=2, label="Print Bed Limit (200mm)")

ax.legend(loc="upper left")
plt.tight_layout()
output_img = "export/optimization_map.png"
plt.savefig(output_img, dpi=150)
plt.close()
print(f"Optimization map saved: {output_img}")
