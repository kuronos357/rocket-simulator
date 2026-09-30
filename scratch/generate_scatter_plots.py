"""
Generate High-Quality Multi-Panel Scatter Plots
from Non-Linear Fin Optimization Data:
  - Samples 200,000+ feasible designs across all parameters
  - Panel 1: Margin vs Hang Time (Colored by Shape Category)
  - Panel 2: Margin vs Apogee (Colored by Fin Mass)
  - Panel 3: Margin vs Hang Time (Colored by LE Exponent p_le)
  - Panel 4: Fin Mass vs Hang Time (Colored by Architecture)
  - Highlights Top Candidates (Setting A: 14.27s, Setting B: 14.20s)
"""

import os
import sys
import math
import time
import numpy as np
import matplotlib.pyplot as plt
from numba import njit, prange

sys.path.insert(0, os.path.abspath("."))
from sim_engine.motor_db import get_motor

# 日本語フォント対応
plt.rcParams['font.sans-serif'] = ['Meiryo', 'Yu Gothic', 'MS Gothic', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

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
    le_sweep_h = cr_mm - ct_mm + te_sweep_mm
    
    # Check local chord
    for k in range(11):
        eta_k = k * 0.1
        c_local = cr_mm + te_sweep_mm * (eta_k ** p_te) - le_sweep_h * (eta_k ** p_le)
        if c_local < 1.4:
            return -999.0, 0.0, 0.0, 99.0, 99.0, 99.0, 0.0, 0.0
            
    int_c_h = cr_mm + te_sweep_mm / (p_te + 1.0) - le_sweep_h / (p_le + 1.0)
    if int_c_h <= 0.0:
        return -999.0, 0.0, 0.0, 99.0, 99.0, 99.0, 0.0, 0.0
        
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
    
    # Vertical fin
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
    
    proj_fins_m2 = (2.0 * area_1side_cm2 * math.cos(theta_rad) + 0.15 * num_v * area_1v_cm2) * 1e-4
    body_cd_A = (1.1 / math.pi) * wet_body_m2
    fins_cd_A = 1.25 * proj_fins_m2
    total_cd_A = streamer_cd_A + body_cd_A + fins_cd_A
    v_descent = math.sqrt((2.0 * (burnout_mass_g * 1e-3) * 9.8) / (1.225 * total_cd_A)) if total_cd_A > 0 else 15.0
    t_descent = apogee_m / v_descent if v_descent > 0 else 0.0
    total_time = burn_t + t_coast + t_descent
    
    return margin_eff, total_time, apogee_m, v_descent, fin_mass_g, total_launch_mass_g, total_cg_mm, cp_pitch

@njit(parallel=True, fastmath=True)
def sample_configurations(grid, const_params):
    N = grid.shape[0]
    out = np.empty((N, 8), dtype=np.float64)
    
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
    
    for i in prange(N):
        span = grid[i, 0]
        cr = grid[i, 1]
        ct = grid[i, 2]
        te_sw = grid[i, 3]
        oh = grid[i, 4]
        p_le = grid[i, 5]
        p_te = grid[i, 6]
        theta = grid[i, 7]
        v_sc = grid[i, 8]
        is_4f = bool(grid[i, 9])
        
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
        out[i, 0] = m_eff
        out[i, 1] = t_tot
        out[i, 2] = apo
        out[i, 3] = v_desc
        out[i, 4] = f_m
        out[i, 5] = tot_m
        out[i, 6] = cg
        out[i, 7] = cp
        
    return out

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
    print("Sampling 250,000 diverse configurations for scatter plots...")
    motor = get_motor("1/2A6-2")
    burn_t = motor.burn_time
    avg_thrust = motor.total_impulse / motor.burn_time
    prop_m = motor.propellant_mass_g
    
    D = 24.0
    R = 12.0
    thick_mm = 0.4
    rho = 1.24
    S_ref = math.pi * (R * 1e-3)**2
    
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
    
    # Generate balanced grid for scatter
    spans = np.linspace(25.0, 100.0, 16)
    crs = np.linspace(14.0, 44.0, 11)
    trs = np.array([0.06, 0.12, 0.20, 0.30])
    te_angles = np.array([-5.0, 0.0, 10.0, 20.0, 25.0])
    overhangs = np.array([0.0, 10.0, 17.5, 20.0])
    p_les = np.array([0.5, 0.7, 0.85, 1.0, 1.4, 2.0, 2.6])
    p_tes = np.array([0.8, 1.0, 1.3, 1.6, 2.0])
    configs = [
        (35.0, 0.70, 0.0), # 3-fin
        (35.0, 0.80, 0.0), # 3-fin
        (0.0,  1.00, 1.0), # 4-fin
    ]
    
    total = (len(spans) * len(crs) * len(trs) * len(te_angles) * 
             len(overhangs) * len(p_les) * len(p_tes) * len(configs))
    print(f"Total points to evaluate: {total:,}")
    
    grid = np.empty((total, 10), dtype=np.float64)
    idx = 0
    for span in spans:
        for cr in crs:
            for tr in trs:
                ct = max(1.5, cr * tr)
                for te_ang in te_angles:
                    te_sw = span * math.tan(math.radians(te_ang))
                    for oh in overhangs:
                        for p_le in p_les:
                            for p_te in p_tes:
                                for theta, v_sc, is_4f in configs:
                                    grid[idx, 0] = span
                                    grid[idx, 1] = cr
                                    grid[idx, 2] = ct
                                    grid[idx, 3] = te_sw
                                    grid[idx, 4] = oh
                                    grid[idx, 5] = p_le
                                    grid[idx, 6] = p_te
                                    grid[idx, 7] = theta
                                    grid[idx, 8] = v_sc
                                    grid[idx, 9] = is_4f
                                    idx += 1
                                    
    # Evaluate
    _ = sample_configurations(grid[:10], const_params)
    res = sample_configurations(grid, const_params)
    
    # Filter valid
    m_eff = res[:, 0]
    t_tot = res[:, 1]
    apogee = res[:, 2]
    f_mass = res[:, 4]
    
    valid = (m_eff >= 0.85) & (m_eff <= 2.20) & (f_mass > 0.1) & (t_tot > 5.0)
    v_grid = grid[valid]
    v_res = res[valid]
    print(f"Valid points for plotting: {len(v_res):,}")
    
    # -------------------------------------------------------------
    # Create 4-Panel Master Scatter Plot
    # -------------------------------------------------------------
    fig, axes = plt.subplots(2, 2, figsize=(18, 14))
    
    # Panel 1: Margin vs Hang Time (Colored by Category)
    ax1 = axes[0, 0]
    p_les_v = v_grid[:, 5]
    p_tes_v = v_grid[:, 6]
    
    # Categorize
    is_fillet = (p_les_v <= 0.85)
    is_straight = (np.abs(p_les_v - 1.0) < 0.05) & (np.abs(p_tes_v - 1.0) < 0.05)
    is_ogive = (p_les_v >= 2.0) & (np.abs(p_tes_v - 1.0) < 0.05)
    is_crescent = (p_les_v >= 1.4) & (p_tes_v >= 1.3)
    is_other = ~(is_fillet | is_straight | is_ogive | is_crescent)
    
    ax1.scatter(v_res[is_other, 0], v_res[is_other, 1], c='#cccccc', s=6, alpha=0.3, label='その他中間形状', rasterized=True)
    ax1.scatter(v_res[is_ogive, 0], v_res[is_ogive, 1], c='#d62728', s=10, alpha=0.5, label='オージー/ゴシック翼 ($p_{le} \\geq 2.0$)', rasterized=True)
    ax1.scatter(v_res[is_crescent, 0], v_res[is_crescent, 1], c='#9467bd', s=10, alpha=0.5, label='クレセント/三日月翼 ($p_{te} \\geq 1.3$)', rasterized=True)
    ax1.scatter(v_res[is_straight, 0], v_res[is_straight, 1], c='#2ca02c', s=14, alpha=0.7, label='直線クリップトデルタ ($p=1.0$)', rasterized=True)
    ax1.scatter(v_res[is_fillet, 0], v_res[is_fillet, 1], c='#1f77b4', s=14, alpha=0.7, label='凹前縁フィレット翼 ($p_{le} \\leq 0.85$)', rasterized=True)
    
    # Highlights
    ax1.scatter([1.02], [14.27], c='gold', edgecolors='black', s=220, marker='*', zorder=10, label='★ 新・設定A (3枚逆Y字: 14.27s)')
    ax1.scatter([1.00], [14.20], c='cyan', edgecolors='black', s=200, marker='P', zorder=10, label='★ 新・設定B (4枚十字: 14.20s)')
    ax1.axvline(1.0, color='red', ls='--', lw=1.5, alpha=0.7, label='推奨静安定限界 (+1.0 cal)')
    ax1.set_xlabel('静安定マージン [cal]', fontsize=11, fontweight='bold')
    ax1.set_ylabel('総滞空時間 [秒]', fontsize=11, fontweight='bold')
    ax1.set_title('(A) 静安定マージン vs 滞空時間（翼形状カテゴリー別分布）', fontsize=12, fontweight='bold')
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc='lower left', fontsize=9.5, framealpha=0.9)
    ax1.set_xlim(0.85, 2.15)
    ax1.set_ylim(12.8, 14.4)
    
    # Panel 2: Margin vs Apogee (Colored by Fin Mass)
    ax2 = axes[0, 1]
    sc2 = ax2.scatter(v_res[:, 0], v_res[:, 2], c=v_res[:, 4], cmap='viridis_r', s=8, alpha=0.6, rasterized=True)
    cbar2 = plt.colorbar(sc2, ax=ax2)
    cbar2.set_label('翼合計質量 [g]（軽量なほど黄色）', fontsize=10.5, fontweight='bold')
    ax2.scatter([1.02], [62.49], c='gold', edgecolors='black', s=220, marker='*', zorder=10, label='★ 新・設定A (62.49m, 0.87g)')
    ax2.scatter([1.00], [62.61], c='cyan', edgecolors='black', s=200, marker='P', zorder=10, label='★ 新・設定B (62.61m, 0.81g)')
    ax2.axvline(1.0, color='red', ls='--', lw=1.5, alpha=0.7)
    ax2.set_xlabel('静安定マージン [cal]', fontsize=11, fontweight='bold')
    ax2.set_ylabel('最高到達高度 [m]', fontsize=11, fontweight='bold')
    ax2.set_title('(B) 静安定マージン vs 最高高度（翼質量によるグラデーション）', fontsize=12, fontweight='bold')
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(loc='lower left', fontsize=9.5, framealpha=0.9)
    ax2.set_xlim(0.85, 2.15)
    ax2.set_ylim(52.0, 63.5)
    
    # Panel 3: Margin vs Hang Time (Colored by LE Exponent p_le)
    ax3 = axes[1, 0]
    sc3 = ax3.scatter(v_res[:, 0], v_res[:, 1], c=v_grid[:, 5], cmap='coolwarm', s=8, alpha=0.6, rasterized=True)
    cbar3 = plt.colorbar(sc3, ax=ax3)
    cbar3.set_label('前縁曲率指数 $p_{le}$ (青:フィレット < 1.0 < 赤:オージー)', fontsize=10.5, fontweight='bold')
    ax3.scatter([1.02], [14.27], c='gold', edgecolors='black', s=220, marker='*', zorder=10)
    ax3.scatter([1.00], [14.20], c='cyan', edgecolors='black', s=200, marker='P', zorder=10)
    ax3.axvline(1.0, color='red', ls='--', lw=1.5, alpha=0.7)
    ax3.set_xlabel('静安定マージン [cal]', fontsize=11, fontweight='bold')
    ax3.set_ylabel('総滞空時間 [秒]', fontsize=11, fontweight='bold')
    ax3.set_title('(C) 静安定マージン vs 滞空時間（前縁曲率 $p_{le}$ の影響）', fontsize=12, fontweight='bold')
    ax3.grid(True, linestyle=':', alpha=0.6)
    ax3.set_xlim(0.85, 2.15)
    ax3.set_ylim(12.8, 14.4)
    
    # Panel 4: Fin Mass vs Hang Time (Split by Architecture)
    ax4 = axes[1, 1]
    is_4f = v_grid[:, 9] == 1.0
    ax4.scatter(v_res[~is_4f, 4], v_res[~is_4f, 1], c='#1f77b4', s=10, alpha=0.35, label='3枚非対称 逆Y字35°', rasterized=True)
    ax4.scatter(v_res[is_4f, 4], v_res[is_4f, 1], c='#ff7f0e', s=10, alpha=0.35, label='4枚対称 十字翼 (+)', rasterized=True)
    ax4.scatter([0.87], [14.27], c='gold', edgecolors='black', s=220, marker='*', zorder=10, label='★ 新・設定A (0.87g, 14.27s)')
    ax4.scatter([0.81], [14.20], c='cyan', edgecolors='black', s=200, marker='P', zorder=10, label='★ 新・設定B (0.81g, 14.20s)')
    ax4.set_xlabel('翼合計質量 [g]', fontsize=11, fontweight='bold')
    ax4.set_ylabel('総滞空時間 [秒]', fontsize=11, fontweight='bold')
    ax4.set_title('(D) 翼合計質量 vs 滞空時間（形態別クラスタリング）', fontsize=12, fontweight='bold')
    ax4.grid(True, linestyle=':', alpha=0.6)
    ax4.legend(loc='upper right', fontsize=9.5, framealpha=0.9)
    ax4.set_xlim(0.5, 3.5)
    ax4.set_ylim(12.8, 14.4)
    
    plt.suptitle('【1.5億パターン最適化 全域散布図解析】非線形翼の安定性・質量・滞空時間の包括的相関分析', 
                 fontsize=15, fontweight='bold', y=0.98)
    plt.tight_layout()
    
    os.makedirs('output', exist_ok=True)
    out_path = 'output/nonlinear_multipanel_scatter_analysis.png'
    plt.savefig(out_path, dpi=300)
    print(f"Successfully saved {out_path}")

if __name__ == "__main__":
    main()
