"""
Practical & Realistic Wing Design Optimization & Ranking for Model Rocket
Constraints:
  1. Tip chord Ct >= 8.0 mm (no ultra-thin knife-edges that break on touch or grass landing)
  2. Local chord c(y) >= 8.0 mm everywhere (prevents aeroelastic flutter and thin-waist flexing)
  3. Span b <= 65.0 mm (avoids floppy 100mm wings; rigid, robust, easy to transport and load on launch rod)
  4. Rear Overhang <= 5.0 mm (prevents fin from touching blast deflector or getting scorched by rocket motor exhaust)
  5. Static Margin >= +1.30 cal (realistic safety buffer against wind gusts / crosswinds, not razor-thin 1.0cal)
  6. Root chord Cr >= 25.0 mm (solid adhesive joint to 24mm body tube)
"""

import os
import sys
import math
import time
import json
import numpy as np
from numba import njit, prange

sys.path.insert(0, os.path.abspath("."))
from sim_engine.motor_db import get_motor

@njit(fastmath=True)
def calc_practical_fin_aero(
    span_mm, cr_mm, ct_mm, te_sweep_mm, overhang_mm,
    p_le, p_te,
    theta_deg, v_scale, is_4fin,
    D, R, thick_mm, rho,
    cna_body_base, cp_body_base, m_base_launch, mom_base_launch,
    wet_area_body_cm2, S_ref, tail_len_mm,
    burn_t, avg_thrust, prop_mass_g,
    streamer_cd_A, wet_body_m2,
    min_chord_limit=8.0
):
    theta_rad = math.radians(theta_deg)
    
    # 1. Main wings (2 horizontal / dihedral fins)
    le_sweep_h = cr_mm - ct_mm + te_sweep_mm
    
    # Check minimum local chord everywhere (prevent flutter and fragile waists)
    for k in range(11):
        eta_k = k * 0.1
        c_local = cr_mm + te_sweep_mm * (eta_k ** p_te) - le_sweep_h * (eta_k ** p_le)
        if c_local < min_chord_limit:
            return -999.0, 0.0, 0.0, 99.0, 99.0, 99.0, 0.0, 0.0
            
    int_c_h = cr_mm + te_sweep_mm / (p_te + 1.0) - le_sweep_h / (p_le + 1.0)
    if int_c_h <= 0.0:
        return -999.0, 0.0, 0.0, 99.0, 99.0, 99.0, 0.0, 0.0
        
    area_1side_cm2 = (span_mm * int_c_h) * 0.01
    
    # MAC calculation
    int_c2_h = (cr_mm**2 + (te_sweep_mm**2) / (2.0 * p_te + 1.0) + (le_sweep_h**2) / (2.0 * p_le + 1.0)
                + (2.0 * cr_mm * te_sweep_mm) / (p_te + 1.0) - (2.0 * cr_mm * le_sweep_h) / (p_le + 1.0)
                - (2.0 * te_sweep_mm * le_sweep_h) / (p_te + p_le + 1.0))
    mac_h = int_c2_h / int_c_h
    
    # Aerodynamic Center (CP)
    int_xle_c_h = ((cr_mm * le_sweep_h) / (p_le + 1.0) + (te_sweep_mm * le_sweep_h) / (p_le + p_te + 1.0)
                   - (le_sweep_h**2) / (2.0 * p_le + 1.0))
    x_le_mac_h = int_xle_c_h / int_c_h
    xf_from_le_h = x_le_mac_h + 0.25 * mac_h
    cp_fin_h = -overhang_mm + (cr_mm - xf_from_le_h)
    
    # Center of Gravity (CG)
    int_diff2_h = (cr_mm**2 + (2.0 * cr_mm * te_sweep_mm) / (p_te + 1.0) 
                   + (te_sweep_mm**2) / (2.0 * p_te + 1.0) - (le_sweep_h**2) / (2.0 * p_le + 1.0))
    x_cg_from_le_h = int_diff2_h / (2.0 * int_c_h)
    z_fin_cg_h = -overhang_mm + (cr_mm - x_cg_from_le_h)
    
    # Mid-chord sweep line
    mid_sweep_h = 0.5 * (te_sweep_mm + le_sweep_h)
    Lf_h = math.sqrt(mid_sweep_h**2 + span_mm**2)
    
    # Normal force coefficient slope (Barrowman)
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
        if c_local_v < min_chord_limit * v_scale:
            return -999.0, 0.0, 0.0, 99.0, 99.0, 99.0, 0.0, 0.0
            
    int_c_v = cr_v + te_sweep_v / (p_te + 1.0) - le_sweep_v / (p_le + 1.0)
    if int_c_v <= 0.0:
        return -999.0, 0.0, 0.0, 99.0, 99.0, 99.0, 0.0, 0.0
        
    area_1v_cm2 = (span_v * int_c_v) * 0.01
    
    int_c2_v = (cr_v**2 + (te_sweep_v**2) / (2.0 * p_te + 1.0) + (le_sweep_v**2) / (2.0 * p_le + 1.0)
                + (2.0 * cr_v * te_sweep_v) / (p_te + 1.0) - (2.0 * cr_v * le_sweep_v) / (p_le + 1.0)
                - (2.0 * te_sweep_v * le_sweep_v) / (p_te + p_le + 1.0))
    mac_v = int_c2_v / int_c_v
    
    int_xle_c_v = ((cr_v * le_sweep_v) / (p_le + 1.0) + (te_sweep_v * le_sweep_v) / (p_le + p_te + 1.0)
                   - (le_sweep_v**2) / (2.0 * p_le + 1.0))
    x_le_mac_v = int_xle_c_v / int_c_v
    xf_from_le_v = x_le_mac_v + 0.25 * mac_v
    cp_fin_v = -overhang_mm + (cr_v - xf_from_le_v)
    
    int_diff2_v = (cr_v**2 + (2.0 * cr_v * te_sweep_v) / (p_te + 1.0) 
                   + (te_sweep_v**2) / (2.0 * p_te + 1.0) - (le_sweep_v**2) / (2.0 * p_le + 1.0))
    x_cg_from_le_v = int_diff2_v / (2.0 * int_c_v)
    z_fin_cg_v = -overhang_mm + (cr_v - x_cg_from_le_v)
    
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
    
    # Stability
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
    
    # Aerodynamic drag
    wet_area_m2 = (wet_area_body_cm2 + total_fin_area_cm2 * 2.0) * 1e-4
    cd_interference = 0.005 * (2.0 + num_v)
    base_cd = 0.05 if tail_len_mm > 0 else 0.10
    Cd = 0.0045 * (wet_area_m2 / S_ref) + base_cd + 0.08 + cd_interference
    
    # Powered flight & coast flight
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
    t_ascent = burn_t + t_coast
    
    # Descent
    burnout_mass_kg = burnout_mass_g * 1e-3
    v_desc = math.sqrt(2.0 * burnout_mass_kg * 9.8 / (1.225 * streamer_cd_A))
    t_desc = apogee_m / v_desc if v_desc > 0 else 0.0
    t_total = t_ascent + t_desc
    
    return margin_eff, t_total, apogee_m, v_desc, fin_mass_g, total_launch_mass_g, total_cg_mm, min(cp_pitch, cp_yaw)

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

