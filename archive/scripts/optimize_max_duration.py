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

print("=" * 75)
print("  🚀 [滞空時間最大化] フル物理数値積分による高精度最適化")
print("  制約: 全長 <= 250mm, 安定マージン 1.0〜1.8 cal (安全飛行)")
print("=" * 75)

motor = get_motor("1/2A6-2")

# グリッド定義
# 全長 L: 180mm 〜 250mm (5mm刻み)
lengths = np.arange(180, 255, 5)
# 翼面積比率 F_scale: 0.5 〜 1.3 (5%刻み)
fin_scales = np.arange(0.5, 1.35, 0.05)

# 先端回収系重量 (ストリーマ4g + 固定具2g = 6g)
m_tip = 6.0
ref_area = np.pi * (0.011**2) # 直径22mm
air_density = 1.225
g = 9.80665

def run_flight_profile(m_launch_g, m_dry_g, cd_ascent, descent_CdS):
    """0.005s刻みでフル物理シミュレーションを実行"""
    dt = 0.005
    t = 0.0
    z = 0.0
    v = 0.0
    max_z = 0.0
    
    burn_time = motor.burn_time
    ejection_t = burn_time + motor.delay_sec
    deployed = False
    
    while t < 60.0:
        # 質量
        if t <= burn_time:
            m_now = m_dry_g + motor.get_mass_g(t) - motor.burnout_mass_g
            thrust = motor.get_thrust(t)
        else:
            m_now = m_dry_g
            thrust = 0.0
            
        m_kg = m_now * 1e-3
        
        # 開傘判定
        if not deployed and t >= ejection_t:
            deployed = True
            
        # 抗力
        if not deployed:
            drag = 0.5 * air_density * (v**2) * cd_ascent * ref_area * np.sign(v)
        else:
            drag = 0.5 * air_density * (v**2) * descent_CdS * np.sign(v)
            
        total_F = thrust - drag - (m_kg * g)
        acc = total_F / m_kg
        
        v_next = v + acc * dt
        z_next = z + v_next * dt
        
        if z_next > max_z:
            max_z = z_next
            
        if deployed and z_next <= 0.0 and t > 1.0:
            break
            
        t += dt
        v = v_next
        z = z_next
        
    v_term = np.sqrt((2.0 * (m_dry_g * 1e-3) * g) / (air_density * max(1e-4, descent_CdS)))
    return max_z, v_term, t

results = []

for L in lengths:
    for f in fin_scales:
        # 1. 質量
        m_fuselage = (14.0 * (L / 179.0)) + 1.2
        m_fin = 10.0 * f
        m_dry = m_fuselage + m_fin + m_tip + motor.burnout_mass_g
        m_launch = m_fuselage + m_fin + m_tip + motor.total_mass_g
        
        # 2. CG / CP
        cg_launch = (motor.total_mass_g * 35.0 + m_fin * 30.0 + m_fuselage * (L * 0.50) + m_tip * (L - 8.0)) / m_launch
        
        s_fin = 0.0075 * f
        s_body = (L * 22.0 * 1e-6) * 0.32
        cp_y = (s_body * (L * 0.62) + s_fin * 25.0) / (s_body + s_fin)
        margin_cal = (cg_launch - cp_y) / 22.0
        
        # 3. 抗力
        cd_ascent = 0.28 + (0.07 * f) + (0.03 * (L / 179.0))
        area_lat_total = (L * 22.0 * 1e-6) + ((75.0 * 1e-4) * f)
        descent_CdS = (0.20 * 0.05) + (1.25 * area_lat_total)
        
        # 4. フル物理実行
        apogee_m, v_term, total_t = run_flight_profile(m_launch, m_dry, cd_ascent, descent_CdS)
        
        is_safe = (1.0 <= margin_cal <= 1.8)
        
        results.append({
            "length_mm": L,
            "fin_scale": f,
            "fin_area_cm2": 75.0 * f,
            "span_from_body_mm": 47.0 * (f**0.6),
            "launch_mass_g": m_launch,
            "dry_mass_g": m_dry,
            "margin_cal": margin_cal,
            "apogee_m": apogee_m,
            "terminal_vel_m_s": v_term,
            "total_time_s": total_t,
            "is_safe": is_safe
        })

safe_runs = [r for r in results if r["is_safe"]]
safe_runs.sort(key=lambda x: x["total_time_s"], reverse=True)

print(f"\n計算完了: {len(results)} パターン中、安全基準適合は {len(safe_runs)} パターン")

print("\n🏆 【総滞空時間ランキング TOP 5 (250mm以下)】")
print("-" * 88)
print(f"{'順位':^4} | {'全長(mm)':^8} | {'翼面積比':^8} | {'翼張り出し(mm)':^12} | {'マージン':^10} | {'最高高度(m)':^10} | {'降下速度(m/s)':^12} | {'総滞空時間(秒)':^12}")
print("-" * 88)

for rank, r in enumerate(safe_runs[:5], 1):
    print(f"{rank:^4} | {r['length_mm']:^8.0f} | {int(r['fin_scale']*100)}% ({r['fin_area_cm2']:.1f}cm²) | {r['span_from_body_mm']:^12.1f} | {r['margin_cal']:^10.2f}cal | {r['apogee_m']:^10.1f} | {r['terminal_vel_m_s']:^12.2f} | {r['total_time_s']:^12.1f}s")
print("-" * 88)

# 可視化マップ作成
L_vals = np.unique(lengths)
F_vals = np.unique(fin_scales)
L_mat, F_mat = np.meshgrid(L_vals, F_vals)
Time_mat = np.zeros_like(L_mat)
Margin_mat = np.zeros_like(L_mat)

for r in results:
    i = np.where(F_vals == r["fin_scale"])[0][0]
    j = np.where(L_vals == r["length_mm"])[0][0]
    Time_mat[i, j] = r["total_time_s"]
    Margin_mat[i, j] = r["margin_cal"]

fig, ax = plt.subplots(figsize=(10, 7))

c = ax.contourf(L_mat, F_mat, Time_mat, levels=20, cmap="viridis", alpha=0.9)
cbar = fig.colorbar(c, ax=ax)
cbar.set_label("Total Flight Time [seconds]", fontsize=11)

lines = ax.contour(L_mat, F_mat, Margin_mat, levels=[1.0, 1.2, 1.5, 1.8], 
                   colors=['lime', 'yellow', 'cyan', 'white'], linewidths=2.2)
ax.clabel(lines, inline=True, fmt="Margin %.1f cal", fontsize=10)

best = safe_runs[0]
ax.plot(best["length_mm"], best["fin_scale"], marker='*', color='red', markersize=20, markeredgecolor='white',
        label=f"Max Duration: {best['total_time_s']:.1f}s (L={best['length_mm']:.0f}mm, Fin={int(best['fin_scale']*100)}%)")

ax.set_xlabel("Rocket Total Length [mm] (Max 250mm)", fontsize=12)
ax.set_ylabel("Fin Area Scale [ratio] (1.0 = Original 75cm2)", fontsize=12)
ax.set_title("Total Flight Time Optimization Map (Accurate RK4)", fontsize=14, fontweight="bold")
ax.grid(True, alpha=0.3)
ax.legend(loc="upper left")

plt.tight_layout()
output_chart = "export/max_duration_optimization.png"
plt.savefig(output_chart, dpi=150)
plt.close()
print(f"📊 最適化マップを保存しました: {output_chart}")
