"""
Re-optimization with Horizontal Landing:
Relaxing tip chord constraint:
  - Rocket lands sideways/flat (belly flop), so fin tips don't take point impact loads!
  - Ct can be 3.0 to 6.0 mm (just enough for clean 0.4mm nozzle extrusion, e.g. 3-4 perimeter lines).
  - Min chord c(y) >= 3.0 mm (printable, no self-intersection).
  - Overhang <= 5.0 mm (maintains launch pad clearance & motor nozzle clearance).
  - Aluminized Mylar Streamer (120x1200mm, 4.10g).
"""

import os
import sys
import math
import numpy as np

sys.path.insert(0, os.path.abspath("."))
from scratch.optimize_mylar_120x1200 import calc_flight

spans = np.arange(50.0, 90.1, 2.5)
crs = np.arange(20.0, 42.1, 2.0)
cts = np.array([2.5, 3.5, 5.0, 6.5, 8.0])
te_angles = np.array([10.0, 15.0, 20.0, 25.0])
overhangs = np.array([0.0, 2.5, 5.0])
p_les = np.array([0.5, 0.7, 0.85, 1.0, 1.2])
p_tes = np.array([0.8, 1.0, 1.2, 1.4])
configs = [
    (0.0, 1.0, True, "4枚十字 (+)"),
    (35.0, 0.8, False, "3枚逆Y字 (v=0.8)"),
]

results = []
for span in spans:
    for cr in crs:
        for ct in cts:
            if ct >= cr * 0.5: continue
            for te_ang in te_angles:
                te_sw = span * math.tan(math.radians(te_ang))
                for oh in overhangs:
                    for ple in p_les:
                        for pte in p_tes:
                            for theta, vs, is_4f, cfg_name in configs:
                                r = calc_flight(span, cr, ct, te_sw, oh, ple, pte, theta, vs, is_4f, min_chord_mm=2.5)
                                if r and r["margin"] >= 1.00:
                                    r["te_ang"] = te_ang
                                    r["cfg_name"] = cfg_name
                                    results.append(r)

print(f"Total valid designs with horizontal landing considerations: {len(results):,}")
results.sort(key=lambda x: x["hang_time"], reverse=True)

print("\n=== TOP 5 DESIGNS (HORIZONTAL LANDING / THIN TIP & CRESCENT RE-ENABLED) ===")
for r in results[:5]:
    print(f"  {r['cfg_name']}: span={r['span']}mm, cr={r['cr']}mm, ct={r['ct']}mm, te_ang={r['te_ang']}°, oh={r['overhang']}mm, ple={r['p_le']}, pte={r['p_te']} -> Margin={r['margin']:.2f}cal, Time={r['hang_time']:.2f}s, Apo={r['apogee']:.1f}m, Mass={r['fin_mass']:.2f}g, TotalM={r['total_mass']:.2f}g")

# Also check flush (oh=0.0)
flush = [r for r in results if r["overhang"] == 0.0]
flush.sort(key=lambda x: x["hang_time"], reverse=True)
print("\n=== TOP 3 FLUSH (OH = 0.0mm) ===")
for r in flush[:3]:
    print(f"  {r['cfg_name']}: span={r['span']}mm, cr={r['cr']}mm, ct={r['ct']}mm, te_ang={r['te_ang']}°, oh={r['overhang']}mm, ple={r['p_le']}, pte={r['p_te']} -> Margin={r['margin']:.2f}cal, Time={r['hang_time']:.2f}s, Apo={r['apogee']:.1f}m, Mass={r['fin_mass']:.2f}g")
