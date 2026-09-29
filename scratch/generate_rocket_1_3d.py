import os
import sys
import numpy as np
import trimesh
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['Yu Gothic', 'Meiryo', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def create_nose_cone_spline(nose_len=120.0, radius=12.0, power=0.75, n_slices=80, n_radial=64):
    """Create a high-resolution power-series nose cone mesh."""
    x_vals = np.linspace(0.0, nose_len, n_slices)
    # y = R * (x / L)^power
    r_vals = radius * (x_vals / nose_len) ** power
    
    angles = np.linspace(0, 2 * np.pi, n_radial, endpoint=False)
    vertices = []
    
    for x, r in zip(x_vals, r_vals):
        z = nose_len - x
        for a in angles:
            vx = r * np.cos(a)
            vy = r * np.sin(a)
            vertices.append([vx, vy, z])
            
    vertices = np.array(vertices)
    faces = []
    
    for i in range(n_slices - 1):
        for j in range(n_radial):
            next_j = (j + 1) % n_radial
            p1 = i * n_radial + j
            p2 = i * n_radial + next_j
            p3 = (i + 1) * n_radial + j
            p4 = (i + 1) * n_radial + next_j
            faces.append([p1, p3, p2])
            faces.append([p2, p3, p4])
            
    # Base closure
    base_center_idx = len(vertices)
    vertices = np.vstack([vertices, [0.0, 0.0, 0.0]])
    last_ring_start = (n_slices - 1) * n_radial
    for j in range(n_radial):
        next_j = (j + 1) % n_radial
        faces.append([last_ring_start + next_j, last_ring_start + j, base_center_idx])
        
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
    mesh.fix_normals()
    return mesh

def create_cylinder_body(length=130.0, radius=12.0, n_radial=64):
    cylinder = trimesh.creation.cylinder(radius=radius, height=length, sections=n_radial)
    cylinder.apply_translation([0, 0, length / 2.0])
    return cylinder

def create_delta_fin_3d(span, root_chord, thickness=0.8, body_radius=12.0):
    half_t = thickness / 2.0
    pts_2d = np.array([
        [body_radius - 0.5, 0.0],
        [body_radius - 0.5, root_chord],
        [body_radius + span, 0.0]
    ])
    v_pos = [[p[0], half_t, p[1]] for p in pts_2d]
    v_neg = [[p[0], -half_t, p[1]] for p in pts_2d]
    vertices = np.array(v_pos + v_neg)
    faces = [
        [0, 1, 2],
        [3, 5, 4],
        [0, 2, 5],
        [0, 5, 3],
        [0, 3, 4],
        [0, 4, 1],
        [1, 4, 5],
        [1, 5, 2]
    ]
    fin = trimesh.Trimesh(vertices=vertices, faces=faces)
    fin.fix_normals()
    return fin

def build_rocket_model_1():
    print("Building Rocket Candidate 1 (Asymmetric 4-Fin, 0.80 cal, 30.43s)...")
    
    total_len = 250.0
    nose_len = 120.0
    body_len = 130.0
    radius = 12.0
    
    # Candidate 1 Fin dimensions:
    # Main fins (horizontal, 2 fins): span = 55.0mm, cr = 31.0mm
    main_span = 55.0
    main_cr = 31.0
    
    # Sub fins (vertical, 2 fins, kv = 0.90): span = 49.5mm, cr = 27.9mm
    sub_span = 49.5
    sub_cr = 27.9
    
    fin_thick = 0.8
    
    # 1. Cylinder body (Z = 0 to 130)
    body = create_cylinder_body(length=body_len, radius=radius)
    
    # 2. Nose cone (Z = 130 to 250)
    nose = create_nose_cone_spline(nose_len=nose_len, radius=radius, power=0.75)
    nose.apply_translation([0, 0, body_len])
    
    # 3. Horizontal Main Fins (+X and -X)
    fin_h1 = create_delta_fin_3d(span=main_span, root_chord=main_cr, thickness=fin_thick, body_radius=radius)
    rot_180 = trimesh.transformations.rotation_matrix(np.pi, [0, 0, 1])
    fin_h2 = fin_h1.copy()
    fin_h2.apply_transform(rot_180)
    
    # 4. Vertical Sub Fins (+Y and -Y, 90 deg and 270 deg)
    fin_v_base = create_delta_fin_3d(span=sub_span, root_chord=sub_cr, thickness=fin_thick, body_radius=radius)
    rot_90 = trimesh.transformations.rotation_matrix(np.pi / 2.0, [0, 0, 1])
    rot_270 = trimesh.transformations.rotation_matrix(3.0 * np.pi / 2.0, [0, 0, 1])
    
    fin_v1 = fin_v_base.copy()
    fin_v1.apply_transform(rot_90)
    fin_v2 = fin_v_base.copy()
    fin_v2.apply_transform(rot_270)
    
    all_meshes = [body, nose, fin_h1, fin_h2, fin_v1, fin_v2]
    full_rocket = trimesh.util.concatenate(all_meshes)
    
    os.makedirs("input", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    
    out_stl_input = os.path.join("input", "rocket_candidate_1_asym4fin.stl")
    out_stl_output = os.path.join("output", "rocket_candidate_1_asym4fin.stl")
    full_rocket.export(out_stl_input)
    full_rocket.export(out_stl_output)
    
    print(f"Exported Candidate 1 STL to: {out_stl_input} and {out_stl_output}")
    print(f"Bounding Box: {full_rocket.bounds}")
    
    # Generate 3-view rendering
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    fig = plt.figure(figsize=(15, 6))
    
    ax1 = fig.add_subplot(131, projection='3d')
    ax2 = fig.add_subplot(132)
    ax3 = fig.add_subplot(133)
    
    # 1. 3D Isometric View
    faces_coords = full_rocket.vertices[full_rocket.faces]
    mesh_coll = Poly3DCollection(faces_coords[::2], alpha=0.85, edgecolor='black', linewidths=0.2)
    mesh_coll.set_facecolor('mediumseagreen')
    ax1.add_collection3d(mesh_coll)
    ax1.set_xlim(-75, 75)
    ax1.set_ylim(-75, 75)
    ax1.set_zlim(0, 260)
    ax1.set_box_aspect([1, 1, 2.2])
    ax1.view_init(elev=20, azim=45)
    ax1.set_title("3D アイソメトリック外観\n(全長250mm, 十字アンバランス4枚翼)", fontsize=11, fontweight="bold")
    ax1.set_xlabel("X [mm]")
    ax1.set_ylabel("Y [mm]")
    ax1.set_zlabel("Z [mm]")

    # 2. Side View (X-Z)
    xs_nose = np.linspace(0, nose_len, 100)
    rs_nose = radius * (xs_nose / nose_len)**0.75
    zs_nose = 250.0 - xs_nose
    
    ax2.plot(rs_nose, zs_nose, 'darkgreen', lw=2)
    ax2.plot(-rs_nose, zs_nose, 'darkgreen', lw=2)
    ax2.plot([radius, radius], [0, body_len], 'darkgreen', lw=2)
    ax2.plot([-radius, -radius], [0, body_len], 'darkgreen', lw=2)
    ax2.plot([-radius, radius], [0, 0], 'darkgreen', lw=2)
    
    # Main Fins (+/- X)
    ax2.plot([radius, radius + main_span, radius], [main_cr, 0, 0], 'crimson', lw=2.2, label=f"主翼 (55×31mm)")
    ax2.plot([-radius, -(radius + main_span), -radius], [main_cr, 0, 0], 'crimson', lw=2.2)
    
    # Stability marks
    cg_z = 64.37
    cp_pitch_z = 41.97
    cp_yaw_z = 45.38
    ax2.axhline(cg_z, color='blue', ls='--', lw=1.5, label=f"重心 CG (Z={cg_z:.1f}mm)")
    ax2.axhline(cp_yaw_z, color='purple', ls=':', lw=1.8, label=f"風圧中心 Yaw (Z={cp_yaw_z:.1f}mm)")
    ax2.axhline(cp_pitch_z, color='magenta', ls='-.', lw=1.5, label=f"風圧中心 Pitch (Z={cp_pitch_z:.1f}mm)")
    
    ax2.set_xlim(-80, 80)
    ax2.set_ylim(-10, 260)
    ax2.set_aspect('equal')
    ax2.grid(True, ls='--', alpha=0.5)
    ax2.legend(loc='upper right', fontsize=8.5)
    ax2.set_title("側面断面・バランス図 (Side View)\n実効安全率: +0.79 cal (高度145.6m特化)", fontsize=11, fontweight="bold")
    ax2.set_xlabel("X [mm]")
    ax2.set_ylabel("Z (長軸高さ) [mm]")

    # 3. Rear View (X-Y) - Highlights asymmetry
    circle_body = plt.Circle((0, 0), radius, color='mediumseagreen', alpha=0.3, ec='darkgreen', lw=2, label="胴体 (D=24mm)")
    circle_motor = plt.Circle((0, 0), 9.0, color='darkorange', alpha=0.4, ec='brown', lw=1.5, label="モーター (18mm)")
    ax3.add_patch(circle_body)
    ax3.add_patch(circle_motor)
    
    half_t = fin_thick / 2.0
    # Horizontal Main fins (Span=55mm, Red)
    ax3.fill([radius, radius + main_span, radius + main_span, radius], [-half_t, -half_t, half_t, half_t], 'crimson', alpha=0.85, label=f"主翼 (スパン55mm)")
    ax3.fill([-radius, -(radius + main_span), -(radius + main_span), -radius], [-half_t, -half_t, half_t, half_t], 'crimson', alpha=0.85)
    
    # Vertical Sub fins (Span=49.5mm, kv=0.90, RoyalBlue)
    ax3.fill([-half_t, -half_t, half_t, half_t], [radius, radius + sub_span, radius + sub_span, radius], 'royalblue', alpha=0.85, label=f"尾翼 (スパン49.5mm, kv=0.9)")
    ax3.fill([-half_t, -half_t, half_t, half_t], [-radius, -(radius + sub_span), -(radius + sub_span), -radius], 'royalblue', alpha=0.85)
    
    ax3.scatter([0], [0], color='black', s=30, label="中心軸")
    ax3.set_xlim(-80, 80)
    ax3.set_ylim(-80, 80)
    ax3.set_aspect('equal')
    ax3.grid(True, ls='--', alpha=0.5)
    ax3.legend(loc='upper right', fontsize=8.5)
    ax3.set_title("後方視界・翼配置図 (Rear View)\n十字アンバランス配置 (主翼55mm / 尾翼49.5mm)", fontsize=11, fontweight="bold")
    ax3.set_xlabel("X [mm]")
    ax3.set_ylabel("Y [mm]")

    plt.suptitle("【機体①】アンバランス4枚翼機 (0.80 cal, 30.43s) 3D CAD形状＆配置図", fontsize=14, fontweight="bold", y=0.98)
    preview_path = os.path.join("output", "rocket_candidate_1_preview.png")
    plt.tight_layout(rect=[0.02, 0.02, 0.98, 0.93])
    plt.savefig(preview_path, dpi=200)
    print(f"Rendered Candidate 1 3D preview to {preview_path}")

    # Copy to artifact
    import shutil
    art_dir = r"C:\Users\kuron.HX99G\.gemini\antigravity\brain\f5d3bd8b-8307-472d-83e6-9bd725805a5f"
    shutil.copy(preview_path, os.path.join(art_dir, "rocket_candidate_1_preview.png"))

if __name__ == "__main__":
    build_rocket_model_1()
