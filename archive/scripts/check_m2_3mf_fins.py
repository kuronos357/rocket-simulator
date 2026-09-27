import zipfile
import xml.etree.ElementTree as ET
import numpy as np
import trimesh
import matplotlib.pyplot as plt

path = "つくば＿ロケットm2.3mf"
with zipfile.ZipFile(path, 'r') as z:
    xml_data = z.read("3D/3dmodel.model")
    root = ET.fromstring(xml_data)

default_ns = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
ns = f"{{{default_ns}}}"

# Object 3 is the fuselage + fins
for obj in root.iter(f"{ns}object"):
    if obj.attrib.get("id") == "3":
        mesh_el = obj.find(f"{ns}mesh")
        v_el = mesh_el.find(f"{ns}vertices")
        t_el = mesh_el.find(f"{ns}triangles")
        verts = np.array([[float(v.attrib['x']), float(v.attrib['y']), float(v.attrib['z'])] for v in v_el.findall(f"{ns}vertex")])
        tris = np.array([[int(t.attrib['v1']), int(t.attrib['v2']), int(t.attrib['v3'])] for t in t_el.findall(f"{ns}triangle")])
        m_body = trimesh.Trimesh(vertices=verts, faces=tris)
        break

print("Extracted Fuselage Mesh (Object 3):")
print(f"  Vertices: {len(m_body.vertices)}, Faces: {len(m_body.faces)}")
print(f"  Bounds: {m_body.bounds}")

# 3時フィン (X > 10) を調べる
p3 = m_body.vertices[m_body.vertices[:, 0] > 10.0]
print(f"  Points with X > 10: {len(p3)}")

# X ごとの Y 範囲
for x_val in np.linspace(10, 45, 8):
    sub = p3[abs(p3[:, 0] - x_val) < 2.5]
    if len(sub) > 0:
        print(f"  X = {x_val:5.1f} mm: Y in [{sub[:, 1].min():5.1f}, {sub[:, 1].max():5.1f}] (len={sub[:, 1].max()-sub[:, 1].min():4.1f}mm), Z in [{sub[:, 2].min():4.1f}, {sub[:, 2].max():4.1f}]")
    else:
        print(f"  X = {x_val:5.1f} mm: (no points)")

# プロットして保存
fig, ax = plt.subplots(figsize=(8, 6))
ax.scatter(p3[:, 1], p3[:, 0], s=3, c='red')
ax.set_title("3MF Object 3: 3-oclock Fin Vertices (Y vs X)")
ax.set_xlabel("Y (mm)")
ax.set_ylabel("X (mm)")
ax.grid(True)
plt.savefig("export/m2_3mf_fin3_check.png", dpi=150)
print("Saved fin check plot to export/m2_3mf_fin3_check.png")
