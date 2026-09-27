import trimesh
import numpy as np

mesh = trimesh.load("export/つくば＿ロケットm2 v3.stl")

# Y=10mm (テール付近) の断面プロファイルをプロットしてフィンの位置を確認
sl = mesh.section(plane_origin=[0, 10, 0], plane_normal=[0, 1, 0])
pts = sl.vertices

print("Slice at Y=10mm:")
print("X range:", pts[:, 0].min(), "to", pts[:, 0].max())
print("Z range:", pts[:, 2].min(), "to", pts[:, 2].max())

# 各フィンの先端座標を調べる
# Xの正側 (3時フィン?)
p_3 = pts[pts[:, 0] > 15]
print(f"3-oclock fin: X max = {p_3[:, 0].max():.1f}, Z range = [{p_3[:, 2].min():.1f}, {p_3[:, 2].max():.1f}]")

# Xの負側 (9時フィン?)
p_9 = pts[pts[:, 0] < -15]
print(f"9-oclock fin: X min = {p_9[:, 0].min():.1f}, Z range = [{p_9[:, 2].min():.1f}, {p_9[:, 2].max():.1f}]")

# Zの正側 (12時フィン?)
p_12 = pts[pts[:, 2] > 15]
print(f"12-oclock fin: Z max = {p_12[:, 2].max():.1f}, X range = [{p_12[:, 0].min():.1f}, {p_12[:, 0].max():.1f}]")
