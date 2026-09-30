import json
import numpy as np
import sys, os
sys.path.insert(0, ".")
from scratch.run_practical_ranking import calc_practical_flight

for span in [55, 60, 65, 70, 75]:
    for oh in [0, 5, 10]:
        for te_ang in [15, 20, 25]:
            te_sw = span * np.tan(np.radians(te_ang))
            r = calc_practical_flight(
                span, 40.0, 10.0, te_sw, oh,
                0.85, 1.1,
                0.0, 1.0, True, min_chord_mm=8.0
            )
            if r:
                print(f"span={span}, oh={oh}, te_ang={te_ang} -> margin={r['margin']:.2f}, time={r['hang_time']:.2f}, apo={r['apogee']:.1f}, mass={r['fin_mass']:.2f}g")
