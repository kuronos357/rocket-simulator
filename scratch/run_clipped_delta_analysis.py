"""
Comprehensive Clipped Delta Wing and Nose Length Optimization
Parameters:
  - Material: PLA (rho = 1.24 g/cm3)
  - Nozzle: 0.4mm, 1 wall (thickness = 0.4mm)
  - Infill: 2% (0.02)
  - Streamer: 12mm x 120mm (14.4 cm2)
  - Total Length: 250.0mm, Body Diameter: 24.0mm
  - Motor: 1/2A6-2
"""

import sys
import os
import math
import json
import time
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath("."))
from sim_engine.motor_db import get_motor
from sim_engine.optimizer import RocketSpec, FinOptimizer

def run_comprehensive_sweep():
    print("=" * 80)
    print("CLIPPED DELTA WING & NOSE LENGTH COMPREHENSIVE OPTIMIZATION")
    print("Material: PLA (1.24 g/cm3), Wall: 0.4mm (1 perimeter), Infill: 2%")
    print("Streamer: 12mm x 120mm (Area: 14.4 cm2)")
    print("Rocket Dimensions: Total Length = 250mm, Body Diameter = 24mm (Motor: 1/2A6-2)")
    print("=" * 80)

    # 1. Parameter Grids
    nose_lengths = [40, 50, 60, 70, 80, 90, 100, 110, 120, 125] # Up to 125mm (JAR 50% limit)
    taper_ratios = [0.0, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50] # 0.0=Delta, >0=Clipped Delta
    
    architectures = [
        {"name": "4枚対称 十字翼 (+)", "is_4fin": True, "theta": 0.0, "vs": 1.0},
        {"name": "4枚非対称 十字翼 (Cross-Asym)", "is_4fin": True, "theta": 0.0, "vs": 0.85},
        {"name": "3枚対称 120°翼 (Y)", "is_4fin": False, "theta": 30.0, "vs": 1.0},
        {"name": "3枚非対称 逆Y字翼 (Inv-Y 35°)", "is_4fin": False, "theta": 35.0, "vs": 0.70},
        {"name": "3枚T字型 飛行機翼 (T-shape)", "is_4fin": False, "theta": 0.0, "vs": 0.85},
    ]

    spans = list(range(26, 76, 2))      # 26mm to 74mm (step 2)
    root_chords = list(range(18, 56, 2))# 18mm to 54mm (step 2)

    total_combinations_checked = 0
    valid_points = []

    t0 = time.time()

    # Streamer parameters: 12mm x 120mm = 14.4 cm2, mass ~ 0.15g
    streamer_area_cm2 = 14.4
    streamer_mass_g = 0.15
    streamer_cd = 0.25

    print(f"Scanning {len(nose_lengths)} nose lengths x {len(taper_ratios)} taper ratios x {len(architectures)} architectures...")

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
            recovery_area_cm2=streamer_area_cm2,
            recovery_cd=streamer_cd,
            descent_horizontal=True # Horizontal descent
        )
        opt = FinOptimizer(spec)

        for arch in architectures:
            is_4fin = arch["is_4fin"]
            theta = arch["theta"]
            vs = arch["vs"]

            for tr in taper_ratios:
                for span in spans:
                    for cr in root_chords:
                        # Aspect ratio filter: prevent extreme unphysical needles or stubs
                        if span > 2.0 * cr or span < 0.35 * cr:
                            continue

                        total_combinations_checked += 1

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
                        if m_eff < 0.60:
                            continue # Unstable

                        # Calculate non-horizontal (pure streamer) descent for comparison
                        ct = tr * cr
                        # burnout mass
                        burnout_m_kg = (res["total_mass_g"] - 1.56) * 1e-3
                        g = 9.80665
                        rho_air = 1.225
                        cd_pure_rec = streamer_cd * (streamer_area_cm2 * 1e-4) + (res["Cd"] * opt.spec.body_diameter_mm**2 * math.pi / 4.0 * 1e-6)
                        v_desc_pure = math.sqrt((2.0 * burnout_m_kg * g) / (rho_air * cd_pure_rec))
                        t_desc_pure = res["apogee_m"] / v_desc_pure if v_desc_pure > 0 else 0.0
                        t_pure_total = (res["apogee_m"] / max(1.0, res["max_vel_km_h"] / 7.2)) + t_desc_pure

                        valid_points.append({
                            "nose_mm": nose,
                            "taper_ratio": tr,
                            "ct_mm": round(ct, 1),
                            "span_mm": span,
                            "cr_mm": cr,
                            "arch_name": arch["name"],
                            "is_4fin": is_4fin,
                            "theta_deg": theta,
                            "v_scale": vs,
                            "fin_mass_g": res["fin_mass_g"],
                            "total_mass_g": res["total_mass_g"],
                            "CG_mm": res["cg_mm"],
                            "margin_pitch": res["pitch_margin_cal"],
                            "margin_yaw": res["yaw_margin_cal"],
                            "margin_eff": m_eff,
                            "Cd": res["Cd"],
                            "apogee_m": res["apogee_m"],
                            "total_time_horiz_s": res["total_flight_time_s"],
                            "v_desc_horiz": res["v_descent_m_s"],
                            "total_time_pure_s": round(t_pure_total, 2),
                            "v_desc_pure": round(v_desc_pure, 2)
                        })

    t1 = time.time()
    print(f"Sweep completed in {t1 - t0:.2f} s.")
    print(f"Combinations checked: {total_combinations_checked:,}, Valid stable points: {len(valid_points):,}")

    # Save full sweep results
    out_file = os.path.join("scratch", "clipped_delta_optimization_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(valid_points, f, indent=2, ensure_ascii=False)
    print(f"Results saved to {out_file}")

    return valid_points

if __name__ == "__main__":
    run_comprehensive_sweep()
