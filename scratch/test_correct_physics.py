import sys
import os
sys.path.insert(0, os.path.abspath("."))
import math
from sim_engine.motor_db import get_motor
from sim_engine.optimizer import RocketSpec, FinOptimizer

def evaluate_physically_correct_fins(
    opt: FinOptimizer,
    span_mm: float,
    cr_mm: float,
    taper_ratio: float,
    theta_deg: float, # Dihedral angle of side fins from horizontal (0=airplane, 30=120deg symmetric)
    v_scale: float,   # Vertical fin scale factor
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
    
    num_v = 2.0 if is_4fin else 1.0
    num_total_fins = 2.0 + num_v
    
    # Barrowman normal force for vertical fin(s)
    cna_1v = k_body_v * (4.0 * 1.0 * (span_v / D)**2) / denom_v
    cna_v_total = num_v * cna_1v
    
    denom_cv = (cr_v + ct_v) if (cr_v + ct_v) > 0 else 1.0
    xf_v_from_le = ((cr_v - ct_v) / 3.0) * ((cr_v + 2.0 * ct_v) / denom_cv) + (1.0 / 6.0) * (cr_v + ct_v - (cr_v * ct_v) / denom_cv)
    cp_fin_v = (root_offset_mm + cr_v) - xf_v_from_le
    
    total_fin_area_cm2 = 2.0 * area_1side_cm2 + num_v * area_1v_cm2
    fin_mass_g = total_fin_area_cm2 * (fin_thickness_mm * 0.1) * rho
    
    if total_fin_area_cm2 > 0:
        z_fin_cg = (2.0 * area_1side_cm2 * z_fin_cg_h + num_v * area_1v_cm2 * z_fin_cg_v) / total_fin_area_cm2
    else:
        z_fin_cg = root_offset_mm
        
    # Pitch & Yaw Aerodynamic Forces
    cos2_theta = math.cos(theta_rad)**2
    sin2_theta = math.sin(theta_rad)**2
    
    cna_pitch_fins = cos2_theta * cna_1pair_h
    cna_yaw_fins = sin2_theta * cna_1pair_h + cna_v_total
    
    cna_pitch = opt.cna_body_base + cna_pitch_fins
    cp_pitch = (opt.cna_body_base * opt.cp_body_base + cna_pitch_fins * cp_fin_h) / cna_pitch if cna_pitch > 0 else cp_fin_h
    
    yaw_fins_moment = sin2_theta * cna_1pair_h * cp_fin_h + cna_v_total * cp_fin_v
    cna_yaw = opt.cna_body_base + cna_yaw_fins
    cp_yaw = (opt.cna_body_base * opt.cp_body_base + yaw_fins_moment) / cna_yaw if cna_yaw > 0 else cp_fin_v
    
    total_launch_mass_g = opt.m_base_launch + fin_mass_g
    total_cg_mm = (opt.mom_base_launch + fin_mass_g * z_fin_cg) / total_launch_mass_g
    
    margin_pitch_cal = (total_cg_mm - cp_pitch) / D
    margin_yaw_cal = (total_cg_mm - cp_yaw) / D
    margin_eff_cal = min(margin_pitch_cal, margin_yaw_cal)
    
    if margin_eff_cal < 0.50:
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
            "apogee_m": 0.0,
            "total_time_s": 0.0,
            "v_descent": 0.0
        }
    
    # Flight Simulation
    S_ref = math.pi * (R * 1e-3)**2
    wet_area_m2 = (opt.wet_area_body_cm2 + total_fin_area_cm2 * 2.0) * 1e-4
    cd_interference = 0.005 * num_total_fins
    Cd = 0.0045 * (wet_area_m2 / S_ref) + 0.08 + cd_interference
    
    motor_obj = get_motor(opt.motor_id)
    burn_t = motor_obj.burn_time
    burnout_mass_g = total_launch_mass_g - motor_obj.propellant_mass_g

    # Fast coupled numerical integration for boost and coast (dt=0.005s)
    dt = 0.005
    t = 0.0
    v = 0.0
    z = 0.0
    rho = 1.225
    g = 9.80665

    while t < 10.0:
        mass_kg = (burn_t > 0 and motor_obj.get_mass_g(t) * 1e-3 + (total_launch_mass_g - motor_obj.total_mass_g) * 1e-3) if t <= burn_t else (burnout_mass_g * 1e-3)
        thrust = motor_obj.get_thrust(t) if t <= burn_t else 0.0
        drag = 0.5 * rho * (v**2) * Cd * S_ref * (1.0 if v >= 0 else -1.0)
        acc = (thrust - drag - mass_kg * g) / mass_kg
        v += acc * dt
        z += v * dt
        if v <= 0.0 and z > 1.0:
            break
        t += dt

    apogee_m = max(z, 1.0)
    t_to_apogee = t

    # Descent phase: OpenRocket standard streamer model (CdA = 0.0055 m2)
    rec_cdA = 0.0055
    v_descent = math.sqrt((2.0 * (burnout_mass_g * 1e-3) * g) / (rho * rec_cdA))
    t_descent = apogee_m / v_descent if v_descent > 0 else 0.0
    total_time_s = t_to_apogee + t_descent
    
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

