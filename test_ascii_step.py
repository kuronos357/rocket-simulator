import cascadio
import shutil
import tempfile
import os
import trimesh

src = r"export/つくば＿ロケットm2 v7.step"
with tempfile.TemporaryDirectory() as tmpdir:
    ascii_step = os.path.join(tmpdir, "model.step")
    ascii_glb = os.path.join(tmpdir, "model.glb")
    shutil.copy(src, ascii_step)
    
    print("Calling cascadio.step_to_glb with ascii path...")
    ret = cascadio.step_to_glb(ascii_step, ascii_glb, tol_linear=0.05, tol_angular=0.5)
    print("cascadio returned:", ret)
    print("GLB exists:", os.path.exists(ascii_glb), "Size:", os.path.getsize(ascii_glb))
    
    scene = trimesh.load(ascii_glb)
    print("Scene type:", type(scene))
    if isinstance(scene, trimesh.Scene):
        mesh = scene.dump(concatenate=True)
    else:
        mesh = scene
    print("Mesh vertices:", len(mesh.vertices), "Faces:", len(mesh.faces))
    print("Mesh bounds:", mesh.bounds)
    print("Mesh extents:", mesh.extents)
