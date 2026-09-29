import sys
import os
import math
import numpy as np
import json

sys.path.insert(0, os.path.abspath("."))
from sim_engine.optimizer import RocketSpec, FinOptimizer
from scratch.test_correct_physics import evaluate_physically_correct_fins

def find_exact_candidates():
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
                    infill_ratio=0.02, # 2% unified
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
                                if 0.65 <= m_eff <= 1.35 and r["total_time_s"] >= 27.5:
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
                            if 0.65 <= m_eff <= 1.35 and r["total_time_s"] >= 27.5:
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

    print(f"Total results: {len(results)}")

    # 1. 0.8cal, 30.48s 4-fin-asym
    cands_4asym = [r for r in results if r["type"] == "4-fin-asym"]
    best_4asym = min(cands_4asym, key=lambda x: (x["margin_eff"] - 0.80)**2 + (x["time"] - 30.48)**2)

    # 2. 0.86cal, 30.25s 3-fin-asym
    cands_3asym = [r for r in results if r["type"] == "3-fin-asym"]
    best_3asym = min(cands_3asym, key=lambda x: (x["margin_eff"] - 0.86)**2 + (x["time"] - 30.25)**2)

    # 3. 1.22cal, 28.44s
    best_122 = min(results, key=lambda x: (x["margin_eff"] - 1.22)**2 + (x["time"] - 28.44)**2)

    output = {
        "candidate_1_4fin_asym": best_4asym,
        "candidate_2_3fin_asym": best_3asym,
        "candidate_3_high_stability": best_122
    }

    with open("scratch/selected_candidates.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("Successfully saved selected candidates!")

if __name__ == "__main__":
    find_exact_candidates()
