import trimesh
import numpy as np

m10 = trimesh.load("export/つくば＿ロケット v10.stl")
m11 = trimesh.load("export/つくば＿ロケット v11.stl")

print("v10 bounds:", m10.bounds)
print("v11 bounds:", m11.bounds)

print("v10 extents:", m10.extents)
print("v11 extents:", m11.extents)

print("v10 area:", m10.area)
print("v11 area:", m11.area)
