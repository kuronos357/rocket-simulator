"""
Parametric Sweep of Streamer Length (L_streamer) alongside
Nose Length and Clipped Delta Wing Geometries.
Evaluates the trade-off between:
  - Streamer Length (Aerodynamic drag vs Recovery Mass penalty)
  - Nose Length (CG forward shift vs Airframe mass)
  - Clipped Delta Wing Geometries (Span, Root Chord, Taper Ratio, Architecture)
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

def run_streamer_length_sweep():
    print("=" * 80)
    print("PARAMETRIC SWEEP: STREAMER LENGTH DOF + NOSE LENGTH + CLIPPED DELTA FINS")
    print("Base: PLA (1.24 g/cm3), Wall: 0.4mm, Infill: 2%, Total L=250mm, D=24mm")
    print("=" * 80)

    # 1. Parameter Ranges
    # Streamer width is 120mm. Lengths to explore:
    # 200mm, 400mm, 600mm, 800mm, 1000mm, 1200mm (standard), 1500mm, 1800mm
    streamer_width_mm = 120.0
    streamer_lengths_mm = [200, 400, 600, 800, 1000, 1200, 1500, 1800]
    streamer_cd = 0.25

    # Nose lengths: 70mm to 125mm (JAR 50% limit)
    nose_lengths = [85, 100, 115, 125]

    # Clipped delta taper ratios
    taper_ratios = [0.10, 0.15, 0.20, 0.25, 0.30]

    # Architectures
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

    print(f"Scanning {len(streamer_lengths_mm)} streamer lengths x {len(nose_lengths)} nose lengths x {len(architectures)} wing architectures...")

    for L_str in streamer_lengths_mm:
        # Calculate streamer area and realistic mass (film 25g/m2 + lines/reinforcement)
        area_cm2 = (streamer_width_mm * 0.1) * (L_str * 0.1) # mm2 -> cm2
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

                            if 0.60 <= m_eff <= 1.55 and t_hang >= 10.0:
                                results.append({
                                    "streamer_L": L_str,
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
    print(f"Sweep finished in {t1 - t0:.2f} s. Total valid configurations: {len(results):,}")

    out_file = os.path.join("scratch", "streamer_length_sweep_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Results saved to {out_file}")

    return results

if __name__ == "__main__":
    run_streamer_length_sweep()