print("Searching optimal fin dimensions for L=250mm, D=24mm with target margin >= 1.20 cal:")
print("Testing various theta (0, 15, 30 deg) and fin arrangements:")

# Test 3-fin across thetas and v_scales
for th in [0.0, 10.0, 20.0, 30.0]:
    for vs in [0.6, 0.8, 1.0, 1.2, 1.4]:
        best = None
        for span in range(20, 80, 2):
            for cr in range(25, 90, 2):
                if span > 1.5 * cr or span < 0.3 * cr:
                    continue
                r = evaluate_physically_correct_fins(opt, span, cr, 0.0, th, vs, is_4fin=False)
                if r["margin_eff"] >= 1.20:
                    if best is None or r["fin_mass_g"] < best["fin_mass_g"]:
                        best = r
        if best:
            print(f"3-fin theta={th:4.1f}°, v_scale={vs:3.1f} -> fin={best['fin_mass_g']:.2f}g, span={best['span']}, cr={best['cr']} | Apogee: {best['apogee_m']:.1f}m, Time: {best['total_time_s']:.2f}s | P_mar={best['margin_pitch']:+.2f}, Y_mar={best['margin_yaw']:+.2f}")

# Test 4-fin (+) across v_scales
print("\nTesting 4-fin (+ shape):")
for vs in [0.4, 0.5, 0.6, 0.7, 0.8, 1.0]:
    best = None
    for span in range(20, 80, 2):
        for cr in range(25, 90, 2):
            if span > 1.5 * cr or span < 0.3 * cr:
                continue
            r = evaluate_physically_correct_fins(opt, span, cr, 0.0, 0.0, vs, is_4fin=True)
            if r["margin_eff"] >= 1.20:
                if best is None or r["fin_mass_g"] < best["fin_mass_g"]:
                    best = r
    if best:
        print(f"4-fin (+) v_scale={vs:3.1f} -> fin={best['fin_mass_g']:.2f}g, h_span={best['span']}, h_cr={best['cr']}, v_span={best['span']*vs:.1f} | Apogee: {best['apogee_m']:.1f}m, Time: {best['total_time_s']:.2f}s | P_mar={best['margin_pitch']:+.2f}, Y_mar={best['margin_yaw']:+.2f}")

# Test 4-fin symmetric (x shape, 4 identical fins at 45 deg)
print("\nTesting 4-fin (x shape, 45 deg symmetric):")
best = None
for span in range(20, 80, 2):
    for cr in range(25, 90, 2):
        if span > 1.5 * cr or span < 0.3 * cr:
            continue
        r = evaluate_physically_correct_fins(opt, span, cr, 0.0, 45.0, 1.0, is_4fin=True)
        if r["margin_eff"] >= 1.20:
            if best is None or r["fin_mass_g"] < best["fin_mass_g"]:
                best = r
if best:
    print(f"4-fin (x) symmetric -> fin={best['fin_mass_g']:.2f}g, span={best['span']}, cr={best['cr']} | Apogee: {best['apogee_m']:.1f}m, Time: {best['total_time_s']:.2f}s | P_mar={best['margin_pitch']:+.2f}, Y_mar={best['margin_yaw']:+.2f}")
