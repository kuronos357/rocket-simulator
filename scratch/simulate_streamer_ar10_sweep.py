"""
Parametric Sweep with Streamer Aspect Ratio fixed at 1:10 (JAR Competition Rule: L >= 10*W, W >= 25mm).
Here AR is fixed to 1:10, so W = 0.1 * L, Area = 0.1 * L^2.
Explores:
  - Streamer Lengths: L = 250mm (min by rule) to 1800mm (with W = 0.1*L)
  - Nose lengths: 85, 100, 115, 125mm
  - Wing Architectures: 5 types
  - Clipped Delta Finned geometries
"""

import sys
import os
import math
import json
import time
import numpy as np

sys.path.insert(0, os.path.abspath("."))
from sim_engine.motor_db import get_motor
from sim_engine.optimizer import RocketSpec, FinOptimizer

def run_sweep():
    print("=" * 80)
    print("PARAMETRIC SWEEP: STREAMER AR 1:10 FIXED (W = 0.1*L, W >= 25mm)")
    print("=" * 80)

    # Rule: W >= 25mm, L >= 10*W -> Min L = 250mm
    # Let's explore L = 250, 400, 600, 800, 1000, 1200, 1400, 1600, 1800 mm
    streamer_lengths_mm = [250, 400, 600, 800, 1000, 1200, 1400, 1600, 1800]
    streamer_cd = 0.25 # Effective Cd of fluttering streamer

    nose_lengths = [85, 100, 115, 125]
    taper_ratios = [0.10, 0.15, 0.20, 0.25, 0.30]

    architectures = [
        {"name": "4枚非対称 十字翼 (Cross-Asym)", "type_key": "4-fin-asym", "is_4fin": True, "theta": 0.0, "vs": 0.85, "color": "#1f77b4"},
        {"name": "4枚対称 十字翼 (+)", "type_key": "4-fin-sym", "is_4fin": True, "theta": 0.0, "vs": 1.0, "color": "#7f7f7f"},
        {"name": "3枚非対称 逆Y字翼 (Inv-Y 35°)", "type_key": "3-fin-asym", "is_4fin": False, "theta": 35.0, "vs": 0.70, "color": "#2ca02c"},
        {"name": "3枚対称 120°翼 (Y)", "type_key": "3-fin-sym", "is_4fin": False, "theta": 30.0, "vs": 1.0, "color": "#17becf"},
        {"name": "3枚T字型 飛行機翼 (T-shape)", "type_key": "3-fin-t", "is_4fin": False, "theta": 0.0, "vs": 0.85, "color": "#ff7f0e"},
    ]

    spans = list(range(28, 76, 2))       # 28 to 74 mm
    root_chords = list(range(18, 54, 2)) # 18 to 52 mm

    results = []
    t0 = time.time()

    for L_str in streamer_lengths_mm:
        W_str = 0.1 * L_str # Aspect ratio 1:10 fixed
        area_cm2 = (W_str * 0.1) * (L_str * 0.1) # mm2 -> cm2
        film_mass_g = (area_cm2 * 1e-4) * 25.0
        lines_reinforce_g = 0.5 + 0.0003 * L_str
        streamer_mass_g = round(film_mass_g + lines_reinforce_g, 2)

        for nose in nose_lengths:
            spec = RocketSpec(
                total_length_mm=250.0,
                body_diameter_mm=24.0,
                nose_length_mm=float(nose),
                nose_shape_n=0.75,
                tail_length_mm=0.0,
                wall_thickness_mm=0.4,
                infill_ratio=0.02,
                material="PLA",
                material_density=1.24,
                motor_type="1/2A6-2",
                ballast_mass_g=0.0,
                ballast_z_mm=float(250.0 - 5.0),
                recovery_mass_g=streamer_mass_g,
                recovery_area_cm2=area_cm2,
                recovery_cd=streamer_cd,
                descent_horizontal=True
            )
            opt = FinOptimizer(spec)

            for arch in architectures:
                is_4fin = arch["is_4fin"]
                theta = arch["theta"]
                vs = arch["vs"]

                for tr in taper_ratios:
                    for span in spans:
                        for cr in root_chords:
                            if span > 2.0 * cr or span < 0.35 * cr:
                                continue

                            res = opt.evaluate_fins(
                                span_mm=float(span),
                                cr_mm=float(cr),
                                shape_type="trapezoid",
                                taper_ratio=float(tr),
                                fin_thickness_mm=0.4,
                                theta_deg=theta,
                                v_scale=vs,
                                is_4fin=is_4fin
                            )

                            m_eff = res["margin_cal"]
                            t_hang = res["total_flight_time_s"]

                            if 0.55 <= m_eff <= 1.55 and t_hang >= 8.0:
                                results.append({
                                    "streamer_L": L_str,
                                    "streamer_W": W_str,
                                    "streamer_area": area_cm2,
                                    "streamer_mass": streamer_mass_g,
                                    "nose": nose,
                                    "arch_name": arch["name"],
                                    "type_key": arch["type_key"],
                                    "color": arch["color"],
                                    "tr": tr,
                                    "ct": round(tr * cr, 1),
                                    "span": span,
                                    "cr": cr,
                                    "margin": m_eff,
                                    "time": t_hang,
                                    "apogee": res["apogee_m"],
                                    "v_desc": res["v_descent_m_s"],
                                    "fin_mass": res["fin_mass_g"],
                                    "total_mass": res["total_mass_g"]
                                })

    t1 = time.time()
    print(f"Completed {len(results)} simulations in {t1 - t0:.1f} seconds.")

    out_json = os.path.join("scratch", "streamer_ar10_sweep_results.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f)
    print(f"Saved results to {out_json}")

if __name__ == "__main__":
    run_sweep()
