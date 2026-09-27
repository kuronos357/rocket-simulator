import trimesh
import numpy as np

mesh = trimesh.load("export/つくば＿ロケット v8.stl")

y_samples = np.linspace(70, 185, 15)
print("Cross section bounds along Y:")
for y in y_samples:
    slice_3d = mesh.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
    if slice_3d:
        # min and max coordinates
        pts = slice_3d.vertices
        x_min, x_max = pts[:, 0].min(), pts[:, 0].max()
        z_min, z_max = pts[:, 2].min(), pts[:, 2].max()
        print(f"Y={y:5.1f}mm: X=[{x_min:5.2f}, {x_max:5.2f}] (span={x_max-x_min:4.1f}), Z=[{z_min:5.2f}, {z_max:5.2f}] (span={z_max-z_min:4.1f})")
    else:
        print(f"Y={y:5.1f}mm: None")
