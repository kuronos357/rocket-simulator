import math

L = 200.0
D = 20.0
R = 10.0
cg_current = 57.15

print("=== フィンサイズ変更によるマージン変化シミュレーション (Barrowman) ===")
print("現行 m3v2: 根元cr=35mm, 翼端ct=12mm, スパンspan=35mm => マージン: -0.89 cal (不安定)\n")

print(f"{'プラン':<16} | {'フィン寸法 (cr x span)':<24} | {'フィン面積 (片面)':<18} | {'推定CP (テールから)':<18} | {'推定マージン':<15}")
print("-" * 100)

for span in [35.0, 40.0, 45.0, 50.0]:
    for cr in [35.0, 50.0, 65.0]:
        ct = 12.0
        sweep = cr - ct
        area_1fin = 0.5 * (cr + ct) * span
        Lf = math.sqrt(sweep**2 + span**2)
        k = 1.0 + R / (R + span)
        cna_fin1 = k * (4.0 * 2.0 * (span / D)**2) / (1.0 + math.sqrt(1.0 + (2.0 * Lf / (cr + ct))**2))
        xb_fin = (L - cr) + (sweep * (cr + 2*ct) / (3*(cr+ct))) + (1.0/6.0)*(cr + ct - cr*ct/(cr+ct))
        cp_fin_tail = L - xb_fin
        
        cna_fin2 = 1.5 * (4.0 * 1.0 * (30 / D)**2) / (1.0 + math.sqrt(1.0 + (2.0 * 30 / 35)**2))
        cp_fin2_tail = 12.0
        
        cna_nose = 2.0
        cp_nose_tail = L - 0.466 * 130.0 # 200 - 60.5 = 139.5 mm
        
        tot_cna = cna_nose + cna_fin1 + cna_fin2
        cp_tail = (cna_nose * cp_nose_tail + cna_fin1 * cp_fin_tail + cna_fin2 * cp_fin2_tail) / tot_cna
        
        m_fin_add = (area_1fin * 2 * 2 * 1e-2) * 0.035
        cg_val = (28.0 * cg_current + m_fin_add * 15.0) / (28.0 + m_fin_add)
        
        margin_cal = (cg_val - cp_tail) / D
        plan_name = f"スパン{span:.0f}mm / コード{cr:.0f}mm"
        status = "[OK] 安定" if margin_cal >= 1.0 else ("[△] 準安定" if margin_cal >= 0.0 else "[×] 不安定")
        print(f"{plan_name:<16} | cr={cr:4.1f}mm, span={span:4.1f}mm  | {area_1fin*1e-2:5.1f} cm2/枚        | {cp_tail:5.1f} mm           | {margin_cal:+5.2f} cal {status}")
