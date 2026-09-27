import trimesh
import cascadio

# trimesh is integrated with cascadio automatically in recent versions,
# or we can use cascadio.step_to_glb / trimesh.load
print("cascadio.step_to_glb is available:", hasattr(cascadio, "step_to_glb"))
print("cascadio.to_glb_bytes is available:", hasattr(cascadio, "to_glb_bytes"))
