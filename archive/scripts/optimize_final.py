"""
ロケット形状最適化 - 滞空時間最大化
"""
import math
import numpy as np
import sys
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass
from itertools import product

# ===== 定数 =====
D_OUTER = 20.0        # mm 胴体外径
WALL_T  = 0.4         # mm 壁厚
D_INNER = D_OUTER - 2 * WALL_T  # 19.2mm
R_OUTER = D_OUTER / 2.0         # 10.0mm
NOSE_RATIO = 0.30     # ノーズコーン長 / 全長 (オジーブ)

# PLA 1層の面密度 (スライサー実測ベース v12 → 20mm に補正)
# v12(22mm, L=180): 11.07g / 320cm2 = 0.0346 g/cm2
SURF_DENSITY = 0.0346  # g/cm2

# モーター: Estes 1/2A6-2
MOTOR_MASS_TOTAL  = 15.0   # g (点火時)
MOTOR_PROPELLANT  = 1.56   # g
MOTOR_IMPULSE     = 1.25   # Ns
MOTOR_BURN_TIME   = 0.32   # s
MOTOR_DELAY       = 2.0    # s
MOTOR_LENGTH      = 70.0   # mm
MOTOR_DIAMETER    = 18.0   # mm
MOTOR_CG_Y        = 35.0   # mm (後端から)

# 空気力学
RHO_AIR = 1.225  # kg/m3
G       = 9.81   # m/s2
CD_AXIAL = 0.40  # 軸方向抗力係数
CD_SIDE  = 1.20  # 横向き抗力係数

# ストリーマ
STREAMER_MASS = 2.5  # g
MISC_MASS     = 0.3  # g (ランチラグ等)

