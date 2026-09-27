import trimesh
import numpy as np

m = trimesh.load("export/つくば＿ロケットm2 v5.stl")
p3 = m.vertices[m.vertices[:, 0] > 10.0]

for x_val in np.linspace(10, 45, 8):
    sub = p3[abs(p3[:, 0] - x_val) < 2.5]
    if len(sub) > 0:
        print(f"X = {x_val:5.1f} mm: Y in [{sub[:, 1].min():5.1f}, {sub[:, 1].max():5.1f}] (len={sub[:, 1].max()-sub[:, 1].min():4.1f}mm), Z in [{sub[:, 2].min():4.1f}, {sub[:, 2].max():4.1f}]")
    else:
        print(f"X = {x_val:5.1f} mm: (no points)")
