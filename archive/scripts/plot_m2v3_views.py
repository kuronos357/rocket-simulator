import trimesh
import matplotlib.pyplot as plt
import numpy as np

mesh = trimesh.load("export/つくば＿ロケットm2 v3.stl")

fig, (ax_side, ax_top) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

# 側面図 (X-Y 平面投影: 横から見た輪郭)
# 点群を取得
pts = mesh.vertices
# ダウンサンプリング
idx = np.random.choice(len(pts), min(5000, len(pts)), replace=False)
sample_pts = pts[idx]

# 側面図: 横軸 Y (飛行軸 0~250), 縦軸 Z (上下)
ax_side.scatter(sample_pts[:, 1], sample_pts[:, 2], s=1, c='blue', alpha=0.5)
ax_side.set_title("Side View (Y vs Z: Blue = Mesh points)")
ax_side.set_ylabel("Z (mm)")
ax_side.axis('equal')
ax_side.grid(True)
ax_side.axvline(70, color='r', linestyle='--', label='Y=70 (Motor front)')
ax_side.axvline(180, color='g', linestyle='--', label='Y=180')
ax_side.legend()

# 上面図: 横軸 Y (飛行軸 0~250), 縦軸 X (左右)
ax_top.scatter(sample_pts[:, 1], sample_pts[:, 0], s=1, c='red', alpha=0.5)
ax_top.set_title("Top View (Y vs X: Red = Mesh points)")
ax_top.set_xlabel("Y (mm) [Flight Axis: 0=Tail, 250=Nose]")
ax_top.set_ylabel("X (mm)")
ax_top.axis('equal')
ax_top.grid(True)
ax_top.axvline(70, color='r', linestyle='--')
ax_top.axvline(180, color='g', linestyle='--')

plt.tight_layout()
plt.savefig("export/m2v3_side_top_view.png", dpi=150)
print("Saved inspection view to export/m2v3_side_top_view.png")
