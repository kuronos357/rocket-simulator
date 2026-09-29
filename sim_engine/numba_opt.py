"""
Numba-accelerated Aerodynamic and Geometry Optimizer for Rocket Fins
Vectorized and JIT-compiled for sub-millisecond evaluation of fin dimensions,
dihedral angles (theta), and vertical fin scaling (v_scale).
"""

import math
from numba import njit
import numpy as np

@njit(cache=True)
def evaluate_fin_aero_fast(
    span_mm: float, 
    cr_mm: float, 
    ct_mm: float,
    body_diameter_mm: float,
    root_offset_mm: float,
    theta_deg: float,
    v_scale: float,
    is_4fin: bool,
    fin_thickness_mm: float,
    rho: float,
    cna_body_base: float,
    cp_body_base: float,
    m_base_launch: float,
    mom_base_launch: float
) -> tuple:
    """
    Physically rigorous, unified evaluation of fin aerodynamics, mass, CG, and stability.
    Supports continuous dihedral angle theta_deg and vertical fin scaling v_scale.
    """
    D = body_diameter_mm
    R = D / 2.0
    theta_rad = math.radians(theta_deg)
    
    # 1. Side fins (2 fins at +/- theta from horizontal)
    area_1side_cm2 = (0.5 * (cr_mm + ct_mm) * span_mm) * 0.01
    denom_cg = 3.0 * (cr_mm + ct_mm) if (cr_mm + ct_mm) > 0 else 1.0
    # Correct chordwise centroid formula for trapezoid with flush trailing edge
    z_fin_local_cg_h = (cr_mm**2 + cr_mm * ct_mm + ct_mm**2) / denom_cg
    z_fin_cg_h = root_offset_mm + z_fin_local_cg_h
    
    sweep_h = cr_mm - ct_mm
    mid_sweep_h = sweep_h + (ct_mm - cr_mm) / 2.0
    Lf_h = math.sqrt(mid_sweep_h**2 + span_mm**2)
    k_body_h = 1.0 + R / (R + span_mm)
    denom_h = 1.0 + math.sqrt(1.0 + (2.0 * Lf_h / (cr_mm + ct_mm))**2) if (cr_mm + ct_mm) > 0 else 2.0
    # Barrowman normal force derivative for 1 opposing pair (2 fins)
    cna_1pair_h = k_body_h * (4.0 * 2.0 * (span_mm / D)**2) / denom_h
    
    denom_c = (cr_mm + ct_mm) if (cr_mm + ct_mm) > 0 else 1.0
    xf_h_from_le = ((cr_mm - ct_mm) / 3.0) * ((cr_mm + 2.0 * ct_mm) / denom_c) + (1.0 / 6.0) * (cr_mm + ct_mm - (cr_mm * ct_mm) / denom_c)
    cp_fin_h = (root_offset_mm + cr_mm) - xf_h_from_le
    
    # 2. Vertical fin(s) (1 fin at 90 deg for 3-fin; 2 fins at +/-90 deg for 4-fin)
    span_v = span_mm * v_scale
    cr_v = cr_mm * v_scale
    ct_v = ct_mm * v_scale
    area_1v_cm2 = (0.5 * (cr_v + ct_v) * span_v) * 0.01
    denom_cg_v = 3.0 * (cr_v + ct_v) if (cr_v + ct_v) > 0 else 1.0
    z_fin_local_cg_v = (cr_v**2 + cr_v * ct_v + ct_v**2) / denom_cg_v if (cr_v + ct_v) > 0 else 0.0
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
    
    # Total Fin Area & Mass
    total_fin_area_cm2 = 2.0 * area_1side_cm2 + num_v * area_1v_cm2
    fin_mass_g = total_fin_area_cm2 * (fin_thickness_mm * 0.1) * rho
    
    if total_fin_area_cm2 > 0:
        z_fin_cg = (2.0 * area_1side_cm2 * z_fin_cg_h + num_v * area_1v_cm2 * z_fin_cg_v) / total_fin_area_cm2
    else:
        z_fin_cg = root_offset_mm
        
    # Pitch & Yaw Aerodynamic Normal Forces (Barrowman-consistent)
    # Side fins at angle +/- theta contribute cos^2(theta) to pitch and sin^2(theta) to yaw
    cos2_theta = math.cos(theta_rad)**2
    sin2_theta = math.sin(theta_rad)**2
    
    cna_pitch_fins = cos2_theta * cna_1pair_h
    cna_yaw_fins = sin2_theta * cna_1pair_h + cna_v_total
    
    cna_pitch = cna_body_base + cna_pitch_fins
    cp_pitch = (cna_body_base * cp_body_base + cna_pitch_fins * cp_fin_h) / cna_pitch if cna_pitch > 0 else cp_fin_h
    
    yaw_fins_moment = sin2_theta * cna_1pair_h * cp_fin_h + cna_v_total * cp_fin_v
    cna_yaw = cna_body_base + cna_yaw_fins
    cp_yaw = (cna_body_base * cp_body_base + yaw_fins_moment) / cna_yaw if cna_yaw > 0 else cp_fin_v
    
    # Total Rocket CG
    total_launch_mass_g = m_base_launch + fin_mass_g
    total_cg_mm = (mom_base_launch + fin_mass_g * z_fin_cg) / total_launch_mass_g
    
    margin_pitch_cal = (total_cg_mm - cp_pitch) / D
    margin_yaw_cal = (total_cg_mm - cp_yaw) / D
    margin_eff_cal = min(margin_pitch_cal, margin_yaw_cal)
    
    return (fin_mass_g, z_fin_cg, margin_eff_cal, margin_pitch_cal, margin_yaw_cal, cp_pitch, cp_yaw, total_fin_area_cm2)


