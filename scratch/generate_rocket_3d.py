import os
import sys
import numpy as np
import trimesh
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['Yu Gothic', 'Meiryo', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def create_nose_cone(nose_len=120.0, radius=12.0, power=0.75, n_slices=60, n_radial=48):
    """Create a power-series nose cone mesh."""
    x_vals = np.linspace(0.0, nose_len, n_slices)
    # y = R * (x / L)^power
    r_vals = radius * (x_vals / nose_len) ** power
    
    # Generate revolution mesh
    angles = np.linspace(0, 2 * np.pi, n_radial, endpoint=False)
    vertices = []
    
    # Tip vertex at (0, 0, nose_len) or relative
    # Let's orient along Z axis: Tip at Z = nose_len, Base at Z = 0
    # x is distance from tip: z = nose_len - x
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
            
            # Two triangles per quad
            faces.append([p1, p3, p2])
            faces.append([p2, p3, p4])
            
    # Add tip closure if r[0] == 0
    # Add base closure (flat circle at z = 0)
    base_center_idx = len(vertices)
    vertices = np.vstack([vertices, [0.0, 0.0, 0.0]])
    last_ring_start = (n_slices - 1) * n_radial
    for j in range(n_radial):
        next_j = (j + 1) % n_radial
        faces.append([last_ring_start + next_j, last_ring_start + j, base_center_idx])
        
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
    mesh.fix_normals()
    return mesh

def create_cylinder_body(length=130.0, radius=12.0, n_radial=48):
    """Create a cylinder along Z axis from Z=0 to Z=length."""
    cylinder = trimesh.creation.cylinder(radius=radius, height=length, sections=n_radial)
    # trimesh cylinder is centered at origin along Z (-height/2 to height/2)
    cylinder.apply_translation([0, 0, length / 2.0])
    return cylinder

def create_delta_fin(span=59.0, root_chord=33.0, thickness=0.8, body_radius=12.0):
    """
    Create a 3D solid delta fin attached to the cylinder.
    Root runs along Z from Z=0 to Z=root_chord at X=body_radius.
    Fin extends in +X direction up to X=body_radius + span.
    Leading edge sweeps from (body_radius, root_chord) to (body_radius + span, 0).
    Trailing edge is flat at Z=0.
    """
    # 3D wedge / prism
    # Vertices on positive Y (+thickness/2) and negative Y (-thickness/2)
    half_t = thickness / 2.0
    
    # 3 key points of delta triangle in X-Z plane:
    # A: (body_radius, 0) - root trailing edge
    # B: (body_radius, root_chord) - root leading edge
    # C: (body_radius + span, 0) - tip
    pts_2d = np.array([
        [body_radius - 0.5, 0.0],              # Sink slightly into body for clean union
        [body_radius - 0.5, root_chord],
        [body_radius + span, 0.0]
    ])
    
    # Extrude along Y
    v_pos = [[p[0], half_t, p[1]] for p in pts_2d]
    v_neg = [[p[0], -half_t, p[1]] for p in pts_2d]
    vertices = np.array(v_pos + v_neg)
    
    # Triangular prism faces
    # v_pos indices: 0, 1, 2
    # v_neg indices: 3, 4, 5
    faces = [
        # Side 1 (Y = +half_t)
        [0, 1, 2],
        # Side 2 (Y = -half_t)
        [3, 5, 4],
        # Bottom (Z = 0)
        [0, 2, 5],
        [0, 5, 3],
        # Root (X = body_radius)
        [0, 3, 4],
        [0, 4, 1],
        # Leading edge (hypotenuse)
        [1, 4, 5],
        [1, 5, 2]
    ]
    fin = trimesh.Trimesh(vertices=vertices, faces=faces)
    fin.fix_normals()
    return fin

def build_rocket_model_3():
    print("Building Rocket Candidate 3 (1.22 cal, 28.44s)...")
    
    # Dimensions
    total_len = 250.0
    nose_len = 120.0
    body_len = 130.0
    radius = 12.0
    fin_span = 59.0
    fin_cr = 33.0
    fin_thick = 0.8 # Clean 3D printable thickness
    
    # 1. Cylinder body (Z = 0 to 130)
    body = create_cylinder_body(length=body_len, radius=radius)
    
    # 2. Nose cone (Z = 130 to 250)
    nose = create_nose_cone(nose_len=nose_len, radius=radius, power=0.75)
    nose.apply_translation([0, 0, body_len])
    
    # 3. 4 Fins (90 degrees symmetric: +X, +Y, -X, -Y)
    fins = []
    base_fin = create_delta_fin(span=fin_span, root_chord=fin_cr, thickness=fin_thick, body_radius=radius)
    
    angles = [0.0, 90.0, 180.0, 270.0]
    for ang in angles:
        fin_copy = base_fin.copy()
        if ang != 0.0:
            rot_matrix = trimesh.transformations.rotation_matrix(np.radians(ang), [0, 0, 1])
            fin_copy.apply_transform(rot_matrix)
        fins.append(fin_copy)
        
    # Combine all parts
    all_meshes = [body, nose] + fins
    full_rocket = trimesh.util.concatenate(all_meshes)
    
    # Export STL
    os.makedirs("input", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    
    out_stl_input = os.path.join("input", "rocket_candidate_3_ironclad.stl")
    out_stl_output = os.path.join("output", "rocket_candidate_3_ironclad.stl")
    
    full_rocket.export(out_stl_input)
    full_rocket.export(out_stl_output)
    
    print(f"Exported STL to: {out_stl_input} and {out_stl_output}")
    print(f"Total Vertices: {len(full_rocket.vertices)}, Total Faces: {len(full_rocket.faces)}")
    print(f"Bounding Box: {full_rocket.bounds}")
    
    # Generate 3-view rendering
    try:
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection
        
        fig = plt.figure(figsize=(15, 6))
        
        # Subplot 1: 3D Isometric View
        ax1 = fig.add_subplot(131, projection='3d')
        # Subplot 2: Side View (X-Z)
        ax2 = fig.add_subplot(132)
        # Subplot 3: Rear Fin View (X-Y)
        ax3 = fig.add_subplot(133)
        
        # 1. Isometric
        # Sample faces for smooth rendering
        faces_coords = full_rocket.vertices[full_rocket.faces]
        mesh_collection = Poly3DCollection(faces_coords[::2], alpha=0.85, edgecolor='black', linewidths=0.2)
        mesh_collection.set_facecolor('cornflowerblue')
        ax1.add_collection3d(mesh_collection)
        ax1.set_xlim(-75, 75)
        ax1.set_ylim(-75, 75)
        ax1.set_zlim(0, 260)
        ax1.set_box_aspect([1, 1, 2.2])
        ax1.view_init(elev=20, azim=45)
        ax1.set_title("3D アイソメトリック外観\n(全長250mm, 正十字4枚翼)", fontsize=11, fontweight="bold")
        ax1.set_xlabel("X [mm]")
        ax1.set_ylabel("Y [mm]")
        ax1.set_zlabel("Z [mm]")

        # 2. Side View (X-Z)
        # Nose outline
        xs_nose = np.linspace(0, nose_len, 100)
        rs_nose = radius * (xs_nose / nose_len)**0.75
        zs_nose = 250.0 - xs_nose
        
        ax2.plot(rs_nose, zs_nose, 'navy', lw=2)
        ax2.plot(-rs_nose, zs_nose, 'navy', lw=2)
        # Body cylinder
        ax2.plot([radius, radius], [0, body_len], 'navy', lw=2)
        ax2.plot([-radius, -radius], [0, body_len], 'navy', lw=2)
        # Base
        ax2.plot([-radius, radius], [0, 0], 'navy', lw=2)
        # Fins in side view (two extending to X = +/- (radius + span))
        ax2.plot([radius, radius + fin_span, radius], [fin_cr, 0, 0], 'crimson', lw=2.2, label="主翼 (59×33mm)")
        ax2.plot([-radius, -(radius + fin_span), -radius], [fin_cr, 0, 0], 'crimson', lw=2.2)
        # Mark CG and CP
        cg_z = 69.4
        cp_z = 40.1
        ax2.axhline(cg_z, color='green', ls='--', lw=1.5, label=f"重心 CG (Z={cg_z}mm)")
        ax2.axhline(cp_z, color='purple', ls=':', lw=1.8, label=f"風圧中心 CP (Z={cp_z}mm)")
        # Annotate ballast at nose tip
        ax2.scatter([0], [245], color='gold', s=120, edgecolor='black', zorder=5, label="先端バラスト (1.0g)")
        
        ax2.set_xlim(-85, 85)
        ax2.set_ylim(-10, 260)
        ax2.set_aspect('equal')
        ax2.grid(True, ls='--', alpha=0.5)
        ax2.legend(loc='upper right', fontsize=8.5)
        ax2.set_title("側面断面・バランス図 (Side View)\n実効安全率: +1.22 cal (余裕度 29.3mm)", fontsize=11, fontweight="bold")
        ax2.set_xlabel("X [mm]")
        ax2.set_ylabel("Z (長軸高さ) [mm]")

        # 3. Rear View (X-Y)
        circle_body = plt.Circle((0, 0), radius, color='royalblue', alpha=0.3, ec='navy', lw=2, label="胴体 (D=24mm)")
        circle_motor = plt.Circle((0, 0), 9.0, color='darkorange', alpha=0.4, ec='brown', lw=1.5, label="モーター (18mm)")
        ax3.add_patch(circle_body)
        ax3.add_patch(circle_motor)
        
        # 4 Fins (90 deg cross)
        half_t = fin_thick / 2.0
        # +X
        ax3.fill([radius, radius + fin_span, radius + fin_span, radius], [-half_t, -half_t, half_t, half_t], 'crimson', alpha=0.8)
        # -X
        ax3.fill([-radius, -(radius + fin_span), -(radius + fin_span), -radius], [-half_t, -half_t, half_t, half_t], 'crimson', alpha=0.8)
        # +Y
        ax3.fill([-half_t, -half_t, half_t, half_t], [radius, radius + fin_span, radius + fin_span, radius], 'crimson', alpha=0.8)
        # -Y
        ax3.fill([-half_t, -half_t, half_t, half_t], [-radius, -(radius + fin_span), -(radius + fin_span), -radius], 'crimson', alpha=0.8)
        
        ax3.scatter([0], [0], color='black', s=30, label="中心軸")
        ax3.set_xlim(-85, 85)
        ax3.set_ylim(-85, 85)
        ax3.set_aspect('equal')
        ax3.grid(True, ls='--', alpha=0.5)
        ax3.legend(loc='upper right', fontsize=8.5)
        ax3.set_title("後方視界・翼配置図 (Rear View)\n正十字完全対称 4枚翼配置", fontsize=11, fontweight="bold")
        ax3.set_xlabel("X [mm]")
        ax3.set_ylabel("Y [mm]")

        plt.suptitle("【機体③】鉄壁安全重視機 (1.22 cal, 28.44s) 3D CAD形状＆配置図", fontsize=14, fontweight="bold", y=0.98)
        preview_path = os.path.join("output", "rocket_candidate_3_preview.png")
        plt.tight_layout(rect=[0.02, 0.02, 0.98, 0.93])
        plt.savefig(preview_path, dpi=200)
        print(f"Rendered 3D preview to {preview_path}")

        # Copy to artifact
        import shutil
        art_dir = r"C:\Users\kuron.HX99G\.gemini\antigravity\brain\f5d3bd8b-8307-472d-83e6-9bd725805a5f"
        shutil.copy(preview_path, os.path.join(art_dir, "rocket_candidate_3_preview.png"))
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Preview rendering skipped: {e}")

if __name__ == "__main__":
    build_rocket_model_3()