def evaluate_design(L, nose_len,
                    cr1, ct1, span1,   # 3時・9時フィン (2枚)
                    cr2, ct2, span2,   # 12時フィン (1枚)
                    endplate1_h=10.0,  # T字エンドプレート高さ (mm)
                    endplate2_h=8.0):
    """
    全パラメータから飛翔性能を算出。
    座標系: Y=後端(モーターノズル), Y=L が先端。
    """
    sweep1 = cr1 - ct1  # 後退量（後端揃え）
    sweep2 = cr2 - ct2
    
    tube_len = L - nose_len
    
    # ========== 1. 質量・重心 ==========
    # 胴体チューブ (円筒)
    area_tube_cm2 = 2 * math.pi * (R_OUTER / 10.0) * (tube_len / 10.0)
    m_tube = area_tube_cm2 * SURF_DENSITY
    y_tube = tube_len / 2.0
    
    # ノーズコーン (オジーブ近似: 表面積 ≈ π*R*√(R²+h²) * 1.1)
    area_nose_cm2 = math.pi * (R_OUTER / 10.0) * math.sqrt((R_OUTER / 10.0)**2 + (nose_len / 10.0)**2) * 1.1
    m_nose = area_nose_cm2 * SURF_DENSITY
    y_nose = tube_len + nose_len * 0.40  # ノーズコーンのCG (先端から約60%)
    
    # ノーズ先端の成形部 (ソリッド)
    m_nose_tip = 0.8  # g
    y_nose_tip = L - 10.0
    
    # ストリーマ (チューブ内、モーター上方)
    y_streamer = MOTOR_LENGTH + (tube_len - MOTOR_LENGTH) * 0.45
    
    # 3時・9時フィン (2枚)
    area_fin1_one = 0.5 * (cr1 + ct1) * span1  # mm2 (片面)
    area_ep1 = ct1 * endplate1_h  # エンドプレート mm2
    total_area_fin1_cm2 = 2.0 * (2.0 * area_fin1_one + 2.0 * area_ep1) * 1e-2  # 両面+EP両面 x2枚
    m_fin1 = total_area_fin1_cm2 * SURF_DENSITY
    # フィンCG (台形の図心Y座標)
    if (cr1 + ct1) > 0:
        y_fin1 = (cr1**2 + cr1*ct1 + ct1**2) / (3.0 * (cr1 + ct1))
    else:
        y_fin1 = 10.0
    
    # 12時フィン (1枚)
    area_fin2_one = 0.5 * (cr2 + ct2) * span2
    area_ep2 = ct2 * endplate2_h
    total_area_fin2_cm2 = (2.0 * area_fin2_one + 2.0 * area_ep2) * 1e-2
    m_fin2 = total_area_fin2_cm2 * SURF_DENSITY
    if (cr2 + ct2) > 0:
        y_fin2 = (cr2**2 + cr2*ct2 + ct2**2) / (3.0 * (cr2 + ct2))
    else:
        y_fin2 = 10.0
    
    # 合計
    masses = [MOTOR_MASS_TOTAL, m_tube, m_nose, m_nose_tip, STREAMER_MASS, m_fin1, m_fin2, MISC_MASS]
    ys     = [MOTOR_CG_Y,      y_tube, y_nose, y_nose_tip, y_streamer,    y_fin1, y_fin2, 43.0]
    total_mass = sum(masses)
    cg_y = sum(m * y for m, y in zip(masses, ys)) / total_mass
    dry_mass = total_mass - MOTOR_PROPELLANT
    struct_mass = total_mass - MOTOR_MASS_TOTAL - STREAMER_MASS
    
    # ========== 2. 圧力中心 (Barrowman法) ==========
    # A. ノーズコーン
    cna_nose = 2.0
    cp_nose_y = L - 0.466 * nose_len  # テールからの位置
    
    # B. 3時・9時フィン (N=2)
    mid_sweep1 = sweep1 + (ct1 - cr1) / 2.0
    Lf1 = math.sqrt(mid_sweep1**2 + span1**2)
    k1 = 1.0 + R_OUTER / (R_OUTER + span1)
    denom1 = 1.0 + math.sqrt(1.0 + (2.0 * Lf1 / max(cr1 + ct1, 1.0))**2)
    cna_fin1 = k1 * (4.0 * 2.0 * (span1 / D_OUTER)**2) / denom1
    
    xr1 = L - cr1  # フィン前縁の先端からの位置
    mac1 = cr1 + ct1 - cr1 * ct1 / max(cr1 + ct1, 1.0)
    xb1 = xr1 + sweep1 * (cr1 + 2*ct1) / (3.0 * max(cr1 + ct1, 1.0)) + mac1 / 6.0
    cp_fin1_y = L - xb1  # テールから
    
    # C. 12時フィン (N=1)
    mid_sweep2 = sweep2 + (ct2 - cr2) / 2.0
    Lf2 = math.sqrt(mid_sweep2**2 + span2**2)
    k2 = 1.0 + R_OUTER / (R_OUTER + span2)
    denom2 = 1.0 + math.sqrt(1.0 + (2.0 * Lf2 / max(cr2 + ct2, 1.0))**2)
    cna_fin2 = k2 * (4.0 * 1.0 * (span2 / D_OUTER)**2) / denom2
    
    xr2 = L - cr2
    mac2 = cr2 + ct2 - cr2 * ct2 / max(cr2 + ct2, 1.0)
    xb2 = xr2 + sweep2 * (cr2 + 2*ct2) / (3.0 * max(cr2 + ct2, 1.0)) + mac2 / 6.0
    cp_fin2_y = L - xb2
    
    # 合成CP
    tot_cna = cna_nose + cna_fin1 + cna_fin2
    if tot_cna <= 0:
        return None
    cp_y = (cna_nose * cp_nose_y + cna_fin1 * cp_fin1_y + cna_fin2 * cp_fin2_y) / tot_cna
    
    # 安定マージン
    margin_mm = cg_y - cp_y
    margin_cal = margin_mm / D_OUTER
    
    # ========== 3. 上昇性能 ==========
    S_frontal = math.pi * (R_OUTER * 1e-3)**2  # m2
    
    # バーンアウト速度 (推力プロファイル平均)
    m_avg_boost = (total_mass - MOTOR_PROPELLANT / 2.0) * 1e-3  # kg
    F_avg = MOTOR_IMPULSE / MOTOR_BURN_TIME  # N
    a_avg = F_avg / m_avg_boost - G
    v_burnout = a_avg * MOTOR_BURN_TIME
    h_burnout = 0.5 * a_avg * MOTOR_BURN_TIME**2
    
    if v_burnout <= 0:
        return None
    
    # コースト上昇 (抗力込み)
    m_coast = dry_mass * 1e-3  # kg
    k_drag = 0.5 * RHO_AIR * CD_AXIAL * S_frontal / m_coast
    # dv/dt = -g - k*v^2 → h_coast = (1/(2k)) * ln(1 + k*v0^2/g)
    h_coast = (1.0 / (2.0 * k_drag)) * math.log(1.0 + k_drag * v_burnout**2 / G)
    
    # コースト時間
    v_at_delay_end = v_burnout * math.exp(-2 * k_drag * G * MOTOR_DELAY)  # 近似
    t_coast_to_apo = math.atan(v_burnout * math.sqrt(k_drag / G)) / math.sqrt(k_drag * G)
    
    h_apogee = h_burnout + h_coast
    t_to_apogee = MOTOR_BURN_TIME + t_coast_to_apo
    
    # ========== 4. 横向き降下 ==========
    # 横投影面積
    # 胴体: D * L (長方形)
    # 3時・9時フィン: 両方ともZ=0面にあるので横から見ると胴体と同一面
    #   → エンドプレートだけが追加 (2枚 x endplate1_h x ct1 相当の厚み)
    #   ただし横倒しで90度回転すると、フィンの板面が横風に当たる
    # ここでは簡略化: 胴体 + フィン板面の合計投影面積
    
    # 0度/180度方向から見た投影 (3時・9時フィンが見える方向)
    area_side_0 = D_OUTER * L + 2 * area_fin1_one + area_ep2  # 12時EPは横から見える
    
    # 90度方向から見た投影 (12時フィンが見える方向)
    area_side_90 = D_OUTER * L + area_fin2_one + 2 * area_ep1  # 3/9時EPは前後から見える
    
    # 横倒し時は回転しながら降下するので、平均を取る
    area_side_avg = (area_side_0 + area_side_90) / 2.0
    S_side = area_side_avg * 1e-6  # m2
    
    v_terminal = math.sqrt(2.0 * dry_mass * 1e-3 * G / (RHO_AIR * S_side * CD_SIDE))
    
    # ========== 5. 総滞空時間 ==========
    # エジェクション: t_to_apogee 付近 (delay 2.0s はバーンアウト後)
    t_ejection = MOTOR_BURN_TIME + MOTOR_DELAY
    h_at_ejection = h_burnout + h_coast * (1.0 - max(0, t_coast_to_apo - MOTOR_DELAY) / max(t_coast_to_apo, 0.01))**2
    h_at_ejection = min(h_apogee, h_at_ejection)
    # 簡略: エジェクション = ほぼ頂点
    
    t_descent = h_apogee / v_terminal
    total_flight_time = t_to_apogee + t_descent
    
    return {
        "L": L, "nose_len": nose_len,
        "total_mass": total_mass, "dry_mass": dry_mass, "struct_mass": struct_mass,
        "cg_y": cg_y, "cp_y": cp_y,
        "margin_cal": margin_cal, "margin_mm": margin_mm,
        "h_apogee": h_apogee, "v_burnout": v_burnout,
        "v_terminal": v_terminal,
        "t_to_apogee": t_to_apogee, "t_descent": t_descent,
        "total_time": total_flight_time,
        "area_side_0": area_side_0 * 1e-2,
        "area_side_90": area_side_90 * 1e-2,
        "cr1": cr1, "ct1": ct1, "span1": span1,
        "cr2": cr2, "ct2": ct2, "span2": span2,
        "cna_fin1": cna_fin1, "cna_fin2": cna_fin2, "cna_nose": cna_nose,
    }

