import zipfile
import xml.etree.ElementTree as ET
import numpy as np
import trimesh

path = "つくば＿ロケット.gcode.3mf"
with zipfile.ZipFile(path, 'r') as z:
    for name in z.namelist():
        if name.endswith(".model"):
            print("Found model file:", name)
            xml_data = z.read(name)
            root = ET.fromstring(xml_data)
            # 3MF namespace
            ns = {'m': 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
            
            # mesh vertices & triangles
            for obj in root.findall('.//m:object', ns):
                obj_id = obj.attrib.get('id')
                name_attr = obj.attrib.get('name', 'unnamed')
                mesh_el = obj.find('m:mesh', ns)
                if mesh_el is not None:
                    verts = []
                    for v in mesh_el.findall('.//m:vertex', ns):
                        verts.append([float(v.attrib['x']), float(v.attrib['y']), float(v.attrib['z'])])
                    tris = []
                    for t in mesh_el.findall('.//m:triangle', ns):
                        tris.append([int(t.attrib['v1']), int(t.attrib['v2']), int(t.attrib['v3'])])
                    verts = np.array(verts)
                    tris = np.array(tris)
                    print(f"Object {obj_id} ({name_attr}): {len(verts)} vertices, {len(tris)} triangles")
                    if len(verts) > 0:
                        m = trimesh.Trimesh(vertices=verts, faces=tris)
                        print(f"  Bounds: {m.bounds}")
