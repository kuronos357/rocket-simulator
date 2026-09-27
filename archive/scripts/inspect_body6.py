import trimesh
import numpy as np

# ボディ6の領域: X in [-1, 1], Y in [0, 75], Z in [9, 40]
m = trimesh.load("export/つくば＿ロケットm2 v3.stl")
pts = m.vertices

mask_b6 = (pts[:, 0] >= -1.0) & (pts[:, 0] <= 1.0) & (pts[:, 1] >= 0.0) & (pts[:, 1] <= 75.0) & (pts[:, 2] >= 9.0)
pts_b6 = pts[mask_b6]

print(f"Points in Body 6 region: {len(pts_b6)}")
print(f"Y min: {pts_b6[:, 1].min():.2f}, Y max: {pts_b6[:, 1].max():.2f}")
print(f"Z min: {pts_b6[:, 2].min():.2f}, Z max: {pts_b6[:, 2].max():.2f}")

# YごとのZの最大値を調べる (前縁・後端のプロファイル)
y_samples = np.linspace(pts_b6[:, 1].min(), pts_b6[:, 1].max(), 10)
print("\nProfile of Body 6 (Y vs Z_max):")
for y in y_samples:
    sub = pts_b6[abs(pts_b6[:, 1] - y) < 4.0]
    if len(sub) > 0:
        print(f"  Y = {y:5.1f} mm: Z_min = {sub[:, 2].min():4.1f}, Z_max = {sub[:, 2].max():4.1f}")