@njit(cache=True)
def _fast_generalized_search(
    min_span: float, max_span: float, step: float,
    min_cr: float, max_cr: float,
    taper_ratios: np.ndarray,
    thetas_deg: np.ndarray,
    v_scales: np.ndarray,
    is_4fin: bool,
    target_margin_cal: float,
    body_diameter_mm: float,
    root_offset_mm: float,
    fin_thickness_mm: float,
    rho: float,
    cna_body_base: float,
    cp_body_base: float,
    m_base_launch: float,
    mom_base_launch: float
) -> tuple:
    best_mass = 999999.0
    best_res = (-1.0, -1.0, -1.0, -1.0, -1.0)
    
    for tr in taper_ratios:
        for th in thetas_deg:
            for vs in v_scales:
                span = min_span
                while span <= max_span:
                    cr = min_cr
                    while cr <= max_cr:
                        # Aspect ratio / flutter constraint: 0.3 <= span/cr <= 1.5
                        if span > 1.5 * cr or span < 0.3 * cr:
                            cr += step
                            continue
                            
                        ct = cr * tr
                        res = evaluate_fin_aero_fast(
                            span, cr, ct,
                            body_diameter_mm, root_offset_mm,
                            th, vs, is_4fin,
                            fin_thickness_mm, rho,
                            cna_body_base, cp_body_base,
                            m_base_launch, mom_base_launch
                        )
                        fin_mass_g = res[0]
                        margin_eff = res[2]
                        
                        if margin_eff >= target_margin_cal:
                            if fin_mass_g < best_mass:
                                best_mass = fin_mass_g
                                best_res = (span, cr, tr, th, vs)
                        cr += step
                    span += step
                    
    return (best_res[0], best_res[1], best_res[2], best_res[3], best_res[4], best_mass)


# Legacy wrapper for backwards compatibility
@njit(cache=True)
def _fast_2d_search(
    min_span: float, max_span: float, step: float,
    min_cr: float, max_cr: float,
    taper_ratios: np.ndarray,
    target_margin_cal: float,
    body_diameter_mm: float,
    root_offset_mm: float,
    fin_thickness_mm: float,
    rho: float,
    cna_body_base: float,
    cp_body_base: float,
    arrangement_int: int,
    m_base_launch: float,
    mom_base_launch: float
) -> tuple:
    if arrangement_int == 0:
        # airplane 3-fin: theta=0, v_scale=0.85, 3-fin
        thetas = np.array([0.0], dtype=np.float64)
        v_scales = np.array([0.85], dtype=np.float64)
        is_4fin = False
    elif arrangement_int == 4:
        # symmetric 4-fin: theta=0, v_scale=1.0, 4-fin
        thetas = np.array([0.0], dtype=np.float64)
        v_scales = np.array([1.0], dtype=np.float64)
        is_4fin = True
    else:
        # symmetric 3-fin: theta=30, v_scale=1.0, 3-fin
        thetas = np.array([30.0], dtype=np.float64)
        v_scales = np.array([1.0], dtype=np.float64)
        is_4fin = False
        
    res = _fast_generalized_search(
        min_span, max_span, step,
        min_cr, max_cr,
        taper_ratios,
        thetas,
        v_scales,
        is_4fin,
        target_margin_cal,
        body_diameter_mm,
        root_offset_mm,
        fin_thickness_mm,
        rho,
        cna_body_base,
        cp_body_base,
        m_base_launch,
        mom_base_launch
    )
    return (res[0], res[1], res[2])
