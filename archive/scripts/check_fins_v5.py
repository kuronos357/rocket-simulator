import trimesh
import numpy as np

m = trimesh.load("export/つくば＿ロケットm2 v5.stl")

# Y=10mm での断面
sl = m.section(plane_origin=[0, 10, 0], plane_normal=[0, 1, 0])
pts = sl.vertices

print("Slice at Y=10mm for m2 v5:")
print(f"X min/max: [{pts[:, 0].min():.1f}, {pts[:, 0].max():.1f}]")
print(f"Z min/max: [{pts[:, 2].min():.1f}, {pts[:, 2].max():.1f}]")

# フィンの枚数と位置を確認
p_3 = pts[pts[:, 0] > 12]
p_9 = pts[pts[:, 0] < -12]
p_12 = pts[pts[:, 2] > 12]
p_6 = pts[pts[:, 2] < -12]

print(f"3-oclock fin (X>12): {len(p_3)} points, max X = {p_3[:, 0].max() if len(p_3)>0 else 'None'}")
print(f"9-oclock fin (X<-12): {len(p_9)} points, min X = {p_9[:, 0].min() if len(p_9)>0 else 'None'}")
print(f"12-oclock fin (Z>12): {len(p_12)} points, max Z = {p_12[:, 2].max() if len(p_12)>0 else 'None'}")
print(f"6-oclock fin (Z<-12): {len(p_6)} points, min Z = {p_6[:, 2].min() if len(p_6)>0 else 'None'}")
