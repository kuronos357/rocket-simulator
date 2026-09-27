import math

AIRFRAME_SURF_DENSITY = 0.0346  # g/cm2 (スライサー実測ベース)

def calc_with_diameter(D_outer, wall_t, L=230.0, cr1=45, ct1=18, span1=40, cr2=35, ct2=15, span2=25, m_streamer=2.5, m_nose_tip=1.0):
    R = D_outer / 2.0
    ID = D_outer - 2 * wall_t
    motor_clearance = (ID - 18.0) / 2.0  # 片側クリアランス
    
    # 質量
    m_motor = 15.0
    y_motor = 35.0
    
    tube_len = L - 55.0  # ノーズコーン55mm
    # 表面積は外径ベース
    area_tube = 2 * math.pi * (R / 10.0) * (tube_len / 10.0)  # cm2
    area_nose = math.pi * (R / 10.0) * math.sqrt((R / 10.0)**2 + 5.5**2)  # cm2
    
    m_tube = area_tube * AIRFRAME_SURF_DENSITY
    y_tube = tube_len / 2.0
    
    m_nose_shell = area_nose * AIRFRAME_SURF_DENSITY
    y_nose_shell = tube_len + 55.0 * 0.4
    
    y_nose_tip_pos = L - 15.0
    y_streamer = tube_len - 15.0
    
    # フィン（形状は同じ）
    area_fin1 = 0.5 * (cr1 + ct1) * span1
    area_plate1 = ct1 * 10.0
    tot_area_fin1 = 2 * (2 * area_fin1 + area_plate1) * 1e-2
    m_fin1 = tot_area_fin1 * AIRFRAME_SURF_DENSITY
    sweep1 = cr1 - ct1
    y_fin1 = (cr1**2 + cr1*ct1 + ct1**2 + (2*cr1+ct1)*sweep1) / (3 * (cr1 + ct1))
    
    area_fin2 = 0.5 * (cr2 + ct2) * span2
    area_plate2 = ct2 * 8.0
    tot_area_fin2 = (2 * area_fin2 + area_plate2) * 1e-2
    m_fin2 = tot_area_fin2 * AIRFRAME_SURF_DENSITY
    sweep2 = cr2 - ct2
    y_fin2 = (cr2**2 + cr2*ct2 + ct2**2 + (2*cr2+ct2)*sweep2) / (3 * (cr2 + ct2))
    
    m_misc = 0.3
    y_misc = 45.0
    
    masses = [m_motor, m_tube, m_nose_shell, m_nose_tip, m_streamer, m_fin1, m_fin2, m_misc]
    ys = [y_motor, y_tube, y_nose_shell, y_nose_tip_pos, y_streamer, y_fin1, y_fin2, y_misc]
    total_mass = sum(masses)
    cg_tail = sum(m * y for m, y in zip(masses, ys)) / total_mass
    
    # CP (Barrowman)
    cna_nose = 2.0
    cp_nose_tail = L - 0.466 * 55.0
    
    mid_sweep1 = sweep1 + (ct1 - cr1) / 2.0
    Lf1 = math.sqrt(mid_sweep1**2 + span1**2)
    k1 = 1.0 + R / (R + span1)
    cna_fin1 = k1 * (4.0 * 2.0 * (span1 / D_outer)**2) / (1.0 + math.sqrt(1.0 + (2.0 * Lf1 / (cr1 + ct1))**2))
    xr1 = L - cr1
    xb1 = xr1 + (sweep1 * (cr1 + 2*ct1)/(3*(cr1+ct1))) + (1.0/6.0)*(cr1+ct1-(cr1*ct1)/(cr1+ct1))
    cp_fin1_tail = L - xb1
    
    mid_sweep2 = sweep2 + (ct2 - cr2) / 2.0
    Lf2 = math.sqrt(mid_sweep2**2 + span2**2)
    k2 = 1.0 + R / (R + span2)
    cna_fin2 = k2 * (4.0 * 1.0 * (span2 / D_outer)**2) / (1.0 + math.sqrt(1.0 + (2.0 * Lf2 / (cr2 + ct2))**2))
    xr2 = L - cr2
    xb2 = xr2 + (sweep2 * (cr2 + 2*ct2)/(3*(cr2+ct2))) + (1.0/6.0)*(cr2+ct2-(cr2*ct2)/(cr2+ct2))
    cp_fin2_tail = L - xb2
    
    tot_cna = cna_nose + cna_fin1 + cna_fin2
    cp_tail = (cna_nose * cp_nose_tail + cna_fin1 * cp_fin1_tail + cna_fin2 * cp_fin2_tail) / tot_cna
    margin_cal = (cg_tail - cp_tail) / D_outer
    margin_mm = cg_tail - cp_tail
    
    # 前面投影面積 (ドラッグ)
    frontal_area_mm2 = math.pi * R**2
    frontal_area_22 = math.pi * 11.0**2  # 22mm基準
    drag_ratio = frontal_area_mm2 / frontal_area_22
    
    # 最高高度（軽量化 + 低抵抗の影響）
    m_dry = total_mass - 1.56
    m_avg = total_mass - 0.78
    Cd = 0.35
    S_ref = frontal_area_mm2 * 1e-6  # m2
    v_bo = (1.25 / (m_avg * 1e-3)) - 9.8 * 0.32
    h_bo = 0.5 * v_bo * 0.32
    drag_decel = Cd * 0.5 * 1.225 * S_ref / (m_avg * 1e-3)
    h_coast = v_bo**2 / (2 * 9.8 * (1.0 + drag_decel * v_bo / (2 * 9.8)))
    h_apo = h_bo + h_coast
    
    # 降下
    area_side_mm2 = (D_outer * L) + (2 * area_fin1) + (ct2 * 8.0)
    s_side_m2 = area_side_mm2 * 1e-6
    v_term = math.sqrt((2 * (m_dry * 1e-3) * 9.8) / (1.225 * s_side_m2 * 1.2))
    
    # ストリーマ格納庫容積
    streamer_ID = ID  # mm
    streamer_len = tube_len - 70.0 - 5.0  # モーター後ろ5mm + 前方マージン
    streamer_vol = math.pi * (streamer_ID / 2.0 / 10.0)**2 * (streamer_len / 10.0)  # cm3
    
    return {
        "D_outer": D_outer, "wall_t": wall_t, "ID": ID,
        "motor_clearance": motor_clearance,
        "L": L, "total_mass": total_mass, "dry_mass": m_dry,
        "cg_tail": cg_tail, "cp_tail": cp_tail,
        "margin_cal": margin_cal, "margin_mm": margin_mm,
        "apogee": h_apo, "v_term": v_term,
        "drag_ratio_vs_22": drag_ratio,
        "frontal_area_mm2": frontal_area_mm2,
        "streamer_vol_cm3": streamer_vol,
        "tube_mass": m_tube, "nose_mass": m_nose_shell,
        "struct_mass": m_tube + m_nose_shell + m_fin1 + m_fin2 + m_misc
    }