# ===== グリッドサーチ =====
print("="*80)
print("  ロケット形状 完全最適化")
print("  制約: L≤250mm, D=20mm, 1層PLA, 横向き降下, マージン≥1.0cal")
print("  目的: 滞空時間（到達高度/降下速度）の最大化")
print("="*80)

candidates = []

# パラメータ空間
Ls         = range(200, 251, 5)           # 全長 200~250 mm
nose_fracs = [0.22, 0.25, 0.28, 0.30]     # ノーズ比率
cr1s       = range(35, 66, 5)              # 3/9時 根元コード 35~65
ct1s       = [12, 15, 18, 20]              # 3/9時 翼端コード
span1s     = range(30, 51, 5)              # 3/9時 スパン 30~50
cr2s       = range(25, 46, 5)              # 12時 根元コード 25~45
ct2s       = [10, 12, 15]                  # 12時 翼端コード
span2s     = range(18, 36, 4)              # 12時 スパン 18~34

total_combos = 0
for L in Ls:
    for nf in nose_fracs:
        nose_len = round(L * nf)
        for cr1 in cr1s:
            if cr1 > L * 0.35:  # フィンが長すぎない
                continue
            for ct1 in ct1s:
                if ct1 >= cr1:
                    continue
                for span1 in span1s:
                    for cr2 in cr2s:
                        if cr2 > cr1:  # 12時フィンは3/9時より短い
                            continue
                        for ct2 in ct2s:
                            if ct2 >= cr2:
                                continue
                            for span2 in span2s:
                                total_combos += 1
                                res = evaluate_design(L, nose_len, cr1, ct1, span1, cr2, ct2, span2)
                                if res is None:
                                    continue
                                if res["margin_cal"] >= 1.0 and res["margin_cal"] <= 2.0:
                                    candidates.append(res)

