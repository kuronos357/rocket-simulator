import trimesh
import numpy as np
import matplotlib.pyplot as plt

m = trimesh.load("export/つくば＿ロケットm2 v7.stl")
print("=== m2 v7 Mesh Inspection ===")
print("Bounds:", m.bounds)
print("Extents:", m.extents)
print(f"Vertices: {len(m.vertices)}, Faces: {len(m.faces)}")

# 1. Yごとの断面寸法
print("\n--- Cross Sections along Y ---")
for y in [10, 30, 50, 70, 100, 130, 160, 175, 200, 220, 240]:
    sl = m.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
    if sl:
        pts = sl.vertices
        x_min, x_max = pts[:, 0].min(), pts[:, 0].max()
        z_min, z_max = pts[:, 2].min(), pts[:, 2].max()
        print(f"Y={y:>3}mm: X=[{x_min:>6.1f}, {x_max:>6.1f}] span={x_max-x_min:>5.1f}, Z=[{z_min:>6.1f}, {z_max:>6.1f}] span={z_max-z_min:>5.1f}")
    else:
        print(f"Y={y:>3}mm: None")

# 2. フィン (X > 10) の点群確認 (面抜けが直ったか？)
p3 = m.vertices[m.vertices[:, 0] > 10.0]
print(f"\n3-oclock fin points (X > 10): {len(p3)}")
for x_val in np.linspace(10, 45, 8):
    sub = p3[abs(p3[:, 0] - x_val) < 2.5]
    if len(sub) > 0:
        print(f"  X = {x_val:5.1f} mm: Y in [{sub[:, 1].min():5.1f}, {sub[:, 1].max():5.1f}] (len={sub[:, 1].max()-sub[:, 1].min():4.1f}mm), Z in [{sub[:, 2].min():4.1f}, {sub[:, 2].max():4.1f}]")
    else:
        print(f"  X = {x_val:5.1f} mm: (no points)")

# 3. 側面図・上面図をプロット
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
idx = np.random.choice(len(m.vertices), min(6000, len(m.vertices)), replace=False)
sample = m.vertices[idx]

ax1.scatter(sample[:, 1], sample[:, 2], s=1, c='blue', alpha=0.5)
ax1.set_title("Side View (Y vs Z) - m2 v7")
ax1.set_ylabel("Z (mm)")
ax1.axis('equal')
ax1.grid(True)
ax1.axvline(70, color='r', linestyle='--', label='Y=70')
ax1.axvline(175, color='g', linestyle='--', label='Y=175')
ax1.legend()

ax2.scatter(sample[:, 1], sample[:, 0], s=1, c='red', alpha=0.5)
ax2.set_title("Top View (Y vs X) - m2 v7")
ax2.set_xlabel("Y (mm)")
ax2.set_ylabel("X (mm)")
ax2.axis('equal')
ax2.grid(True)
ax2.axvline(70, color='r', linestyle='--')
ax2.axvline(175, color='g', linestyle='--')

plt.tight_layout()
plt.savefig("export/m2v7_views.png", dpi=150)
print("\nSaved projection views to export/m2v7_views.png")
