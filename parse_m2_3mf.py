import zipfile
import xml.etree.ElementTree as ET
import numpy as np
import trimesh

path = "つくば＿ロケットm2.3mf"
with zipfile.ZipFile(path, 'r') as z:
    xml_data = z.read("3D/3dmodel.model")
    root = ET.fromstring(xml_data)

# Print root info and namespaces
print("Root tag:", root.tag)
print("Root attrib:", root.attrib)

# Find all namespaces
ns = {}
for prefix, uri in root.attrib.items():
    if prefix.startswith("xmlns"):
        ns[prefix] = uri

# Parse objects and meshes
# Standard 3MF namespace is http://schemas.microsoft.com/3dmanufacturing/core/2015/02
# Tag without prefix if default xmlns
default_ns = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"

objects = []
for obj in root.iter(f"{{{default_ns}}}object"):
    obj_id = obj.attrib.get("id")
    obj_name = obj.attrib.get("name", "unnamed")
    obj_type = obj.attrib.get("type", "model")
    mesh_el = obj.find(f"{{{default_ns}}}mesh")
    if mesh_el is not None:
        v_el = mesh_el.find(f"{{{default_ns}}}vertices")
        t_el = mesh_el.find(f"{{{default_ns}}}triangles")
        verts = [[float(v.attrib['x']), float(v.attrib['y']), float(v.attrib['z'])] for v in v_el.findall(f"{{{default_ns}}}vertex")]
        tris = [[int(t.attrib['v1']), int(t.attrib['v2']), int(t.attrib['v3'])] for t in t_el.findall(f"{{{default_ns}}}triangle")]
        verts = np.array(verts)
        tris = np.array(tris)
        m = trimesh.Trimesh(vertices=verts, faces=tris)
        print(f"\nObject ID={obj_id}, Name='{obj_name}', Type={obj_type}")
        print(f"  Vertices: {len(verts)}, Faces: {len(tris)}")
        print(f"  Bounds: {m.bounds}")
        print(f"  Extents: {m.extents}")
        objects.append((obj_id, obj_name, m))

# Build items (components/instances)
build_el = root.find(f"{{{default_ns}}}build")
if build_el is not None:
    print("\nBuild items:")
    for item in build_el.findall(f"{{{default_ns}}}item"):
        obj_id = item.attrib.get("objectid")
        transform = item.attrib.get("transform", "identity")
        print(f"  Item objectid={obj_id}, transform={transform}")
