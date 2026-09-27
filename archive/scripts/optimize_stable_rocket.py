import numpy as np
import math

# パラメータ設定と最適化探索
# モーター: 1/2A6-2 (mass=15.0g, com=35mm from tail, prop=1.56g, impulse=1.25Ns, burn_t=0.32s, delay=2.0s)
# 機体: PLA 1層 0.4mm (外径 D=22mm, 半径 R=11mm)
# 材料密度: PLA 1.24 g/cm3, 表面積あたりの機体重量 ~ 0.0496 g/cm2 (0.4mm厚)
# スライサー実績: v12 (L=180, area~320cm2) で 11.07g -> 実効面密度 = 11.07 / 320 ~ 0.0346 g/cm2

REF_D = 22.0 # mm
REF_R = 11.0 # mm
AIRFRAME_SURF_DENSITY = 0.0346 # g/cm2
STREAMER_MASS = 2.0 # g (ストリーマ + ショックコード)

def calc_rocket_properties(L, cr1, ct1, span1, sweep1, cr2, ct2, span2, sweep2):
    """
    L: 全長 mm (180 ~ 245 mm)
    cr1, ct1, span1, sweep1: 3時・9時フィン (root chord, tip chord, span, sweep back mm)
    cr2, ct2, span2, sweep2: 12時フィン
    フィンの後端はテール Y=0 (または Y=2mm) に揃える
    """
    # 1. 質量とCGの計算
    # モーター
    m_motor = 15.0 # g
    y_motor = 35.0 # mm
    
    # 胴体チューブ + ノーズコーン
    # ノーズコーン長: 約 50mm, 胴体チューブ長: L - 50mm
    # 円筒部表面積: 2 * pi * R * (L - 50)
    # ノーズコーン表面積: pi * R * sqrt(R^2 + 50^2) ~ pi * 11 * 51.2 ~ 1770 mm2 = 17.7 cm2
    # チューブ部表面積: 2 * pi * 1.1 * (L - 50)/10 cm2
    tube_len = L - 50.0
    area_tube = 2 * math.pi * (REF_R / 10.0) * (tube_len / 10.0) # cm2
    area_nose = math.pi * (REF_R / 10.0) * math.sqrt((REF_R/10.0)**2 + 5.0**2) # cm2
    
    m_tube = area_tube * AIRFRAME_SURF_DENSITY
    y_tube = tube_len / 2.0 # mm
    
    m_nose = area_nose * AIRFRAME_SURF_DENSITY * 1.3 # 蓋の合わせ目等でやや厚め
    y_nose = tube_len + 50.0 * 0.45 # ノーズCG
    
    # ストリーマ (チューブ前方、ノーズ直下に格納)
    m_streamer = STREAMER_MASS
    y_streamer = tube_len - 30.0 # mm
    
    # フィン (0.4mm 1重、両面+T字エンドプレート)
    # フィン1 (3時・9時, 2枚)
    area_fin1_1side = 0.5 * (cr1 + ct1) * span1 # mm2
    # エンドプレート (長方形: ct1 * 10mm)
    area_plate1 = ct1 * 10.0 # mm2
    tot_area_fin1 = 2 * (2 * area_fin1_1side + area_plate1) * 1e-2 # cm2
    m_fin1 = tot_area_fin1 * AIRFRAME_SURF_DENSITY
    # フィン1の重心 Y (テール Y=0 から)
    # 前縁根元: cr1, 後端 Y=0 とすると、前縁は Y = cr1
    # 重心Y: テールから (cr1 + 2*ct1)/(3*(cr1+ct1)) * cr1 的な台心
    y_fin1 = (cr1**2 + cr1*ct1 + ct1**2 + (2*cr1+ct1)*sweep1) / (3 * (cr1 + ct1)) if (cr1+ct1)>0 else 10.0
    
    # フィン2 (12時, 1枚)
    area_fin2_1side = 0.5 * (cr2 + ct2) * span2 # mm2
    area_plate2 = ct2 * 8.0 # mm2
    tot_area_fin2 = (2 * area_fin2_1side + area_plate2) * 1e-2 # cm2
    m_fin2 = tot_area_fin2 * AIRFRAME_SURF_DENSITY
    y_fin2 = (cr2**2 + cr2*ct2 + ct2**2 + (2*cr2+ct2)*sweep2) / (3 * (cr2 + ct2)) if (cr2+ct2)>0 else 10.0
    
    # ランチラグ等小物
    m_misc = 0.3
    y_misc = 45.0
    
    # 合成重心 CG
    masses = [m_motor, m_tube, m_nose, m_streamer, m_fin1, m_fin2, m_misc]
    ys = [y_motor, y_tube, y_nose, y_streamer, y_fin1, y_fin2, y_misc]
    total_mass = sum(masses)
    cg_from_tail = sum(m * y for m, y in zip(masses, ys)) / total_mass
    
    # 2. Barrowman 法による CP (Center of Pressure) の算出
    # A. ノーズコーン
    # CNa_nose = 2.0
    # Xb_nose (先端からの距離) = 0.466 * L_nose = 0.466 * 50 = 23.3 mm
    # テールからの距離:
    cna_nose = 2.0
    cp_nose_tail = L - 23.3
    
    # B. フィン (Barrowman 方程式)
    # 3枚フィン（または合成）の法線力傾斜 CNa
    # フィン1 (2枚、左右)
    # CNa_1 = (1 + R / (R + span1)) * (4 * N * (span1/d)^2) / (1 + sqrt(1 + (2*Lf/(cr1+ct1))^2))
    # ここで N=2 (左右)
    mid_chord_sweep1 = sweep1 + (ct1 - cr1)/2.0
    Lf1 = math.sqrt(mid_chord_sweep1**2 + span1**2)
    k_body1 = 1.0 + REF_R / (REF_R + span1)
    cna_fin1 = k_body1 * (4.0 * 2.0 * (span1 / REF_D)**2) / (1.0 + math.sqrt(1.0 + (2.0 * Lf1 / (cr1 + ct1))**2))
    
    # フィン1の先端からのCP位置 Xb
    # 後端が Y=0 なので、先端からの前縁根元 Xr = L - cr1
    xr1 = L - cr1
    xb_fin1 = xr1 + (sweep1 * (cr1 + 2*ct1)/(3*(cr1+ct1))) + (1.0/6.0) * (cr1 + ct1 - (cr1*ct1)/(cr1+ct1))
    cp_fin1_tail = L - xb_fin1
    
    # フィン2 (1枚、12時)
    mid_chord_sweep2 = sweep2 + (ct2 - cr2)/2.0
    Lf2 = math.sqrt(mid_chord_sweep2**2 + span2**2)
    k_body2 = 1.0 + REF_R / (REF_R + span2)
    cna_fin2 = k_body2 * (4.0 * 1.0 * (span2 / REF_D)**2) / (1.0 + math.sqrt(1.0 + (2.0 * Lf2 / (cr2 + ct2))**2))
    xr2 = L - cr2
    xb_fin2 = xr2 + (sweep2 * (cr2 + 2*ct2)/(3*(cr2+ct2))) + (1.0/6.0) * (cr2 + ct2 - (cr2*ct2)/(cr2+ct2))
    cp_fin2_tail = L - xb_fin2
    
    # 合成 CP
    tot_cna = cna_nose + cna_fin1 + cna_fin2
    cp_from_tail = (cna_nose * cp_nose_tail + cna_fin1 * cp_fin1_tail + cna_fin2 * cp_fin2_tail) / tot_cna
    
    # 静安定マージン (cal)
    # CG が CP より前（先端側＝Yが大きい）のとき正
    margin_cal = (cg_from_tail - cp_from_tail) / REF_D
    
    # 3. 横倒し降下投影面積 (エアブレーキ性能)
    # 胴体の横投影面積: REF_D * L
    # フィン1の投影面積: 2 * (area_fin1_1side) (左右)
    # フィン2のエンドプレート投影面積: ct2 * 8
    area_side_mm2 = (REF_D * L) + (2 * area_fin1_1side) + (ct2 * 8.0)
    
    # 4. 最高高度概算 (インパルス 1.25 Ns, 質量 total_mass)
    # 簡易弾道計算: v_burnout ~ I / m - g*t_burn
    m_avg = total_mass - 0.78 # 平均質量
    v_bo = (1.25 / (m_avg * 1e-3)) - 9.8 * 0.32
    h_bo = 0.5 * v_bo * 0.32
    # 抗力による減速を考慮したコースト高度: h_coast ~ v_bo^2 / (2 * g * (1 + drag_factor))
    drag_factor = 0.35 * 0.5 * 1.225 * (math.pi * 0.011**2) / (m_avg * 1e-3 * 9.8) * (v_bo**2 / 2) / 9.8
    h_apo = h_bo + (v_bo**2) / (2 * 9.8 * (1.0 + drag_factor*0.5))
    
    # 5. 終末降下速度 (横倒し降下)
    # Cd_side ~ 1.2
    # v_term = sqrt(2 * m_dry * g / (rho * S * Cd_side))
    m_dry = total_mass - 1.56
    s_side_m2 = area_side_mm2 * 1e-6
    v_term = math.sqrt((2 * (m_dry * 1e-3) * 9.8) / (1.225 * s_side_m2 * 1.2))
    flight_time = (h_apo / v_term) + 2.0
    
    return {
        "L": L,
        "total_mass": total_mass,
        "dry_mass": m_dry,
        "cg_tail": cg_from_tail,
        "cp_tail": cp_from_tail,
        "margin_cal": margin_cal,
        "apogee": h_apo,
        "v_term": v_term,
        "flight_time": flight_time,
        "area_side_cm2": area_side_mm2 * 1e-2,
        "cr1": cr1, "ct1": ct1, "span1": span1, "sweep1": sweep1,
        "cr2": cr2, "ct2": ct2, "span2": span2, "sweep2": sweep2
    }