print(f"\n探索した組合せ数: {total_combos:,}")
print(f"安定条件を満たす候補数: {len(candidates):,}")

# 滞空時間でソート
candidates.sort(key=lambda x: x["total_time"], reverse=True)

print(f"\n{'='*80}")
print(f"  TOP 15: 滞空時間最大の設計案")
print(f"{'='*80}")
print(f"{'#':<3} | {'L':>4} | {'Nose':>4} | {'Mass':>5} | {'CG':>5} | {'CP':>5} | {'Margin':>7} | {'Apogee':>7} | {'V_desc':>6} | {'Time':>6} | {'3/9Fin(cr,ct,sp)':>17} | {'12Fin(cr,ct,sp)':>15}")
print("-" * 120)
for i, d in enumerate(candidates[:15]):
    f1 = f"{d['cr1']:>2},{d['ct1']:>2},{d['span1']:>2}"
    f2 = f"{d['cr2']:>2},{d['ct2']:>2},{d['span2']:>2}"
    print(f"{i+1:<3} | {d['L']:>4.0f} | {d['nose_len']:>4.0f} | {d['total_mass']:>4.1f}g | {d['cg_y']:>4.1f}m | {d['cp_y']:>4.1f}m | {d['margin_cal']:>+5.2f}cal | {d['h_apogee']:>5.1f}m | {d['v_terminal']:>5.2f}m/s | {d['total_time']:>5.1f}s | {f1:>17} | {f2:>15}")

# ベスト設計の詳細
print(f"\n{'='*80}")
print(f"  ★ 推奨ベストデザイン 詳細")
print(f"{'='*80}")
best = candidates[0]
print(f"全長                 : {best['L']:.0f} mm (制限 250mm)")
print(f"ノーズコーン長       : {best['nose_len']:.0f} mm")
print(f"胴体チューブ長       : {best['L'] - best['nose_len']:.0f} mm")
print(f"胴体外径             : {D_OUTER:.1f} mm (壁厚 {WALL_T}mm, 内径 {D_INNER}mm)")
print(f"")
print(f"3時・9時フィン (2枚) :")
print(f"  根元コード (cr)    : {best['cr1']:.0f} mm")
print(f"  翼端コード (ct)    : {best['ct1']:.0f} mm")
print(f"  スパン             : {best['span1']:.0f} mm")
print(f"  後退量 (sweep)     : {best['cr1']-best['ct1']:.0f} mm")
print(f"  翼端エンドプレート : 幅 10mm (Z方向 ±5mm)")
print(f"")
print(f"12時フィン (1枚)     :")
print(f"  根元コード (cr)    : {best['cr2']:.0f} mm")
print(f"  翼端コード (ct)    : {best['ct2']:.0f} mm")
print(f"  スパン             : {best['span2']:.0f} mm")
print(f"  後退量 (sweep)     : {best['cr2']-best['ct2']:.0f} mm")
print(f"  翼端エンドプレート : 幅 8mm (X方向 ±4mm)")
print(f"")
print(f"打ち上げ全備重量     : {best['total_mass']:.2f} g")
print(f"乾燥重量             : {best['dry_mass']:.2f} g")
print(f"構造重量 (機体のみ)  : {best['struct_mass']:.2f} g")
print(f"重心 CG (後端から)   : {best['cg_y']:.2f} mm")
print(f"圧力中心 CP (後端から): {best['cp_y']:.2f} mm")
print(f"安定マージン         : +{best['margin_cal']:.2f} cal (+{best['margin_mm']:.1f} mm)")
print(f"")
print(f"最高到達高度         : {best['h_apogee']:.1f} m")
print(f"バーンアウト速度     : {best['v_burnout']:.1f} m/s ({best['v_burnout']*3.6:.0f} km/h)")
print(f"頂点到達時間         : T+{best['t_to_apogee']:.2f} s")
print(f"横倒し終末降下速度   : {best['v_terminal']:.2f} m/s")
print(f"降下時間             : {best['t_descent']:.1f} s")
print(f"★ 推定総滞空時間     : {best['total_time']:.1f} s")
print(f"")
print(f"横投影面積 (0/180°)  : {best['area_side_0']:.1f} cm2")
print(f"横投影面積 (90°)     : {best['area_side_90']:.1f} cm2")

