import numpy as np
import trimesh

mesh = trimesh.load("export/つくば＿ロケットm2 v3.stl")
verts = mesh.vertices[:, [0, 2, 1]] # X, Z, Y -> X, Y, Z
normals = mesh.face_normals[:, [0, 2, 1]]
centers = mesh.triangles_center[:, [0, 2, 1]]
areas = mesh.area_faces * 1e-6

# alpha = 2 deg
alpha_rad = np.radians(2.0)
wind_dir = np.array([0, -np.sin(alpha_rad), -np.cos(alpha_rad)])
cos_theta = np.dot(normals, -wind_dir)

q = 0.5 * 1.225 * (40.0**2)
Cp = np.zeros_like(cos_theta)
windward = cos_theta > 0
Cp[windward] = 1.8 * (cos_theta[windward]**1.5)

F_faces = -normals * (q * Cp[:, np.newaxis] * areas[:, np.newaxis])
cg_pos = np.array([0, 0, 62.0])
r_m = (centers - cg_pos) * 1e-3
moments = np.cross(r_m, F_faces)

print("=== Force and Moment by Z-segment (Z = 0 is Tail, Z = 250 is Nose) ===")
print(f"{'Z range (mm)':<18} | {'Faces':<6} | {'Area (cm2)':<10} | {'Fy (N)':<10} | {'Mx (Nm)':<10} | {'Local CP Z (mm)':<15}")
print("-" * 75)

z_bins = [0, 35, 70, 100, 150, 200, 250]
for i in range(len(z_bins)-1):
    z0, z1 = z_bins[i], z_bins[i+1]
    mask = (centers[:, 2] >= z0) & (centers[:, 2] < z1)
    if np.any(mask):
        sub_Fy = np.sum(F_faces[mask, 1])
        sub_Mx = np.sum(moments[mask, 0])
        sub_area = np.sum(areas[mask]) * 1e4
        local_cp = 62.0 + (-sub_Mx / sub_Fy * 1000.0) if abs(sub_Fy) > 1e-5 else 0.0
        print(f"{z0:>3} - {z1:>3} mm       | {np.sum(mask):<6} | {sub_area:<10.1f} | {sub_Fy:<10.4f} | {sub_Mx:<10.5f} | {local_cp:<15.1f}")

total_Fy = np.sum(F_faces[:, 1])
total_Mx = np.sum(moments[:, 0])
cp_overall = 62.0 + (-total_Mx / total_Fy * 1000.0)
print("-" * 75)
print(f"Total: Fy = {total_Fy:.4f} N, Mx = {total_Mx:.5f} Nm, Overall CP = {cp_overall:.2f} mm")
