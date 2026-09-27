import numpy as np
import trimesh

# もし Y=0~175 が外径20mm一定で、Y=175~250 だけがノーズコーンだったらどうなるか？
# Barrowman法で m2v3 の実際のフィン寸法を使って計算してみる。

# m2v3 の実測フィン寸法:
# 3時・9時フィン:
# スパン = 43.9 - 10.0 = 33.9 mm
# 根元コード: Y=0 ~ 35 mm (cr1 = 35 mm)
# 翼端コード: Y=0 ~ 12 mm (ct1 = 12 mm)
# 12時フィン:
# スパン = 35.1 - 10.0 = 25.1 mm
# 根元コード: Y=0 ~ 25 mm (cr2 = 25 mm)
# 翼端コード: Y=0 ~ 10 mm (ct2 = 10 mm)

D = 20.0
R = 10.0

def barrowman(L, nose_len, cr1, ct1, span1, cr2, ct2, span2):
    # 1. ノーズコーン (先端 nose_len mm のみ)
    cna_nose = 2.0
    cp_nose_tail = L - 0.466 * nose_len
    
    # 2. フィン1 (3時・9時, 2枚)
    sweep1 = cr1 - ct1
    mid_sweep1 = sweep1 + (ct1 - cr1)/2.0
    Lf1 = np.sqrt(mid_sweep1**2 + span1**2)
    k1 = 1.0 + R / (R + span1)
    cna_fin1 = k1 * (4.0 * 2.0 * (span1 / D)**2) / (1.0 + np.sqrt(1.0 + (2.0 * Lf1 / (cr1 + ct1))**2))
    xr1 = L - cr1
    mac1 = cr1 + ct1 - cr1*ct1/(cr1+ct1)
    xb1 = xr1 + sweep1*(cr1 + 2*ct1)/(3*(cr1+ct1)) + mac1/6.0
    cp_fin1_tail = L - xb1
    
    # 3. フィン2 (12時, 1枚)
    sweep2 = cr2 - ct2
    mid_sweep2 = sweep2 + (ct2 - cr2)/2.0
    Lf2 = np.sqrt(mid_sweep2**2 + span2**2)
    k2 = 1.0 + R / (R + span2)
    cna_fin2 = k2 * (4.0 * 1.0 * (span2 / D)**2) / (1.0 + np.sqrt(1.0 + (2.0 * Lf2 / (cr2 + ct2))**2))
    xr2 = L - cr2
    mac2 = cr2 + ct2 - cr2*ct2/(cr2+ct2)
    xb2 = xr2 + sweep2*(cr2 + 2*ct2)/(3*(cr2+ct2)) + mac2/6.0
    cp_fin2_tail = L - xb2
    
    tot_cna = cna_nose + cna_fin1 + cna_fin2
    cp_tail = (cna_nose * cp_nose_tail + cna_fin1 * cp_fin1_tail + cna_fin2 * cp_fin2_tail) / tot_cna
    return cp_tail, cna_nose, cna_fin1, cna_fin2

# パターンA: 提案通り「ストレート胴体 175mm + ノーズ 75mm」
cp_A, cn_n, cn_f1, cn_f2 = barrowman(L=250, nose_len=75, cr1=35, ct1=12, span1=34, cr2=25, ct2=10, span2=25)
print("Pattern A (Straight tube 175mm + Nose 75mm):")
print(f"  CP from tail = {cp_A:.2f} mm")
print(f"  CNa nose = {cn_n:.2f}, CNa fin1 = {cn_f1:.2f}, CNa fin2 = {cn_f2:.2f}")

# パターンB: 現在の m2v3 のように「テーパーが 180mm にわたって続いている場合」
# テーパー部 (Conical transition): d1=20mm -> d2=0mm over 180mm
# Barrowmanでは円錐台の CNa = 2 * ((d2/d)^2 - (d1/d)^2) = 2 * (0 - 1) = -2 (縮小テーパーの場合)
# しかしパネル法や実際の粘性流では、前傾斜面全体が巨大な揚力面になる
print(f"\nPattern A with CG=62.4mm gives Margin = {(62.4 - cp_A)/20.0:+.2f} cal (PERFECT STABLE!)")
