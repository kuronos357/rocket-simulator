"""
Find the streamer area threshold where asymmetric / unbalanced fin configurations
hold a decisive advantage over symmetrical fin configurations.
"""

import sys
import os
import math
import numpy as np

sys.path.insert(0, os.path.abspath("."))
from sim_engine.optimizer import RocketSpec, FinOptimizer

def find_threshold():
    print("=" * 80)
    print("ANALYSIS: DECISIVE STREAMER AREA THRESHOLD FOR UNBALANCED (ASYMMETRIC) FINS")
    print("=" * 80)

    # Test streamer areas from 15 cm2 to 1440 cm2
    areas_cm2 = [
        14.4,   # 12 x 120 mm (Micro)
        30.0,   # ~17 x 170 mm
        62.5,   # 25 x 250 mm (JAR regulation minimum)
        100.0,  # ~31 x 316 mm
        150.0,  # ~38 x 380 mm
        200.0,  # ~45 x 450 mm
        250.0,  # 50 x 500 mm (Standard)
        350.0,  # ~60 x 600 mm
        500.0,  # ~70 x 700 mm
        750.0,  # ~86 x 860 mm
        1000.0, # 100 x 1000 mm
        1440.0  # 120 x 1200 mm (User's large streamer)
    ]

    spans = list(range(28, 76, 2))
    root_chords = list(range(18, 54, 2))
    taper_ratios = [0.10, 0.15, 0.20, 0.25, 0.30]

    results = []

    for area in areas_cm2:
        # Approximate mass based on ~25g/m2 film + lines
        film_mass = (area * 1e-4) * 25.0 # g
        mass_g = round(max(0.15, film_mass + 0.5), 2)

        spec = RocketSpec(
            total_length_mm=250.0,
            body_diameter_mm=24.0,
            nose_length_mm=125.0, # Optimal nose length (50%)
            tail_length_mm=0.0,
            wall_thickness_mm=0.4,
            infill_ratio=0.02,
            material="PLA",
            material_density=1.24,
            motor_type="1/2A6-2",
            ballast_mass_g=0.0,
            recovery_mass_g=mass_g,
            recovery_area_cm2=area,
            recovery_cd=0.25,
            descent_horizontal=True
        )
        opt = FinOptimizer(spec)

        # 1. Best Symmetric (4-fin sym v_scale=1.0 or 3-fin 120deg theta=30, v_scale=1.0)
        best_sym = None
        # 4-fin sym
        for tr in taper_ratios:
            for span in spans:
                for cr in root_chords:
                    if span > 2.0 * cr or span < 0.35 * cr: continue
                    r = opt.evaluate_fins(span, cr, shape_type="trapezoid", taper_ratio=tr, theta_deg=0.0, v_scale=1.0, is_4fin=True)
                    if r["margin_cal"] >= 0.85: # Safe margin threshold
                        if best_sym is None or r["total_flight_time_s"] > best_sym["total_flight_time_s"]:
                            best_sym = {**r, "arch": "4-fin Sym (+)", "tr": tr}
        # 3-fin sym
        for tr in taper_ratios:
            for span in spans:
                for cr in root_chords:
                    if span > 2.0 * cr or span < 0.35 * cr: continue
                    r = opt.evaluate_fins(span, cr, shape_type="trapezoid", taper_ratio=tr, theta_deg=30.0, v_scale=1.0, is_4fin=False)
                    if r["margin_cal"] >= 0.85:
                        if best_sym is None or r["total_flight_time_s"] > best_sym["total_flight_time_s"]:
                            best_sym = {**r, "arch": "3-fin Sym (120°)", "tr": tr}

        # 2. Best Asymmetric (4-fin asym v_scale=0.85 or 3-fin Inv-Y theta=35, v_scale=0.70)
        best_asym = None
        # 4-fin asym
        for tr in taper_ratios:
            for span in spans:
                for cr in root_chords:
                    if span > 2.0 * cr or span < 0.35 * cr: continue
                    r = opt.evaluate_fins(span, cr, shape_type="trapezoid", taper_ratio=tr, theta_deg=0.0, v_scale=0.85, is_4fin=True)
                    if r["margin_cal"] >= 0.85:
                        if best_asym is None or r["total_flight_time_s"] > best_asym["total_flight_time_s"]:
                            best_asym = {**r, "arch": "4-fin Asym (kv=0.85)", "tr": tr}
        # 3-fin Inv-Y asym
        for tr in taper_ratios:
            for span in spans:
                for cr in root_chords:
                    if span > 2.0 * cr or span < 0.35 * cr: continue
                    r = opt.evaluate_fins(span, cr, shape_type="trapezoid", taper_ratio=tr, theta_deg=35.0, v_scale=0.70, is_4fin=False)
                    if r["margin_cal"] >= 0.85:
                        if best_asym is None or r["total_flight_time_s"] > best_asym["total_flight_time_s"]:
                            best_asym = {**r, "arch": "3-fin Inv-Y (θ=35°, kv=0.70)", "tr": tr}

        diff_t = best_asym["total_flight_time_s"] - best_sym["total_flight_time_s"]
        pct_gain = (diff_t / best_sym["total_flight_time_s"]) * 100.0

        results.append({
            "area_cm2": area,
            "mass_g": mass_g,
            "sym_time": best_sym["total_flight_time_s"],
            "sym_arch": best_sym["arch"],
            "sym_span": best_sym["span_mm"],
            "sym_cr": best_sym["root_chord_mm"],
            "asym_time": best_asym["total_flight_time_s"],
            "asym_arch": best_asym["arch"],
            "asym_span": best_asym["span_mm"],
            "asym_cr": best_asym["root_chord_mm"],
            "diff_s": diff_t,
            "pct_gain": pct_gain
        })

    print(f"\n{'Streamer Area':16s} | {'Symmetric Best':24s} | {'Asymmetric Best':26s} | {'Advantage (Asym - Sym)':22s}")
    print("-" * 95)
    for r in results:
        print(f"{r['area_cm2']:6.1f} cm2 (m={r['mass_g']:4.2f}g) | {r['sym_arch']:15s} {r['sym_time']:5.2f}s | {r['asym_arch']:17s} {r['asym_time']:5.2f}s | {r['diff_s']:+5.2f}s ({r['pct_gain']:+5.1f}%)")

if __name__ == "__main__":
    find_threshold()
