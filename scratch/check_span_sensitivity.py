import os
import sys
import numpy as np

sys.path.insert(0, os.path.abspath("."))
from scratch.find_practical_optimal_wings import calc_practical_fin_aero, compute_fuselage_base
from sim_engine.motor_db import get_motor

motor = get_motor("1/2A6-2")
burn_t = motor.burn_time
avg_thrust = motor.total_impulse / motor.burn_time
prop_m = motor.propellant_mass_g
D, R, thick_mm, rho = 24.0, 12.0, 0.4, 1.24
S_ref = 3.14159 * (R * 1e-3)**2
streamer_cd_A = 0.25 * (250.0 * 1e-4)
streamer_mass_g = 1.27
m_base, mom_base, cna_body, cp_body, wet_cm2 = compute_fuselage_base(
    nose_len_mm=125.0, tail_len_mm=20.0, streamer_mass_g=streamer_mass_g
)
wet_m2 = wet_cm2 * 1e-4

print("Span sweep for 4-fin (cr=40, ct=10, te_ang=10, oh=5):")
for span in [40, 50, 60, 65, 70, 75, 80]:
    te_sw = span * np.tan(np.radians(10.0))
    res = calc_practical_fin_aero(
        span, 40.0, 10.0, te_sw, 5.0,
        1.0, 1.0,
        0.0, 1.0, True,
        D, R, thick_mm, rho,
        cna_body, cp_body, m_base, mom_base,
        wet_cm2, S_ref, 20.0,
        burn_t, avg_thrust, prop_m,
        streamer_cd_A, wet_m2,
        min_chord_limit=5.0
    )
    print(f"span={span}mm: Margin={res[0]:.2f} cal, HangTime={res[1]:.2f}s, Apogee={res[2]:.1f}m, Mass={res[4]:.2f}g")

print("\nSweep with oh=0 (flush with body tail):")
for span in [50, 60, 70, 75, 80]:
    te_sw = span * np.tan(np.radians(15.0))
    res = calc_practical_fin_aero(
        span, 45.0, 10.0, te_sw, 0.0,
        0.8, 1.2,
        0.0, 1.0, True,
        D, R, thick_mm, rho,
        cna_body, cp_body, m_base, mom_base,
        wet_cm2, S_ref, 20.0,
        burn_t, avg_thrust, prop_m,
        streamer_cd_A, wet_m2,
        min_chord_limit=5.0
    )
    print(f"span={span}mm: Margin={res[0]:.2f} cal, HangTime={res[1]:.2f}s, Apogee={res[2]:.1f}m, Mass={res[4]:.2f}g")
