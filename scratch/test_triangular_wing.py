import math
import numpy as np

# v14 基本パラメータ
L = 190.0
D = 22.0
R = 11.0
cg_v14 = 56.91
m_tot_v14 = 27.57
surf_density = 0.0346 # g/cm2 (PLA 1層 0.4mm)

# ノーズ・胴体パラメータ
cna_nose = 2.0
cp_nose_tail = L - 0.466 * 60.0 # ~ 162 mm

def evaluate_wing_plan(name, cr, ct, span, sweep_le):
    """
    cr: 根元コード長 [mm]
    ct: 翼端コード長 [mm]
    span: スパン (突出長) [mm]
    sweep_le: 前縁後退量 [mm] (後縁直角なら sweep_le = cr - ct)
    """
    # 1. 幾何学
    area_1fin_mm2 = 0.5 * (cr + ct) * span
    area_1fin_cm2 = area_1fin_mm2 * 1e-2
    # 3時・9時 2枚の表面積 (表裏+端面)
    surf_area_cm2 = 2 * (2 * area_1fin_cm2 + (ct * 0.4 * 1e-1))
    m_fins_g = surf_area_cm2 * surf_density
    # フィン重心 Y (テールからの距離: 根元後縁がY=0)
    # 三角形/台形の面図心
    y_fin = (cr**2 + cr*ct + ct**2) / (3.0 * (cr + ct)) if (cr + ct) > 0 else 0.0
    
    # 全体重量と重心の変化 (v14のベース機体からフィンの差分を計算)
    # v14現行フィン質量 (cr=51, ct=20, span=31)
    area_v14_mm2 = 0.5 * (51 + 20) * 31
    m_v14_fins = 2 * (2 * area_v14_mm2 * 1e-2) * surf_density
    
    m_new_tot = m_tot_v14 - m_v14_fins + m_fins_g
    cg_new = (m_tot_v14 * cg_v14 - m_v14_fins * 20.0 + m_fins_g * y_fin) / m_new_tot
    
    # 2. Barrowman 空力計算 (3時・9時フィン)
    mid_sweep = sweep_le + (ct - cr)/2.0
    Lf = math.sqrt(mid_sweep**2 + span**2)
    k_body = 1.0 + R / (R + span)
    denom = 1.0 + math.sqrt(1.0 + (2.0 * Lf / (cr + ct))**2)
    cna_fins = k_body * (4.0 * 2.0 * (span / D)**2) / denom
    
    # フィン空力中心 (後端 Y=0 からの距離)
    # Barrowman 式: xb_fin は前縁最先端からの距離
    # 後端 Y=0 からの距離 cp_fin = cr - [ sweep * (cr+2ct)/(3(cr+ct)) + (1/6)(cr+ct - cr*ct/(cr+ct)) ]
    term1 = sweep_le * (cr + 2*ct) / (3.0 * (cr + ct))
    term2 = (1.0 / 6.0) * (cr + ct - (cr * ct) / (cr + ct))
    cp_fin = cr - (term1 + term2)
    
    # 12時フィン (垂直尾翼: cr2=35.8, span2=27)
    cna_12 = 1.5 * (4.0 * 1.0 * (27 / D)**2) / (1.0 + math.sqrt(1.0 + (2.0 * 27 / 35.8)**2))
    cp_12 = 15.0
    
    # 全体 CP
    tot_cna = cna_nose + cna_fins + cna_12
    cp_total = (cna_nose * cp_nose_tail + cna_fins * cp_fin + cna_12 * cp_12) / tot_cna
    
    # 静安定マージン
    margin_mm = cg_new - cp_total
    margin_cal = margin_mm / D
    
    # 3. 飛翔予測 (抗力 & 到達高度)
    S_ref = math.pi * (R * 1e-3)**2
    total_wet_cm2 = 330.0 - (area_v14_mm2 * 4 * 1e-2) + (area_1fin_mm2 * 4 * 1e-2)
    Cd = 0.0045 * (total_wet_cm2 * 1e-4 / S_ref) + 0.12 + 0.08
    
    # 簡易飛翔高度
    m_avg = m_new_tot - 0.78
    v_bo = (1.25 / (m_avg * 1e-3)) - 9.8 * 0.32
    h_bo = 0.5 * v_bo * 0.32
    k_drag = 0.5 * 1.225 * Cd * S_ref / (m_new_tot * 1e-3)
    h_coast = (1.0 / (2.0 * k_drag)) * math.log(1.0 + k_drag * v_bo**2 / 9.8) if k_drag > 0 else 0
    apogee = h_bo + h_coast
    
    return {
        "name": name,
        "cr": cr, "ct": ct, "span": span,
        "area_1fin": area_1fin_cm2,
        "mass_tot": m_new_tot,
        "cg": cg_new,
        "cp": cp_total,
        "margin_mm": margin_mm,
        "margin_cal": margin_cal,
        "cna_fins": cna_fins,
        "Cd": Cd,
        "apogee": apogee
    }

plans = [
    evaluate_wing_plan("現行 v14 (台形翼)", cr=51.0, ct=20.0, span=31.0, sweep_le=31.0),
    evaluate_wing_plan("案1: 前縁延長三角翼 (後縁0, 翼端0)", cr=51.0, ct=0.0, span=51.0, sweep_le=51.0),
    evaluate_wing_plan("案2: スパン維持三角翼 (スパン31mm固定)", cr=31.0, ct=0.0, span=31.0, sweep_le=31.0),
    evaluate_wing_plan("案3: 中間三角翼 (スパン41mm, コード41mm)", cr=41.0, ct=0.0, span=41.0, sweep_le=41.0),
]

print("=" * 115)
print(f"{'プラン':<26} | {'翼寸法 (根元x翼端xスパン)':<24} | {'片面面積':<10} | {'重心CG':<8} | {'空力中心CP':<10} | {'静安定マージン':<16} | {'最高高度':<8}")
print("=" * 115)
for p in plans:
    dims = f"{p['cr']:.0f} x {p['ct']:.0f} x {p['span']:.0f} mm"
    status = "[OK] 安定域" if p["margin_cal"] >= 1.0 else ("[○] 安定" if p["margin_cal"] >= 0.5 else ("[△] 弱安定" if p["margin_cal"] >= 0.0 else "[×] 不安定"))
    print(f"{p['name']:<24} | {dims:<22} | {p['area_1fin']:5.1f} cm2  | {p['cg']:5.1f}mm  | {p['cp']:5.1f}mm    | {p['margin_cal']:+5.2f} cal ({status}) | {p['apogee']:5.1f} m")
print("=" * 115)
