import cascadio
import shutil
import tempfile
import os
import trimesh
import numpy as np
import matplotlib.pyplot as plt

src = r"export/つくば＿ロケットm2 v7.step"
with tempfile.TemporaryDirectory() as tmpdir:
    ascii_step = os.path.join(tmpdir, "model.step")
    ascii_glb = os.path.join(tmpdir, "model.glb")
    shutil.copy(src, ascii_step)
    
    cascadio.step_to_glb(ascii_step, ascii_glb, tol_linear=0.01, tol_angular=0.5)
    scene = trimesh.load(ascii_glb)
    
    # Check individual geometries
    print("Geometries in STEP scene:")
    for name, geom in scene.geometry.items():
        print(f"  {name}: {len(geom.vertices)} verts, {len(geom.faces)} faces, extents={geom.extents}")

    mesh = scene.to_geometry()
    if isinstance(mesh, list):
        mesh = trimesh.util.concatenate(mesh)

    # 単位がメートルなら mm に変換
    if mesh.extents[1] < 1.0: # 0.25m -> 250mm
        print("Converting from meters to mm (x1000)...")
        mesh.apply_scale(1000.0)

    print("Converted mesh bounds (mm):", mesh.bounds)
    print("Converted mesh extents (mm):", mesh.extents)

    # 3時フィン (X > 10mm) を検査
    p3 = mesh.vertices[mesh.vertices[:, 0] > 10.0]
    print(f"\n3-oclock fin points (X > 10): {len(p3)}")
    for x_val in np.linspace(10, 45, 8):
        sub = p3[abs(p3[:, 0] - x_val) < 2.5]
        if len(sub) > 0:
            print(f"  X = {x_val:5.1f} mm: Y in [{sub[:, 1].min():5.1f}, {sub[:, 1].max():5.1f}] (len={sub[:, 1].max()-sub[:, 1].min():4.1f}mm), Z in [{sub[:, 2].min():4.1f}, {sub[:, 2].max():4.1f}]")
        else:
            print(f"  X = {x_val:5.1f} mm: (no points)")

    # 断面プロファイル
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(p3[:, 1], p3[:, 0], s=3, c='green')
    ax.set_title("STEP Mesh: 3-oclock Fin Vertices (Y vs X)")
    ax.set_xlabel("Y (mm)")
    ax.set_ylabel("X (mm)")
    ax.grid(True)
    plt.savefig("export/step_fin3_check.png", dpi=150)
    print("Saved STEP fin check to export/step_fin3_check.png")
