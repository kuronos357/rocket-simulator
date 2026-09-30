import sys, os
sys.path.insert(0, ".")
from scratch.run_practical_ranking import calc_practical_flight
import numpy as np

# Check 3-fin with oh=5 and oh=0
for oh in [5.0, 0.0]:
    bests = []
    for span in np.arange(65.0, 85.1, 2.5):
        for cr in np.arange(28.0, 48.1, 2.0):
            for ct in [10.0, 12.0, 14.0]:
                for te_ang in [15.0, 20.0, 25.0]:
                    te_sw = span * np.tan(np.radians(te_ang))
                    for p_le in [0.7, 0.85, 1.0]:
                        for p_te in [0.8, 1.0]:
                            for v_sc in [0.80, 1.00]:
                                r = calc_practical_flight(
                                    span, cr, ct, te_sw, oh,
                                    p_le, p_te,
                                    35.0, v_sc, False,
                                    min_chord_mm=8.0
                                )
                                if r and r["margin"] >= 0.98:
                                    r["te_angle"] = te_ang
                                    bests.append(r)
    bests.sort(key=lambda x: x["hang_time"], reverse=True)
    print(f"3-Fin OH={oh}mm best count: {len(bests)}")
    if bests:
        r = bests[0]
        print(f"  Best OH={oh}mm: v_sc={r['v_scale']}, span={r['span']}mm, cr={r['cr']}mm, ct={r['ct']}mm, te_ang={r['te_angle']}°, ple={r['p_le']}, pte={r['p_te']} -> margin={r['margin']:.2f}cal, time={r['hang_time']:.2f}s, apo={r['apogee']:.1f}m, mass={r['fin_mass']:.2f}g")
