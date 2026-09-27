import trimesh
import numpy as np

mesh_v10 = trimesh.load("export/つくば＿ロケット v10.stl")
mesh_v11 = trimesh.load("export/つくば＿ロケット v11.stl")

for name, m in [("v10", mesh_v10), ("v11", mesh_v11)]:
    sl = m.section(plane_origin=[0, 20, 0], plane_normal=[0, 1, 0])
    pts = sl.vertices
    print(f"=== {name} at Y=20mm ===")
    print("X min/max:", pts[:, 0].min(), pts[:, 0].max())
    print("Z min/max:", pts[:, 2].min(), pts[:, 2].max())
    # 翼がある場所 (X > 15mm)
    mask = pts[:, 0] > 15
    if np.any(mask):
        sub_pts = pts[mask]
        print("Fin area X>15mm, Z range:", sub_pts[:, 2].min(), "to", sub_pts[:, 2].max(), "diff:", sub_pts[:, 2].max() - sub_pts[:, 2].min())
        # check thickness locally
        x_val = 20.0
        local = pts[(pts[:, 0] > 19.5) & (pts[:, 0] < 20.5)]
        if len(local) > 0:
            print("Thickness around X=20:", local[:, 2].max() - local[:, 2].min())
