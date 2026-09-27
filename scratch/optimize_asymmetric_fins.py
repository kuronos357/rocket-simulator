import os
import sys
import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

from sim_engine.motor_db import get_motor

print("=" * 80)
print("  🚀 [非対称T字翼の最適解逆算]")
print("  水平翼 (0°/180°: ブレーキ用) vs 垂直翼 (90°: ヨー安定用) の異径最適化")
print("=" * 80)

motor = get_motor("1/2A6-2")

# パラメータグリッド
# 全長 L: 190mm, 200mm, 210mm, 220mm
lengths = [190, 200, 210, 220]

# 水平翼(3時・9時) 面積スケール (片側): 0.6 〜 1.5 (基準片側11.2cm2に対して)
horiz_scales = np.linspace(0.6, 1.5, 10)

# 垂直翼(12時) 面積スケール (1枚): 0.3 〜 1.0 (最小限のヨー安定性を狙う)
vert_scales = np.linspace(0.3, 1.0, 8)

ref_d = 22.0
ref_area = np.pi * ((ref_d / 2.0) * 1e-3)**2
air_density = 1.225
g = 9.80665

# 基準フィン1枚 (スパン32mm, 根本50mm, 翼端20mm): 面積 11.2 cm2, 重量約 2.2g
s1_base_m2 = 11.2 * 1e-4
m1_base_g = 2.2

results = []

def run_flight_profile(m_launch_g, m_dry_g, cd_ascent, descent_CdS):
    dt = 0.005
    t = 0.0
    z = 0.0
    v = 0.0
    max_z = 0.0
    
    burn_time = motor.burn_time
    ejection_t = burn_time + motor.delay_sec
    deployed = False
    
    while t < 60.0:
        if t <= burn_time:
            m_now = m_dry_g + motor.get_mass_g(t) - motor.burnout_mass_g
            thrust = motor.get_thrust(t)
        else:
            m_now = m_dry_g
            thrust = 0.0
            
        m_kg = m_now * 1e-3
        if not deployed and t >= ejection_t:
            deployed = True
            
        cd = cd_ascent if not deployed else descent_CdS
        area = ref_area if not deployed else 1.0
        drag = 0.5 * air_density * (v**2) * cd * area * np.sign(v)
        
        a = (thrust - drag - (m_kg * g)) / m_kg
        v += a * dt
        z += v * dt
        if z > max_z:
            max_z = z
        if deployed and z <= 0.0 and t > 1.0:
            break
        t += dt
        
    v_term = np.sqrt((2.0 * (m_dry_g * 1e-3) * g) / (air_density * max(1e-4, descent_CdS)))
    return max_z, v_term, t

for L in lengths:
    for h_scale in horiz_scales:
        for v_scale in vert_scales:
            # 1. フィン寸法 & 質量
            # 水平翼2枚 + 垂直翼1枚
            m_fin_horiz = 2 * (m1_base_g * h_scale)
            m_fin_vert = 1 * (m1_base_g * v_scale)
            m_fin_tot = m_fin_horiz + m_fin_vert
            
            m_fuselage = (14.0 * (L / 179.0)) + 1.2
            m_tip = 6.0 # 先端回収系
            
            m_dry = m_fuselage + m_fin_tot + m_tip + motor.burnout_mass_g
            m_launch = m_fuselage + m_fin_tot + m_tip + motor.total_mass_g
            
            # 2. 重心 (CG)
            # フィンは後端集中 (Z=25mm)
            cg_y = (motor.total_mass_g * 35.0 + m_fin_tot * 25.0 + m_fuselage * (L * 0.50) + m_tip * (L - 8.0)) / m_launch
            
            # 3. 空力中心 (CP): ピッチとヨーで独立計算！
            # 胴体揚力
            s_body = (L * ref_d * 1e-6) * 0.32
            cp_body = L * 0.62
            
            # A. ヨー方向 (垂直尾翼 1枚が受持つ)
            s_fin_yaw = s1_base_m2 * v_scale
            cp_yaw = (s_body * cp_body + s_fin_yaw * 25.0) / (s_body + s_fin_yaw)
            margin_yaw = (cg_y - cp_yaw) / ref_d
            
            # B. ピッチ方向 (水平尾翼 2枚が受持つ)
            s_fin_pitch = 2 * s1_base_m2 * h_scale
            cp_pitch = (s_body * cp_body + s_fin_pitch * 25.0) / (s_body + s_fin_pitch)
            margin_pitch = (cg_y - cp_pitch) / ref_d
            
            # 総合マージン (両方が1.0cal以上であること)
            min_margin = min(margin_yaw, margin_pitch)
            is_safe = (margin_yaw >= 1.0) and (margin_pitch >= 1.0) and (max(margin_yaw, margin_pitch) <= 2.2)
            
            # 4. 上昇時抗力 Cd
            # 水平翼2枚 + 垂直翼1枚の総表面積に比例
            total_fin_area_ratio = (2 * h_scale + v_scale) / 3.0
            cd_ascent = 0.27 + (0.07 * total_fin_area_ratio) + (0.03 * (L / 179.0))
            
            # 5. 横向き降下時 (0°/180°姿勢: 水平翼が真向から風を受ける)
            # 水平翼2枚の面積 (2 * 11.2cm2 * h_scale) + 胴体側面
            area_horiz_fins_m2 = 2 * s1_base_m2 * h_scale
            area_lat_total = (L * ref_d * 1e-6) + area_horiz_fins_m2
            
            # 垂直翼は横向き風に対してエッジを向けるため、ブレーキ面積への寄与はほぼゼロ！
            descent_CdS = (0.20 * 0.05) + (1.25 * area_lat_total)
            
            # 6. フル物理シミュレーション
            apogee_m, v_term, total_t = run_flight_profile(m_launch, m_dry, cd_ascent, descent_CdS)
            
            results.append({
                "L_mm": L,
                "h_scale": h_scale,
                "v_scale": v_scale,
                "horiz_span_mm": 32.0 * (h_scale**0.6), # 水平翼スパン
                "vert_span_mm": 32.0 * (v_scale**0.6),  # 垂直翼スパン
                "margin_yaw": margin_yaw,
                "margin_pitch": margin_pitch,
                "min_margin": min_margin,
                "m_launch_g": m_launch,
                "apogee_m": apogee_m,
                "v_term_m_s": v_term,
                "total_t_s": total_t,
                "is_safe": is_safe
            })

