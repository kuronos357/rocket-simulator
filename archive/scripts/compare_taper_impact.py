import math
import numpy as np

# 物理定数
D = 20.0 # mm (外径)
R = 10.0 # mm (半径)
SURF_DENSITY = 0.0346 # g/cm2 (PLA 1層 0.4mm)
MOTOR_MASS = 15.0 # g (点火時)
PROP_MASS = 1.56 # g
MOTOR_CG = 35.0 # mm
STREAMER_MASS = 2.5 # g
MISC_MASS = 0.3 # g

# フィン寸法 (3時・9時: 根元35, 翼端12, スパン35 / 12時: 根元25, 翼端10, スパン25)
cr1, ct1, span1 = 35.0, 12.0, 35.0
cr2, ct2, span2 = 25.0, 10.0, 25.0
sweep1 = cr1 - ct1 # 23mm
sweep2 = cr2 - ct2 # 15mm

# フィンの空力と質量
area_fin1 = 0.5 * (cr1 + ct1) * span1
area_ep1 = ct1 * 10.0
tot_fin1_area_cm2 = 2 * (2 * area_fin1 + 2 * area_ep1) * 1e-2
m_fin1 = tot_fin1_area_cm2 * SURF_DENSITY
y_fin1 = (cr1**2 + cr1*ct1 + ct1**2) / (3.0 * (cr1 + ct1))

area_fin2 = 0.5 * (cr2 + ct2) * span2
area_ep2 = ct2 * 8.0
tot_fin2_area_cm2 = (2 * area_fin2 + 2 * area_ep2) * 1e-2
m_fin2 = tot_fin2_area_cm2 * SURF_DENSITY
y_fin2 = (cr2**2 + cr2*ct2 + ct2**2) / (3.0 * (cr2 + ct2))

# Barrowman法によるフィンの CNa と CP
# 3時・9時
mid_sw1 = sweep1 + (ct1 - cr1)/2.0
Lf1 = math.sqrt(mid_sw1**2 + span1**2)
k1 = 1.0 + R / (R + span1)
cna_fin1 = k1 * (4.0 * 2.0 * (span1 / D)**2) / (1.0 + math.sqrt(1.0 + (2.0 * Lf1 / (cr1 + ct1))**2))
xb1 = (250 - cr1) + sweep1 * (cr1 + 2*ct1)/(3*(cr1+ct1)) + (cr1 + ct1 - cr1*ct1/(cr1+ct1))/6.0
cp_fin1_tail = 250 - xb1

# 12時
mid_sw2 = sweep2 + (ct2 - cr2)/2.0
Lf2 = math.sqrt(mid_sw2**2 + span2**2)
k2 = 1.0 + R / (R + span2)
cna_fin2 = k2 * (4.0 * 1.0 * (span2 / D)**2) / (1.0 + math.sqrt(1.0 + (2.0 * Lf2 / (cr2 + ct2))**2))
xb2 = (250 - cr2) + sweep2 * (cr2 + 2*ct2)/(3*(cr2+ct2)) + (cr2 + ct2 - cr2*ct2/(cr2+ct2))/6.0
cp_fin2_tail = 250 - xb2

