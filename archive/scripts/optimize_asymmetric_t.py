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
print("  🚀 [非対称T字翼の最適解逆算: 0°/180°水平翼 vs 90°垂直翼]")
print("  水平翼: 降下エアブレーキ最大化")
print("  垂直翼: ヨー安定限界まで極小化 (軽量・低抗力化)")
print("=" * 80)

motor = get_motor("1/2A6-2")

# パラメータ探索範囲
# 全長 L: 190mm, 200mm, 210mm, 220mm
# 水平翼 スパン s_h: 25mm 〜 45mm
# 水平翼 翼根コード cr_h: 40mm 〜 75mm (翼端コード ct_h = cr_h * 0.4)
# 垂直翼 スパン s_v: 20mm 〜 40mm
# 垂直翼 翼根コード cr_v: 30mm 〜 60mm

R = 11.0; d = 22.0
ref_area = np.pi * ((d / 2.0) * 1e-3)**2
air_density = 1.225
g = 9.80665
m_tip = 6.0

def evaluate_t_rocket(L, s_h, cr_h, s_v, cr_v):
    ct_h = cr_h * 0.45
    ct_v = cr_v * 0.40
    
    # 面積 (cm2)
    area_h = ((cr_h + ct_h) / 2.0 * s_h) * 1e-2 # 片側
    area_v = ((cr_v + ct_v) / 2.0 * s_v) * 1e-2 # 1枚
    
    # 質量 (PLA 1層0.4mm + 2%インフィル)
    m_fin_h = 2 * (area_h * 0.065)
    m_fin_v = 1 * (area_v * 0.065)
    m_fin_tot = m_fin_h + m_fin_v
    
    m_fuselage = 14.0 * (L / 179.0) + 1.2
    m_dry = m_fuselage + m_fin_tot + m_tip + motor.burnout_mass_g
    m_launch = m_fuselage + m_fin_tot + m_tip + motor.total_mass_g
    
    # 重心 CG (Y=0 から)
    z_fin = cr_h * 0.38
    cg = (motor.total_mass_g * 35.0 + m_fin_tot * z_fin + m_fuselage * (L * 0.50) + m_tip * (L - 8.0)) / m_launch
    
    # Barrowman CP
    cn_body = 2.0
    cp_body = L - 28.0
    
    def fin_cn_cp(N, s, cr, ct):
        mid_chord = np.sqrt(s**2 + (0.5 * (cr - ct))**2)
        k_int = 1.0 + (R / (s + R))
        cn = N * (2 * np.pi * (s / d)**2) / (1.0 + np.sqrt(1.0 + (2 * mid_chord / (cr + ct))**2)) * k_int
        x_cp_le = (cr / 3.0) * ((cr + 2*ct) / (cr + ct)) + (1.0/6.0) * ((cr + ct) - (cr*ct)/(cr+ct))
        cp_fin_y = cr - x_cp_le
        return cn, cp_fin_y
        
    cn_h, cp_h_fin = fin_cn_cp(2, s_h, cr_h, ct_h)
    cn_v, cp_v_fin = fin_cn_cp(1, s_v, cr_v, ct_v)
    
    cp_pitch = (cn_body * cp_body + cn_h * cp_h_fin) / (cn_body + cn_h)
    cp_yaw = (cn_body * cp_body + cn_v * cp_v_fin) / (cn_body + cn_v)
    
    margin_pitch = (cg - cp_pitch) / d
    margin_yaw = (cg - cp_yaw) / d
    
    # 安全基準: Yaw >= 1.0, Pitch >= 1.0, どちらも <= 2.2
    if margin_yaw < 1.0 or margin_pitch < 1.0 or margin_yaw > 2.2 or margin_pitch > 2.2:
        return None
        
    # 上昇時抗力 Cd
    total_fin_area_cm2 = 2 * area_h + area_v
    cd_ascent = 0.28 + (0.0035 * total_fin_area_cm2) + (0.03 * (L / 179.0))
    
    # 横向き降下ブレーキ (水平翼2枚 + 胴体側面)
    area_lat_body_m2 = L * d * 1e-6
    area_lat_fins_m2 = 2 * (area_h * 1e-4) # 3時と9時の2枚
    # 垂直翼は真横向きなのでブレーキ面積への寄与ゼロ！
    descent_CdS = (0.20 * 0.05) + 1.25 * (area_lat_body_m2 + area_lat_fins_m2)
    
    # フル物理数値積分 (0.005sステップ)
    dt = 0.005
    t = 0.0; z = 0.0; v = 0.0; max_z = 0.0
    burn_time = motor.burn_time
    ejection_t = burn_time + motor.delay_sec
    deployed = False
    
    while t < 60.0:
        if t <= burn_time:
            m_now = m_dry + motor.get_mass_g(t) - motor.burnout_mass_g
            thrust = motor.get_thrust(t)
        else:
            m_now = m_dry
            thrust = 0.0
        m_kg = m_now * 1e-3
        
        if not deployed and t >= ejection_t:
            deployed = True
            
        cd = cd_ascent if not deployed else descent_CdS
        area = ref_area if not deployed else 1.0
        drag = 0.5 * air_density * (v**2) * cd * area * np.sign(v)
        
        a = (thrust - drag - m_kg * g) / m_kg
        v += a * dt
        z += v * dt
        if z > max_z:
            max_z = z
        if deployed and z <= 0.0 and t > 1.0:
            break
        t += dt
        
    v_term = np.sqrt((2.0 * (m_dry * 1e-3) * g) / (air_density * max(1e-4, descent_CdS)))
    
    return {
        "L": L,
        "s_h": s_h, "cr_h": cr_h, "area_h_single": area_h,
        "s_v": s_v, "cr_v": cr_v, "area_v_single": area_v,
        "m_launch": m_launch, "m_dry": m_dry,
        "cg": cg, "margin_p": margin_pitch, "margin_y": margin_yaw,
        "apogee": max_z, "v_term": v_term, "total_time": t
    }