# 3次元座標出力
print(f"\n{'='*80}")
print(f"  Fusion 360 入力用 3次元座標")
print(f"  原点: モーター後端面の中心 (0,0,0)")
print(f"  Y: 飛行軸 (後端=0, 先端=+{best['L']:.0f})")
print(f"  X: 左右 (3時=+X, 9時=-X)")
print(f"  Z: 上下 (12時=+Z, 6時=-Z)")
print(f"{'='*80}")

R = R_OUTER
cr1, ct1, sp1 = best['cr1'], best['ct1'], best['span1']
cr2, ct2, sp2 = best['cr2'], best['ct2'], best['span2']
sw1 = cr1 - ct1
sw2 = cr2 - ct2

print(f"\n■ 3時フィン (+X側)")
print(f"  根元・前縁 : ({R:.1f}, {cr1:.1f}, 0.0)")
print(f"  根元・後端 : ({R:.1f}, 0.0, 0.0)")
print(f"  翼端・前縁 : ({R+sp1:.1f}, {ct1:.1f}, 0.0)")
print(f"  翼端・後端 : ({R+sp1:.1f}, 0.0, 0.0)")
print(f"  EP上端     : ({R+sp1:.1f}, 0.0, +5.0) → ({R+sp1:.1f}, {ct1:.1f}, +5.0)")
print(f"  EP下端     : ({R+sp1:.1f}, 0.0, -5.0) → ({R+sp1:.1f}, {ct1:.1f}, -5.0)")

print(f"\n■ 9時フィン (-X側)")
print(f"  根元・前縁 : ({-R:.1f}, {cr1:.1f}, 0.0)")
print(f"  根元・後端 : ({-R:.1f}, 0.0, 0.0)")
print(f"  翼端・前縁 : ({-(R+sp1):.1f}, {ct1:.1f}, 0.0)")
print(f"  翼端・後端 : ({-(R+sp1):.1f}, 0.0, 0.0)")
print(f"  EP上端     : ({-(R+sp1):.1f}, 0.0, +5.0) → ({-(R+sp1):.1f}, {ct1:.1f}, +5.0)")
print(f"  EP下端     : ({-(R+sp1):.1f}, 0.0, -5.0) → ({-(R+sp1):.1f}, {ct1:.1f}, -5.0)")

print(f"\n■ 12時フィン (+Z側)")
print(f"  根元・前縁 : (0.0, {cr2:.1f}, {R:.1f})")
print(f"  根元・後端 : (0.0, 0.0, {R:.1f})")
print(f"  翼端・前縁 : (0.0, {ct2:.1f}, {R+sp2:.1f})")
print(f"  翼端・後端 : (0.0, 0.0, {R+sp2:.1f})")
print(f"  EP右端     : (+4.0, 0.0, {R+sp2:.1f}) → (+4.0, {ct2:.1f}, {R+sp2:.1f})")
print(f"  EP左端     : (-4.0, 0.0, {R+sp2:.1f}) → (-4.0, {ct2:.1f}, {R+sp2:.1f})")
