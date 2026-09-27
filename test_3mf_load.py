import trimesh

scene = trimesh.load("つくば＿ロケット.gcode.3mf")
print("Scene loaded successfully!")
print("Type:", type(scene))
if isinstance(scene, trimesh.Scene):
    print("Geometries in 3MF scene:")
    for name, geom in scene.geometry.items():
        print(f"  {name}: {len(geom.vertices)} vertices, {len(geom.faces)} faces, bounds={geom.bounds}")
    # 合成メッシュ
    combined = scene.dump(concatenate=True)
    print("Combined bounds:", combined.bounds)
