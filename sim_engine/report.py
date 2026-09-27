"""
Report and Visualization Generator
Generates clean console summary and flight trajectory plots.
"""

import os
import matplotlib.pyplot as plt

def print_summary_report(model, aero_res, flight_res):
    print("\n" + "=" * 60)
    print(f"       [ 3D Rocket Physical Analysis Report: {model.design_name} ]")
    print("=" * 60)
    
    axis_idx = {"x": 0, "y": 1, "z": 2}.get(model.flight_axis, 1)
    cg_flight = model.cg_mm[axis_idx]
    motor_info = f"{model.motor_part['motor_id']} ({model.motor_part['mass_g']:.1f}g)" if model.motor_part else "None"
    
    print("\n[ 1. Mass & CG Properties (3D Print & Real Scaling) ]")
    print("-" * 60)
    print(f"  - Airframe Mass (Fuselage + Streamer): {model.dry_mass_g:.2f} g")
    print(f"  - Equipped Motor                     : {motor_info}")
    print(f"  - Launch Gross Mass (at Ignition)    : {model.launch_mass_g:.2f} g")
    print(f"  - Burnout Mass (Post-Burn)           : {model.burnout_mass_g:.2f} g")
    print(f"  - Center of Gravity (CG)             : {cg_flight:.2f} mm (from tail)")
    print(f"  - Rocket Total Length                : {model.total_length_mm:.1f} mm")
    print(f"  - Pitch/Yaw Moment of Inertia        : {model.moi_g_cm2['Ixx']:.1f} g*cm2")
    print(f"  - Roll Moment of Inertia             : {model.moi_g_cm2['Iyy']:.1f} g*cm2")

    print("\n[ 2. Aerodynamics & Stability (3D Mesh Integration) ]")
    print("-" * 60)
    print(f"  - Reference Drag Coeff (Cd)          : {aero_res['Cd']:.3f} (Drag: {aero_res['Drag_N']:.2f} N)")
    print(f"  - Center of Pressure (CP)            : {aero_res['CP_z_mm']:.2f} mm (from tail)")
    print(f"  - Static Stability Margin (Overall)  : {aero_res['margin_cal']:+.2f} cal ({aero_res.get('margin_mm', 0):+.1f} mm)")
    if "pitch_margin_cal" in aero_res and "yaw_margin_cal" in aero_res:
        print(f"    * Pitch Stability (Main Fins)      : {aero_res['pitch_margin_cal']:+.2f} cal (CP: {aero_res['pitch_cp_mm']:.1f} mm)")
        print(f"    * Yaw Stability (Vertical Fin)     : {aero_res['yaw_margin_cal']:+.2f} cal (CP: {aero_res['yaw_cp_mm']:.1f} mm)")
    
    status_str = "[OK] Stable" if aero_res['is_stable'] else ("[△] Marginal / Weak" if aero_res['margin_cal'] >= 0.0 else "[WARN] Unstable (Nose ballast recommended)")
    print(f"  - Stability Check                    : {status_str}")
    if abs(aero_res['Roll_Torque_Nm']) > 1e-5:
        print(f"  - Asymmetric Fin Roll Torque         : {aero_res['Roll_Torque_Nm']*1000:.3f} mN*m (Spinning)")
    else:
        print(f"  - Induced Roll Torque                : ~0 (Axisymmetric)")

    print("\n[ 3. Flight Performance Prediction ]")
    print("-" * 60)
    print(f"  - Apogee Altitude                    : {flight_res['apogee_alt_m']:.1f} m (at T+{flight_res['apogee_time_s']:.2f} s)")
    print(f"  - Max Velocity                       : {flight_res['max_velocity_km_h']:.1f} km/h ({flight_res['max_velocity_m_s']:.1f} m/s)")
    print(f"  - Max Acceleration                   : {flight_res['max_accel_G']:.1f} G")
    
    rod_status = "[OK] Safe Clear" if flight_res['is_rod_speed_safe'] else "[WARN] Low Speed (Wind drift risk)"
    print(f"  - Launch Rod Clear Speed (0.9m)      : {flight_res['rod_clear_speed_m_s']:.1f} m/s ({rod_status})")
    print(f"  - Ejection Timing                    : T+{flight_res['ejection_time_s']:.2f} s (Alt: {flight_res['ejection_alt_m']:.1f} m)")
    landing_spd = flight_res.get('landing_speed_m_s', flight_res['terminal_velocity_m_s'])
    print(f"  - Terminal Descent Velocity          : {flight_res['terminal_velocity_m_s']:.1f} m/s (Landing: {landing_spd:.1f} m/s)")
    print(f"  - Total Flight Time (to landing)     : {flight_res['total_flight_time_s']:.1f} s")
    print("=" * 60 + "\n")


def plot_flight_profile(flight_res, output_path="flight_profile.png"):
    ts = flight_res["time_series"]
    t = ts["t"]
    alt = ts["alt"]
    vel = ts["vel"]
    acc = ts["acc"]
    
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(9, 8), sharex=True)
    
    # Altitude
    ax1.plot(t, alt, color='tab:blue', lw=2)
    ax1.set_ylabel("Altitude [m]")
    ax1.grid(True, alpha=0.3)
    ax1.axhline(flight_res["apogee_alt_m"], color='red', ls='--', alpha=0.7, 
                label=f"Apogee: {flight_res['apogee_alt_m']} m")
    ax1.legend(loc="upper right")
    ax1.set_title("Flight Trajectory Profile", fontsize=13, fontweight='bold')
    
    # Velocity
    ax2.plot(t, vel, color='tab:green', lw=2)
    ax2.set_ylabel("Velocity [m/s]")
    ax2.grid(True, alpha=0.3)
    ax2.axhline(0, color='gray', ls=':', alpha=0.5)
    
    # Acceleration
    ax3.plot(t, acc, color='tab:orange', lw=2)
    ax3.set_ylabel("Accel [G]")
    ax3.set_xlabel("Time [s]")
    ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"📊 飛翔グラフ画像を保存しました: {output_path}")
