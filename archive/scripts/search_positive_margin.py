import math
import numpy as np

REF_D = 22.0
REF_R = 11.0
AIRFRAME_SURF_DENSITY = 0.0346 # g/cm2

def calc_detailed(L, cr1, ct1, span1, sweep1, cr2, ct2, span2, sweep2, m_streamer=2.5, m_nose_tip=1.0):
    m_motor = 15.0
    y_motor = 35.0
    
    tube_len = L - 50.0
    area_tube = 2 * math.pi * (REF_R / 10.0) * (tube_len / 10.0)
    area_nose = math.pi * (REF_R / 10.0) * math.sqrt((REF_R/10.0)**2 + 5.0**2)
    
    m_tube = area_tube * AIRFRAME_SURF_DENSITY
    y_tube = tube_len / 2.0
    
    m_nose_shell = area_nose * AIRFRAME_SURF_DENSITY
    y_nose_shell = tube_len + 50.0 * 0.4
    
    # ノーズ先端の成形部 (通常1g程度のソリッド部)
    y_nose_tip = L - 15.0
    
    # ストリーマ (最前部)
    y_streamer = tube_len - 15.0
    
    # フィン1 (3時・9時)
    area_fin1 = 0.5 * (cr1 + ct1) * span1
    area_plate1 = ct1 * 10.0
    tot_area_fin1 = 2 * (2 * area_fin1 + area_plate1) * 1e-2
    m_fin1 = tot_area_fin1 * AIRFRAME_SURF_DENSITY
    y_fin1 = (cr1**2 + cr1*ct1 + ct1**2 + (2*cr1+ct1)*sweep1) / (3 * (cr1 + ct1)) if (cr1+ct1)>0 else 10.0
    
    # フィン2 (12時)
    area_fin2 = 0.5 * (cr2 + ct2) * span2
    area_plate2 = ct2 * 8.0
    tot_area_fin2 = (2 * area_fin2 + area_plate2) * 1e-2
    m_fin2 = tot_area_fin2 * AIRFRAME_SURF_DENSITY
    y_fin2 = (cr2**2 + cr2*ct2 + ct2**2 + (2*cr2+ct2)*sweep2) / (3 * (cr2 + ct2)) if (cr2+ct2)>0 else 10.0
    
    m_misc = 0.3
    y_misc = 45.0
    
    masses = [m_motor, m_tube, m_nose_shell, m_nose_tip, m_streamer, m_fin1, m_fin2, m_misc]
    ys = [y_motor, y_tube, y_nose_shell, y_nose_tip, y_streamer, y_fin1, y_fin2, y_misc]
    total_mass = sum(masses)
    cg_from_tail = sum(m * y for m, y in zip(masses, ys)) / total_mass
    
    # CP (Barrowman)
    cna_nose = 2.0
    cp_nose_tail = L - 23.3
    
    mid_chord_sweep1 = sweep1 + (ct1 - cr1)/2.0
    Lf1 = math.sqrt(mid_chord_sweep1**2 + span1**2)
    k_body1 = 1.0 + REF_R / (REF_R + span1)
    cna_fin1 = k_body1 * (4.0 * 2.0 * (span1 / REF_D)**2) / (1.0 + math.sqrt(1.0 + (2.0 * Lf1 / (cr1 + ct1))**2))
    xr1 = L - cr1
    xb_fin1 = xr1 + (sweep1 * (cr1 + 2*ct1)/(3*(cr1+ct1))) + (1.0/6.0) * (cr1 + ct1 - (cr1*ct1)/(cr1+ct1))
    cp_fin1_tail = L - xb_fin1
    
    mid_chord_sweep2 = sweep2 + (ct2 - cr2)/2.0
    Lf2 = math.sqrt(mid_chord_sweep2**2 + span2**2)
    k_body2 = 1.0 + REF_R / (REF_R + span2)
    cna_fin2 = k_body2 * (4.0 * 1.0 * (span2 / REF_D)**2) / (1.0 + math.sqrt(1.0 + (2.0 * Lf2 / (cr2 + ct2))**2))
    xr2 = L - cr2
    xb_fin2 = xr2 + (sweep2 * (cr2 + 2*ct2)/(3*(cr2+ct2))) + (1.0/6.0) * (cr2 + ct2 - (cr2*ct2)/(cr2+ct2))
    cp_fin2_tail = L - xb_fin2
    
    tot_cna = cna_nose + cna_fin1 + cna_fin2
    cp_from_tail = (cna_nose * cp_nose_tail + cna_fin1 * cp_fin1_tail + cna_fin2 * cp_fin2_tail) / tot_cna
    margin_cal = (cg_from_tail - cp_from_tail) / REF_D
    
    # 横倒し降下性能
    area_side_mm2 = (REF_D * L) + (2 * area_fin1) + (ct2 * 8.0)
    m_dry = total_mass - 1.56
    s_side_m2 = area_side_mm2 * 1e-6
    v_term = math.sqrt((2 * (m_dry * 1e-3) * 9.8) / (1.225 * s_side_m2 * 1.2))
    
    m_avg = total_mass - 0.78
    v_bo = (1.25 / (m_avg * 1e-3)) - 9.8 * 0.32
    h_bo = 0.5 * v_bo * 0.32
    drag_factor = 0.35 * 0.5 * 1.225 * (math.pi * 0.011**2) / (m_avg * 1e-3 * 9.8) * (v_bo**2 / 2) / 9.8
    h_apo = h_bo + (v_bo**2) / (2 * 9.8 * (1.0 + drag_factor*0.5))
    flight_time = (h_apo / v_term) + 2.0
    
    return {
        "L": L, "total_mass": total_mass, "cg_tail": cg_from_tail, "cp_tail": cp_from_tail,
        "margin_cal": margin_cal, "apogee": h_apo, "v_term": v_term, "flight_time": flight_time,
        "area_side_cm2": area_side_mm2 * 1e-2,
        "cr1": cr1, "ct1": ct1, "span1": span1, "sweep1": sweep1,
        "cr2": cr2, "ct2": ct2, "span2": span2, "sweep2": sweep2
    }

