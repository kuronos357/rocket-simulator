"""
Benchmark Parallel Acceleration: Pure Python vs Multiprocessing (16-core) vs Numba JIT (16-thread)
Running on AMD Ryzen 9 6900HX (8 cores / 16 threads).
"""

import sys
import os
import time
import math
import numpy as np
from multiprocessing import Pool, cpu_count
from numba import njit, prange

sys.path.insert(0, os.path.abspath("."))
from sim_engine.optimizer import RocketSpec, FinOptimizer

# Numba compiled single-fin evaluation
@njit(fastmath=True)
def numba_eval_single(
    span_mm, cr_mm, ct_mm, theta_deg, v_scale, is_4fin,
    D, R, root_offset_mm, fin_thickness_mm, rho,
    cna_body_base, cp_body_base, m_base_launch, mom_base_launch,
    wet_area_body_cm2, S_ref, tail_len, burn_t, avg_thrust, prop_mass_g,
    streamer_cd_A, wet_body_m2
):
    theta_rad = math.radians(theta_deg)
    
    # 1. Horizontal / main fins (2 fins)
    area_1side_cm2 = (0.5 * (cr_mm + ct_mm) * span_mm) * 0.01
    denom_cg = 3.0 * (cr_mm + ct_mm) if (cr_mm + ct_mm) > 0 else 1.0
    z_fin_local_cg_h = (cr_mm**2 + cr_mm * ct_mm + ct_mm**2) / denom_cg
    z_fin_cg_h = root_offset_mm + z_fin_local_cg_h
    
    sweep_h = cr_mm - ct_mm
    mid_sweep_h = sweep_h + (ct_mm - cr_mm) / 2.0
    Lf_h = math.sqrt(mid_sweep_h**2 + span_mm**2)
    k_body_h = 1.0 + R / (R + span_mm)
    denom_h = 1.0 + math.sqrt(1.0 + (2.0 * Lf_h / (cr_mm + ct_mm))**2) if (cr_mm + ct_mm) > 0 else 2.0
    cna_1pair_h = k_body_h * (4.0 * 2.0 * (span_mm / D)**2) / denom_h
    
    denom_c = (cr_mm + ct_mm) if (cr_mm + ct_mm) > 0 else 1.0
    xf_h_from_le = ((cr_mm - ct_mm) / 3.0) * ((cr_mm + 2.0 * ct_mm) / denom_c) + (1.0 / 6.0) * (cr_mm + ct_mm - (cr_mm * ct_mm) / denom_c)
    cp_fin_h = (root_offset_mm + cr_mm) - xf_h_from_le
    
    # 2. Vertical fin(s)
    span_v = span_mm * v_scale
    cr_v = cr_mm * v_scale
    ct_v = ct_mm * v_scale
    area_1v_cm2 = (0.5 * (cr_v + ct_v) * span_v) * 0.01
    z_fin_local_cg_v = (cr_v**2 + cr_v * ct_v + ct_v**2) / (3.0 * (cr_v + ct_v)) if (cr_v + ct_v) > 0 else 0.0
    z_fin_cg_v = root_offset_mm + z_fin_local_cg_v
    
    k_body_v = 1.0 + R / (R + span_v)
    mid_sweep_v = (cr_v - ct_v) + (ct_v - cr_v) / 2.0
    Lf_v = math.sqrt(mid_sweep_v**2 + span_v**2)
    denom_v = 1.0 + math.sqrt(1.0 + (2.0 * Lf_v / (cr_v + ct_v))**2) if (cr_v + ct_v) > 0 else 2.0
    
    num_v = 2.0 if is_4fin else 1.0
    cna_1v = k_body_v * (4.0 * 1.0 * (span_v / D)**2) / denom_v
    cna_v_total = num_v * cna_1v
    denom_cv = (cr_v + ct_v) if (cr_v + ct_v) > 0 else 1.0
    xf_v_from_le = ((cr_v - ct_v) / 3.0) * ((cr_v + 2.0 * ct_v) / denom_cv) + (1.0 / 6.0) * (cr_v + ct_v - (cr_v * ct_v) / denom_cv)
    cp_fin_v = (root_offset_mm + cr_v) - xf_v_from_le
    
    # Fin mass & CG
    total_fin_area_cm2 = 2.0 * area_1side_cm2 + num_v * area_1v_cm2
    fin_mass_g = total_fin_area_cm2 * (fin_thickness_mm * 0.1) * rho
    z_fin_cg = (2.0 * area_1side_cm2 * z_fin_cg_h + num_v * area_1v_cm2 * z_fin_cg_v) / total_fin_area_cm2 if total_fin_area_cm2 > 0 else root_offset_mm
    
    # Barrowman forces
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
    
    # Flight trajectory (apogee & descent)
    wet_area_m2 = (wet_area_body_cm2 + total_fin_area_cm2 * 2.0) * 1e-4
    cd_interference = 0.005 * (2.0 + num_v)
    Cd = 0.0045 * (wet_area_m2 / S_ref) + (0.05 if tail_len > 0 else 0.10) + 0.08 + cd_interference
    
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
    
    # Horizontal descent
    proj_fins_m2 = (2.0 * area_1side_cm2 * math.cos(theta_rad) + 0.15 * num_v * area_1v_cm2) * 1e-4
    body_cd_A = (1.1 / math.pi) * wet_body_m2
    fins_cd_A = 1.25 * proj_fins_m2
    total_cd_A = streamer_cd_A + body_cd_A + fins_cd_A
    v_descent = math.sqrt((2.0 * (burnout_mass_g * 1e-3) * 9.8) / (1.225 * total_cd_A)) if total_cd_A > 0 else 15.0
    t_descent = apogee_m / v_descent if v_descent > 0 else 0.0
    total_time = burn_t + t_coast + t_descent
    
    return margin_eff, total_time, apogee_m, v_descent, fin_mass_g

