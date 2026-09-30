import os
import sys
import math
import numpy as np

sys.path.insert(0, os.path.abspath("."))
from sim_engine.motor_db import get_motor
from scratch.find_practical_optimal_wings import calc_practical_fin_aero, compute_fuselage_base

motor = get_motor("1/2A6-2")
burn_t = motor.burn_time
avg_thrust = motor.total_impulse / motor.burn_time
prop_m = motor.propellant_mass_g

D = 24.0
R = 12.0
thick_mm = 0.4
rho = 1.24
S_ref = math.pi * (R * 1e-3)**2

streamer_cd_A = 0.25 * (250.0 * 1e-4) # 50x500mm
streamer_mass_g = 1.27

m_base, mom_base, cna_body, cp_body, wet_cm2 = compute_fuselage_base(
    nose_len_mm=125.0, tail_len_mm=20.0, streamer_mass_g=streamer_mass_g
)
wet_m2 = wet_cm2 * 1e-4

# Test sweeps with various practical bounds
# What are the margins when span varies from 50 to 80mm, overhang 0 to 10mm, te_sweep 10 to 35mm?
results = []

spans = np.arange(45.0, 85.1, 5.0)
crs = np.arange(30.0, 55.1, 5.0)
cts = np.array([8.0, 10.0, 12.0, 15.0])
te_angles = np.array([0.0, 10.0, 15.0, 20.0, 25.0])
overhangs = np.array([0.0, 5.0, 10.0])
p_les = np.array([0.7, 0.85, 1.0, 1.2])
p_tes = np.array([0.9, 1.0, 1.2])
configs = [
    (35.0, 0.80, 0.0, "3枚逆Y字 (v=0.80)"),
    (35.0, 1.00, 0.0, "3枚逆Y字 (v=1.00)"),
    (0.0,  1.00, 1.0, "4枚十字 (+)"),
]

for span in spans:
    for cr in crs:
        for ct in cts:
            if ct >= cr:
                continue
            for te_ang in te_angles:
                te_sw = span * math.tan(math.radians(te_ang))
                for oh in overhangs:
                    for p_le in p_les:
                        for p_te in p_tes:
                            for theta, v_sc, is_4f, cfg_name in configs:
                                m_eff, t_tot, apo, v_desc, f_m, tot_m, cg, cp = calc_practical_fin_aero(
                                    span, cr, ct, te_sw, oh,
                                    p_le, p_te,
                                    theta, v_sc, bool(is_4f),
                                    D, R, thick_mm, rho,
                                    cna_body, cp_body, m_base, mom_base,
                                    wet_cm2, S_ref, 20.0,
                                    burn_t, avg_thrust, prop_m,
                                    streamer_cd_A, wet_m2,
                                    min_chord_limit=7.5 # minimum local chord
                                )
                                if m_eff >= 1.0:
                                    results.append({
                                        "span": span, "cr": cr, "ct": ct, "te_ang": te_ang,
                                        "overhang": oh, "p_le": p_le, "p_te": p_te,
                                        "config": cfg_name, "margin": m_eff, "hang_time": t_tot,
                                        "apogee": apo, "fin_mass": f_m
                                    })

print(f"Total practical designs with Margin >= 1.0 cal: {len(results):,}")
if results:
    results.sort(key=lambda x: x["hang_time"], reverse=True)
    print("\nTop 5 by Hang Time (Margin >= 1.0 cal):")
    for r in results[:5]:
        print(f"  {r['config']}: span={r['span']}mm, cr={r['cr']}mm, ct={r['ct']}mm, oh={r['overhang']}mm, ple={r['p_le']}, pte={r['p_te']} -> Margin={r['margin']:.2f}cal, Time={r['hang_time']:.2f}s, Apo={r['apogee']:.1f}m, Mass={r['fin_mass']:.2f}g")

    # Filter for margin >= 1.3 cal (weathercocking & gust safety buffer)
    m13 = [r for r in results if r["margin"] >= 1.30]
    print(f"\nTotal practical designs with Margin >= 1.30 cal: {len(m13):,}")
    if m13:
        m13.sort(key=lambda x: x["hang_time"], reverse=True)
        print("Top 5 by Hang Time (Margin >= 1.30 cal):")
        for r in m13[:5]:
            print(f"  {r['config']}: span={r['span']}mm, cr={r['cr']}mm, ct={r['ct']}mm, oh={r['overhang']}mm, ple={r['p_le']}, pte={r['p_te']} -> Margin={r['margin']:.2f}cal, Time={r['hang_time']:.2f}s, Apo={r['apogee']:.1f}m, Mass={r['fin_mass']:.2f}g")