def run_practical_search():
    print("================================================================================")
    print(" REALISTIC & PRACTICAL WING OPTIMIZATION (実用性・耐破損性・耐風安全性フォーカス)")
    print("================================================================================")
    
    motor = get_motor("1/2A6-2")
    burn_t = motor.burn_time
    avg_thrust = motor.total_impulse / motor.burn_time
    prop_m = motor.propellant_mass_g
    
    D = 24.0
    R = 12.0
    thick_mm = 0.4
    rho = 1.24
    S_ref = math.pi * (R * 1e-3)**2
    
    streamer_cd_A = 0.25 * (250.0 * 1e-4) # 50x500mm
    streamer_mass_g = 1.27
    
    m_base, mom_base, cna_body, cp_body, wet_cm2 = compute_fuselage_base(
        nose_len_mm=125.0, tail_len_mm=20.0, streamer_mass_g=streamer_mass_g
    )
    wet_m2 = wet_cm2 * 1e-4
    
    # Practical search grids:
    # 1. Spans: 30mm to 65mm (rigid, no floppy wings)
    spans = np.arange(30.0, 65.1, 2.5) # 15 values
    # 2. Root chords: 25mm to 45mm (solid gluing area)
    crs = np.arange(25.0, 45.1, 2.0) # 11 values
    # 3. Tip chords: 8mm to 20mm (robust, won't break on touch or landing)
    cts = np.arange(8.0, 20.1, 2.0) # 7 values
    # 4. Trailing edge angles: -5 to +20 deg (realistic sweeps)
    te_angles = np.arange(-5.0, 20.1, 5.0) # 6 values
    # 5. Overhangs: 0.0 to 5.0 mm (0mm flush or modest 2.5/5mm, clears blast deflector!)
    overhangs = np.array([0.0, 2.5, 5.0]) # 3 values
    # 6. Exponents: realistic shapes
    p_les = np.array([0.7, 0.85, 1.0, 1.2, 1.5]) # 5 values
    p_tes = np.array([0.8, 1.0, 1.2, 1.4]) # 4 values
    # 7. Configs
    configs = [
        (35.0, 0.80, 0.0, "3-Fin (v=0.80)"),
        (35.0, 1.00, 0.0, "3-Fin (v=1.00)"),
        (0.0,  1.00, 1.0, "4-Fin (+)"),
    ]
    
    total = (len(spans) * len(crs) * len(cts) * len(te_angles) * 
             len(overhangs) * len(p_les) * len(p_tes) * len(configs))
    print(f"Total practical candidate space: {total:,} configurations")
    
    records = []
    
    t0 = time.time()
    for span in spans:
        for cr in crs:
            for ct in cts:
                if ct >= cr:
                    continue
                for te_ang in te_angles:
                    te_sw = span * math.tan(math.radians(te_ang))
                    for oh in overhangs:
                        for p_le in p_les:
                            for p_te in p_tes:
                                for theta, v_sc, is_4f, cfg_name in configs:
                                    m_eff, t_tot, apo, v_desc, f_m, tot_m, cg, cp = calc_practical_fin_aero(
                                        span, cr, ct, te_sw, oh,
                                        p_le, p_te,
                                        theta, v_sc, bool(is_4f),
                                        D, R, thick_mm, rho,
                                        cna_body, cp_body, m_base, mom_base,
                                        wet_cm2, S_ref, 20.0,
                                        burn_t, avg_thrust, prop_m,
                                        streamer_cd_A, wet_m2,
                                        min_chord_limit=8.0 # at least 8mm everywhere!
                                    )
                                    # Realistic practical safety margin: Margin >= +1.30 cal
                                    if m_eff >= 1.30 and t_tot > 10.0:
                                        records.append({
                                            "span": float(span),
                                            "cr": float(cr),
                                            "ct": float(ct),
                                            "te_sweep": float(te_sw),
                                            "te_angle": float(te_ang),
                                            "overhang": float(oh),
                                            "p_le": float(p_le),
                                            "p_te": float(p_te),
                                            "is_4fin": bool(is_4f),
                                            "v_scale": float(v_sc),
                                            "config_name": cfg_name,
                                            "margin": float(m_eff),
                                            "hang_time": float(t_tot),
                                            "apogee": float(apo),
                                            "fin_mass": float(f_m),
                                            "total_mass": float(tot_m),
                                            "cg": float(cg),
                                            "cp": float(cp)
                                        })
                                        
    t_elapsed = time.time() - t0
    print(f"Evaluated in {t_elapsed:.2f} s. Found {len(records):,} practical candidates satisfying Margin >= 1.30 cal & Chord >= 8mm.")
    
    # Sort by hang time descending
    records.sort(key=lambda x: x["hang_time"], reverse=True)
    
    # Save top records to json
    os.makedirs("output", exist_ok=True)
    with open("output/practical_optimal_wings.json", "w", encoding="utf-8") as f:
        json.dump(records[:200], f, indent=2, ensure_ascii=False)
        
    return records

if __name__ == "__main__":
    records = run_practical_search()
