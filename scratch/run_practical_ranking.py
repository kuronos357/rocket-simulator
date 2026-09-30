"""
Practical & Realistic Model Rocket Wing Optimization & Ranking
==============================================================
Evaluates realistic, field-ready, 3D-printable wing designs that won't break,
won't flutter, won't interfere with launch pad / blast deflector,
and can handle outdoor wind gusts safely.
"""

import os
import sys
import math
import time
import json
import numpy as np
import matplotlib.pyplot as plt

# Matplotlib Japanese Font Setup
plt.rcParams['font.sans-serif'] = ['Yu Gothic', 'Meiryo', 'MS Gothic', 'TakaoPGothic', 'IPAexGothic', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

sys.path.insert(0, os.path.abspath("."))
from sim_engine.motor_db import get_motor

def compute_fuselage_base(nose_len_mm=125.0, tail_len_mm=20.0, total_len_mm=250.0, D=24.0, t_wall=0.4, rho=1.24, streamer_mass_g=1.27):
    R = D / 2.0
    r_tail = 18.8 / 2.0 if tail_len_mm > 0 else R
    cyl_len = max(10.0, total_len_mm - nose_len_mm - tail_len_mm)
    
    slices = 50
    dx = nose_len_mm / slices
    area_nose_mm2 = 0.0
    moment_nose_shell = 0.0
    for i in range(slices):
        x_mid = (i + 0.5) * dx
        y_mid = R * (x_mid / nose_len_mm)**0.75
        dy_dx = 0.75 * (R / nose_len_mm) * (x_mid / nose_len_mm)**(-0.25) if x_mid > 0 else 0.0
        ds = math.sqrt(1.0 + dy_dx**2) * dx
        dA = 2.0 * math.pi * y_mid * ds
        area_nose_mm2 += dA
        moment_nose_shell += dA * x_mid
    
    mass_nose_shell_g = (area_nose_mm2 * 1.65) * (t_wall * 0.1) * rho * 0.01
    x_nose_cg = moment_nose_shell / area_nose_mm2 if area_nose_mm2 > 0 else nose_len_mm * 0.6
    z_nose_cg = total_len_mm - x_nose_cg
    
    area_cyl_mm2 = 2.0 * math.pi * R * cyl_len
    mass_cyl_g = (area_cyl_mm2 * 1.65) * (t_wall * 0.1) * rho * 0.01
    z_cyl_cg = tail_len_mm + cyl_len / 2.0
    
    if tail_len_mm > 0:
        slant = math.sqrt(tail_len_mm**2 + (R - r_tail)**2)
        area_tail_mm2 = math.pi * (R + r_tail) * slant
        mass_tail_g = (area_tail_mm2 * 1.65) * (t_wall * 0.1) * rho * 0.01
        z_tail_cg = (tail_len_mm / 3.0) * (2.0 * r_tail + R) / (r_tail + R)
    else:
        area_tail_mm2 = 0.0
        mass_tail_g = 0.0
        z_tail_cg = 0.0
        
    m_motor = 15.0
    z_motor = 35.0
    m_rec = streamer_mass_g
    z_rec = tail_len_mm + cyl_len * 0.5
    
    total_base_mass = mass_nose_shell_g + mass_cyl_g + mass_tail_g + m_motor + m_rec
    total_base_mom = (mass_nose_shell_g * z_nose_cg + mass_cyl_g * z_cyl_cg + 
                      mass_tail_g * z_tail_cg + m_motor * z_motor + m_rec * z_rec)
    
    cna_nose = 2.0
    cp_nose_from_nose = 0.466 * nose_len_mm
    cp_nose_from_tail = total_len_mm - cp_nose_from_nose
    
    if tail_len_mm > 0:
        d = (2.0 * r_tail) / D
        cna_tail = 2.0 * (d**2 - 1.0)
        x_tail_cp_local = (tail_len_mm / 3.0) * (1.0 + (1.0 - d) / (1.0 - d**2))
        cp_tail_from_tail = tail_len_mm - x_tail_cp_local
        cna_body_base = cna_nose + cna_tail
        cp_body_base = (cna_nose * cp_nose_from_tail + cna_tail * cp_tail_from_tail) / cna_body_base
    else:
        cna_body_base = cna_nose
        cp_body_base = cp_nose_from_tail
        
    wet_area_body_cm2 = (area_nose_mm2 + area_cyl_mm2 + area_tail_mm2) * 1e-2
    return total_base_mass, total_base_mom, cna_body_base, cp_body_base, wet_area_body_cm2

def calc_practical_flight(
    span_mm, cr_mm, ct_mm, te_sweep_mm, overhang_mm,
    p_le, p_te,
    theta_deg, v_scale, is_4fin,
    min_chord_mm=8.0
):
    motor = get_motor("1/2A6-2")
    burn_t = motor.burn_time
    avg_thrust = motor.total_impulse / motor.burn_time
    prop_mass_g = motor.propellant_mass_g
    
    D = 24.0
    R = 12.0
    thick_mm = 0.4
    rho = 1.24
    S_ref = math.pi * (R * 1e-3)**2
    streamer_cd_A = 0.25 * (250.0 * 1e-4) # 50x500mm
    streamer_mass_g = 1.27
    
    m_base_launch, mom_base_launch, cna_body_base, cp_body_base, wet_area_body_cm2 = compute_fuselage_base(
        nose_len_mm=125.0, tail_len_mm=20.0, streamer_mass_g=streamer_mass_g
    )
    wet_body_m2 = wet_area_body_cm2 * 1e-4
    theta_rad = math.radians(theta_deg)
    
    # 1. Main wings (2 fins)
    le_sweep_h = cr_mm - ct_mm + te_sweep_mm
    
    # Check minimum local chord everywhere (prevent flutter and fragile waists)
    for k in range(11):
        eta_k = k * 0.1
        c_local = cr_mm + te_sweep_mm * (eta_k ** p_te) - le_sweep_h * (eta_k ** p_le)
        if c_local < min_chord_mm:
            return None
            
    int_c_h = cr_mm + te_sweep_mm / (p_te + 1.0) - le_sweep_h / (p_le + 1.0)
    if int_c_h <= 0.0:
        return None
        
    area_1side_cm2 = (span_mm * int_c_h) * 0.01
    
    int_c2_h = (cr_mm**2 + (te_sweep_mm**2) / (2.0 * p_te + 1.0) + (le_sweep_h**2) / (2.0 * p_le + 1.0)
                + (2.0 * cr_mm * te_sweep_mm) / (p_te + 1.0) - (2.0 * cr_mm * le_sweep_h) / (p_le + 1.0)
                - (2.0 * te_sweep_mm * le_sweep_h) / (p_te + p_le + 1.0))
    mac_h = int_c2_h / int_c_h
    
    int_xle_c_h = ((cr_mm * le_sweep_h) / (p_le + 1.0) + (te_sweep_mm * le_sweep_h) / (p_le + p_te + 1.0)
                   - (le_sweep_h**2) / (2.0 * p_le + 1.0))
    x_le_mac_h = int_xle_c_h / int_c_h
    xf_from_le_h = x_le_mac_h + 0.25 * mac_h
    cp_fin_h = -overhang_mm + (cr_mm - xf_from_le_h)
    
    int_diff2_h = (cr_mm**2 + (2.0 * cr_mm * te_sweep_mm) / (p_te + 1.0) 
                   + (te_sweep_mm**2) / (2.0 * p_te + 1.0) - (le_sweep_h**2) / (2.0 * p_le + 1.0))
    x_cg_from_le_h = int_diff2_h / (2.0 * int_c_h)
    z_fin_cg_h = -overhang_mm + (cr_mm - x_cg_from_le_h)
    
    mid_sweep_h = 0.5 * (te_sweep_mm + le_sweep_h)
    Lf_h = math.sqrt(mid_sweep_h**2 + span_mm**2)
    k_body_h = 1.0 + R / (R + span_mm)
    denom_h = 1.0 + math.sqrt(1.0 + (2.0 * Lf_h / mac_h)**2) if mac_h > 0 else 2.0
    cna_1pair_h = k_body_h * (4.0 * 2.0 * (span_mm / D)**2) / denom_h
    
    # 2. Vertical fin(s)
    span_v = span_mm * v_scale
    cr_v = cr_mm
    ct_v = ct_mm * v_scale
    te_sweep_v = te_sweep_mm * v_scale
    le_sweep_v = cr_v - ct_v + te_sweep_v
    
    for k in range(11):
        eta_k = k * 0.1
        c_local_v = cr_v + te_sweep_v * (eta_k ** p_te) - le_sweep_v * (eta_k ** p_le)
        if c_local_v < min_chord_mm * v_scale:
            return None
            
    int_c_v = cr_v + te_sweep_v / (p_te + 1.0) - le_sweep_v / (p_le + 1.0)
    if int_c_v <= 0.0:
        return None
        
    area_1v_cm2 = (span_v * int_c_v) * 0.01
    
    int_c2_v = (cr_v**2 + (te_sweep_v**2) / (2.0 * p_te + 1.0) + (le_sweep_v**2) / (2.0 * p_le + 1.0)
                + (2.0 * cr_v * te_sweep_v) / (p_te + 1.0) - (2.0 * cr_v * le_sweep_v) / (p_le + 1.0)
                - (2.0 * te_sweep_v * le_sweep_v) / (p_te + p_le + 1.0))
    mac_v = int_c2_v / int_c_v
    
    int_xle_c_v = ((cr_v * le_sweep_v) / (p_le + 1.0) + (te_sweep_v * le_sweep_v) / (p_le + p_te + 1.0)
                   - (le_sweep_v**2) / (2.0 * p_le + 1.0))
    x_le_mac_v = int_xle_c_v / int_c_v
    xf_from_le_v = x_le_mac_v + 0.25 * mac_v
    cp_fin_v = -overhang_mm + (cr_mm - xf_from_le_v)
    
    int_diff2_v = (cr_v**2 + (2.0 * cr_v * te_sweep_v) / (p_te + 1.0) 
                   + (te_sweep_v**2) / (2.0 * p_te + 1.0) - (le_sweep_v**2) / (2.0 * p_le + 1.0))
    x_cg_from_le_v = int_diff2_v / (2.0 * int_c_v)
    z_fin_cg_v = -overhang_mm + (cr_mm - x_cg_from_le_v)
    
    mid_sweep_v = 0.5 * (te_sweep_v + le_sweep_v)
    Lf_v = math.sqrt(mid_sweep_v**2 + span_v**2)
    k_body_v = 1.0 + R / (R + span_v)
    denom_v = 1.0 + math.sqrt(1.0 + (2.0 * Lf_v / mac_v)**2) if mac_v > 0 else 2.0
    num_v = 2.0 if is_4fin else 1.0
    cna_1v = k_body_v * (4.0 * 1.0 * (span_v / D)**2) / denom_v
    cna_v_total = num_v * cna_1v
    
    total_fin_area_cm2 = 2.0 * area_1side_cm2 + num_v * area_1v_cm2
    fin_mass_g = total_fin_area_cm2 * (thick_mm * 0.1) * rho
    z_fin_cg = (2.0 * area_1side_cm2 * z_fin_cg_h + num_v * area_1v_cm2 * z_fin_cg_v) / total_fin_area_cm2 if total_fin_area_cm2 > 0 else -overhang_mm
    
    cos2_theta = math.cos(theta_rad)**2
    sin2_theta = math.sin(theta_rad)**2
    cna_pitch_fins = cos2_theta * cna_1pair_h
    cna_yaw_fins = sin2_theta * cna_1pair_h + cna_v_total
    
    cna_pitch = cna_body_base + cna_pitch_fins
    cp_pitch = (cna_body_base * cp_body_base + cna_pitch_fins * cp_fin_h) / cna_pitch if cna_pitch > 0 else cp_fin_h
    yaw_fins_moment = sin2_theta * cna_1pair_h * cp_fin_h + cna_v_total * cp_fin_v
    cna_yaw = cna_body_base + cna_yaw_fins
    cp_yaw = (cna_body_base * cp_body_base + yaw_fins_moment) / cna_yaw if cna_yaw > 0 else cp_fin_v
    
    total_launch_mass_g = m_base_launch + fin_mass_g
    total_cg_mm = (mom_base_launch + fin_mass_g * z_fin_cg) / total_launch_mass_g
    margin_pitch = (total_cg_mm - cp_pitch) / D
    margin_yaw = (total_cg_mm - cp_yaw) / D
    margin_eff = min(margin_pitch, margin_yaw)
    
    # Drag
    wet_area_m2 = (wet_area_body_cm2 + total_fin_area_cm2 * 2.0) * 1e-4
    cd_interference = 0.005 * (2.0 + num_v)
    base_cd = 0.05
    Cd = 0.0045 * (wet_area_m2 / S_ref) + base_cd + 0.08 + cd_interference
    
    # Ascent
    m_avg_kg = (total_launch_mass_g - prop_mass_g * 0.5) * 1e-3
    v_bo = max(0.0, (avg_thrust / m_avg_kg - 9.8) * burn_t)
    h_bo = 0.5 * v_bo * burn_t
    burnout_mass_g = total_launch_mass_g - prop_mass_g
    k_drag = 0.5 * 1.225 * Cd * S_ref / (burnout_mass_g * 1e-3)
    
    if k_drag > 0 and v_bo > 0:
        h_coast = (1.0 / (2.0 * k_drag)) * math.log(1.0 + k_drag * v_bo**2 / 9.8)
        t_coast = (1.0 / math.sqrt(9.8 * k_drag)) * math.atan(v_bo * math.sqrt(k_drag / 9.8))
    else:
        h_coast = 0.0
        t_coast = 0.0
        
    apogee_m = h_bo + h_coast
    
    # Descent (Streamer + Body tumbling + Fin drag)
    proj_fins_m2 = (2.0 * area_1side_cm2 * math.cos(theta_rad) + 0.15 * num_v * area_1v_cm2) * 1e-4
    body_cd_A = (1.1 / math.pi) * wet_body_m2
    fins_cd_A = 1.25 * proj_fins_m2
    total_cd_A = streamer_cd_A + body_cd_A + fins_cd_A
    v_descent = math.sqrt((2.0 * (burnout_mass_g * 1e-3) * 9.8) / (1.225 * total_cd_A)) if total_cd_A > 0 else 15.0
    t_descent = apogee_m / v_descent if v_descent > 0 else 0.0
    total_time = burn_t + t_coast + t_descent
    
    return {
        "span": span_mm, "cr": cr_mm, "ct": ct_mm, "te_sweep": te_sweep_mm,
        "overhang": overhang_mm, "p_le": p_le, "p_te": p_te,
        "is_4fin": is_4fin, "v_scale": v_scale, "theta": theta_deg,
        "margin": margin_eff, "hang_time": total_time, "apogee": apogee_m,
        "v_desc": v_descent, "fin_mass": fin_mass_g, "total_mass": total_launch_mass_g,
        "cg": total_cg_mm, "cp": min(cp_pitch, cp_yaw)
    }

def main():
    print("Evaluating practical, realistic designs...")
    # Practical Grid:
    # Span: 45 to 75mm (rigid, no flutter)
    # Root: 30 to 55mm (solid gluing length)
    # Tip: 8.0 to 18.0mm (tough, withstands grass landing)
    # TE Sweep Angle: 0 to 25 deg
    # Overhang: 0.0, 5.0, 10.0 mm
    # Exponents: 0.7 to 1.4 (gentle curvature, no razor waists)
    
    spans = np.arange(45.0, 75.1, 5.0)
    crs = np.arange(30.0, 55.1, 5.0)
    cts = np.array([8.0, 10.0, 12.0, 15.0, 18.0])
    te_angles = np.array([0.0, 10.0, 15.0, 20.0, 25.0])
    overhangs = np.array([0.0, 5.0, 10.0])
    p_les = np.array([0.7, 0.85, 1.0, 1.2])
    p_tes = np.array([0.8, 1.0, 1.2])
    configs = [
        (35.0, 0.80, False, "3枚逆Y字35° (v=0.80)"),
        (35.0, 1.00, False, "3枚逆Y字35° (v=1.00)"),
        (0.0,  1.00, True,  "4枚十字 (+)"),
    ]
    
    all_results = []
    
    for span in spans:
        for cr in crs:
            for ct in cts:
                if ct >= cr * 0.7: # sensible taper
                    continue
                for te_ang in te_angles:
                    te_sw = span * math.tan(math.radians(te_ang))
                    for oh in overhangs:
                        for p_le in p_les:
                            for p_te in p_tes:
                                for theta, v_sc, is_4f, cfg_name in configs:
                                    r = calc_practical_flight(
                                        span, cr, ct, te_sw, oh,
                                        p_le, p_te,
                                        theta, v_sc, is_4f,
                                        min_chord_mm=8.0
                                    )
                                    if r is not None and r["margin"] >= 1.00:
                                        r["config_name"] = cfg_name
                                        r["te_angle"] = te_ang
                                        all_results.append(r)
                                        
    print(f"Total practical designs found (Margin >= 1.0 cal, Chord >= 8mm): {len(all_results):,}")
    
    # -------------------------------------------------------------------------
    # Categorization of Practical Archetypes
    # -------------------------------------------------------------------------
    # Archetype 1: 【実用最高峰・バランス王】 (Span <= 70mm, Ct >= 10mm, Margin >= 1.25cal, Overhang <= 5mm)
    cat_balance = [r for r in all_results if r["span"] <= 70.0 and r["ct"] >= 10.0 and r["margin"] >= 1.25 and r["overhang"] <= 5.0]
    cat_balance.sort(key=lambda x: x["hang_time"], reverse=True)
    
    # Archetype 2: 【完全ツライチ自立機】 (Overhang == 0mm, Ct >= 10mm, Margin >= 1.20cal)
    cat_flush = [r for r in all_results if r["overhang"] == 0.0 and r["ct"] >= 10.0 and r["margin"] >= 1.20]
    cat_flush.sort(key=lambda x: x["hang_time"], reverse=True)
    
    # Archetype 3: 【高剛性直線クリップトデルタ】 (p_le == 1.0, p_te == 1.0, Ct >= 10mm, Margin >= 1.20cal, Overhang <= 5mm)
    cat_straight = [r for r in all_results if abs(r["p_le"] - 1.0) < 0.05 and abs(r["p_te"] - 1.0) < 0.05 and r["ct"] >= 10.0 and r["margin"] >= 1.20 and r["overhang"] <= 5.0]
    cat_straight.sort(key=lambda x: x["hang_time"], reverse=True)
    
    # Archetype 4: 【強風耐性・超安定機】 (Margin >= 1.50cal, Ct >= 10mm, Overhang <= 5mm)
    cat_high_stability = [r for r in all_results if r["margin"] >= 1.50 and r["ct"] >= 10.0 and r["overhang"] <= 5.0]
    cat_high_stability.sort(key=lambda x: x["hang_time"], reverse=True)
    
    print("\n--- Archetype 1: 実用最高峰・バランス王 (Span<=70, Ct>=10, Margin>=1.25, OH<=5) ---")
    for r in cat_balance[:3]:
        print(f"  {r['config_name']}: span={r['span']}mm, cr={r['cr']}mm, ct={r['ct']}mm, te_ang={r['te_angle']}°, oh={r['overhang']}mm, ple={r['p_le']}, pte={r['p_te']} -> Margin={r['margin']:.2f}cal, Time={r['hang_time']:.2f}s, Apo={r['apogee']:.1f}m, Mass={r['fin_mass']:.2f}g")

    print("\n--- Archetype 2: 完全ツライチ自立機 (OH=0mm, Ct>=10, Margin>=1.20) ---")
    for r in cat_flush[:3]:
        print(f"  {r['config_name']}: span={r['span']}mm, cr={r['cr']}mm, ct={r['ct']}mm, te_ang={r['te_angle']}°, oh={r['overhang']}mm, ple={r['p_le']}, pte={r['p_te']} -> Margin={r['margin']:.2f}cal, Time={r['hang_time']:.2f}s, Apo={r['apogee']:.1f}m, Mass={r['fin_mass']:.2f}g")

    print("\n--- Archetype 3: 高剛性直線クリップトデルタ (p=1.0, Ct>=10, Margin>=1.20, OH<=5) ---")
    for r in cat_straight[:3]:
        print(f"  {r['config_name']}: span={r['span']}mm, cr={r['cr']}mm, ct={r['ct']}mm, te_ang={r['te_angle']}°, oh={r['overhang']}mm, ple={r['p_le']}, pte={r['p_te']} -> Margin={r['margin']:.2f}cal, Time={r['hang_time']:.2f}s, Apo={r['apogee']:.1f}m, Mass={r['fin_mass']:.2f}g")

    print("\n--- Archetype 4: 強風耐性・超安定機 (Margin>=1.50, Ct>=10, OH<=5) ---")
    for r in cat_high_stability[:3]:
        print(f"  {r['config_name']}: span={r['span']}mm, cr={r['cr']}mm, ct={r['ct']}mm, te_ang={r['te_angle']}°, oh={r['overhang']}mm, ple={r['p_le']}, pte={r['p_te']} -> Margin={r['margin']:.2f}cal, Time={r['hang_time']:.2f}s, Apo={r['apogee']:.1f}m, Mass={r['fin_mass']:.2f}g")

    # Save to JSON
    summary_data = {
        "balance_top": cat_balance[0] if cat_balance else None,
        "flush_top": cat_flush[0] if cat_flush else None,
        "straight_top": cat_straight[0] if cat_straight else None,
        "stability_top": cat_high_stability[0] if cat_high_stability else None,
        "top_10_balance": cat_balance[:10],
        "top_10_flush": cat_flush[:10]
    }
    with open("output/practical_archetypes_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
        
    return summary_data

if __name__ == "__main__":
    main()
