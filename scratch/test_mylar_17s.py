import math
import sys, os
sys.path.insert(0, ".")
from scratch.calculate_120x1200_streamer import calc_flight, compute_fuselage_base

# Let's test with streamer mass = 4.10g (25 g/m2 competition thin mylar film + shroud lines)
# In calc_flight, let's modify streamer_mass_g to 4.10g and see the hang time!

from sim_engine.motor_db import get_motor

def evaluate_with_mylar(streamer_mass_g=4.10, area_m2=0.144):
    motor = get_motor("1/2A6-2")
    burn_t = motor.burn_time
    avg_thrust = motor.total_impulse / motor.burn_time
    prop_mass_g = motor.propellant_mass_g
    D, R, thick_mm, rho = 24.0, 12.0, 0.4, 1.24
    S_ref = math.pi * (R * 1e-3)**2
    streamer_cd_A = 0.25 * area_m2
    
    m_base_launch, mom_base_launch, cna_body_base, cp_body_base, wet_area_body_cm2 = compute_fuselage_base(
        nose_len_mm=125.0, tail_len_mm=20.0, streamer_mass_g=streamer_mass_g
    )
    wet_body_m2 = wet_area_body_cm2 * 1e-4
    
    # Test best wing from earlier (or best balance 75mm)
    # Span 75, Cr 28, Ct 10, te_ang 25, oh 5, ple 0.7, pte 0.8
    span_mm, cr_mm, ct_mm = 75.0, 28.0, 10.0
    te_sweep_mm = span_mm * math.tan(math.radians(25.0))
    oh_mm = 5.0
    p_le, p_te = 0.70, 0.80
    
    # We can run calc_flight directly by passing params or modifying
    # Let's see:
    burnout_mass_g = m_base_launch + 2.42 - prop_mass_g # ~30g - 3.12g ~ 27g
    # Let's compute apogee and descent:
    total_launch_mass_g = m_base_launch + 2.42
    m_avg_kg = (total_launch_mass_g - prop_mass_g * 0.5) * 1e-3
    v_bo = max(0.0, (avg_thrust / m_avg_kg - 9.8) * burn_t)
    h_bo = 0.5 * v_bo * burn_t
    Cd = 0.45 # approx
    k_drag = 0.5 * 1.225 * Cd * S_ref / ((total_launch_mass_g - prop_mass_g) * 1e-3)
    h_coast = (1.0 / (2.0 * k_drag)) * math.log(1.0 + k_drag * v_bo**2 / 9.8)
    t_coast = (1.0 / math.sqrt(9.8 * k_drag)) * math.atan(v_bo * math.sqrt(k_drag / 9.8))
    apogee = h_bo + h_coast
    
    # Descent:
    total_cd_A = streamer_cd_A + (1.1 / math.pi) * wet_body_m2 + 1.25 * 0.003
    v_desc = math.sqrt((2.0 * (total_launch_mass_g - prop_mass_g) * 1e-3 * 9.8) / (1.225 * total_cd_A))
    t_desc = apogee / v_desc
    total_time = burn_t + t_coast + t_desc
    
    print(f"With streamer_mass={streamer_mass_g:.2f}g (Thin Mylar):")
    print(f"  Launch Mass: {total_launch_mass_g:.2f}g")
    print(f"  Apogee: {apogee:.1f}m")
    print(f"  Descent Vel: {v_desc:.2f}m/s")
    print(f"  Total Hang Time: {total_time:.2f}s")

evaluate_with_mylar(streamer_mass_g=4.10)
