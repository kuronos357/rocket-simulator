import zipfile
import xml.etree.ElementTree as ET
import numpy as np
import trimesh

path = "つくば＿ロケット.gcode.3mf"
with zipfile.ZipFile(path, 'r') as z:
    xml_data = z.read("3D/3dmodel.model")
    root = ET.fromstring(xml_data)
    
    # xmlns default is 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
    ns = '{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}'
    
    meshes = []
    for obj in root.iter(f'{ns}object'):
        obj_id = obj.attrib.get('id')
        mesh_el = obj.find(f'{ns}mesh')
        if mesh_el is not None:
            v_el = mesh_el.find(f'{ns}vertices')
            t_el = mesh_el.find(f'{ns}triangles')
            verts = [[float(v.attrib['x']), float(v.attrib['y']), float(v.attrib['z'])] for v in v_el.iter(f'{ns}vertex')]
            tris = [[int(t.attrib['v1']), int(t.attrib['v2']), int(t.attrib['v3'])] for t in t_el.iter(f'{ns}triangle')]
            m = trimesh.Trimesh(vertices=verts, faces=tris)
            print(f"Object {obj_id}: {len(verts)} verts, {len(tris)} faces, bounds={m.bounds}")
            meshes.append(m)

combined = trimesh.util.concatenate(meshes)
print(f"\nTotal combined 3MF mesh: {len(combined.vertices)} verts, {len(combined.faces)} faces")
print(f"Combined bounds: {combined.bounds}")