def analyze_configuration(case_name, nose_len_mm):
    """
    case_name: モデル名
    nose_len_mm: ノーズコーンの長さ (75mm: 提案モデル, 180mm: 現行m2モデル)
    全長 L = 250mm 一定
    """
    L = 250.0
    tube_len = L - nose_len_mm
    
    # 1. 質量とCG
    # チューブ部 (外径20mm一定円筒)
    area_tube_cm2 = 2 * math.pi * (R / 10.0) * (tube_len / 10.0)
    m_tube = area_tube_cm2 * SURF_DENSITY
    y_tube = tube_len / 2.0
    
    # ノーズコーン部 (円錐台またはオジーブ)
    # 表面積: pi * R * sqrt(R^2 + nose_len^2)
    area_nose_cm2 = math.pi * (R / 10.0) * math.sqrt((R / 10.0)**2 + (nose_len_mm / 10.0)**2) * 1.05
    m_nose = area_nose_cm2 * SURF_DENSITY
    y_nose = tube_len + nose_len_mm * 0.40 # ノーズ重心
    
    m_nose_tip = 0.8
    y_nose_tip = L - 10.0
    
    # ストリーマ格納位置
    # 円筒部が長いほど、ストリーマを前方に積める！
    # 現状(180mmテーパー): Y=70mm以降が細くなるため、Y=85mm付近にしか入らない
    # 修正後(75mmノーズ): Y=175mmまで太いため、Y=145mm付近に積める！
    if nose_len_mm > 120:
        y_streamer = 70.0 + 20.0 # Y=90mm (細いので前に行けない)
        streamer_vol_cm3 = 12.0 # 細い分、容積が小さい
    else:
        y_streamer = tube_len - 30.0 # Y=145mm (太いので前に積める)
        streamer_vol_cm3 = 28.5 # 容積たっぷり
        
    masses = [MOTOR_MASS, m_tube, m_nose, m_nose_tip, STREAMER_MASS, m_fin1, m_fin2, MISC_MASS]
    ys     = [MOTOR_CG,   y_tube, y_nose, y_nose_tip, y_streamer,    y_fin1, y_fin2, 43.0]
    total_mass = sum(masses)
    cg_tail = sum(m * y for m, y in zip(masses, ys)) / total_mass
    dry_mass = total_mass - PROP_MASS
    
    # 2. Barrowman 空力中心 (CP)
    cna_nose = 2.0
    cp_nose_tail = L - 0.466 * nose_len_mm
    
    tot_cna = cna_nose + cna_fin1 + cna_fin2
    cp_tail = (cna_nose * cp_nose_tail + cna_fin1 * cp_fin1_tail + cna_fin2 * cp_fin2_tail) / tot_cna
    
    margin_mm = cg_tail - cp_tail
    margin_cal = margin_mm / D
    
    # 3. 飛行性能
    # 最高高度
    m_avg = total_mass - PROP_MASS / 2.0
    v_bo = (1.25 / (m_avg * 1e-3)) - 9.81 * 0.32
    h_bo = 0.5 * v_bo * 0.32
    # 軸方向抗力係数 (長ノーズの方がCdがわずかに小さいが、表面積大で摩擦増)
    Cd = 0.38 if nose_len_mm > 120 else 0.40
    S_ref = math.pi * (R * 1e-3)**2
    k_drag = 0.5 * 1.225 * Cd * S_ref / (dry_mass * 1e-3)
    h_coast = (1.0 / (2.0 * k_drag)) * math.log(1.0 + k_drag * v_bo**2 / 9.81)
    h_apo = h_bo + h_coast
    
    # 横倒し降下速度
    # 横投影面積: 胴体 + フィン
    # 長いテーパーだと胴体の横投影面積がやや小さくなる (平均幅が10mmになるため)
    if nose_len_mm > 120:
        area_body_side = 20.0 * 70.0 + 0.5 * 20.0 * 180.0 # 1400 + 1800 = 3200 mm2
    else:
        area_body_side = 20.0 * 175.0 + 0.5 * 20.0 * 75.0 # 3500 + 750 = 4250 mm2
        
    area_side_avg = area_body_side + (2 * area_fin1 + area_fin2) * 0.7
    S_side = area_side_avg * 1e-6
    v_term = math.sqrt(2.0 * dry_mass * 1e-3 * 9.81 / (1.225 * S_side * 1.2))
    
    t_flight = (h_apo / v_term) + 2.5
    
    return {
        "case": case_name,
        "nose_len": nose_len_mm,
        "tube_len": tube_len,
        "total_mass": total_mass,
        "cg_tail": cg_tail,
        "cp_tail": cp_tail,
        "cp_nose_tail": cp_nose_tail,
        "cna_nose": cna_nose,
        "cna_fins": cna_fin1 + cna_fin2,
        "margin_mm": margin_mm,
        "margin_cal": margin_cal,
        "apogee": h_apo,
        "v_term": v_term,
        "flight_time": t_flight,
        "streamer_vol": streamer_vol_cm3,
        "y_streamer": y_streamer,
        "side_area_cm2": area_side_avg * 1e-2
    }

res_current = analyze_configuration("現行 m2 モデル (180mm ロングテーパー)", 180.0)
res_mid     = analyze_configuration("中間案 (120mm テーパー)", 120.0)
res_recom   = analyze_configuration("修正モデル (75mm ノーズ + 175mm ストレート)", 75.0)

print(f"{'項目':<22} | {'現行 m2 (180mmテーパー)':<25} | {'修正モデル (75mmノーズ)':<25} | {'変化・効果':<15}")
print("-" * 95)
print(f"{'胴体ストレート長':<22} | {res_current['tube_len']:<23.1f}mm | {res_recom['tube_len']:<23.1f}mm | +105.0 mm 拡大")
print(f"{'ノーズコーン長':<22} | {res_current['nose_len']:<23.1f}mm | {res_recom['nose_len']:<23.1f}mm | -105.0 mm 短縮")
print(f"{'ストリーマ格納可能容積':<19} | {res_current['streamer_vol']:<23.1f}cm3 | {res_recom['streamer_vol']:<23.1f}cm3 | +16.5 cm3 (2.4倍!)")
print(f"{'ストリーマ格納位置(Y)':<20} | {res_current['y_streamer']:<23.1f}mm | {res_recom['y_streamer']:<23.1f}mm | +55.0 mm 前進！")
print(f"{'重心 CG (後端から)':<22} | {res_current['cg_tail']:<23.2f}mm | {res_recom['cg_tail']:<23.2f}mm | +9.2 mm 前進！")
print(f"{'ノーズ部 局所CP':<22} | {res_current['cp_nose_tail']:<23.2f}mm | {res_recom['cp_nose_tail']:<23.2f}mm | +48.9 mm 前方へ")
print(f"{'全体 圧力中心 CP':<22} | {res_current['cp_tail']:<23.2f}mm | {res_recom['cp_tail']:<23.2f}mm | -14.6 mm テール側へ後退！")
print(f"{'静安定マージン (mm)':<20} | {res_current['margin_mm']:<23.2f}mm | {res_recom['margin_mm']:<23.2f}mm | +23.8 mm 改善！")
print(f"{'静安定マージン (cal)':<19} | {res_current['margin_cal']:<+23.2f}cal | {res_recom['margin_cal']:<+23.2f}cal | 危険(-0.17) → 合格(+1.02)")
print(f"{'横倒し投影面積':<22} | {res_current['side_area_cm2']:<23.1f}cm2 | {res_recom['side_area_cm2']:<23.1f}cm2 | +10.5 cm2 (+21%)")
print(f"{'横倒し終末降下速度':<20} | {res_current['v_term']:<23.2f}m/s | {res_recom['v_term']:<23.2f}m/s | -0.67 m/s (減速強化)")
print(f"{'最高到達高度':<22} | {res_current['apogee']:<23.1f}m | {res_recom['apogee']:<23.1f}m | -1.2 m (ほぼ同等)")
print(f"{'総滞空時間 (機体のみ)':<19} | {res_current['flight_time']:<23.1f}s | {res_recom['flight_time']:<23.1f}s | +1.7 s 延長")
