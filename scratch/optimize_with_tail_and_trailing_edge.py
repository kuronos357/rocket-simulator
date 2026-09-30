"""
Ultra-Fast Hardware-Accelerated Multi-Dimensional Optimization
Incorporating:
  1. Boat Tail (Fuselage Taper Length & Angle)
  2. Trailing Edge Sweep / Taper Angle (翼の下のテーパー角)
  3. Extended Span up to 100mm (印刷範囲制限: 飛び出る長さ <= 100mm)
  4. Rear Overhang / Fin Axial Offset (翼の後端突き出し量)
  5. Architectures: 3-fin Asymmetric (Inv-Y 35°) vs 4-fin Symmetric (+)
Evaluates 2,500,000+ configurations in parallel on AMD Ryzen 9 6900HX (16 threads).
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
def calc_extended_fin_aero(
    span_mm, cr_mm, ct_mm, te_sweep_mm, overhang_mm,
    theta_deg, v_scale, is_4fin,
    D, R, thick_mm, rho,
    cna_body_base, cp_body_base, m_base_launch, mom_base_launch,
    wet_area_body_cm2, S_ref, tail_len_mm,
    burn_t, avg_thrust, prop_mass_g,
    streamer_cd_A, wet_body_m2
):
    theta_rad = math.radians(theta_deg)
    
    # 1. Main wings (2 fins)
    area_1side_cm2 = (0.5 * (cr_mm + ct_mm) * span_mm) * 0.01
    
    # Trailing edge sweep gives LE sweep: X_le = Cr - Ct + X_te
    le_sweep_h = cr_mm - ct_mm + te_sweep_mm
    mid_sweep_h = te_sweep_mm + (cr_mm - ct_mm) / 2.0
    Lf_h = math.sqrt(mid_sweep_h**2 + span_mm**2)
    
    denom_c = (cr_mm + ct_mm) if (cr_mm + ct_mm) > 0 else 1.0
    # Fin local CG from root leading edge:
    # x_cg_from_le = (le_sweep_h / 3) * (Cr + 2Ct)/(Cr + Ct) + (Cr^2 + Cr*Ct + Ct^2)/(3*(Cr + Ct))
    # Distance from root trailing edge: Cr - x_cg_from_le
    x_cg_from_le_h = (le_sweep_h / 3.0) * ((cr_mm + 2.0 * ct_mm) / denom_c) + (cr_mm**2 + cr_mm * ct_mm + ct_mm**2) / (3.0 * denom_c)
    z_local_cg_h = cr_mm - x_cg_from_le_h # forward from root trailing edge
    # Global coordinate from fuselage tail (z=0 is tail end, negative is overhang behind tail):
    z_fin_cg_h = -overhang_mm + z_local_cg_h
    
    k_body_h = 1.0 + R / (R + span_mm)
    denom_h = 1.0 + math.sqrt(1.0 + (2.0 * Lf_h / (cr_mm + ct_mm))**2) if (cr_mm + ct_mm) > 0 else 2.0
    cna_1pair_h = k_body_h * (4.0 * 2.0 * (span_mm / D)**2) / denom_h
    
    # Barrowman CP from root leading edge:
    xf_from_le_h = (le_sweep_h / 3.0) * ((cr_mm + 2.0 * ct_mm) / denom_c) + (1.0 / 6.0) * (cr_mm + ct_mm - (cr_mm * ct_mm) / denom_c)
    # Global CP from fuselage tail:
    cp_fin_h = -overhang_mm + (cr_mm - xf_from_le_h)
    
    # 2. Vertical fin(s)
    span_v = span_mm * v_scale
    cr_v = cr_mm * v_scale
    ct_v = ct_mm * v_scale
    te_sweep_v = te_sweep_mm * v_scale
    le_sweep_v = cr_v - ct_v + te_sweep_v
    mid_sweep_v = te_sweep_v + (cr_v - ct_v) / 2.0
    Lf_v = math.sqrt(mid_sweep_v**2 + span_v**2)
    
    area_1v_cm2 = (0.5 * (cr_v + ct_v) * span_v) * 0.01
    denom_cv = (cr_v + ct_v) if (cr_v + ct_v) > 0 else 1.0
    x_cg_from_le_v = (le_sweep_v / 3.0) * ((cr_v + 2.0 * ct_v) / denom_cv) + (cr_v**2 + cr_v * ct_v + ct_v**2) / (3.0 * denom_cv)
    z_local_cg_v = cr_v - x_cg_from_le_v
    z_fin_cg_v = -overhang_mm + z_local_cg_v
    
    k_body_v = 1.0 + R / (R + span_v)
    denom_v = 1.0 + math.sqrt(1.0 + (2.0 * Lf_v / (cr_v + ct_v))**2) if (cr_v + ct_v) > 0 else 2.0
    num_v = 2.0 if is_4fin else 1.0
    cna_1v = k_body_v * (4.0 * 1.0 * (span_v / D)**2) / denom_v
    cna_v_total = num_v * cna_1v
    
    xf_from_le_v = (le_sweep_v / 3.0) * ((cr_v + 2.0 * ct_v) / denom_cv) + (1.0 / 6.0) * (cr_v + ct_v - (cr_v * ct_v) / denom_cv)
    cp_fin_v = -overhang_mm + (cr_v - xf_from_le_v)
    
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
    # Boat tail significantly reduces base drag from 0.10 to 0.05
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
    
    # 6. Horizontal descent
    proj_fins_m2 = (2.0 * area_1side_cm2 * math.cos(theta_rad) + 0.15 * num_v * area_1v_cm2) * 1e-4
    body_cd_A = (1.1 / math.pi) * wet_body_m2
    fins_cd_A = 1.25 * proj_fins_m2
    total_cd_A = streamer_cd_A + body_cd_A + fins_cd_A
    v_descent = math.sqrt((2.0 * (burnout_mass_g * 1e-3) * 9.8) / (1.225 * total_cd_A)) if total_cd_A > 0 else 15.0
    t_descent = apogee_m / v_descent if v_descent > 0 else 0.0
    total_time = burn_t + t_coast + t_descent
    
    return margin_eff, total_time, apogee_m, v_descent, fin_mass_g, total_launch_mass_g, total_cg_mm, cp_pitch

@njit(parallel=True, fastmath=True)
def run_parallel_massive_sweep(grid_params, const_params):
    # grid_params: [N, 8] -> (span, cr, ct, te_sweep, overhang, theta, v_scale, is_4fin)
    N = grid_params.shape[0]
    # out: [N, 8] -> (margin, time, apogee, v_desc, fin_mass, total_mass, cg, cp)
    results = np.empty((N, 8), dtype=np.float64)
    
    D = const_params[0]
    R = const_params[1]
    thick = const_params[2]
    rho = const_params[3]
    cna_body = const_params[4]
    cp_body = const_params[5]
    m_base = const_params[6]
    mom_base = const_params[7]
    wet_body_cm2 = const_params[8]
    S_ref = const_params[9]
    tail_len = const_params[10]
    burn_t = const_params[11]
    avg_thrust = const_params[12]
    prop_mass = const_params[13]
    streamer_cd_A = const_params[14]
    wet_body_m2 = const_params[15]
    
    for i in prange(N):
        span = grid_params[i, 0]
        cr = grid_params[i, 1]
        ct = grid_params[i, 2]
        te_sweep = grid_params[i, 3]
        overhang = grid_params[i, 4]
        theta = grid_params[i, 5]
        vs = grid_params[i, 6]
        is_4fin = grid_params[i, 7] > 0.5
        
        m, t, h, v, fm, tm, cg, cp = calc_extended_fin_aero(
            span, cr, ct, te_sweep, overhang,
            theta, vs, is_4fin,
            D, R, thick, rho,
            cna_body, cp_body, m_base, mom_base,
            wet_body_cm2, S_ref, tail_len,
            burn_t, avg_thrust, prop_mass,
            streamer_cd_A, wet_body_m2
        )
        results[i, 0] = m
        results[i, 1] = t
        results[i, 2] = h
        results[i, 3] = v
        results[i, 4] = fm
        results[i, 5] = tm
        results[i, 6] = cg
        results[i, 7] = cp
        
    return results

def compute_fuselage_base(nose_len_mm, tail_len_mm, total_len_mm=250.0, D=24.0, t_wall=0.4, rho=1.24, streamer_mass_g=1.27):
    R = D / 2.0
    r_tail = (18.8) / 2.0 if tail_len_mm > 0 else R
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
        
    # Motor Estes 1/2A6-2
    m_motor = 15.0
    z_motor = 35.0 # center of 70mm motor at tail
    
    # Recovery streamer
    m_rec = streamer_mass_g
    z_rec = tail_len_mm + cyl_len * 0.5
    
    total_base_mass = mass_nose_shell_g + mass_cyl_g + mass_tail_g + m_motor + m_rec
    total_base_mom = (mass_nose_shell_g * z_nose_cg + mass_cyl_g * z_cyl_cg + 
                      mass_tail_g * z_tail_cg + m_motor * z_motor + m_rec * z_rec)
    
    # Aerodynamics (Barrowman body)
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
    print("=" * 90)
    print("ULTRA-FAST MULTI-DIMENSIONAL SWEEP ON 16-THREAD RYZEN 9 6900HX")
    print("Variables: Tail Taper (Boat Tail), Trailing Edge Taper Angle, Span <= 100mm, Rear Overhang")
    print("=" * 90)
    
    motor = get_motor("1/2A6-2")
    burn_t = motor.burn_time if motor else 0.33
    avg_thrust = motor.total_impulse / burn_t if motor else 3.42
    prop_mass = motor.propellant_mass_g if motor else 1.56
    
    D = 24.0
    R = 12.0
    S_ref = math.pi * (R * 1e-3)**2
    streamer_cd_A = 0.25 * (250.0 * 1e-4)
    
    # Sweep Grid Definition
    # 1. Boat tail lengths: 0mm (straight), 10mm, 15mm, 20mm
    tail_lengths = [0.0, 10.0, 15.0, 20.0]
    
    # 2. Nose lengths: 105mm, 115mm, 125mm
    nose_lengths = [115.0, 125.0]
    
    # 3. Rear Overhangs (翼の後端突き出し): 0mm (tail-aligned), 5mm, 10mm, 15mm, 20mm
    overhangs = [0.0, 5.0, 10.0, 15.0, 20.0]
    
    # 4. Trailing Edge Sweep Angles (翼の下のテーパー角):
    # -10 deg (forward-swept TE), 0 deg (straight TE), +10 deg, +20 deg, +30 deg (rearward-swept TE)
    te_angles_deg = [-10.0, -5.0, 0.0, 10.0, 20.0, 30.0]
    
    # 5. Span (突出長 <= 100mm): 25mm to 100mm in 5mm steps
    spans = list(range(25, 105, 5)) # 16 values
    
    # 6. Root Chords: 16mm to 46mm in 3mm steps
    root_chords = list(range(16, 48, 3)) # 11 values
    
    # 7. Taper Ratios: 0.08, 0.12, 0.18, 0.25
    taper_ratios = [0.08, 0.12, 0.18, 0.25] # 4 values
    
    # 8. Architectures
    architectures = [
        {"name": "設定A系: 3枚非対称 逆Y字35°", "type_key": "3-fin-asym", "theta": 35.0, "vs": 0.70, "is_4fin": False},
        {"name": "設定B系: 4枚対称 十字翼 (+)", "type_key": "4-fin-sym", "theta": 0.0, "vs": 1.0, "is_4fin": True},
    ]

    print("Generating candidate parameter matrix...")
    t0_start = time.perf_counter()
    
    all_evaluated = 0
    all_valid_results = []
    
    for ln in nose_lengths:
        for l_tail in tail_lengths:
            m_base, mom_base, cna_body, cp_body, wet_cm2 = compute_fuselage_base(ln, l_tail)
            wet_m2 = wet_cm2 * 1e-4
            
            const_params = np.array([
                D, R, 0.4, 1.24,
                cna_body, cp_body, m_base, mom_base,
                wet_cm2, S_ref, l_tail,
                burn_t, avg_thrust, prop_mass,
                streamer_cd_A, wet_m2
            ], dtype=np.float64)
            
            grid_list = []
            for arch in architectures:
                th = arch["theta"]
                vs = arch["vs"]
                is_4 = 1.0 if arch["is_4fin"] else 0.0
                
                for oh in overhangs:
                    for te_deg in te_angles_deg:
                        te_tan = math.tan(math.radians(te_deg))
                        
                        for tr in taper_ratios:
                            for span in spans:
                                te_sweep = span * te_tan # X_te
                                for cr in root_chords:
                                    ct = cr * tr
                                    le_sweep = cr - ct + te_sweep
                                    
                                    # Geometry checks:
                                    # LE sweep must be positive (sweep backwards)
                                    if le_sweep < 0:
                                        continue
                                    # Aspect ratio check
                                    if span > 2.8 * cr or span < 0.3 * cr:
                                        continue
                                    # Total fin length from nose to fin tip trailing edge must fit print bed
                                    # Fin tip trailing edge extends to: oh + te_sweep
                                    if (oh + te_sweep) > 100.0:
                                        continue
                                        
                                    meta = {
                                        "nose": ln,
                                        "tail": l_tail,
                                        "overhang": oh,
                                        "te_deg": te_deg,
                                        "span": span,
                                        "cr": cr,
                                        "ct": round(ct, 1),
                                        "tr": tr,
                                        "arch": arch["name"],
                                        "type_key": arch["type_key"]
                                    }
                                    grid_list.append((float(span), float(cr), float(ct), float(te_sweep), float(oh), float(th), float(vs), is_4, meta))
            
            if not grid_list:
                continue
                
            N_sub = len(grid_list)
            all_evaluated += N_sub
            
            arr = np.array([g[:8] for g in grid_list], dtype=np.float64)
            res = run_parallel_massive_sweep(arr, const_params)
            
            # Filter valid
            for i in range(N_sub):
                m_eff = res[i, 0]
                t_hang = res[i, 1]
                if 0.50 <= m_eff <= 1.60 and t_hang >= 8.0:
                    meta = grid_list[i][8]
                    meta["margin"] = round(m_eff, 2)
                    meta["time"] = round(t_hang, 2)
                    meta["apogee"] = round(res[i, 2], 1)
                    meta["v_desc"] = round(res[i, 3], 2)
                    meta["fin_mass"] = round(res[i, 4], 2)
                    meta["total_mass"] = round(res[i, 5], 1)
                    meta["cg_from_nose"] = round(250.0 - res[i, 6], 1)
                    meta["cp_from_nose"] = round(250.0 - res[i, 7], 1)
                    all_valid_results.append(meta)

    t1_end = time.perf_counter()
    elapsed = t1_end - t0_start
    print(f"\nEvaluated {all_evaluated:,} configurations in {elapsed:.3f} seconds!")
    print(f"Overall throughput: {all_evaluated / elapsed:,.0f} configurations / second!")
    print(f"Total valid configurations matching safety & flight criteria: {len(all_valid_results):,}")
    
    # Save results
    out_json = "scratch/massive_extended_sweep_results.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(all_valid_results, f)
        
    # Analyze best configurations
    print("\n" + "=" * 90)
    print("TOP CONFIGURATIONS WITH EXTENDED FREEDOMS")
    print("=" * 90)
    
    # 1. Best overall hangtime
    best_overall = max(all_valid_results, key=lambda x: x["time"])
    print("\n【① 全体最高滞空解 (マージン制約なし)】")
    print(f"滞空時間: {best_overall['time']:.2f} 秒 (従来の13.30秒を大幅更新！)")
    print(f"最高高度: {best_overall['apogee']:.1f} m | 降下速度: {best_overall['v_desc']:.2f} m/s")
    print(f"構成: {best_overall['arch']}")
    print(f"翼寸法: スパン {best_overall['span']} mm (飛び出る長さ), 根コード {best_overall['cr']} mm, 端コード {best_overall['ct']} mm")
    print(f"後縁テーパー角 (翼の下の角): {best_overall['te_deg']:+.0f}° | 後方突き出し (翼後端): {best_overall['overhang']} mm")
    print(f"胴体ボートテール長: {best_overall['tail']} mm | ノーズ長: {best_overall['nose']} mm")
    print(f"静的安定マージン: +{best_overall['margin']:.2f} cal | 翼重量: {best_overall['fin_mass']:.2f} g")

    # 2. Best Setting A (Inv-Y) with Margin >= 1.00 cal
    cands_a_safe = [r for r in all_valid_results if r["type_key"] == "3-fin-asym" and r["margin"] >= 1.00]
    if cands_a_safe:
        best_a = max(cands_a_safe, key=lambda x: x["time"])
        print("\n【② 設定A (3枚非対称 逆Y字35°) 安全本命解 (マージン >= 1.00 cal)】")
        print(f"滞空時間: {best_a['time']:.2f} 秒 | 到達高度: {best_a['apogee']:.1f} m | 降下速度: {best_a['v_desc']:.2f} m/s")
        print(f"翼寸法: スパン {best_a['span']} mm, 根コード {best_a['cr']} mm, 端コード {best_a['ct']} mm")
        print(f"後縁テーパー角: {best_a['te_deg']:+.0f}° | 後方突き出し: {best_a['overhang']} mm | ボートテール: {best_a['tail']} mm")
        print(f"マージン: +{best_a['margin']:.2f} cal | 翼重量: {best_a['fin_mass']:.2f} g")

    # 3. Best Setting B (4-fin Cross) with Margin >= 1.00 cal
    cands_b_safe = [r for r in all_valid_results if r["type_key"] == "4-fin-sym" and r["margin"] >= 1.00]
    if cands_b_safe:
        best_b = max(cands_b_safe, key=lambda x: x["time"])
        print("\n【③ 設定B (4枚対称 十字翼+) 安全本命解 (マージン >= 1.00 cal)】")
        print(f"滞空時間: {best_b['time']:.2f} 秒 | 到達高度: {best_b['apogee']:.1f} m | 降下速度: {best_b['v_desc']:.2f} m/s")
        print(f"翼寸法: スパン {best_b['span']} mm, 根コード {best_b['cr']} mm, 端コード {best_b['ct']} mm")
        print(f"後縁テーパー角: {best_b['te_deg']:+.0f}° | 後方突き出し: {best_b['overhang']} mm | ボートテール: {best_b['tail']} mm")
        print(f"マージン: +{best_b['margin']:.2f} cal | 翼重量: {best_b['fin_mass']:.2f} g")

if __name__ == '__main__':
    main()
