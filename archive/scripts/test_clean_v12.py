import trimesh
import numpy as np
from scipy.sparse import coo_matrix, csgraph
from sim_engine.loader import RocketModel
from sim_engine.aero import AeroEngine
from sim_engine.flight_sim import FlightSimulator

m12 = trimesh.load("export/つくば＿ロケット v12.stl")

# face adjacency
edges = m12.face_adjacency
n_faces = len(m12.faces)
row = edges[:, 0]
col = edges[:, 1]
data = np.ones(len(edges), dtype=bool)
adj = coo_matrix((data, (row, col)), shape=(n_faces, n_faces))
n_comp, labels = csgraph.connected_components(adj, directed=False)

# Identify streamer component (Comp 8: Y=[73, 173.9], X=[-8, 8], Z=[-8, 8])
clean_faces_mask = np.ones(n_faces, dtype=bool)
for i in range(n_comp):
    faces_i = m12.faces[labels == i]
    verts_i = m12.vertices[np.unique(faces_i)]
    y_min, y_max = verts_i[:, 1].min(), verts_i[:, 1].max()
    x_min, x_max = verts_i[:, 0].min(), verts_i[:, 0].max()
    # Check if this is the internal streamer body
    if y_min > 70 and y_max < 175 and abs(x_max - 8.0) < 0.5 and abs(x_min - (-8.0)) < 0.5:
        print(f"Removing internal streamer component {i}: {len(faces_i)} faces")
        clean_faces_mask[labels == i] = False

# Create clean mesh without internal streamer
clean_mesh = m12.submesh([clean_faces_mask], append=True)
clean_stl_path = "export/つくば＿ロケット v12_clean.stl"
clean_mesh.export(clean_stl_path)
print(f"Exported clean mesh to {clean_stl_path}: {len(clean_mesh.faces)} faces")

# Run aero and sim on clean mesh
json_path = "export/つくば＿ロケット v12_params.json"
model = RocketModel(json_path)
aero = AeroEngine(stl_path=clean_stl_path, flight_axis=model.flight_axis, ref_diameter_mm=22.0)
cg_flight = model.cg_mm[1] if model.flight_axis == 'y' else model.cg_mm[2]
aero_res = aero.compute_aerodynamics(velocity_m_s=40.0, alpha_deg=2.0, cg_z_mm=cg_flight)

sim = FlightSimulator(rocket_model=model, aero_engine=aero)
flight_res = sim.run_simulation()

print("\n=== Clean v12 Analysis (without internal streamer in aero mesh) ===")
print(f"CG (mm)         : {cg_flight:.2f} mm")
print(f"CP (mm)         : {aero_res['CP_z_mm']:.2f} mm")
print(f"Margin (cal)    : {aero_res['margin_cal']:.2f} cal")
print(f"Cd              : {aero_res['Cd']:.3f}")
print(f"Roll Torque     : {aero_res['Roll_Torque_Nm']*1000:.3f} mN*m")
print(f"Apogee (m)      : {flight_res['apogee_alt_m']:.1f} m")
print(f"Flight Time (s) : {flight_res['total_flight_time_s']:.1f} s")
print(f"V_desc (m/s)    : {flight_res['terminal_velocity_m_s']:.1f} m/s")