@njit(parallel=True, fastmath=True)
def numba_batch_eval(grid_params, const_params):
    # grid_params: [N, 6] -> (span, cr, ct, theta, v_scale, is_4fin)
    N = grid_params.shape[0]
    results = np.empty((N, 5), dtype=np.float64) # margin, time, apogee, v_desc, mass
    
    D = const_params[0]
    R = const_params[1]
    root_offset = const_params[2]
    thick = const_params[3]
    rho = const_params[4]
    cna_body = const_params[5]
    cp_body = const_params[6]
    m_base = const_params[7]
    mom_base = const_params[8]
    wet_body_cm2 = const_params[9]
    S_ref = const_params[10]
    tail_len = const_params[11]
    burn_t = const_params[12]
    avg_thrust = const_params[13]
    prop_mass = const_params[14]
    streamer_cd_A = const_params[15]
    wet_body_m2 = const_params[16]
    
    for i in prange(N):
        span = grid_params[i, 0]
        cr = grid_params[i, 1]
        ct = grid_params[i, 2]
        theta = grid_params[i, 3]
        vs = grid_params[i, 4]
        is_4fin = grid_params[i, 5] > 0.5
        
        m, t, h, v, f_mass = numba_eval_single(
            span, cr, ct, theta, vs, is_4fin,
            D, R, root_offset, thick, rho,
            cna_body, cp_body, m_base, mom_base,
            wet_body_cm2, S_ref, tail_len, burn_t, avg_thrust, prop_mass,
            streamer_cd_A, wet_body_m2
        )
        results[i, 0] = m
        results[i, 1] = t
        results[i, 2] = h
        results[i, 3] = v
        results[i, 4] = f_mass
        
    return results

def run_pure_python_worker(args):
    opt, span, cr, tr, theta, vs, is_4fin = args
    return opt.evaluate_fins(span_mm=span, cr_mm=cr, shape_type="trapezoid", taper_ratio=tr, fin_thickness_mm=0.4, theta_deg=theta, v_scale=vs, is_4fin=is_4fin)