results = []
for L in [210, 220, 230, 240, 248]:
    for span1 in [30, 35, 40]:
        for cr1 in [40, 50, 60]:
            for ct1 in [15, 20, 25]:
                sweep1 = cr1 - ct1
                for span2 in [22, 26, 30]:
                    for cr2 in [30, 40]:
                        ct2 = 15
                        sweep2 = cr2 - ct2
                        r = calc_detailed(L, cr1, ct1, span1, sweep1, cr2, ct2, span2, sweep2, m_streamer=2.5, m_nose_tip=1.0)
                        if 1.0 <= r["margin_cal"] <= 1.4:
                            results.append(r)

print(f"Total matching designs with Margin 1.0 ~ 1.4 cal: {len(results)}")
results.sort(key=lambda x: x["flight_time"], reverse=True)

print(f"{'Rank':<4} | {'L(mm)':<6} | {'Mass':<7} | {'CG':<7} | {'CP':<7} | {'Margin':<10} | {'Apogee':<8} | {'V_desc':<8} | {'FlightTime':<11} | {'Fin1 (cr,ct,span)':<18} | {'Fin2 (cr,ct,span)':<18}")
print("-" * 125)
for i, d in enumerate(results[:8]):
    fin1 = f"{d['cr1']},{d['ct1']},{d['span1']}"
    fin2 = f"{d['cr2']},{d['ct2']},{d['span2']}"
    print(f"{i+1:<4} | {d['L']:<6} | {d['total_mass']:<6.1f}g | {d['cg_tail']:<5.1f}mm | {d['cp_tail']:<5.1f}mm | {d['margin_cal']:<8.2f}cal | {d['apogee']:<6.1f}m | {d['v_term']:<6.2f}m/s | {d['flight_time']:<9.1f}s | {fin1:<18} | {fin2:<18}")
