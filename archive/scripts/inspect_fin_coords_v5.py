import trimesh
import numpy as np

m = trimesh.load("export/つくば＿ロケットm2 v5.stl")
pts = m.vertices

# 3時フィン (X > 12)
p3 = pts[pts[:, 0] > 12]
print("3-oclock fin (X > 12):")
print(f"  X: [{p3[:, 0].min():.1f}, {p3[:, 0].max():.1f}]")
print(f"  Y: [{p3[:, 1].min():.1f}, {p3[:, 1].max():.1f}]")
print(f"  Z: [{p3[:, 2].min():.1f}, {p3[:, 2].max():.1f}]")

# 12時フィン (Z > 12)
p12 = pts[pts[:, 2] > 12]
print("\n12-oclock fin (Z > 12):")
print(f"  X: [{p12[:, 0].min():.1f}, {p12[:, 0].max():.1f}]")
print(f"  Y: [{p12[:, 1].min():.1f}, {p12[:, 1].max():.1f}]")
print(f"  Z: [{p12[:, 2].min():.1f}, {p12[:, 2].max():.1f}]")

# Yごとの断面でフィンのコード長（根元と翼端）を測定
print("\n3-oclock fin chord inspection:")
for x in [12, 20, 30, 40]:
    sub = p3[abs(p3[:, 0] - x) < 2.0]
    if len(sub) > 0:
        print(f"  X={x}mm: Y in [{sub[:, 1].min():.1f}, {sub[:, 1].max():.1f}], length = {sub[:, 1].max() - sub[:, 1].min():.1f}mm")

print("\n12-oclock fin chord inspection:")
for z in [12, 20, 30]:
    sub = p12[abs(p12[:, 2] - z) < 2.0]
    if len(sub) > 0:
        print(f"  Z={z}mm: Y in [{sub[:, 1].min():.1f}, {sub[:, 1].max():.1f}], length = {sub[:, 1].max() - sub[:, 1].min():.1f}mm")
