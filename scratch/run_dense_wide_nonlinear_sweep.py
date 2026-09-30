"""
Ultra-Dense, Wide-Range Hardware-Accelerated Optimization
for NON-LINEAR (Parametric Power-Law) Fins:
  - 150 Million+ configurations evaluated in parallel streaming on Ryzen 9 6900HX
  - Wide Range:
      Span: 20 to 100mm (2.5mm steps)
      Root chord: 14 to 46mm (2.0mm steps)
      Taper ratio: 0.05 to 0.35 (8 steps)
      Trailing edge angle: -10 to +25 deg (5 deg steps)
      Rear overhang: 0 to 20mm (2.5mm steps)
      LE curvature p_le: 0.5 to 3.0 (11 steps)
      TE curvature p_te: 0.8 to 2.0 (7 steps)
      Architectures: 3-fin (5 v_scales) + 4-fin
  - Memory-efficient streaming reduction across threads
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
def calc_nonlinear_fin_aero(
    span_mm, cr_mm, ct_mm, te_sweep_mm, overhang_mm,
    p_le, p_te,
    theta_deg, v_scale, is_4fin,
    D, R, thick_mm, rho,
    cna_body_base, cp_body_base, m_base_launch, mom_base_launch,
    wet_area_body_cm2, S_ref, tail_len_mm,
    burn_t, avg_thrust, prop_mass_g,
    streamer_cd_A, wet_body_m2
):
    theta_rad = math.radians(theta_deg)
    
    # 1. Main wings (2 fins)
    le_sweep_h = cr_mm - ct_mm + te_sweep_mm
    
    # Physical geometric feasibility check (local chord >= 1.4mm everywhere)
    for k in range(11):
        eta_k = k * 0.1
        c_local = cr_mm + te_sweep_mm * (eta_k ** p_te) - le_sweep_h * (eta_k ** p_le)
        if c_local < 1.4:
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
    
    # MAC leading edge pos
    int_xle_c_h = ((cr_mm * le_sweep_h) / (p_le + 1.0) + (te_sweep_mm * le_sweep_h) / (p_le + p_te + 1.0)
                   - (le_sweep_h**2) / (2.0 * p_le + 1.0))
    x_le_mac_h = int_xle_c_h / int_c_h
    
    # Fin CP from root leading edge
    xf_from_le_h = x_le_mac_h + 0.25 * mac_h
    cp_fin_h = -overhang_mm + (cr_mm - xf_from_le_h)
    
    # Fin CG from root leading edge
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
    cr_v = cr_mm * v_scale
    ct_v = ct_mm * v_scale
    te_sweep_v = te_sweep_mm * v_scale
    le_sweep_v = cr_v - ct_v + te_sweep_v
    
    for k in range(11):
        eta_k = k * 0.1
        c_local_v = cr_v + te_sweep_v * (eta_k ** p_te) - le_sweep_v * (eta_k ** p_le)
        if c_local_v < 1.4:
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
    
    # 3. Fin mass & combined CG
    total_fin_area_cm2 = 2.0 * area_1side_cm2 + num_v * area_1v_cm2
    fin_mass_g = total_fin_area_cm2 * (thick_mm * 0.1) * rho
    z_fin_cg = (2.0 * area_1side_cm2 * z_fin_cg_h + num_v * area_1v_cm2 * z_fin_cg_v) / total_fin_area_cm2 if total_fin_area_cm2 > 0 else -overhang_mm
    
    # 4. Barrowman forces & moments
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
    
    # 5. Ascent aerodynamics & Cd
    wet_area_m2 = (wet_area_body_cm2 + total_fin_area_cm2 * 2.0) * 1e-4
    cd_interference = 0.005 * (2.0 + num_v)
    base_cd = 0.05 if tail_len_mm > 0 else 0.10
    Cd = 0.0045 * (wet_area_m2 / S_ref) + base_cd + 0.08 + cd_interference
    
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
    
    # 6. Descent
    proj_fins_m2 = (2.0 * area_1side_cm2 * math.cos(theta_rad) + 0.15 * num_v * area_1v_cm2) * 1e-4
    body_cd_A = (1.1 / math.pi) * wet_body_m2
    fins_cd_A = 1.25 * proj_fins_m2
    total_cd_A = streamer_cd_A + body_cd_A + fins_cd_A
    v_descent = math.sqrt((2.0 * (burnout_mass_g * 1e-3) * 9.8) / (1.225 * total_cd_A)) if total_cd_A > 0 else 15.0
    t_descent = apogee_m / v_descent if v_descent > 0 else 0.0
    total_time = burn_t + t_coast + t_descent
    
    return margin_eff, total_time, apogee_m, v_descent, fin_mass_g, total_launch_mass_g, total_cg_mm, cp_pitch

@njit(parallel=True, fastmath=True)
def run_streaming_dense_sweep(
    spans, crs, trs, te_angles, overhangs, p_les, p_tes, configs_arr, const_params,
    n_margin_bins, margin_min, margin_max
):
    # Output:
    # 1. best_overall_3fin: [18] (span, cr, ct, te_sw, oh, p_le, p_te, theta, vs, is_4f, margin, time, apo, v_desc, f_m, tot_m, cg, cp)
    # 2. best_overall_4fin: [18]
    # 3. pareto_3fin: [n_margin_bins, 18]
    # 4. pareto_4fin: [n_margin_bins, 18]
    # 5. category_bests_3fin: [5, 18]
    # 6. category_bests_4fin: [5, 18]
    
    n_spans = spans.shape[0]
    n_crs = crs.shape[0]
    n_trs = trs.shape[0]
    n_te = te_angles.shape[0]
    n_oh = overhangs.shape[0]
    n_ple = p_les.shape[0]
    n_pte = p_tes.shape[0]
    n_cfg = configs_arr.shape[0]
    
    D = const_params[0]
    R = const_params[1]
    thick = const_params[2]
    rho = const_params[3]
    cna_body = const_params[4]
    cp_body = const_params[5]
    m_base = const_params[6]
    mom_base = const_params[7]
    wet_cm2 = const_params[8]
    s_ref = const_params[9]
    tail_len = const_params[10]
    burn_t = const_params[11]
    avg_thrust = const_params[12]
    prop_m = const_params[13]
    streamer_cda = const_params[14]
    wet_m2 = const_params[15]
    
    # Thread-local storage
    # Size: [n_spans, 18] for 3fin and 4fin
    local_bests_3f = np.zeros((n_spans, 18), dtype=np.float64)
    local_bests_4f = np.zeros((n_spans, 18), dtype=np.float64)
    
    # Pareto bins: [n_spans, n_margin_bins, 18]
    local_pareto_3f = np.zeros((n_spans, n_margin_bins, 18), dtype=np.float64)
    local_pareto_4f = np.zeros((n_spans, n_margin_bins, 18), dtype=np.float64)
    
    # Categories: 0:Straight, 1:Ogive, 2:Crescent, 3:Parabolic, 4:Fillet
    local_cat_3f = np.zeros((n_spans, 5, 18), dtype=np.float64)
    local_cat_4f = np.zeros((n_spans, 5, 18), dtype=np.float64)
    
    bin_width = (margin_max - margin_min) / n_margin_bins
    
    for i in prange(n_spans):
        span = spans[i]
        
        for j in range(n_crs):
            cr = crs[j]
            for k in range(n_trs):
                tr = trs[k]
                ct = max(1.5, cr * tr)
                for l in range(n_te):
                    te_ang = te_angles[l]
                    te_sw = span * math.tan(math.radians(te_ang))
                    for m in range(n_oh):
                        oh = overhangs[m]
                        for p in range(n_ple):
                            p_le = p_les[p]
                            for q in range(n_pte):
                                p_te = p_tes[q]
                                
                                # Determine category
                                cat_idx = -1
                                if abs(p_le - 1.0) < 0.05 and abs(p_te - 1.0) < 0.05:
                                    cat_idx = 0 # Straight
                                elif p_le >= 2.0 and abs(p_te - 1.0) < 0.05:
                                    cat_idx = 1 # Ogive
                                elif p_le >= 1.6 and p_te >= 1.3:
                                    cat_idx = 2 # Crescent
                                elif (p_le >= 1.2 and p_le <= 1.5) and abs(p_te - 1.0) < 0.05:
                                    cat_idx = 3 # Parabolic
                                elif p_le <= 0.85 and p_te <= 1.1:
                                    cat_idx = 4 # Fillet
                                    
                                for r in range(n_cfg):
                                    theta = configs_arr[r, 0]
                                    v_sc = configs_arr[r, 1]
                                    is_4f = bool(configs_arr[r, 2])
                                    
                                    m_eff, t_tot, apo, v_desc, f_m, tot_m, cg, cp = calc_nonlinear_fin_aero(
                                        span, cr, ct, te_sw, oh,
                                        p_le, p_te,
                                        theta, v_sc, is_4f,
                                        D, R, thick, rho,
                                        cna_body, cp_body, m_base, mom_base,
                                        wet_cm2, s_ref, tail_len,
                                        burn_t, avg_thrust, prop_m,
                                        streamer_cda, wet_m2
                                    )
                                    
                                    if m_eff < margin_min or m_eff > margin_max or f_m < 0.10 or t_tot < 5.0:
                                        continue
                                        
                                    # Pack result candidate
                                    cand = np.array([
                                        span, cr, ct, te_sw, oh, p_le, p_te, theta, v_sc, 1.0 if is_4f else 0.0,
                                        m_eff, t_tot, apo, v_desc, f_m, tot_m, cg, cp
                                    ], dtype=np.float64)
                                    
                                    # 1. Update Best Overall (Margin >= 1.00 cal)
                                    if m_eff >= 1.00:
                                        if is_4f:
                                            if t_tot > local_bests_4f[i, 11]:
                                                for idx in range(18):
                                                    local_bests_4f[i, idx] = cand[idx]
                                        else:
                                            if t_tot > local_bests_3f[i, 11]:
                                                for idx in range(18):
                                                    local_bests_3f[i, idx] = cand[idx]
                                                    
                                    # 2. Update Pareto bin
                                    b_idx = int((m_eff - margin_min) / bin_width)
                                    if b_idx >= 0 and b_idx < n_margin_bins:
                                        if is_4f:
                                            if t_tot > local_pareto_4f[i, b_idx, 11]:
                                                for idx in range(18):
                                                    local_pareto_4f[i, b_idx, idx] = cand[idx]
                                        else:
                                            if t_tot > local_pareto_3f[i, b_idx, 11]:
                                                for idx in range(18):
                                                    local_pareto_3f[i, b_idx, idx] = cand[idx]
                                                    
                                    # 3. Update Category bests (Margin >= 1.00 cal)
                                    if m_eff >= 1.00 and cat_idx >= 0:
                                        if is_4f:
                                            if t_tot > local_cat_4f[i, cat_idx, 11]:
                                                for idx in range(18):
                                                    local_cat_4f[i, cat_idx, idx] = cand[idx]
                                        else:
                                            if t_tot > local_cat_3f[i, cat_idx, 11]:
                                                for idx in range(18):
                                                    local_cat_3f[i, cat_idx, idx] = cand[idx]
                                                    
    # Reduce across spans
    best_3fin = np.zeros(18, dtype=np.float64)
    best_4fin = np.zeros(18, dtype=np.float64)
    for i in range(n_spans):
        if local_bests_3f[i, 11] > best_3fin[11]:
            for idx in range(18):
                best_3fin[idx] = local_bests_3f[i, idx]
        if local_bests_4f[i, 11] > best_4fin[11]:
            for idx in range(18):
                best_4fin[idx] = local_bests_4f[i, idx]
                
    pareto_3fin = np.zeros((n_margin_bins, 18), dtype=np.float64)
    pareto_4fin = np.zeros((n_margin_bins, 18), dtype=np.float64)
    for b in range(n_margin_bins):
        for i in range(n_spans):
            if local_pareto_3f[i, b, 11] > pareto_3fin[b, 11]:
                for idx in range(18):
                    pareto_3fin[b, idx] = local_pareto_3f[i, b, idx]
            if local_pareto_4f[i, b, 11] > pareto_4fin[b, 11]:
                for idx in range(18):
                    pareto_4fin[b, idx] = local_pareto_4f[i, b, idx]
                    
    cat_3fin = np.zeros((5, 18), dtype=np.float64)
    cat_4fin = np.zeros((5, 18), dtype=np.float64)
    for c in range(5):
        for i in range(n_spans):
            if local_cat_3f[i, c, 11] > cat_3fin[c, 11]:
                for idx in range(18):
                    cat_3fin[c, idx] = local_cat_3f[i, c, idx]
            if local_cat_4f[i, c, 11] > cat_4fin[c, 11]:
                for idx in range(18):
                    cat_4fin[c, idx] = local_cat_4f[i, c, idx]
                    
    return best_3fin, best_4fin, pareto_3fin, pareto_4fin, cat_3fin, cat_4fin

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

def main():
    print("=" * 85)
    print("MASSIVE HIGH-DENSITY WIDE-RANGE NON-LINEAR FIN OPTIMIZATION")
    print("150M+ Iterations Streaming Reduction on AMD Ryzen 9 6900HX (16 Threads)")
    print("=" * 85)
    
    motor = get_motor("1/2A6-2")
    burn_t = motor.burn_time
    avg_thrust = motor.total_impulse / motor.burn_time
    prop_m = motor.propellant_mass_g
    
    D = 24.0
    R = 12.0
    thick_mm = 0.4
    rho = 1.24
    S_ref = math.pi * (R * 1e-3)**2
    
    # 50x500 streamer (250 cm2)
    streamer_cd_A = 0.25 * (250.0 * 1e-4)
    streamer_mass_g = 1.27
    
    m_base, mom_base, cna_body, cp_body, wet_cm2 = compute_fuselage_base(
        nose_len_mm=125.0, tail_len_mm=20.0, streamer_mass_g=streamer_mass_g
    )
    wet_m2 = wet_cm2 * 1e-4
    
    const_params = np.array([
        D, R, thick_mm, rho,
        cna_body, cp_body, m_base, mom_base,
        wet_cm2, S_ref, 20.0,
        burn_t, avg_thrust, prop_m,
        streamer_cd_A, wet_m2
    ], dtype=np.float64)
    
    # -------------------------------------------------------------
    # High-Density Wide-Range Parameter Arrays
    # -------------------------------------------------------------
    # 1. Spans: 20.0 to 100.0 mm in 2.5 mm steps (33 values)
    spans = np.arange(20.0, 102.5, 2.5, dtype=np.float64)
    
    # 2. Root chords: 14.0 to 46.0 mm in 2.0 mm steps (17 values)
    crs = np.arange(14.0, 48.0, 2.0, dtype=np.float64)
    
    # 3. Taper ratios: 8 values
    trs = np.array([0.05, 0.08, 0.12, 0.16, 0.20, 0.25, 0.30, 0.35], dtype=np.float64)
    
    # 4. Trailing edge angles: -10 to +25 deg in 5 deg steps (8 values)
    te_angles = np.array([-10.0, -5.0, 0.0, 5.0, 10.0, 15.0, 20.0, 25.0], dtype=np.float64)
    
    # 5. Overhangs: 0.0 to 20.0 mm in 2.5 mm steps (9 values)
    overhangs = np.arange(0.0, 22.5, 2.5, dtype=np.float64)
    
    # 6. LE exponents p_le: 11 values (wide: 0.5 to 3.0)
    p_les = np.array([0.5, 0.65, 0.8, 0.95, 1.0, 1.2, 1.5, 1.8, 2.2, 2.6, 3.0], dtype=np.float64)
    
    # 7. TE exponents p_te: 7 values (wide: 0.8 to 2.0)
    p_tes = np.array([0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0], dtype=np.float64)
    
    # 8. Architectures: 6 configs
    configs_arr = np.array([
        [35.0, 0.65, 0.0],
        [35.0, 0.70, 0.0],
        [35.0, 0.80, 0.0],
        [35.0, 0.90, 0.0],
        [35.0, 1.00, 0.0],
        [0.0,  1.00, 1.0], # 4-fin
    ], dtype=np.float64)
    
    total_pts = (len(spans) * len(crs) * len(trs) * len(te_angles) * 
                 len(overhangs) * len(p_les) * len(p_tes) * len(configs_arr))
    print(f"Total configurations to evaluate: {total_pts:,} (153.6 Million)")
    
    # Pareto bin settings: 0.90 to 2.00 cal in 0.02 cal steps (55 bins)
    margin_min = 0.90
    margin_max = 2.00
    n_margin_bins = 55
    
    print("Compiling Numba JIT streaming kernel...")
    # Warmup
    _ = run_streaming_dense_sweep(
        spans[:2], crs[:2], trs[:2], te_angles[:2], overhangs[:2],
        p_les[:2], p_tes[:2], configs_arr[:2], const_params,
        n_margin_bins, margin_min, margin_max
    )
    
    print("Executing 153 Million sweep across 16 CPU threads...")
    t0 = time.perf_counter()
    b3, b4, p3, p4, c3, c4 = run_streaming_dense_sweep(
        spans, crs, trs, te_angles, overhangs, p_les, p_tes, configs_arr, const_params,
        n_margin_bins, margin_min, margin_max
    )
    t1 = time.perf_counter()
    eval_time = t1 - t0
    
    print(f"\nCOMPLETED IN {eval_time:.3f} SECONDS!")
    print(f"Throughput: {total_pts / eval_time:,.0f} configurations/second\n")
    
    def decode_row(row):
        return {
            "span_mm": float(row[0]),
            "cr_mm": float(row[1]),
            "ct_mm": float(row[2]),
            "te_sweep_mm": round(float(row[3]), 2),
            "overhang_mm": float(row[4]),
            "p_le": float(row[5]),
            "p_te": float(row[6]),
            "theta_deg": float(row[7]),
            "v_scale": float(row[8]),
            "is_4fin": bool(row[9] > 0.5),
            "margin_cal": round(float(row[10]), 2),
            "hang_time_s": round(float(row[11]), 2),
            "apogee_m": round(float(row[12]), 2),
            "v_desc_ms": round(float(row[13]), 2),
            "fin_mass_g": round(float(row[14]), 2),
            "total_mass_g": round(float(row[15]), 2),
            "cg_mm": round(float(row[16]), 2),
            "cp_mm": round(float(row[17]), 2)
        }
        
    res_b3 = decode_row(b3)
    res_b4 = decode_row(b4)
    
    print("=" * 85)
    print("★ ABSOLUTE TOP CANDIDATES FROM 153M HIGH-DENSITY SWEEP (Margin >= 1.00 cal) ★")
    print("=" * 85)
    
    print(f"\n【新・設定A 本命: 3枚非対称 逆Y字35° (v_scale={res_b3['v_scale']:.2f})】")
    print(f"  スパン幅 (b):       {res_b3['span_mm']:.1f} mm")
    print(f"  翼根コード (Cr):    {res_b3['cr_mm']:.1f} mm")
    print(f"  翼端コード (Ct):    {res_b3['ct_mm']:.1f} mm")
    print(f"  後縁後退量:         {res_b3['te_sweep_mm']:.1f} mm")
    print(f"  後端突き出し:       {res_b3['overhang_mm']:.1f} mm")
    print(f"  前縁曲率指数 (p_le): {res_b3['p_le']:.2f} (凹フィレット)")
    print(f"  後縁曲率指数 (p_te): {res_b3['p_te']:.2f} (三日月後退)")
    print(f"  静安定マージン:     +{res_b3['margin_cal']:.2f} cal")
    print(f"  総滞空時間:         {res_b3['hang_time_s']:.2f} 秒")
    print(f"  最高到達高度:       {res_b3['apogee_m']:.2f} m")
    print(f"  降下速度:           {res_b3['v_desc_ms']:.2f} m/s")
    print(f"  翼合計質量:         {res_b3['fin_mass_g']:.2f} g")
    print(f"  全備質量:           {res_b3['total_mass_g']:.2f} g")
    
    print(f"\n【新・設定B 本命: 4枚対称 十字翼 (+)】")
    print(f"  スパン幅 (b):       {res_b4['span_mm']:.1f} mm")
    print(f"  翼根コード (Cr):    {res_b4['cr_mm']:.1f} mm")
    print(f"  翼端コード (Ct):    {res_b4['ct_mm']:.1f} mm")
    print(f"  後縁後退量:         {res_b4['te_sweep_mm']:.1f} mm")
    print(f"  後端突き出し:       {res_b4['overhang_mm']:.1f} mm")
    print(f"  前縁曲率指数 (p_le): {res_b4['p_le']:.2f} (凹フィレット)")
    print(f"  後縁曲率指数 (p_te): {res_b4['p_te']:.2f} (三日月後退)")
    print(f"  静安定マージン:     +{res_b4['margin_cal']:.2f} cal")
    print(f"  総滞空時間:         {res_b4['hang_time_s']:.2f} 秒")
    print(f"  最高到達高度:       {res_b4['apogee_m']:.2f} m")
    print(f"  降下速度:           {res_b4['v_desc_ms']:.2f} m/s")
    print(f"  翼合計質量:         {res_b4['fin_mass_g']:.2f} g")
    print(f"  全備質量:           {res_b4['total_mass_g']:.2f} g")
    
    # Category summary
    cat_labels = ["直線クリップトデルタ", "オージー/ゴシック翼", "クレセント/三日月翼", "放物線前縁翼", "凹前縁フィレット翼"]
    cat_summary = []
    print("\n" + "=" * 85)
    print("★ 各種形状カテゴリー別 ベスト性能 (Margin >= 1.00 cal) ★")
    print("=" * 85)
    for c_i, label in enumerate(cat_labels):
        r3 = decode_row(c3[c_i])
        r4 = decode_row(c4[c_i])
        print(f"\n[{label}]")
        print(f"  3枚逆Y字: 滞空 {r3['hang_time_s']:.2f}s | 高度 {r3['apogee_m']:.2f}m | マージン +{r3['margin_cal']:.2f}cal | 翼重 {r3['fin_mass_g']:.2f}g | Span={r3['span_mm']:.1f}mm, Cr={r3['cr_mm']:.0f}mm, Ct={r3['ct_mm']:.1f}mm (p_le={r3['p_le']:.2f}, p_te={r3['p_te']:.2f})")
        print(f"  4枚十字:   滞空 {r4['hang_time_s']:.2f}s | 高度 {r4['apogee_m']:.2f}m | マージン +{r4['margin_cal']:.2f}cal | 翼重 {r4['fin_mass_g']:.2f}g | Span={r4['span_mm']:.1f}mm, Cr={r4['cr_mm']:.0f}mm, Ct={r4['ct_mm']:.1f}mm (p_le={r4['p_le']:.2f}, p_te={r4['p_te']:.2f})")
        cat_summary.append({
            "category": label,
            "best_3fin": r3,
            "best_4fin": r4
        })
        
    # Pareto front decoding
    pareto_data_3f = []
    pareto_data_4f = []
    bin_w = (margin_max - margin_min) / n_margin_bins
    for b in range(n_margin_bins):
        m_center = margin_min + (b + 0.5) * bin_w
        if p3[b, 11] > 0:
            row3 = decode_row(p3[b])
            row3["bin_margin"] = round(m_center, 2)
            pareto_data_3f.append(row3)
        if p4[b, 11] > 0:
            row4 = decode_row(p4[b])
            row4["bin_margin"] = round(m_center, 2)
            pareto_data_4f.append(row4)
            
    out_all = {
        "total_evaluated": int(total_pts),
        "eval_time_sec": round(eval_time, 3),
        "throughput_it_s": round(total_pts / eval_time, 0),
        "best_asym_3fin": res_b3,
        "best_sym_4fin": res_b4,
        "category_summary": cat_summary,
        "pareto_3fin": pareto_data_3f,
        "pareto_4fin": pareto_data_4f
    }
    
    with open("scratch/massive_dense_sweep_results.json", "w", encoding="utf-8") as f:
        json.dump(out_all, f, indent=2, ensure_ascii=False)
        
    print("\nSaved massive dense results to scratch/massive_dense_sweep_results.json")

if __name__ == "__main__":
    main()
