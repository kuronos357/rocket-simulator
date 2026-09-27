import trimesh
import matplotlib.pyplot as plt
import numpy as np

m = trimesh.load("export/つくば＿ロケットm2 v5.stl")

# 3時フィン (X > 9) の面を抽出
face_centers = m.triangles_center
mask_faces = face_centers[:, 0] > 9.5
submesh = m.submesh([mask_faces], append=True)

fig, ax = plt.subplots(figsize=(8, 6))
# 頂点投影
pts = submesh.vertices
ax.scatter(pts[:, 1], pts[:, 0], s=2, c='blue')
ax.set_title("3-oclock Fin Mesh Vertices (Y vs X)")
ax.set_xlabel("Y (mm) [0 is Tail]")
ax.set_ylabel("X (mm) [10 is Body surface]")
ax.grid(True)
plt.savefig("export/fin3_inspection.png", dpi=150)
print(f"Saved 3-oclock fin inspection to export/fin3_inspection.png (Faces: {len(submesh.faces)}, Vertices: {len(pts)})")