# グリッドサーチ探索
print("Running design optimization for Stable Flight (Margin >= 1.0 cal, Length <= 250mm)...")
best_designs = []

for L in [190, 200, 210, 220, 230, 240]:
    for span1 in [28, 32, 36, 40]: # 3時・9時スパン
        for cr1 in [40, 50, 60, 70]: # 3時・9時根元コード
            for ct1 in [15, 20, 25]: # 3時・9時翼端コード
                sweep1 = cr1 - ct1 # 後退角（後端揃え）
                for span2 in [22, 26, 30]: # 12時スパン
                    for cr2 in [30, 40, 50]: # 12時根元コード
                        ct2 = max(10, cr2 - 20)
                        sweep2 = cr2 - ct2
                        res = calc_rocket_properties(L, cr1, ct1, span1, sweep1, cr2, ct2, span2, sweep2)
                        
                        # 安定条件: マージン 0.95 ~ 1.5 cal
                        if 0.95 <= res["margin_cal"] <= 1.6:
                            best_designs.append(res)

print(f"Total stable candidate designs found: {len(best_designs)}")

# 滞空時間（降下時間）が最大のものをソート
best_designs.sort(key=lambda d: d["flight_time"], reverse=True)

print("\nTop 5 Candidates with Maximum Flight Time & Positive Stability (Margin ~ 1.0 - 1.3 cal):")
print(f"{'Rank':<4} | {'L (mm)':<6} | {'Mass(g)':<7} | {'CG(mm)':<7} | {'CP(mm)':<7} | {'Margin':<10} | {'Apogee':<8} | {'V_desc':<8} | {'Time(s)':<8} | {'Fin1(cr,ct,sp)':<15} | {'Fin2(cr,ct,sp)':<15}")
print("-" * 115)
for i, d in enumerate(best_designs[:5]):
    fin1_str = f"{d['cr1']},{d['ct1']},{d['span1']}"
    fin2_str = f"{d['cr2']},{d['ct2']},{d['span2']}"
    print(f"{i+1:<4} | {d['L']:<6} | {d['total_mass']:<7.1f} | {d['cg_tail']:<7.1f} | {d['cp_tail']:<7.1f} | {d['margin_cal']:<8.2f}cal | {d['apogee']:<6.1f}m | {d['v_term']:<6.2f}m/s | {d['flight_time']:<6.1f}s | {fin1_str:<15} | {fin2_str:<15}")
