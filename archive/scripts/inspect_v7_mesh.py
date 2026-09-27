import trimesh
import matplotlib.pyplot as plt
import numpy as np

# Load STL
mesh = trimesh.load('export/つくば＿ロケット v7.stl')

# Standardize: Y is flight axis (0 -> 190mm)
# Vertices
v = mesh.vertices

fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 6))

# 1. 側面図 (XY面: 左右フィンの広がり)
ax1.scatter(v[:, 0], v[:, 1], s=0.1, color='blue', alpha=0.3)
ax1.set_xlabel("X [mm] (Horizontal Fins: 3h & 9h)")
ax1.set_ylabel("Y [mm] (Flight Axis)")
ax1.set_title("Front View (XY Plane)")
ax1.axis('equal')
ax1.grid(True, alpha=0.3)

# 2. 側面図 (ZY面: 上部垂直フィンの広がり)
ax2.scatter(v[:, 2], v[:, 1], s=0.1, color='green', alpha=0.3)
ax2.set_xlabel("Z [mm] (Vertical Fin: 12h)")
ax2.set_ylabel("Y [mm] (Flight Axis)")
ax2.set_title("Side View (ZY Plane)")
ax2.axis('equal')
ax2.grid(True, alpha=0.3)

# 3. 断面図 (XZ面: 後方からノズルを見た図)
ax3.scatter(v[:, 0], v[:, 2], s=0.1, color='red', alpha=0.3)
ax3.set_xlabel("X [mm]")
ax3.set_ylabel("Z [mm]")
ax3.set_title("Rear View (Cross Section XZ)")
ax3.axis('equal')
ax3.grid(True, alpha=0.3)

plt.tight_layout()
out_png = "export/v7_shape_inspection.png"
plt.savefig(out_png, dpi=150)
plt.close()
print(f"Shape inspection saved: {out_png}")
