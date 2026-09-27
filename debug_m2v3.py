import trimesh
import numpy as np
import sys
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

m = trimesh.load("export/つくば＿ロケットm2 v3.stl")
print(f"Mesh bounds: {m.bounds}")
print(f"Extents: {m.extents}")
print(f"Vertices: {len(m.vertices)}, Faces: {len(m.faces)}")

# Cross sections to understand shape
print("\n=== Cross Sections Along Y ===")
for y in [10, 30, 50, 70, 100, 130, 160, 200, 240]:
    sl = m.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
    if sl:
        pts = sl.vertices
        x_min, x_max = pts[:, 0].min(), pts[:, 0].max()
        z_min, z_max = pts[:, 2].min(), pts[:, 2].max()
        print(f"Y={y:>3}mm: X=[{x_min:>6.1f}, {x_max:>6.1f}] span={x_max-x_min:>5.1f}, Z=[{z_min:>6.1f}, {z_max:>6.1f}] span={z_max-z_min:>5.1f}")
    else:
        print(f"Y={y:>3}mm: (no section)")

# aero.py のCP計算の問題を調査
# aero.py は Z軸を飛行軸と想定している (stdで変換する)
print("\n=== aero.py の座標変換を確認 ===")
from sim_engine.aero import AeroEngine
aero = AeroEngine(stl_path="export/つくば＿ロケットm2 v3.stl", flight_axis="y", ref_diameter_mm=20.0)
print(f"AeroEngine flight_axis: {aero.flight_axis}")
print(f"z_min: {aero.z_min}, z_max: {aero.z_max}")
print(f"ref_diameter: {aero.ref_diameter_mm}")
print(f"ref_area: {aero.ref_area_m2}")

# CGを61.6mmに設定してaero計算
aero_res = aero.compute_aerodynamics(velocity_m_s=40.0, alpha_deg=2.0, cg_z_mm=61.6)
print(f"\nAero result:")
for k, v in aero_res.items():
    print(f"  {k}: {v}")