# グリッドサーチ実行
results = []
for L in [190, 200, 210, 220]:
    for s_h in [28, 32, 36, 40]:
        for cr_h in [50, 60, 70]:
            for s_v in [22, 26, 30, 34]:
                for cr_v in [35, 45, 55]:
                    res = evaluate_t_rocket(L, s_h, cr_h, s_v, cr_v)
                    if res:
                        results.append(res)

results.sort(key=lambda x: x["total_time"], reverse=True)

print(f"\n計算完了: {len(results)} 通りの安全適合設計案が見つかりました！")

print("\n🏆 【0°/180° 水平翼 vs 90° 垂直翼 最適設計 TOP 5】")
print("-" * 105)
print(f"{'順位':^4} | {'全長':^6} | {'水平翼(0/180°:片側)':^22} | {'垂直翼(90°:1枚)':^20} | {'Yaw Margin':^10} | {'Pitch Margin':^12} | {'高度':^8} | {'降下速度':^10} | {'総滞空時間':^10}")
print("-" * 105)

for rank, r in enumerate(results[:5], 1):
    h_str = f"スパン{r['s_h']}mm x 根{r['cr_h']}mm ({r['area_h_single']:.1f}cm²)"
    v_str = f"スパン{r['s_v']}mm x 根{r['cr_v']}mm ({r['area_v_single']:.1f}cm²)"
    print(f"{rank:^4} | {r['L']:^6.0f} | {h_str:^22} | {v_str:^20} | {r['margin_y']:^10.2f} | {r['margin_p']:^12.2f} | {r['apogee']:^8.1f}m | {r['v_term']:^10.2f}m/s | {r['total_time']:^10.1f}秒")
print("-" * 105)

# 第1位の設計のサマリー保存
best = results[0]
with open("export/best_asymmetric_t_fin.txt", "w", encoding="utf-8") as f:
    f.write("=== 異径T字フィン 最適設計スペック ===\n")
    f.write(f"全長: {best['L']:.0f} mm\n")
    f.write(f"水平翼 (0°/180°): スパン {best['s_h']:.0f} mm, 翼根コード {best['cr_h']:.0f} mm, 翼端コード {best['cr_h']*0.45:.1f} mm\n")
    f.write(f"垂直翼 (90°): スパン {best['s_v']:.0f} mm, 翼根コード {best['cr_v']:.0f} mm, 翼端コード {best['cr_v']*0.40:.1f} mm\n")
    f.write(f"全備重量: {best['m_launch']:.1f} g (乾燥重量 {best['m_dry']:.1f} g)\n")
    f.write(f"最高高度: {best['apogee']:.1f} m\n")
    f.write(f"終端降下速度: {best['v_term']:.2f} m/s\n")
    f.write(f"総滞空時間: {best['total_time']:.1f} 秒\n")
    f.write(f"静安定性: ヨー {best['margin_y']:.2f} cal / ピッチ {best['margin_p']:.2f} cal\n")
