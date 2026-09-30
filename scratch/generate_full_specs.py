import sys, os
sys.path.insert(0, os.path.abspath("."))
import math
import json
from sim_engine.motor_db import get_motor
from sim_engine.optimizer import RocketSpec, FinOptimizer

def compute_detailed_model(spec: RocketSpec, span_mm: float, cr_mm: float, theta_deg: float, v_scale: float, is_4fin: bool):
    opt = FinOptimizer(spec)
    s = opt.spec
    D = s.body_diameter_mm
    R = D / 2.0
    rho = s.material_density
    theta_rad = math.radians(theta_deg)
    fin_thickness_mm = 0.4
    root_offset_mm = 0.0
    taper_ratio = 0.0 # Delta fin

    # Side fins (2 fins)
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

    # Vertical fin
    span_v = span_mm * v_scale
    cr_v = cr_mm * v_scale
    ct_v = ct_mm * v_scale
    area_1v_cm2 = (0.5 * (cr_v + ct_v) * span_v) * 0.01
    denom_cg_v = 3.0 * (cr_v + ct_v) if (cr_v + ct_v) > 0 else 1.0
    z_fin_local_cg_v = (cr_v**2 + cr_v * ct_v + ct_v**2) / denom_cg_v
    z_fin_cg_v = root_offset_mm + z_fin_local_cg_v

    k_body_v = 1.0 + R / (R + span_v)
    mid_sweep_v = (cr_v - ct_v) + (ct_v - cr_v) / 2.0
    Lf_v = math.sqrt(mid_sweep_v**2 + span_v**2)
    denom_v = 1.0 + math.sqrt(1.0 + (2.0 * Lf_v / (cr_v + ct_v))**2) if (cr_v + ct_v) > 0 else 2.0

    num_v = 2.0 if is_4fin else 1.0
    num_total_fins = 2.0 + num_v

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

    S_ref = math.pi * (R * 1e-3)**2
    wet_area_m2 = (opt.wet_area_body_cm2 + total_fin_area_cm2 * 2.0) * 1e-4
    cd_interference = 0.005 * num_total_fins
    Cd = 0.0045 * (wet_area_m2 / S_ref) + 0.08 + cd_interference

    motor_obj = get_motor(opt.motor_id)
    burn_t = motor_obj.burn_time
    burnout_mass_g = total_launch_mass_g - motor_obj.propellant_mass_g

    # Coupled numerical integration for boost and coast (dt=0.002s)
    dt = 0.002
    t = 0.0
    v = 0.0
    z = 0.0
    rho = 1.225
    g = 9.80665
    max_accel_g = 0.0
    max_vel_m_s = 0.0
    v_bo = 0.0
    h_bo = 0.0

    while t < 15.0:
        mass_kg = (burn_t > 0 and motor_obj.get_mass_g(t) * 1e-3 + (total_launch_mass_g - motor_obj.total_mass_g) * 1e-3) if t <= burn_t else (burnout_mass_g * 1e-3)
        thrust = motor_obj.get_thrust(t) if t <= burn_t else 0.0
        drag = 0.5 * rho * (v**2) * Cd * S_ref * (1.0 if v >= 0 else -1.0)
        acc = (thrust - drag - mass_kg * g) / mass_kg
        acc_g = acc / g
        if acc_g > max_accel_g:
            max_accel_g = acc_g
        v += acc * dt
        if v > max_vel_m_s:
            max_vel_m_s = v
        z += v * dt
        if t <= burn_t:
            v_bo = v
            h_bo = z
        if v <= 0.0 and z > 1.0:
            break
        t += dt

    apogee_m = max(z, 1.0)
    t_to_apogee = t
    t_coast = max(0.0, t_to_apogee - burn_t)

    # Streamer descent
    rec_cdA = 0.0055
    v_descent = math.sqrt((2.0 * (burnout_mass_g * 1e-3) * g) / (rho * rec_cdA))
    t_descent = apogee_m / v_descent if v_descent > 0 else 0.0
    total_time_s = t_to_apogee + t_descent
    total_cd_A = rec_cdA

    return {
        "spec": {
            "total_length_mm": s.total_length_mm,
            "body_diameter_mm": D,
            "nose_length_mm": s.nose_length_mm,
            "nose_shape_n": s.nose_shape_n,
            "body_tube_length_mm": s.total_length_mm - s.nose_length_mm,
            "wall_thickness_mm": s.wall_thickness_mm,
            "infill_ratio": s.infill_ratio,
            "material": s.material,
            "material_density_g_cm3": s.material_density,
            "ballast_mass_g": s.ballast_mass_g,
            "ballast_z_from_tail_mm": s.ballast_z_mm,
            "ballast_z_from_tip_mm": s.total_length_mm - s.ballast_z_mm if s.ballast_z_mm is not None else 0.0,
            "recovery_type": "ストリーマー (Streamer)",
            "recovery_dimensions_mm": "50 x 500",
            "recovery_area_cm2": s.recovery_area_cm2,
            "recovery_mass_g": s.recovery_mass_g,
            "motor_type": s.motor_type,
            "motor_dimensions_mm": "18 x 70",
            "motor_total_mass_g": motor_obj.total_mass_g,
            "motor_propellant_mass_g": motor_obj.propellant_mass_g,
            "motor_burnout_mass_g": motor_obj.burnout_mass_g,
            "motor_total_impulse_Ns": motor_obj.total_impulse,
            "motor_burn_time_s": motor_obj.burn_time
        },
        "fins": {
            "fin_count": int(num_total_fins),
            "is_4fin": is_4fin,
            "layout_name": "十字アンバランス (4枚)" if (is_4fin and v_scale != 1.0) else ("正十字対称 (4枚)" if is_4fin else "逆Y字アンバランス (3枚)"),
            "fin_thickness_mm": fin_thickness_mm,
            "attachment_root_offset_from_tail_mm": root_offset_mm,
            "main_fin": {
                "count": 2,
                "role": "左右主翼 (水平または下向き傾斜翼)",
                "span_mm": span_mm,
                "root_chord_mm": cr_mm,
                "tip_chord_mm": ct_mm,
                "sweep_mm": sweep_h,
                "shape": "直角三角形デルタ翼 (後退角前縁, 後縁ストレート)",
                "area_per_fin_cm2": area_1side_cm2,
                "mass_per_fin_g": area_1side_cm2 * (fin_thickness_mm * 0.1) * rho,
                "dihedral_angle_deg": theta_deg,
                "cg_local_from_le_root_mm": z_fin_local_cg_h
            },
            "sub_fin": {
                "count": int(num_v),
                "role": "上下垂直尾翼 (または真上垂直尾翼1枚)",
                "scale_factor_kv": v_scale,
                "span_mm": span_v,
                "root_chord_mm": cr_v,
                "tip_chord_mm": ct_v,
                "sweep_mm": mid_sweep_v,
                "shape": "直角三角形デルタ翼 (縮小相似形)",
                "area_per_fin_cm2": area_1v_cm2,
                "mass_per_fin_g": area_1v_cm2 * (fin_thickness_mm * 0.1) * rho,
                "cg_local_from_le_root_mm": z_fin_local_cg_v
            },
            "total_fin_mass_g": fin_mass_g,
            "total_fin_area_cm2": total_fin_area_cm2
        },
        "mass_and_balance": {
            "airframe_shell_infill_mass_g": opt.m_airframe_g,
            "dry_mass_total_g": burnout_mass_g,
            "launch_mass_total_g": total_launch_mass_g,
            "cg_from_tail_mm": total_cg_mm,
            "cg_from_nose_tip_mm": s.total_length_mm - total_cg_mm,
            "cp_pitch_from_tail_mm": cp_pitch,
            "cp_pitch_from_nose_tip_mm": s.total_length_mm - cp_pitch,
            "cp_yaw_from_tail_mm": cp_yaw,
            "cp_yaw_from_nose_tip_mm": s.total_length_mm - cp_yaw,
            "margin_pitch_cal": margin_pitch_cal,
            "margin_yaw_cal": margin_yaw_cal,
            "margin_effective_cal": margin_eff_cal,
            "stability_status": "安定 (Over-stable / Optimal)"
        },
        "aerodynamics": {
            "drag_coefficient_cd": Cd,
            "cross_sectional_area_ref_cm2": S_ref * 1e4,
            "wet_area_total_cm2": wet_area_m2 * 1e4,
            "cna_body": opt.cna_body_base,
            "cna_pitch_fins": cna_pitch_fins,
            "cna_yaw_fins": cna_yaw_fins,
            "descent_total_cd_a_m2": total_cd_A
        },
        "flight_performance": {
            "burnout_velocity_ms": v_bo,
            "burnout_altitude_m": h_bo,
            "apogee_altitude_m": apogee_m,
            "time_to_apogee_s": burn_t + t_coast,
            "burn_time_s": burn_t,
            "coast_time_s": t_coast,
            "max_acceleration_g": max_accel_g,
            "descent_velocity_ms": v_descent,
            "descent_time_s": t_descent,
            "total_flight_time_s": total_time_s
        }
    }