safe_results = [r for r in results if r["is_safe"]]
safe_results.sort(key=lambda x: x["total_t_s"], reverse=True)

print(f"\n計算完了: {len(results)} パターン中、安全基準適合は {len(safe_results)} パターン")

print("\n🏆 【異径T字翼 滞空時間ランキング TOP 5】")
print("-" * 95)
print(f"{'順位':^4} | {'全長':^6} | {'水平翼(0/180°)':^14} | {'垂直翼(90°)':^12} | {'ヨーMargin':^10} | {'ピッチMargin':^10} | {'高度':^8} | {'降下速度':^10} | {'総滞空時間':^10}")
print("-" * 95)

for rank, r in enumerate(safe_results[:5], 1):
    h_str = f"{int(r['h_scale']*100)}% (巾{r['horiz_span_mm']:.1f}mm)"
    v_str = f"{int(r['v_scale']*100)}% (巾{r['vert_span_mm']:.1f}mm)"
    print(f"{rank:^4} | {r['L_mm']:^6.0f} | {h_str:^14} | {v_str:^12} | {r['margin_yaw']:^10.2f} | {r['margin_pitch']:^10.2f} | {r['apogee_m']:^8.1f}m | {r['v_term_m_s']:^10.2f}m/s | {r['total_t_s']:^10.1f}秒")
print("-" * 95)

# グラフ作成: 全長200mmにおける 水平翼スケール vs 垂直翼スケール の滞空時間マップ
L200_res = [r for r in results if r["L_mm"] == 200]
H_vals = np.unique(horiz_scales)
V_vals = np.unique(vert_scales)
H_mat, V_mat = np.meshgrid(H_vals, V_vals)
T_mat = np.zeros_like(H_mat)
Safe_mat = np.zeros_like(H_mat, dtype=bool)

for r in L200_res:
    i = np.where(V_vals == r["v_scale"])[0][0]
    j = np.where(H_vals == r["h_scale"])[0][0]
    T_mat[i, j] = r["total_t_s"]
    Safe_mat[i, j] = r["is_safe"]

fig, ax = plt.subplots(figsize=(10, 7))
c = ax.contourf(H_mat, V_mat, T_mat, levels=20, cmap="plasma", alpha=0.9)
cbar = fig.colorbar(c, ax=ax)
cbar.set_label("Total Flight Time [seconds]", fontsize=11)

# 安全境界線 (Yaw margin >= 1.0)
yaw_lines = ax.contour(H_mat, V_mat, np.array([[r["margin_yaw"] for r in L200_res if r["v_scale"]==v] for v in V_vals]),
                       levels=[1.0, 1.2], colors=['lime', 'white'], linewidths=2.0)
ax.clabel(yaw_lines, inline=True, fmt="Yaw %.1f cal", fontsize=10)

best_200 = [r for r in safe_results if r["L_mm"] == 200][0]
ax.plot(best_200["h_scale"], best_200["v_scale"], marker='*', color='yellow', markersize=20, markeredgecolor='black',
        label=f"Best at 200mm: {best_200['total_t_s']:.1f}s\n(Horiz={int(best_200['h_scale']*100)}%, Vert={int(best_200['v_scale']*100)}%)")

ax.set_xlabel("Horizontal Fin Scale (0° / 180°) [ratio]", fontsize=12)
ax.set_ylabel("Vertical Fin Scale (90°) [ratio]", fontsize=12)
ax.set_title("Asymmetric T-Fin Optimization Map (Length = 200mm)", fontsize=14, fontweight="bold")
ax.grid(True, alpha=0.3)
ax.legend(loc="upper left")

plt.tight_layout()
output_chart = "export/asymmetric_fin_optimization.png"
plt.savefig(output_chart, dpi=150)
plt.close()
print(f"📊 非対称翼最適化マップを保存しました: {output_chart}")
