"""
Detailed extraction of 3 distinct candidates under horizontal landing + mylar streamer
"""

import sys, os
import math
import numpy as np

sys.path.insert(0, ".")
from scratch.optimize_mylar_120x1200 import calc_flight

spans = np.arange(60.0, 95.1, 2.5)
crs = np.arange(24.0, 44.1, 2.0)
cts = np.array([3.0, 4.0, 5.0, 6.0])
te_angles = np.array([15.0, 20.0, 25.0])
overhangs = np.array([0.0, 2.5, 5.0, 10.0])
p_les = np.array([0.5, 0.7, 0.85, 1.0])
p_tes = np.array([0.8, 1.0, 1.2, 1.4])

results = []
for span in spans:
    for cr in crs:
        for ct in cts:
            if ct >= cr * 0.5: continue
            for te_ang in te_angles:
                te_sw = span * math.tan(math.radians(te_ang))
                for oh in overhangs:
                    for ple in p_les:
                        for pte in p_tes:
                            r = calc_flight(span, cr, ct, te_sw, oh, ple, pte, 0.0, 1.0, True, min_chord_mm=2.5)
                            if r and r["margin"] >= 0.98:
                                r["te_ang"] = te_ang
                                results.append(r)

# 1. Candidate 1: Overall Best (Max Hang Time, OH <= 5mm, Margin >= 1.03 cal)
c1 = [r for r in results if r["overhang"] <= 5.0 and r["margin"] >= 1.03]
c1.sort(key=lambda x: x["hang_time"], reverse=True)
cand1 = c1[0]

# 2. Candidate 2: Perfect Flush (OH == 0.0mm, Margin >= 1.03 cal)
c2 = [r for r in results if r["overhang"] == 0.0 and r["margin"] >= 1.03]
c2.sort(key=lambda x: x["hang_time"], reverse=True)
cand2 = c2[0]

# 3. Candidate 3: High Stability (Margin >= 1.25 cal, OH <= 5.0mm)
c3 = [r for r in results if r["margin"] >= 1.25 and r["overhang"] <= 5.0]
c3.sort(key=lambda x: x["hang_time"], reverse=True)
cand3 = c3[0]

cands = [
    ("【候補1：究極滞空・三日月フィレット機】(滞空時間18.52s・総合トップ)", cand1),
    ("【候補2：完全ツライチ自立機】(OH 0mm・机に自立・排気干渉ゼロ)", cand2),
    ("【候補3：耐風・超安全マージン機】(Margin +1.27cal・突風安全バッファ)", cand3),
]

for title, r in cands:
    span = r["span"]
    cr = r["cr"]
    ct = r["ct"]
    te_sw = r["te_sweep"]
    le_sw = cr - ct + te_sw
    oh = r["overhang"]
    ple = r["p_le"]
    pte = r["p_te"]
    
    print("\n" + "="*80)
    print(title)
    print("="*80)
    print(f"スパン幅 b:        {span:.1f} mm (胴体半径12mm含む全幅: {24 + 2*span:.1f} mm)")
    print(f"翼根コード Cr:      {cr:.1f} mm (接着長)")
    print(f"翼端コード Ct:      {ct:.1f} mm (0.4mmノズル造形適性)")
    print(f"後縁後退角:        {r['te_ang']:.1f}° (後縁後退量: {te_sw:.2f} mm)")
    print(f"前縁後退量:        {le_sw:.2f} mm")
    print(f"オーバーハング:    {oh:.1f} mm")
    print(f"前縁曲率指数 ple:  {ple:.2f} (0.50=平方根フィレット, 0.70=マイルドフィレット)")
    print(f"後縁曲率指数 pte:  {pte:.2f} (1.20=三日月反り後退, 0.80=外膨らみ)")
    print(f"--- 性能諸元 ---")
    print(f"総滞空時間:        {r['hang_time']:.2f} 秒")
    print(f"最高到達高度:      {r['apogee']:.1f} m")
    print(f"降下終端速度:      {r['v_desc']:.2f} m/s")
    print(f"静安定マージン:    {r['margin']:.2f} cal")
    print(f"翼合計質量:        {r['fin_mass']:.2f} g (4枚合計)")
    print(f"機体全備質量:      {r['total_mass']:.2f} g")
    print(f"重心位置 (尾部基準): {r['cg']:.1f} mm")
    print(f"空力中心 (尾部基準): {r['cp']:.1f} mm")
    print(f"--- 数式定義 (t in [0, 1], X = span * t) ---")
    print(f"前縁: Y_LE(t) = {-oh + cr:.2f} - {le_sw:.2f} * (t ** {ple:.2f})")
    print(f"後縁: Y_TE(t) = {-oh:.2f} - {te_sw:.2f} * (t ** {pte:.2f})")
