import trimesh
import matplotlib.pyplot as plt
import numpy as np

m11 = trimesh.load("export/つくば＿ロケット v11.stl")
m12 = trimesh.load("export/つくば＿ロケット v12.stl")

print("v11 bounds:", m11.bounds)
print("v12 bounds:", m12.bounds)

print("v11 volume:", m11.volume, "area:", m11.area)
print("v12 volume:", m12.volume, "area:", m12.area)

# Let's inspect sections along Y axis
fig, axes = plt.subplots(1, 4, figsize=(16, 5))
y_cuts = [30, 60, 100, 140]

for idx, y in enumerate(y_cuts):
    ax = axes[idx]
    s11 = m11.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
    s12 = m12.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
    
    if s11:
        p11 = s11.vertices
        ax.scatter(p11[:, 0], p11[:, 2], s=1, c='blue', label='v11' if idx==0 else "")
    if s12:
        p12 = s12.vertices
        ax.scatter(p12[:, 0], p12[:, 2], s=1, c='red', label='v12' if idx==0 else "")
        
    ax.set_title(f"Cut at Y = {y} mm")
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Z (mm)")
    ax.axis('equal')
    ax.grid(True)
    if idx == 0:
        ax.legend()

plt.tight_layout()
plt.savefig("export/v11_v12_sections.png", dpi=150)
print("Saved section comparison to export/v11_v12_sections.png")
