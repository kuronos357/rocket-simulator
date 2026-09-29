import sys
import os
sys.path.insert(0, os.path.abspath("."))
import math
import numpy as np
from sim_engine.motor_db import get_motor
from sim_engine.optimizer import RocketSpec, FinOptimizer

def evaluate_generalized_fins(
    opt: FinOptimizer,
    span_mm: float,
    cr_mm: float,
    taper_ratio: float,
    theta_deg: float, # Dihedral angle of the 2 side fins from horizontal (0=airplane, 30=120deg symmetric, 45=inverted Y)
    v_scale: float,   # Vertical fin scale factor (span_v = v_scale * span, cr_v = v_scale * cr)
    fin_thickness_mm: float = 0.4,
    root_offset_mm: float = 0.0,
    is_4fin: bool = False
):
    s = opt.spec
    D = s.body_diameter_mm
    R = D / 2.0
    rho = s.material_density
    theta_rad = math.radians(theta_deg)
    
    # 1. Side fins (2 fins)
    ct_mm = taper_ratio * cr_mm
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
    
    # 3-fin: 1 vertical fin. 4-fin: 2 vertical fins (top and bottom)
    num_v = 2.0 if is_4fin else 1.0
    num_total_fins = 2.0 + num_v
    
    # Barrowman normal force for vertical fin(s)
    cna_1v = k_body_v * (4.0 * 1.0 * (span_v / D)**2) / denom_v
    cna_v_total = num_v * cna_1v
    
    denom_cv = (cr_v + ct_v) if (cr_v + ct_v) > 0 else 1.0
    xf_v_from_le = ((cr_v - ct_v) / 3.0) * ((cr_v + 2.0 * ct_v) / denom_cv) + (1.0 / 6.0) * (cr_v + ct_v - (cr_v * ct_v) / denom_cv)
    cp_fin_v = (root_offset_mm + cr_v) - xf_v_from_le
    
    # Total fin area and mass
    total_fin_area_cm2 = 2.0 * area_1side_cm2 + num_v * area_1v_cm2
    fin_mass_g = total_fin_area_cm2 * (fin_thickness_mm * 0.1) * rho
    
    # Composite Fin CG
    if total_fin_area_cm2 > 0:
        z_fin_cg = (2.0 * area_1side_cm2 * z_fin_cg_h + num_v * area_1v_cm2 * z_fin_cg_v) / total_fin_area_cm2
    else:
        z_fin_cg = root_offset_mm
        
    # Pitch & Yaw Aerodynamic Forces
    # Side fins contribution:
    # Pitch: cos^2(theta) * cna_1pair
    # Yaw: sin^2(theta) * cna_1pair
    cos2_theta = math.cos(theta_rad)**2
    sin2_theta = math.sin(theta_rad)**2
    
    cna_pitch_fins = cos2_theta * cna_1pair_h
    cna_yaw_fins = sin2_theta * cna_1pair_h + cna_v_total
    
    cna_pitch = opt.cna_body_base + cna_pitch_fins
    cp_pitch = (opt.cna_body_base * opt.cp_body_base + cna_pitch_fins * cp_fin_h) / cna_pitch if cna_pitch > 0 else cp_fin_h
    
    # Yaw CP: weighted combination of side fins and vertical fin
    yaw_fins_moment = sin2_theta * cna_1pair_h * cp_fin_h + cna_v_total * cp_fin_v
    cna_yaw = opt.cna_body_base + cna_yaw_fins
    cp_yaw = (opt.cna_body_base * opt.cp_body_base + yaw_fins_moment) / cna_yaw if cna_yaw > 0 else cp_fin_v
    
    # 3D spatial effective:
    cna_eff = 0.5 * (cna_pitch + cna_yaw)
    cp_eff = (cna_pitch * cp_pitch + cna_yaw * cp_yaw) / (2.0 * cna_eff) if cna_eff > 0 else cp_pitch
    
    # Total Rocket CG
    total_launch_mass_g = opt.m_base_launch + fin_mass_g
    total_cg_mm = (opt.mom_base_launch + fin_mass_g * z_fin_cg) / total_launch_mass_g
    
    margin_pitch_cal = (total_cg_mm - cp_pitch) / D
    margin_yaw_cal = (total_cg_mm - cp_yaw) / D
    margin_eff_cal = min(margin_pitch_cal, margin_yaw_cal)
    
    # Flight Simulation
    S_ref = math.pi * (R * 1e-3)**2
    wet_area_m2 = (opt.wet_area_body_cm2 + total_fin_area_cm2 * 2.0) * 1e-4
    cd_interference = 0.005 * num_total_fins
    Cd = 0.0045 * (wet_area_m2 / S_ref) + 0.08 + cd_interference
    
    motor_obj = get_motor(opt.motor_id)
    avg_thrust = motor_obj.total_impulse / motor_obj.burn_time if motor_obj.burn_time > 0 else 5.0
    burn_t = motor_obj.burn_time
    m_avg_kg = (total_launch_mass_g - motor_obj.propellant_mass_g * 0.5) * 1e-3
    v_bo = max(0.0, (avg_thrust / m_avg_kg - 9.8) * burn_t)
    h_bo = 0.5 * v_bo * burn_t
    
    burnout_mass_g = total_launch_mass_g - motor_obj.propellant_mass_g
    k_drag = 0.5 * 1.225 * Cd * S_ref / (burnout_mass_g * 1e-3)
    
    if k_drag > 0 and v_bo > 0:
        h_coast = (1.0 / (2.0 * k_drag)) * math.log(1.0 + k_drag * v_bo**2 / 9.8)
        t_coast = (1.0 / math.sqrt(9.8 * k_drag)) * math.atan(v_bo * math.sqrt(k_drag / 9.8))
    else:
        h_coast = 0.0
        t_coast = 0.0
        
    apogee_m = h_bo + h_coast
    
    # Descent phase: Horizontal descent crossflow
    streamer_cd_A = s.recovery_cd * (s.recovery_area_cm2 * 1e-4) # m^2
    wet_body_m2 = opt.wet_area_body_cm2 * 1e-4
    body_cd_A = (1.1 / math.pi) * wet_body_m2
    
    # Projected fin area facing crossflow:
    # Side fins at dihedral angle theta: each has projected area A_h * cos(theta)
    # Vertical fin is aligned with crossflow: edge-on contribution ~ 0.15 of A_v
    proj_fins_m2 = (2.0 * area_1side_cm2 * math.cos(theta_rad) + 0.15 * num_v * area_1v_cm2) * 1e-4
    fins_cd_A = 1.25 * proj_fins_m2
    
    total_cd_A = streamer_cd_A + body_cd_A + fins_cd_A
    v_descent = math.sqrt((2.0 * (burnout_mass_g * 1e-3) * 9.8) / (1.225 * total_cd_A))
    t_descent = apogee_m / v_descent if v_descent > 0 else 0.0
    total_time_s = burn_t + t_coast + t_descent
    
    return {
        "span": span_mm,
        "cr": cr_mm,
        "theta": theta_deg,
        "v_scale": v_scale,
        "is_4fin": is_4fin,
        "fin_mass_g": fin_mass_g,
        "total_mass_g": total_launch_mass_g,
        "margin_pitch": margin_pitch_cal,
        "margin_yaw": margin_yaw_cal,
        "margin_eff": margin_eff_cal,
        "apogee_m": apogee_m,
        "total_time_s": total_time_s,
        "v_descent": v_descent
    }

