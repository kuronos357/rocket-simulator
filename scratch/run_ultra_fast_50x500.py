"""
Ultra-Fast 50x500mm Streamer Sweep using Numba 16-Thread JIT Engine.
Evaluates 106,400+ combinations across 5 architectures, 5 nose lengths, and 8 taper ratios.
"""

import os
import sys
import time
import json
import numpy as np

sys.path.insert(0, os.path.abspath("."))
from sim_engine.optimizer import RocketSpec
from sim_engine.ultra_fast_optimizer import UltraFastOptimizer

def main():
    print("=" * 80)
    print("RYZEN 9 6900HX 16-THREAD ULTRA-FAST OPTIMIZATION (50x500mm STREAMER)")
    print("=" * 80)

    area_cm2 = 250.0
    streamer_mass_g = 1.27
    streamer_cd = 0.25

    nose_lengths = [85.0, 95.0, 105.0, 115.0, 125.0]
    taper_ratios = [0.08, 0.10, 0.12, 0.15, 0.18, 0.20, 0.25, 0.30]

    architectures = [
        {"name": "4枚非対称 十字翼 (Cross-Asym)", "type_key": "4-fin-asym", "is_4fin": True, "theta": 0.0, "vs": 0.85, "color": "#1f77b4"},
        {"name": "4枚対称 十字翼 (+)", "type_key": "4-fin-sym", "is_4fin": True, "theta": 0.0, "vs": 1.0, "color": "#7f7f7f"},
        {"name": "3枚非対称 逆Y字翼 (Inv-Y 35°)", "type_key": "3-fin-asym", "is_4fin": False, "theta": 35.0, "vs": 0.70, "color": "#2ca02c"},
        {"name": "3枚対称 120°翼 (Y)", "type_key": "3-fin-sym", "is_4fin": False, "theta": 30.0, "vs": 1.0, "color": "#17becf"},
        {"name": "3枚T字型 飛行機翼 (T-shape)", "type_key": "3-fin-t", "is_4fin": False, "theta": 0.0, "vs": 0.85, "color": "#ff7f0e"},
    ]

    spans = list(range(20, 76, 2))       # 20 to 74 mm (28)
    root_chords = list(range(16, 54, 2)) # 16 to 52 mm (19)

    t_total_start = time.perf_counter()
    all_results = []
    total_evaluated = 0

    for ln in nose_lengths:
        spec = RocketSpec(
            total_length_mm=250.0,
            body_diameter_mm=24.0,
            nose_length_mm=float(ln),
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
        u_opt = UltraFastOptimizer(spec)

        # Build grid for this nose length
        grid = []
        for arch in architectures:
            is_4fin = 1.0 if arch["is_4fin"] else 0.0
            theta = arch["theta"]
            vs = arch["vs"]

            for tr in taper_ratios:
                for span in spans:
                    for cr in root_chords:
                        if span > 2.2 * cr or span < 0.35 * cr:
                            continue
                        ct = cr * tr
                        meta = {
                            "nose": ln,
                            "arch_name": arch["name"],
                            "type_key": arch["type_key"],
                            "color": arch["color"],
                            "tr": tr,
                        }
                        grid.append((float(span), float(cr), float(ct), float(theta), float(vs), is_4fin, meta))

        total_evaluated += len(grid)
        res, elap, spd = u_opt.sweep(grid)

        # Filter valid
        for r in res:
            if 0.50 <= r["margin"] <= 1.55 and r["time"] >= 8.0:
                all_results.append(r)

    t_total_end = time.perf_counter()
    total_time = t_total_end - t_total_start

    print(f"Evaluated {total_evaluated:,} configurations across all nose lengths in {total_time:.3f} seconds!")
    print(f"Total valid configurations found: {len(all_results):,}")
    print(f"Average throughput: {total_evaluated / total_time:,.0f} configurations / second!")

    # Verify Setting A and Setting B are present
    set_a = [r for r in all_results if r["type_key"] == "3-fin-asym" and r["span"] == 66.0 and r["cr"] == 30.0 and r["nose"] == 125.0 and abs(r["tr"] - 0.12) < 1e-4]
    set_b = [r for r in all_results if r["type_key"] == "4-fin-sym" and r["span"] == 56.0 and r["cr"] == 26.0 and r["nose"] == 125.0 and abs(r["tr"] - 0.12) < 1e-4]

    print("\n【検証チェック】")
    if set_a:
        a = set_a[0]
        print(f"設定A: 高度 {a['apogee']} m | 滞空 {a['time']} s | マージン +{a['margin']} cal | 翼重量 {a['fin_mass']} g")
    if set_b:
        b = set_b[0]
        print(f"設定B: 高度 {b['apogee']} m | 滞空 {b['time']} s | マージン +{b['margin']} cal | 翼重量 {b['fin_mass']} g")

if __name__ == '__main__':
    main()