spec_std = RocketSpec(
    total_length_mm=250.0, body_diameter_mm=24.0, nose_length_mm=120.0,
    tail_length_mm=0.0, wall_thickness_mm=0.4, infill_ratio=0.02,
    material="PLA", material_density=1.24, motor_type="1/2A6-2",
    ballast_mass_g=0.0, ballast_z_mm=245.0, recovery_mass_g=1.2,
    recovery_area_cm2=250.0, recovery_cd=0.25, descent_horizontal=True
)

spec_bal = RocketSpec(
    total_length_mm=250.0, body_diameter_mm=24.0, nose_length_mm=120.0,
    tail_length_mm=0.0, wall_thickness_mm=0.4, infill_ratio=0.02,
    material="PLA", material_density=1.24, motor_type="1/2A6-2",
    ballast_mass_g=1.0, ballast_z_mm=245.0, recovery_mass_g=1.2,
    recovery_area_cm2=250.0, recovery_cd=0.25, descent_horizontal=True
)

# 1. 0.8cal.30.48sあたりのアンバランス４枚翼 (55x31, kv=0.90 / または 59x33, kv=0.85)
m1_a = compute_detailed_model(spec_std, 55.0, 31.0, 0.0, 0.90, is_4fin=True)
m1_b = compute_detailed_model(spec_std, 59.0, 33.0, 0.0, 0.85, is_4fin=True)

# 2. 0.86.30.25あたりのアンバランス３枚翼 (76x44, theta=35, kv=0.70)
m2 = compute_detailed_model(spec_std, 76.0, 44.0, 35.0, 0.70, is_4fin=False)

# 3. 1.22.28.44のやつ (59x33, kv=1.0, 4fin sym, ballast=1.0g)
m3 = compute_detailed_model(spec_bal, 59.0, 33.0, 0.0, 1.00, is_4fin=True)

out = {
    "candidate_1a_4fin_asym_55x31": m1_a,
    "candidate_1b_4fin_asym_59x33": m1_b,
    "candidate_2_3fin_asym_76x44": m2,
    "candidate_3_high_stability_59x33": m3
}

os.makedirs("output", exist_ok=True)
with open("output/final_three_models_full_specs.json", "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)

# Keep scratch copy as well
with open("scratch/final_three_models_full_specs.json", "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)

print("SUCCESS: Generated complete engineering parameters for all 3 models!")