def main():
    print("=" * 80)
    print(f"BENCHMARK: MULTI-CORE HARDWARE ACCELERATION on {cpu_count()}-Thread Ryzen 9 6900HX")
    print("=" * 80)
    
    # Setup base spec (Nose 125mm, 50x500mm Streamer)
    spec = RocketSpec(
        total_length_mm=250.0,
        body_diameter_mm=24.0,
        nose_length_mm=125.0,
        nose_shape_n=0.75,
        tail_length_mm=0.0,
        wall_thickness_mm=0.4,
        infill_ratio=0.02,
        material="PLA",
        material_density=1.24,
        motor_type="1/2A6-2",
        ballast_mass_g=0.0,
        ballast_z_mm=245.0,
        recovery_mass_g=1.27,
        recovery_area_cm2=250.0,
        recovery_cd=0.25,
        descent_horizontal=True
    )
    opt = FinOptimizer(spec)
    
    # Generate 50,000 parameter combinations
    spans = np.linspace(20.0, 75.0, 50)
    crs = np.linspace(16.0, 50.0, 40)
    trs = [0.08, 0.12, 0.18, 0.25]
    thetas = [0.0, 35.0]
    
    grid = []
    for span in spans:
        for cr in crs:
            for tr in trs:
                for th in thetas:
                    vs = 0.70 if th > 0 else 1.0
                    is_4 = th == 0.0
                    grid.append((float(span), float(cr), float(tr * cr), float(th), float(vs), 1.0 if is_4 else 0.0))
                    
    grid_arr = np.array(grid, dtype=np.float64)
    N = len(grid_arr)
    print(f"Generated test dataset: {N:,} wing configurations.\n")
    
    # Constant parameters for Numba
    D = 24.0
    R = 12.0
    S_ref = math.pi * (R * 1e-3)**2
    const_params = np.array([
        D, R, 0.0, 0.4, 1.24,
        opt.cna_body_base, opt.cp_body_base, opt.m_base_launch, opt.mom_base_launch,
        opt.wet_area_body_cm2, S_ref, 0.0,
        0.33, 3.79, 3.12,
        0.25 * (250.0 * 1e-4), opt.wet_area_body_cm2 * 1e-4
    ], dtype=np.float64)
    
    # -------------------------------------------------------------
    # 1. Numba JIT (16-Thread Parallel)
    # -------------------------------------------------------------
    print("Testing Method 1: Numba JIT + 16-Thread Parallel (prange)...")
    # Warmup / JIT compilation
    _ = numba_batch_eval(grid_arr[:100], const_params)
    
    t0 = time.perf_counter()
    numba_res = numba_batch_eval(grid_arr, const_params)
    t_numba = time.perf_counter() - t0
    print(f"-> Numba 16-thread time: {t_numba * 1000.0:.2f} ms ({t_numba:.4f} s)")
    print(f"-> Speed: {N / t_numba:,.0f} configurations / second!")
    
    # -------------------------------------------------------------
    # 2. Pure Python Single-Thread (Sample 2,000 for timing projection)
    # -------------------------------------------------------------
    print("\nTesting Method 2: Pure Python Single-Thread (Baseline)...")
    sample_size = 2000
    t0 = time.perf_counter()
    for i in range(sample_size):
        s, c, ct, th, vs, is4 = grid[i]
        tr = ct / c if c > 0 else 0.1
        _ = opt.evaluate_fins(span_mm=s, cr_mm=c, shape_type="trapezoid", taper_ratio=tr, fin_thickness_mm=0.4, theta_deg=th, v_scale=vs, is_4fin=(is4 > 0.5))
    t_sample = time.perf_counter() - t0
    t_single_proj = t_sample * (N / sample_size)
    print(f"-> Single-thread sample time: {t_sample:.3f} s (for {sample_size:,} evals)")
    print(f"-> Projected time for full {N:,} evals: {t_single_proj:.2f} s")
    
    # -------------------------------------------------------------
    # 3. Multiprocessing Pool (16 workers)
    # -------------------------------------------------------------
    print(f"\nTesting Method 3: Python Multiprocessing Pool ({cpu_count()} parallel processes)...")
    tasks = []
    for i in range(sample_size * 2): # 4000 items
        s, c, ct, th, vs, is4 = grid[i]
        tr = ct / c if c > 0 else 0.1
        tasks.append((opt, s, c, tr, th, vs, (is4 > 0.5)))
        
    t0 = time.perf_counter()
    with Pool(processes=cpu_count()) as pool:
        _ = pool.map(run_pure_python_worker, tasks, chunksize=100)
    t_mp = time.perf_counter() - t0
    t_mp_proj = t_mp * (N / (sample_size * 2))
    print(f"-> 16-Process sample time: {t_mp:.3f} s (for {sample_size * 2:,} evals)")
    print(f"-> Projected time for full {N:,} evals: {t_mp_proj:.2f} s")
    
    # Summary Table
    print("\n" + "=" * 80)
    print(f"SUMMARY: 50,000 WING OPTIMIZATION BENCHMARK ON RYZEN 9 6900HX")
    print("=" * 80)
    print(f"  1. 従来 (Python 1スレッド)      : 約 {t_single_proj:.2f} 秒 (基準 1.0x)")
    print(f"  2. Multiprocessing (16プロセス): 約 {t_mp_proj:.2f} 秒 ({t_single_proj / t_mp_proj:.1f}x 高速化)")
    print(f"  3. Numba JIT (16スレッド並列)  : 約 {t_numba * 1000.0:.1f} ミリ秒 ({t_single_proj / t_numba:,.0f}x 爆速化！)")
    print("=" * 80)

if __name__ == '__main__':
    main()