print("=== Body Diameter Comparison (L=230mm, Same Fin Geometry) ===\n")
print(f"{'D(mm)':<6} | {'Wall':<5} | {'ID':<5} | {'Gap':<5} | {'StructMass':<10} | {'TotalMass':<9} | {'CG':<7} | {'CP':<7} | {'Margin':<10} | {'Drag%':<7} | {'Apogee':<8} | {'V_desc':<8} | {'St.Vol':<7}")
print("-" * 120)

for D, wall in [(22.0, 0.4), (21.0, 0.4), (20.0, 0.4), (19.6, 0.4), (20.0, 1.0), (19.2, 0.4)]:
    r = calc_with_diameter(D, wall)
    gap_ok = "OK" if r["motor_clearance"] >= 0.3 else "NG"
    print(f"{D:<6.1f} | {wall:<5.1f} | {r['ID']:<5.1f} | {r['motor_clearance']:<4.1f}{gap_ok} | {r['struct_mass']:<8.2f}g | {r['total_mass']:<7.2f}g | {r['cg_tail']:<5.1f}mm | {r['cp_tail']:<5.1f}mm | {r['margin_cal']:<+7.2f}cal | {r['drag_ratio_vs_22']*100:<5.1f}% | {r['apogee']:<6.1f}m | {r['v_term']:<6.2f}m/s | {r['streamer_vol_cm3']:<5.1f}cm3")

print("\n\n=== 20mm OD で翼形状を微調整して安定 1.0 cal を達成する探索 ===\n")
results = []
D_outer = 20.0
wall = 0.4
for L in [220, 225, 230, 235, 240]:
    for span1 in [35, 40, 45]:
        for cr1 in [40, 45, 50, 55]:
            for ct1 in [15, 18, 20]:
                for span2 in [22, 25, 28]:
                    for cr2 in [30, 35, 40]:
                        ct2 = 15
                        sweep2 = cr2 - ct2
                        sweep1 = cr1 - ct1
                        r = calc_with_diameter(D_outer, wall, L, cr1, ct1, span1, cr2, ct2, span2, m_streamer=2.5, m_nose_tip=1.0)
                        if 0.95 <= r["margin_cal"] <= 1.3:
                            results.append(r)

results.sort(key=lambda x: x["apogee"], reverse=True)
print(f"Total stable designs (D=20mm): {len(results)}\n")
print(f"{'Rank':<4} | {'L':<5} | {'Mass':<7} | {'CG':<7} | {'CP':<7} | {'Margin':<10} | {'Apogee':<8} | {'V_desc':<8} | {'Fin1(cr,ct,sp)':<15} | {'Fin2(cr,ct,sp)':<15}")
print("-" * 110)
for i, d in enumerate(results[:10]):
    f1 = f"{d.get('cr1_v', cr1)},{d.get('ct1_v', ct1)},{d.get('sp1_v', span1)}"
    print(f"{i+1:<4} | {d['L']:<5.0f} | {d['total_mass']:<5.1f}g | {d['cg_tail']:<5.1f}mm | {d['cp_tail']:<5.1f}mm | {d['margin_cal']:<+7.2f}cal | {d['apogee']:<6.1f}m | {d['v_term']:<6.2f}m/s | -               | -")
