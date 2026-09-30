import json

with open("scratch/run_practical_ranking.py", "r", encoding="utf-8") as f:
    pass

import sys, os
sys.path.insert(0, ".")
from scratch.run_practical_ranking import calc_practical_flight
import numpy as np

# Find best 3-fin practical designs
spans = np.arange(55.0, 85.1, 2.5)
crs = np.arange(28.0, 48.1, 2.0)
cts = np.array([8.0, 10.0, 12.0, 14.0, 16.0, 18.0])
te_angles = np.array([0.0, 10.0, 15.0, 20.0, 25.0])
overhangs = np.array([0.0, 5.0, 10.0])
p_les = np.array([0.7, 0.85, 1.0, 1.2])
p_tes = np.array([0.8, 1.0, 1.2])

results_3f = []
for span in spans:
    for cr in crs:
        for ct in cts:
            if ct >= cr * 0.65: continue
            for te_ang in te_angles:
                te_sw = span * np.tan(np.radians(te_ang))
                for oh in overhangs:
                    for p_le in p_les:
                        for p_te in p_tes:
                            for v_sc in [0.80, 0.90, 1.00]:
                                r = calc_practical_flight(
                                    span, cr, ct, te_sw, oh,
                                    p_le, p_te,
                                    35.0, v_sc, False,
                                    min_chord_mm=8.0
                                )
                                if r and r["margin"] >= 1.00:
                                    r["te_angle"] = te_ang
                                    results_3f.append(r)

print(f"3-Fin valid practical count: {len(results_3f)}")
results_3f.sort(key=lambda x: x["hang_time"], reverse=True)
print("\nTop 5 3-Fin Practical Designs:")
for r in results_3f[:5]:
    print(f"  v_sc={r['v_scale']:.2f}, span={r['span']}mm, cr={r['cr']}mm, ct={r['ct']}mm, te_ang={r['te_angle']}°, oh={r['overhang']}mm, ple={r['p_le']}, pte={r['p_te']} -> margin={r['margin']:.2f}cal, time={r['hang_time']:.2f}s, apo={r['apogee']:.1f}m, mass={r['fin_mass']:.2f}g")
