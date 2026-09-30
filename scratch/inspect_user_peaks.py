import sys
import os
import numpy as np

sys.path.insert(0, os.path.abspath("."))
from sim_engine.optimizer import RocketSpec, FinOptimizer
from scratch.test_correct_physics import evaluate_physically_correct_fins

streamer_area = 250.0
streamer_mass = 1.2
streamer_cd = 0.25

results = []
configs = [
    ("PLA", 1.24, [250], [100, 120], [0.0, 1.0]),
]

for mat_name, mat_rho, lengths, noses, ballasts in configs:
    for L in lengths:
        for nose in noses:
            for m_bal in ballasts:
                spec = RocketSpec(
                    total_length_mm=float(L),
                    body_diameter_mm=24.0,
                    nose_length_mm=float(nose),
                    tail_length_mm=0.0,
                    wall_thickness_mm=0.4,
                    infill_ratio=0.02,
                    material=mat_name,
                    material_density=mat_rho,
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
                for th in [25, 30, 35]:
                    for vs in [0.6, 0.7, 0.8, 1.0]:
                        for span in range(35, 85, 4):
                            for cr in range(25, 55, 4):
                                if span > 1.8 * cr or span < 0.35 * cr:
                                    continue
                                r = evaluate_physically_correct_fins(opt, float(span), float(cr), 0.0, float(th), vs, is_4fin=False)
                                m_eff = min(r["margin_pitch"], r["margin_yaw"])
                                if 0.65 <= m_eff <= 1.35 and r["total_time_s"] >= 7.5:
                                    is_asym = (th != 30 or vs != 1.0)
                                    results.append({
                                        "margin_eff": m_eff,
                                        "time": r["total_time_s"],
                                        "apogee": r["apogee_m"],
                                        "L": L,
                                        "nose": nose,
                                        "bal": m_bal,
                                        "span": span,
                                        "cr": cr,
                                        "vs": vs,
                                        "th": th,
                                        "is_4fin": False,
                                        "type": "3-asym" if is_asym else "3-sym"
                                    })

                # 4-Fin scan
                for vs in [0.70, 0.80, 0.85, 0.90, 1.0]:
                    for span in range(35, 75, 4):
                        for cr in range(20, 48, 4):
                            if span > 1.8 * cr or span < 0.35 * cr:
                                continue
                            r = evaluate_physically_correct_fins(opt, float(span), float(cr), 0.0, 0.0, vs, is_4fin=True)
                            m_eff = min(r["margin_pitch"], r["margin_yaw"])
                            if 0.65 <= m_eff <= 1.35 and r["total_time_s"] >= 7.5:
                                results.append({
                                    "margin_eff": m_eff,
                                    "time": r["total_time_s"],
                                    "apogee": r["apogee_m"],
                                    "L": L,
                                    "nose": nose,
                                    "bal": m_bal,
                                    "span": span,
                                    "cr": cr,
                                    "vs": vs,
                                    "th": 0.0,
                                    "is_4fin": True,
                                    "type": "4-sym" if vs == 1.0 else "4-asym"
                                })

print(f"Total points generated: {len(results)}")

# Find peaks circled by user:
# 1. near 0.74
p1_cands = [r for r in results if 0.73 <= r["margin_eff"] <= 0.76]
top1 = sorted(p1_cands, key=lambda x: x["time"], reverse=True)[:5]
print("\n=== TOP AROUND 0.74 CAL ===")
for t in top1:
    print(f"Time: {t['time']:.3f}s, Margin: {t['margin_eff']:.3f}, Type: {t['type']}, span={t['span']}, cr={t['cr']}, vs={t['vs']}, nose={t['nose']}, bal={t['bal']}, apo={t['apogee']:.1f}")

# 2. near 0.925
p2_cands = [r for r in results if 0.91 <= r["margin_eff"] <= 0.94]
top2 = sorted(p2_cands, key=lambda x: x["time"], reverse=True)[:5]
print("\n=== TOP AROUND 0.925 CAL ===")
for t in top2:
    print(f"Time: {t['time']:.3f}s, Margin: {t['margin_eff']:.3f}, Type: {t['type']}, span={t['span']}, cr={t['cr']}, vs={t['vs']}, nose={t['nose']}, bal={t['bal']}, apo={t['apogee']:.1f}")

# 3. near 1.16
p3_cands = [r for r in results if 1.14 <= r["margin_eff"] <= 1.18]
top3 = sorted(p3_cands, key=lambda x: x["time"], reverse=True)[:5]
print("\n=== TOP AROUND 1.16 CAL ===")
for t in top3:
    print(f"Time: {t['time']:.3f}s, Margin: {t['margin_eff']:.3f}, Type: {t['type']}, span={t['span']}, cr={t['cr']}, vs={t['vs']}, nose={t['nose']}, bal={t['bal']}, apo={t['apogee']:.1f}")

# Also check why 機体①, ②, ③ were at (0.79, 9.59), (0.86, 9.25), (1.22, 8.84)
print("\n=== CANDIDATES COMPARISON ===")
for m_target, name in [(0.79, "C1"), (0.86, "C2"), (1.22, "C3")]:
    cands = [r for r in results if abs(r["margin_eff"] - m_target) <= 0.02]
    best = max(cands, key=lambda x: x["time"]) if cands else None
    if best:
        print(f"{name} Target ~{m_target}: Time={best['time']:.3f}s, Margin={best['margin_eff']:.3f}, Type={best['type']}, span={best['span']}, cr={best['cr']}, nose={best['nose']}, bal={best['bal']}")
