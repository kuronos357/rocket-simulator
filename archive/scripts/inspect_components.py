import trimesh
import numpy as np

m12 = trimesh.load("export/つくば＿ロケット v12.stl")

components = m12.split(only_watertight=False)
print(f"Total separate components in v12 STL: {len(components)}")
for i, c in enumerate(components):
    bounds = c.bounds
    print(f"Component {i}: bounds Y=[{bounds[0][1]:.1f}, {bounds[1][1]:.1f}], X=[{bounds[0][0]:.1f}, {bounds[1][0]:.1f}], Z=[{bounds[0][2]:.1f}, {bounds[1][2]:.1f}], area={c.area:.1f}, faces={len(c.faces)}")
