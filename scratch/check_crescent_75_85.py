import sys, os
sys.path.insert(0, ".")
from scratch.optimize_mylar_120x1200 import calc_flight
import math

for span in [75.0, 80.0, 85.0]:
    for cr in [34.0, 36.0, 38.0, 40.0]:
        r = calc_flight(
            span, cr, 5.0, span*math.tan(math.radians(25)), 5.0,
            0.5, 1.2, 0.0, 1.0, True, min_chord_mm=2.5
        )
        if r and r["margin"] >= 1.00:
            print(f"span={span}mm, cr={cr}mm: Margin={r['margin']:.2f}cal, Time={r['hang_time']:.2f}s, Apo={r['apogee']:.1f}m, Mass={r['fin_mass']:.2f}g")
