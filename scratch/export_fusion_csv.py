"""
Export CSV coordinates for Fusion 360 ImportSplineCSV
=====================================================
Fusion 360 has a built-in sample script:
[Utilities] -> [Scripts and Add-Ins] -> [Samples] -> [ImportSplineCSV]
"""

import math
import numpy as np

def generate_csv(
    span_mm=75.0, cr_mm=28.0, ct_mm=10.0, te_deg=25.0,
    oh_mm=5.0, p_le=0.70, p_te=0.80, n_pts=50,
    out_path="output/practical_wing_profile.csv"
):
    te_sweep = span_mm * math.tan(math.radians(te_deg))
    le_sweep = cr_mm - ct_mm + te_sweep
    
    # Generate closed loop of points:
    # 1. Root: (0, -oh) to (0, -oh + cr)
    # 2. Leading Edge: (0, -oh + cr) -> (span, y_tip_le)
    # 3. Tip: (span, y_tip_le) -> (span, y_tip_te)
    # 4. Trailing Edge: (span, y_tip_te) -> (0, -oh)
    
    points = []
    
    # Leading edge (0 to span)
    for i in range(n_pts + 1):
        eta = i / float(n_pts)
        x = span_mm * eta
        y = -oh_mm + cr_mm - le_sweep * (eta ** p_le)
        points.append((x, y, 0.0))
        
    # Trailing edge (span down to 0)
    for i in range(n_pts, -1, -1):
        eta = i / float(n_pts)
        x = span_mm * eta
        y = -oh_mm - te_sweep * (eta ** p_te)
        points.append((x, y, 0.0))
        
    # Close loop
    points.append(points[0])
    
    with open(out_path, "w", encoding="utf-8") as f:
        # Fusion 360 ImportSplineCSV format: X, Y, Z (no header, or standard csv)
        for pt in points:
            f.write(f"{pt[0]:.4f},{pt[1]:.4f},{pt[2]:.4f}\n")
            
    print(f"Exported {len(points)} points to {out_path}")

if __name__ == "__main__":
    generate_csv()
