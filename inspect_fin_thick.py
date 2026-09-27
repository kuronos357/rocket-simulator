import trimesh
import numpy as np

mesh_v10 = trimesh.load("export/つくば＿ロケット v10.stl")
mesh_v11 = trimesh.load("export/つくば＿ロケット v11.stl")

print("v10 vertices:", len(mesh_v10.vertices), "faces:", len(mesh_v10.faces))
print("v11 vertices:", len(mesh_v11.vertices), "faces:", len(mesh_v11.faces))

# フィン断面の厚さを調べる (X軸方向、Y=20mm, Z=0付近)
# 翼の断面を Y=20mm の平面でスライス
slice_v10 = mesh_v10.section(plane_origin=[0, 20, 0], plane_normal=[0, 1, 0])
slice_v11 = mesh_v11.section(plane_origin=[0, 20, 0], plane_normal=[0, 1, 0])

# X方向の翼（3時・9時、X=20〜40mm付近のZ方向厚さ）
pts_v10 = slice_v10.vertices
pts_v11 = slice_v11.vertices

# Xが25〜30mmの領域のZの厚さ
mask10 = (pts_v10[:, 0] > 25) & (pts_v10[:, 0] < 35)
mask11 = (pts_v11[:, 0] > 25) & (pts_v11[:, 0] < 35)

print("v10 fin thickness at span 25~35mm (Z range):", pts_v10[mask10, 2].max() - pts_v10[mask10, 2].min(), "mm")
print("v11 fin thickness at span 25~35mm (Z range):", pts_v11[mask11, 2].max() - pts_v11[mask11, 2].min(), "mm")