spec = RocketSpec(
    total_length_mm=250.0,
    body_diameter_mm=24.0,
    nose_length_mm=60.0,
    tail_length_mm=0.0,
    wall_thickness_mm=0.4,
    infill_ratio=0.02,
    material="PLA",
    material_density=1.24,
    motor_type="1/2A6-2",
    recovery_mass_g=0.5,
    recovery_area_cm2=62.5,
    recovery_cd=0.25,
    descent_horizontal=True
)
opt = FinOptimizer(spec)

# Test search over theta and v_scale to find minimum fin mass for target_margin >= 1.20
print("\n--- Testing angles and vertical scales (Target Margin >= 1.20 cal) ---")
thetas = [0.0, 15.0, 30.0, 45.0]
v_scales = [0.5, 0.7, 0.85, 1.0]

for is_4fin in [False, True]:
    print(f"\nConfiguration: {'4-fin (+/x)' if is_4fin else '3-fin (side pair + vertical)'}")
    for th in thetas:
        for vs in v_scales:
            best_res = None
            best_time_res = None
            # Search span and cr
            for span in range(15, 60, 2):
                for cr in range(20, 80, 2):
                    if span > 1.5 * cr or span < 0.3 * cr:
                        continue
                    r = evaluate_generalized_fins(opt, span, cr, 0.0, th, vs, is_4fin=is_4fin)
                    if r["margin_eff"] >= 1.20:
                        if best_res is None or r["fin_mass_g"] < best_res["fin_mass_g"]:
                            best_res = r
                        if best_time_res is None or r["total_time_s"] > best_time_res["total_time_s"]:
                            best_time_res = r
            if best_res:
                print(f" theta={th:4.1f}°, v_scale={vs:3.2f} | MinMass: fin={best_res['fin_mass_g']:4.2f}g, span={best_res['span']:4.1f}, cr={best_res['cr']:4.1f} | P_mar={best_res['margin_pitch']:+4.2f}, Y_mar={best_res['margin_yaw']:+4.2f} | Apogee={best_res['apogee_m']:4.1f}m, Time={best_res['total_time_s']:5.2f}s | MaxTime: {best_time_res['total_time_s']:5.2f}s (fin={best_time_res['fin_mass_g']:4.2f}g)")
