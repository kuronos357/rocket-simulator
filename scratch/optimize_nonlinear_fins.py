"""
Ultra-Fast Hardware-Accelerated Multi-Dimensional Optimization
for NON-LINEAR (Curved / Parametric) Fins:
  - Generalized Power-Law Model:
      x_le(eta) = le_sweep * eta^p_le
      x_te(eta) = cr + te_sweep * eta^p_te
  - Closed-form Analytical Integration for S, MAC, X_CP, X_CG
  - Physical constraint: c(eta) >= 1.5mm everywhere along span (no self-intersection!)
  - Consistent fuselage physics with compute_fuselage_base (50x500 streamer, Estes 1/2A6-2, Boat Tail 20mm)
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
    
    # -------------------------------------------------------------
    # 1. Main wings (2 fins) - Closed-Form Analytical Formulas
    # -------------------------------------------------------------
    le_sweep_h = cr_mm - ct_mm + te_sweep_mm
    
    # Check physical geometric feasibility: local chord must be >= 1.5mm everywhere
    # Test 11 points along span
    for k in range(11):
        eta_k = k * 0.1
        c_local = cr_mm + te_sweep_mm * (eta_k ** p_te) - le_sweep_h * (eta_k ** p_le)
        if c_local < 1.4:
            return -999.0, 0.0, 0.0, 99.0, 99.0, 99.0, 0.0, 0.0
            
    # Int c(eta) d(eta)
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
    # Global CP from fuselage tail (z=0 is tail end, negative is overhang)
    cp_fin_h = -overhang_mm + (cr_mm - xf_from_le_h)
    
    # Fin CG from root leading edge
    int_diff2_h = (cr_mm**2 + (2.0 * cr_mm * te_sweep_mm) / (p_te + 1.0) 
                   + (te_sweep_mm**2) / (2.0 * p_te + 1.0) - (le_sweep_h**2) / (2.0 * p_le + 1.0))
    x_cg_from_le_h = int_diff2_h / (2.0 * int_c_h)
    z_fin_cg_h = -overhang_mm + (cr_mm - x_cg_from_le_h)
    
    # Mid-chord line length
    mid_sweep_h = 0.5 * (te_sweep_mm + le_sweep_h)
    Lf_h = math.sqrt(mid_sweep_h**2 + span_mm**2)
    
    k_body_h = 1.0 + R / (R + span_mm)
    denom_h = 1.0 + math.sqrt(1.0 + (2.0 * Lf_h / mac_h)**2) if mac_h > 0 else 2.0
    cna_1pair_h = k_body_h * (4.0 * 2.0 * (span_mm / D)**2) / denom_h
    
    # -------------------------------------------------------------
    # 2. Vertical fin(s)
    # -------------------------------------------------------------
    span_v = span_mm * v_scale
    cr_v = cr_mm * v_scale
    ct_v = ct_mm * v_scale
    te_sweep_v = te_sweep_mm * v_scale
    le_sweep_v = cr_v - ct_v + te_sweep_v
    
    # Check vertical fin feasibility
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
    
    # -------------------------------------------------------------
    # 3. Fin mass & combined CG
    # -------------------------------------------------------------
    total_fin_area_cm2 = 2.0 * area_1side_cm2 + num_v * area_1v_cm2
    fin_mass_g = total_fin_area_cm2 * (thick_mm * 0.1) * rho
    z_fin_cg = (2.0 * area_1side_cm2 * z_fin_cg_h + num_v * area_1v_cm2 * z_fin_cg_v) / total_fin_area_cm2 if total_fin_area_cm2 > 0 else -overhang_mm
    
    # -------------------------------------------------------------
    # 4. Barrowman forces & moments
    # -------------------------------------------------------------
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
    
    # -------------------------------------------------------------
    # 5. Ascent aerodynamics & Cd
    # -------------------------------------------------------------
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
    
    # -------------------------------------------------------------
    # 6. Descent
    # -------------------------------------------------------------
    proj_fins_m2 = (2.0 * area_1side_cm2 * math.cos(theta_rad) + 0.15 * num_v * area_1v_cm2) * 1e-4
    body_cd_A = (1.1 / math.pi) * wet_body_m2
    fins_cd_A = 1.25 * proj_fins_m2
    total_cd_A = streamer_cd_A + body_cd_A + fins_cd_A
    v_descent = math.sqrt((2.0 * (burnout_mass_g * 1e-3) * 9.8) / (1.225 * total_cd_A)) if total_cd_A > 0 else 15.0
    t_descent = apogee_m / v_descent if v_descent > 0 else 0.0
    total_time = burn_t + t_coast + t_descent
    
    return margin_eff, total_time, apogee_m, v_descent, fin_mass_g, total_launch_mass_g, total_cg_mm, cp_pitch

@njit(parallel=True, fastmath=True)
def run_parallel_nonlinear_sweep(grid_params, const_params):
    N = grid_params.shape[0]
    results = np.empty((N, 8), dtype=np.float64)
    
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
        span = grid_params[i, 0]
        cr = grid_params[i, 1]
        ct = grid_params[i, 2]
        te_sw = grid_params[i, 3]
        oh = grid_params[i, 4]
        p_le = grid_params[i, 5]
        p_te = grid_params[i, 6]
        theta = grid_params[i, 7]
        v_sc = grid_params[i, 8]
        is_4f = bool(grid_params[i, 9])
        
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
        
        results[i, 0] = m_eff
        results[i, 1] = t_tot
        results[i, 2] = apo
        results[i, 3] = v_desc
        results[i, 4] = f_m
        results[i, 5] = tot_m
        results[i, 6] = cg
        results[i, 7] = cp
        
    return results

def compute_fuselage_base(nose_len_mm=125.0, tail_len_mm=20.0, total_len_mm=250.0, D=24.0, t_wall=0.4, rho=1.24, streamer_mass_g=1.27):
    R = D / 2.0
    r_tail = 18.8 / 2.0 if tail_len_mm > 0 else R
    cyl_len = max(10.0, total_len_mm - nose_len_mm - tail_len_mm)
    
    # 1. Nose cone (Power n=0.75)
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
    
    # 2. Cylindrical body
    area_cyl_mm2 = 2.0 * math.pi * R * cyl_len
    mass_cyl_g = (area_cyl_mm2 * 1.65) * (t_wall * 0.1) * rho * 0.01
    z_cyl_cg = tail_len_mm + cyl_len / 2.0
    
    # 3. Tail cone (Boat tail)
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
    print("=" * 80)
    print("ULTRA-FAST NON-LINEAR (PARAMETRIC POWER-LAW) FIN OPTIMIZATION")
    print("Unified Formula: x_le = sweep * eta^p_le, x_te = cr + te_sweep * eta^p_te")
    print("=" * 80)
    
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
    # Define Parameter Grid
    # -------------------------------------------------------------
    # Spans (up to 100mm)
    spans = np.arange(35.0, 105.0, 5.0)  # 35 to 100 mm (14 values)
    crs = np.arange(16.0, 42.0, 3.0)     # 16, 19, 22, 25, 28, 31, 34, 37, 40 (9 values)
    taper_ratios = np.array([0.08, 0.12, 0.16, 0.22, 0.30]) # 5 values
    
    # Trailing edge sweep angles: 0, 10, 20 deg
    te_angles_deg = np.array([0.0, 10.0, 20.0])
    
    # Overhangs
    overhangs = np.array([10.0, 20.0])
    
    # Non-linear exponents
    # p_le: 0.8(fillet), 1.0(straight), 1.4(parabolic), 1.8, 2.2, 2.6(ogive)
    p_les = np.array([0.8, 1.0, 1.4, 1.8, 2.2, 2.6], dtype=np.float64)
    # p_te: 1.0(straight), 1.3, 1.6(crescent)
    p_tes = np.array([1.0, 1.3, 1.6], dtype=np.float64)
    
    # Architectures
    # 1. 3-fin Asymmetric (Inv-Y 35°, vs=0.70)
    # 2. 4-fin Symmetric (+, vs=1.00)
    configs = [
        ("3-fin-asym", 35.0, 0.70, 0.0),
        ("4-fin-sym",  0.0,  1.00, 1.0),
    ]
    
    total_pts = (len(spans) * len(crs) * len(taper_ratios) * len(te_angles_deg) * 
                 len(overhangs) * len(p_les) * len(p_tes) * len(configs))
    print(f"Total parameter combinations to evaluate: {total_pts:,}")
    
    grid = np.empty((total_pts, 10), dtype=np.float64)
    idx = 0
    for span in spans:
        for cr in crs:
            for tr in taper_ratios:
                ct = max(1.5, cr * tr)
                for te_ang in te_angles_deg:
                    te_sw = span * math.tan(math.radians(te_ang))
                    for oh in overhangs:
                        for p_le in p_les:
                            for p_te in p_tes:
                                for name, theta, v_sc, is_4f in configs:
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
                                    
    print("Compiling and running JIT parallel evaluation on 16 threads...")
    _ = run_parallel_nonlinear_sweep(grid[:10], const_params)
    
    t0 = time.perf_counter()
    results = run_parallel_nonlinear_sweep(grid, const_params)
    t1 = time.perf_counter()
    
    eval_time = t1 - t0
    print(f"Evaluated {total_pts:,} configurations in {eval_time:.3f} seconds!")
    print(f"Throughput: {total_pts / eval_time:,.0f} configurations/second\n")
    
    margins = results[:, 0]
    hang_times = results[:, 1]
    apogees = results[:, 2]
    fin_masses = results[:, 4]
    
    # Filter valid designs: margin >= 0.90 cal
    valid_mask = (margins >= 0.90) & (margins <= 2.50) & (fin_masses > 0.10) & (hang_times > 5.0)
    num_valid = np.sum(valid_mask)
    print(f"Valid configurations meeting Margin >= 0.90 cal: {num_valid:,} ({num_valid/total_pts*100:.1f}%)")
    
    valid_grid = grid[valid_mask]
    valid_res = results[valid_mask]
    
    # -------------------------------------------------------------
    # Extract Best Performers (Margin >= 1.00 cal)
    # -------------------------------------------------------------
    m1_mask = valid_res[:, 0] >= 1.00
    valid_m1_grid = valid_grid[m1_mask]
    valid_m1_res = valid_res[m1_mask]
    
    # 1. 3-fin Asymmetric Top
    asym_mask = valid_m1_grid[:, 9] == 0.0
    res_asym = valid_m1_res[asym_mask]
    grid_asym = valid_m1_grid[asym_mask]
    best_asym_idx = np.argmax(res_asym[:, 1])
    ba_p = grid_asym[best_asym_idx]
    ba_r = res_asym[best_asym_idx]
    
    # 2. 4-fin Symmetric Top
    sym_mask = valid_m1_grid[:, 9] == 1.0
    res_sym = valid_m1_res[sym_mask]
    grid_sym = valid_m1_grid[sym_mask]
    best_sym_idx = np.argmax(res_sym[:, 1])
    bs_p = grid_sym[best_sym_idx]
    bs_r = res_sym[best_sym_idx]
    
    print("=" * 80)
    print("★ TOP NON-LINEAR CONFIGURATIONS (Margin >= 1.00 cal) ★")
    print("=" * 80)
    
    def print_candidate(title, p, r):
        arch_str = "4枚対称 十字 (+)" if p[9] == 1.0 else f"3枚非対称 逆Y字35° (v_scale={p[8]:.2f})"
        print(f"\n【{title}】")
        print(f"  形態:              {arch_str}")
        print(f"  翼スパン (b):       {p[0]:.1f} mm")
        print(f"  翼根コード (Cr):    {p[1]:.1f} mm")
        print(f"  翼端コード (Ct):    {p[2]:.1f} mm")
        print(f"  後縁後退 (TE Sweep): {p[3]:.1f} mm")
        print(f"  後端突き出し (OH):  {p[4]:.1f} mm")
        print(f"  前縁曲率指数 (p_le): {p[5]:.2f}  <-- 1.0=直線, >1.0=凸オージー, <1.0=凹フィレット")
        print(f"  後縁曲率指数 (p_te): {p[6]:.2f}  <-- 1.0=直線, >1.0=三日月後退")
        print(f"  静安定マージン:     +{r[0]:.2f} cal")
        print(f"  滞空時間:           {r[1]:.2f} 秒")
        print(f"  最高高度:           {r[2]:.2f} m")
        print(f"  降下速度:           {r[3]:.2f} m/s")
        print(f"  翼合計質量:         {r[4]:.2f} g")
        print(f"  機体全備質量:       {r[5]:.2f} g")
        
    print_candidate("新・設定A 本命: 3枚非対称 逆Y字35°（非線形最適化）", ba_p, ba_r)
    print_candidate("新・設定B 本命: 4枚対称 十字翼（非線形最適化）", bs_p, bs_r)
    
    # -------------------------------------------------------------
    # Comparison: Straight Baseline vs Non-linear Wings
    # -------------------------------------------------------------
    print("\n" + "=" * 80)
    print("★ 直線翼 vs 各種非線形翼の性能比較 (Margin >= 1.00 cal) ★")
    print("=" * 80)
    
    categories = [
        ("直線クリップトデルタ (Baseline: p_le=1.0, p_te=1.0)", 
         (valid_m1_grid[:, 5] == 1.0) & (valid_m1_grid[:, 6] == 1.0)),
        ("オージー/ゴシック翼 (凸前縁: p_le >= 2.2, p_te == 1.0)", 
         (valid_m1_grid[:, 5] >= 2.2) & (valid_m1_grid[:, 6] == 1.0)),
        ("クレセント/三日月翼 (前縁凸・後縁後退: p_le >= 1.8, p_te >= 1.3)", 
         (valid_m1_grid[:, 5] >= 1.8) & (valid_m1_grid[:, 6] >= 1.3)),
        ("放物線前縁翼 (マイルド凸: p_le == 1.4, p_te == 1.0)", 
         (valid_m1_grid[:, 5] == 1.4) & (valid_m1_grid[:, 6] == 1.0)),
        ("凹前縁フィレット翼 (根元拡大: p_le <= 0.8, p_te == 1.0)", 
         (valid_m1_grid[:, 5] <= 0.8) & (valid_m1_grid[:, 6] == 1.0)),
    ]
    
    summary_records = []
    for cat_name, cat_mask in categories:
        if np.sum(cat_mask) == 0:
            continue
        c_res = valid_m1_res[cat_mask]
        c_grid = valid_m1_grid[cat_mask]
        
        m3 = c_grid[:, 9] == 0.0
        if np.sum(m3) > 0:
            b3_idx = np.argmax(c_res[m3][:, 1])
            p3 = c_grid[m3][b3_idx]
            r3 = c_res[m3][b3_idx]
        else:
            p3, r3 = None, None
            
        m4 = c_grid[:, 9] == 1.0
        if np.sum(m4) > 0:
            b4_idx = np.argmax(c_res[m4][:, 1])
            p4 = c_grid[m4][b4_idx]
            r4 = c_res[m4][b4_idx]
        else:
            p4, r4 = None, None
            
        print(f"\n[{cat_name}]")
        if p3 is not None:
            print(f"  3枚逆Y字: 滞空 {r3[1]:.2f}s | 高度 {r3[2]:.2f}m | マージン +{r3[0]:.2f}cal | 翼重 {r3[4]:.2f}g | Span={p3[0]:.0f}mm, Cr={p3[1]:.0f}mm, Ct={p3[2]:.1f}mm (p_le={p3[5]:.1f}, p_te={p3[6]:.1f})")
        if p4 is not None:
            print(f"  4枚十字:   滞空 {r4[1]:.2f}s | 高度 {r4[2]:.2f}m | マージン +{r4[0]:.2f}cal | 翼重 {r4[4]:.2f}g | Span={p4[0]:.0f}mm, Cr={p4[1]:.0f}mm, Ct={p4[2]:.1f}mm (p_le={p4[5]:.1f}, p_te={p4[6]:.1f})")
            
        summary_records.append({
            "category": cat_name,
            "best_3fin": {
                "hang_time_s": round(float(r3[1]), 2), "apogee_m": round(float(r3[2]), 2),
                "margin_cal": round(float(r3[0]), 2), "fin_mass_g": round(float(r3[4]), 2),
                "span_mm": float(p3[0]), "cr_mm": float(p3[1]), "ct_mm": float(p3[2]),
                "p_le": float(p3[5]), "p_te": float(p3[6])
            } if p3 is not None else None,
            "best_4fin": {
                "hang_time_s": round(float(r4[1]), 2), "apogee_m": round(float(r4[2]), 2),
                "margin_cal": round(float(r4[0]), 2), "fin_mass_g": round(float(r4[4]), 2),
                "span_mm": float(p4[0]), "cr_mm": float(p4[1]), "ct_mm": float(p4[2]),
                "p_le": float(p4[5]), "p_te": float(p4[6])
            } if p4 is not None else None
        })
        
    out_dict = {
        "total_evaluated": int(total_pts),
        "eval_time_sec": round(eval_time, 3),
        "summary_records": summary_records,
        "best_asym_3fin": {
            "span_mm": float(ba_p[0]), "cr_mm": float(ba_p[1]), "ct_mm": float(ba_p[2]),
            "te_sweep_mm": float(ba_p[3]), "overhang_mm": float(ba_p[4]),
            "p_le": float(ba_p[5]), "p_te": float(ba_p[6]),
            "margin_cal": round(float(ba_r[0]), 2), "hang_time_s": round(float(ba_r[1]), 2),
            "apogee_m": round(float(ba_r[2]), 2), "fin_mass_g": round(float(ba_r[4]), 2)
        },
        "best_sym_4fin": {
            "span_mm": float(bs_p[0]), "cr_mm": float(bs_p[1]), "ct_mm": float(bs_p[2]),
            "te_sweep_mm": float(bs_p[3]), "overhang_mm": float(bs_p[4]),
            "p_le": float(bs_p[5]), "p_te": float(bs_p[6]),
            "margin_cal": round(float(bs_r[0]), 2), "hang_time_s": round(float(bs_r[1]), 2),
            "apogee_m": round(float(bs_r[2]), 2), "fin_mass_g": round(float(bs_r[4]), 2)
        }
    }
    with open("scratch/nonlinear_fin_optimization_full.json", "w", encoding="utf-8") as f:
        json.dump(out_dict, f, indent=2, ensure_ascii=False)
        
    print("\nSaved full results to scratch/nonlinear_fin_optimization_full.json")

if __name__ == "__main__":
    main()
