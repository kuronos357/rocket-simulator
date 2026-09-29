import sys
import os
import math
import numpy as np

sys.path.insert(0, os.path.abspath("."))
from sim_engine.optimizer import RocketSpec, FinOptimizer
from scratch.test_correct_physics import evaluate_physically_correct_fins

def find_peaks():
    streamer_area = 250.0  # 50x500mm
    streamer_mass = 1.2
    streamer_cd = 0.25

    results = []

    lengths = [250, 270]
    ballast_masses = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5]

    for L in lengths:
        max_nose = int(0.48 * L)
        for nose in [80, 100, 115, max_nose]:
            for m_bal in ballast_masses:
                spec = RocketSpec(
                    total_length_mm=float(L),
                    body_diameter_mm=24.0,
                    nose_length_mm=float(nose),
                    tail_length_mm=0.0,
                    wall_thickness_mm=0.4,
                    infill_ratio=0.02,
                    material="PLA",
                    material_density=1.24,
                    motor_type="1/2A6-2",
                    ballast_mass_g=m_bal,
                    ballast_z_mm=float(L - 5.0),
                    recovery_mass_g=streamer_mass,
                    recovery_area_cm2=streamer_area,
                    recovery_cd=streamer_cd,
                    descent_horizontal=True
                )
                opt = FinOptimizer(spec)

                # 3-Fin scan
                for th in [20, 25, 30, 35, 40]:
                    for vs in [0.5, 0.6, 0.7, 0.8, 1.0]:
                        for span in range(35, 85, 2):
                            for cr in range(25, 55, 2):
                                if span > 1.8 * cr or span < 0.35 * cr:
                                    continue
                                r = evaluate_physically_correct_fins(opt, float(span), float(cr), 0.0, float(th), vs, is_4fin=False)
                                m_eff = min(r["margin_pitch"], r["margin_yaw"])
                                if 0.50 <= m_eff <= 1.80 and r["total_time_s"] >= 24.0:
                                    is_asym = (th != 30 or vs != 1.0)
                                    results.append({
                                        **r,
                                        "margin_eff": m_eff,
                                        "time": r["total_time_s"],
                                        "apogee": r["apogee_m"],
                                        "L": L,
                                        "nose": nose,
                                        "ballast": m_bal,
                                        "type": "3-fin-asym" if is_asym else "3-fin-sym",
                                        "span": span,
                                        "cr": cr,
                                        "th": th,
                                        "vs": vs
                                    })

                # 4-Fin scan
                for vs in [0.7, 0.8, 1.0]:
                    for span in range(35, 80, 2):
                        for cr in range(25, 55, 2):
                            if span > 1.8 * cr or span < 0.35 * cr:
                                continue
                            r = evaluate_physically_correct_fins(opt, float(span), float(cr), 0.0, 0.0, vs, is_4fin=True)
                            m_eff = min(r["margin_pitch"], r["margin_yaw"])
                            if 0.50 <= m_eff <= 1.80 and r["total_time_s"] >= 24.0:
                                is_asym = (vs != 1.0)
                                results.append({
                                    **r,
                                    "margin_eff": m_eff,
                                    "time": r["total_time_s"],
                                    "apogee": r["apogee_m"],
                                    "L": L,
                                    "nose": nose,
                                    "ballast": m_bal,
                                    "type": "4-fin-asym" if is_asym else "4-fin-sym",
                                    "span": span,
                                    "cr": cr,
                                    "th": 0,
                                    "vs": vs
                                })

    print("SEARCHING PEAK 1: around 0.81 cal (target time ~30.6s)")
    peak1_cands = [r for r in results if 0.79 <= r["margin_eff"] <= 0.83]
    peak1_sorted = sorted(peak1_cands, key=lambda x: x["time"], reverse=True)
    for i, c in enumerate(peak1_sorted[:5]):
        print(f"  P1 #{i+1}: Margin={c['margin_eff']:.2f}cal (P={c['margin_pitch']:+.2f}, Y={c['margin_yaw']:+.2f}) | Time={c['time']:.2f}s | Apogee={c['apogee']:.1f}m | DescV={c['v_descent']:.2f}m/s | L={c['L']}/N={c['nose']}mm, Bal={c['ballast']:.1f}g | {c['type']} th={c['th']}°, vs={c['vs']:.2f} | H={c['span']}x{c['cr']}mm, V={c['span']*c['vs']:.1f}mm | FinMass={c['fin_mass_g']:.2f}g")

    print("\nSEARCHING PEAK 2: around 0.95 cal (target time ~29.7s)")
    peak2_cands = [r for r in results if 0.93 <= r["margin_eff"] <= 0.97]
    peak2_sorted = sorted(peak2_cands, key=lambda x: x["time"], reverse=True)
    for i, c in enumerate(peak2_sorted[:5]):
        print(f"  P2 #{i+1}: Margin={c['margin_eff']:.2f}cal (P={c['margin_pitch']:+.2f}, Y={c['margin_yaw']:+.2f}) | Time={c['time']:.2f}s | Apogee={c['apogee']:.1f}m | DescV={c['v_descent']:.2f}m/s | L={c['L']}/N={c['nose']}mm, Bal={c['ballast']:.1f}g | {c['type']} th={c['th']}°, vs={c['vs']:.2f} | H={c['span']}x{c['cr']}mm, V={c['span']*c['vs']:.1f}mm | FinMass={c['fin_mass_g']:.2f}g")

if __name__ == "__main__":
    find_peaks()
