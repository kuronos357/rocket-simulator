import numpy as np
import trimesh
import os
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

def create_hollow_airframe(n_radial=64, n_z_steps=80):
    """
    Creates a hollow airframe with:
    - 18mm motor mount (Z=0..70, r_in=9.0)
    - Thrust stop ring (Z=70..75, r_in=8.0)
    - Upper tube (Z=75..130, r_in=10.0)
    - Hollow nose cone (Z=130..240, r_in=hollow, Z=240..250 solid tip)
    - Outer: Z=0..130 r=12.0, Z=130..250 r=12.0 * ((250-Z)/120)**0.75
    """
    z_profile = []
    
    # Outer profile points: (z, r_out, r_in)
    # 1. Base ring at Z=0
    z_profile.append((0.0, 12.0, 9.0))
    # 2. Motor section up to Z=70
    z_profile.append((70.0, 12.0, 9.0))
    # 3. Thrust ring step
    z_profile.append((70.0, 12.0, 8.0))
    z_profile.append((75.0, 12.0, 8.0))
    # 4. Streamer tube section up to Z=130
    z_profile.append((75.0, 12.0, 10.0))
    z_profile.append((130.0, 12.0, 10.0))
    
    # 5. Nose cone profile (Z=130..250)
    n_nose_pts = 30
    for i in range(1, n_nose_pts + 1):
        z = 130.0 + (120.0 * i / n_nose_pts)
        dist = 250.0 - z
        r_out = 12.0 * ((dist / 120.0) ** 0.75) if dist > 0 else 0.0
        
        # Hollow cavity inside nose (wall thickness ~ 1.5mm)
        if z < 235.0:
            r_in = max(0.0, r_out - 1.5)
        else:
            r_in = 0.0 # Solid tip
        z_profile.append((z, r_out, r_in))

    # Build outer surface of revolution
    # and inner surface of revolution
    # Then connect them at base Z=0
    angles = np.linspace(0, 2.0 * np.pi, n_radial, endpoint=False)
    cos_a = np.cos(angles)
    sin_a = np.sin(angles)

    verts_out = []
    verts_in = []

    for z, r_out, r_in in z_profile:
        for ca, sa in zip(cos_a, sin_a):
            verts_out.append([r_out * ca, r_out * sa, z])
            verts_in.append([r_in * ca, r_in * sa, z])

    n_layers = len(z_profile)
    verts_out = np.array(verts_out)
    verts_in = np.array(verts_in)

    faces = []

    # Outer wall faces (normals pointing outward)
    for lay in range(n_layers - 1):
        for j in range(n_radial):
            next_j = (j + 1) % n_radial
            p0 = lay * n_radial + j
            p1 = lay * n_radial + next_j
            p2 = (lay + 1) * n_radial + j
            p3 = (lay + 1) * n_radial + next_j
            # Triangle 1: p0 -> p1 -> p3
            # Triangle 2: p0 -> p3 -> p2
            faces.append([p0, p1, p3])
            faces.append([p0, p3, p2])

    offset_in = len(verts_out)
    # Inner wall faces (normals pointing inward, into cavity)
    for lay in range(n_layers - 1):
        for j in range(n_radial):
            next_j = (j + 1) % n_radial
            p0 = offset_in + lay * n_radial + j
            p1 = offset_in + lay * n_radial + next_j
            p2 = offset_in + (lay + 1) * n_radial + j
            p3 = offset_in + (lay + 1) * n_radial + next_j
            # Reversed winding for inner wall
            faces.append([p0, p3, p1])
            faces.append([p0, p2, p3])

    # Connect outer and inner at bottom rim (lay = 0, Z = 0)
    for j in range(n_radial):
        next_j = (j + 1) % n_radial
        out0 = j
        out1 = next_j
        in0 = offset_in + j
        in1 = offset_in + next_j
        faces.append([out0, in0, in1])
        faces.append([out0, in1, out1])

    all_verts = np.vstack([verts_out, verts_in])
    mesh = trimesh.Trimesh(vertices=all_verts, faces=faces)
    mesh.fix_normals()
    return mesh

def create_filleted_fin_mesh(span, root_chord, thickness=0.44, fillet_r=1.5, body_r=12.0, n_fillet_pts=6):
    """
    Creates a fin with a triangular/delta planform and a smooth circular root fillet
    that smoothly blends into the fuselage cylinder (radius body_r).
    """
    # 2D cross sections along span:
    # At span x from body surface (x = 0 is cylinder surface, x = span is tip):
    # Chord length at x: c(x) = root_chord * (1.0 - x / span)
    
    # In the Y direction (thickness):
    # Fin blade thickness is 0.44mm (half_t = 0.22mm)
    # At the root (x near 0), the fillet widens from half_t to (half_t + fillet_r)
    # Fillet profile: width(x) = half_t + fillet_r * (1.0 - sin(pi * x / (2 * fillet_r))) for x < fillet_r
    
    # We slice along X (from 0 to span):
    x_steps = [0.0]
    # Fillet transition steps
    for f in np.linspace(0.1, fillet_r, n_fillet_pts):
        x_steps.append(f)
    # Fin blade steps
    for b in np.linspace(fillet_r + 2.0, span, 12):
        x_steps.append(b)
    x_steps = np.unique(x_steps)

    half_t = thickness / 2.0
    slices_verts = []

    for x in x_steps:
        # Chord at this station:
        chord = max(0.2, root_chord * (1.0 - x / span))
        if x < fillet_r:
            # Quarter circle fillet curve
            theta = (x / fillet_r) * (np.pi / 2.0)
            # local half thickness widens at root
            w = half_t + fillet_r * (1.0 - np.sin(theta))
        else:
            w = half_t
            
        r_actual = body_r + x
        
        # 4 vertices per station (forming a box cross-section along chord):
        # 0: bottom leading (Z = chord, Y = +w)
        # 1: bottom trailing (Z = 0.0, Y = +w)
        # 2: bottom trailing (Z = 0.0, Y = -w)
        # 3: bottom leading (Z = chord, Y = -w)
        # Note: at x=0, to conform to cylinder, Z goes from 0 to chord
        v0 = [r_actual,  w, chord]
        v1 = [r_actual,  w, 0.0]
        v2 = [r_actual, -w, 0.0]
        v3 = [r_actual, -w, chord]
        slices_verts.append([v0, v1, v2, v3])

    # Add tip vertex
    v_tip = [body_r + span, 0.0, 0.0]
    
    vertices = []
    faces = []
    
    for s in slices_verts:
        vertices.extend(s)
        
    n_slices = len(slices_verts)
    
    for i in range(n_slices - 1):
        idx_cur = i * 4
        idx_next = (i + 1) * 4
        # Face 1 (+Y side):
        faces.append([idx_cur + 0, idx_cur + 1, idx_next + 1])
        faces.append([idx_cur + 0, idx_next + 1, idx_next + 0])
        # Face 2 (-Y side):
        faces.append([idx_cur + 2, idx_cur + 3, idx_next + 3])
        faces.append([idx_cur + 2, idx_next + 3, idx_next + 2])
        # Face 3 (Leading edge Z=chord):
        faces.append([idx_cur + 3, idx_cur + 0, idx_next + 0])
        faces.append([idx_cur + 3, idx_next + 0, idx_next + 3])
        # Face 4 (Trailing edge Z=0):
        faces.append([idx_cur + 1, idx_cur + 2, idx_next + 2])
        faces.append([idx_cur + 1, idx_next + 2, idx_next + 1])
        
    # Cap root (i=0):
    faces.append([0, 1, 2])
    faces.append([0, 2, 3])
    
    # Cap tip (last slice):
    last_idx = (n_slices - 1) * 4
    tip_idx = len(vertices)
    vertices.append(v_tip)
    faces.append([last_idx + 0, last_idx + 1, tip_idx])
    faces.append([last_idx + 1, last_idx + 2, tip_idx])
    faces.append([last_idx + 2, last_idx + 3, tip_idx])
    faces.append([last_idx + 3, last_idx + 0, tip_idx])

    mesh = trimesh.Trimesh(vertices=np.array(vertices), faces=np.array(faces))
    mesh.fix_normals()
    return mesh

def create_launch_lug(z_start=35.0, length=9.0, r_inner=1.6, r_outer=2.4, body_r=12.0, angle_deg=-45.0):
    """
    Creates a launch lug pipe attached to the body between fins at -45 deg.
    """
    pipe = trimesh.creation.cylinder(radius=r_outer, height=length, sections=32)
    # Make hollow by subtracting inner cylinder or creating annular prism
    angles = np.linspace(0, 2*np.pi, 32, endpoint=False)
    ca, sa = np.cos(angles), np.sin(angles)
    
    # Annular cylinder mesh
    verts = []
    # Bottom rim Z=0
    for c, s in zip(ca, sa):
        verts.append([r_outer * c, r_outer * s, 0.0])
    for c, s in zip(ca, sa):
        verts.append([r_inner * c, r_inner * s, 0.0])
    # Top rim Z=length
    for c, s in zip(ca, sa):
        verts.append([r_outer * c, r_outer * s, length])
    for c, s in zip(ca, sa):
        verts.append([r_inner * c, r_inner * s, length])
        
    verts = np.array(verts)
    faces = []
    
    # Outer cylindrical wall
    for i in range(32):
        ni = (i + 1) % 32
        faces.append([i, ni, 64 + ni])
        faces.append([i, 64 + ni, 64 + i])
        
    # Inner cylindrical wall
    for i in range(32):
        ni = (i + 1) % 32
        faces.append([32 + i, 96 + ni, 32 + ni])
        faces.append([32 + i, 96 + i, 96 + ni])
        
    # Bottom rim cap
    for i in range(32):
        ni = (i + 1) % 32
        faces.append([i, 32 + i, 32 + ni])
        faces.append([i, 32 + ni, ni])
        
    # Top rim cap
    for i in range(32):
        ni = (i + 1) % 32
        faces.append([64 + i, 64 + ni, 96 + ni])
        faces.append([64 + i, 96 + ni, 96 + i])
        
    lug = trimesh.Trimesh(vertices=verts, faces=faces)
    
    # Position on body: radial distance = body_r + r_outer - 0.2
    lug.apply_translation([body_r + r_outer - 0.3, 0.0, z_start])
    
    # Rotate around Z to angle_deg
    rad = np.radians(angle_deg)
    rot_m = trimesh.transformations.rotation_matrix(rad, [0, 0, 1])
    lug.apply_transform(rot_m)
    lug.fix_normals()
    return lug

def build_candidate_1_complete():
    print("=== Building Candidate 1 Complete Model (ロケットM3type1.stl) ===")
    
    # 1. Hollow Airframe
    airframe = create_hollow_airframe()
    print(f"Airframe created: {len(airframe.vertices)} vertices, {len(airframe.faces)} faces")
    
    # 2. Main Fins (Horizontal 2x, Span 55mm, Root Chord 31mm, Thickness 0.44mm, Fillet 1.5mm)
    fin_h1 = create_filleted_fin_mesh(span=55.0, root_chord=31.0, thickness=0.44, fillet_r=1.5, body_r=12.0)
    rot_180 = trimesh.transformations.rotation_matrix(np.pi, [0, 0, 1])
    fin_h2 = fin_h1.copy()
    fin_h2.apply_transform(rot_180)
    
    # 3. Sub Fins (Vertical 2x, Span 49.5mm, Root Chord 27.9mm, Thickness 0.44mm, Fillet 1.5mm)
    fin_v_base = create_filleted_fin_mesh(span=49.5, root_chord=27.9, thickness=0.44, fillet_r=1.5, body_r=12.0)
    rot_90 = trimesh.transformations.rotation_matrix(np.pi / 2.0, [0, 0, 1])
    rot_270 = trimesh.transformations.rotation_matrix(3.0 * np.pi / 2.0, [0, 0, 1])
    fin_v1 = fin_v_base.copy()
    fin_v1.apply_transform(rot_90)
    fin_v2 = fin_v_base.copy()
    fin_v2.apply_transform(rot_270)
    
    # 4. Launch Lug (between +X and -Y at -45 deg)
    lug = create_launch_lug(z_start=40.0, length=8.0, r_inner=1.6, r_outer=2.4, body_r=12.0, angle_deg=-45.0)
    
    # Combine all into single watertight multi-part assembly
    all_parts = [airframe, fin_h1, fin_h2, fin_v1, fin_v2, lug]
    full_model = trimesh.util.concatenate(all_parts)
    
    # Orient to standard print coordinates (Z along rocket axis, 0 to 250)
    # Export to input/ロケットM3type1.stl and output/
    os.makedirs("input", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    
    out_stl_1 = os.path.join("input", "ロケットM3type1.stl")
    out_stl_2 = os.path.join("output", "ロケットM3type1.stl")
    
    full_model.export(out_stl_1)
    full_model.export(out_stl_2)
    print(f"Successfully exported: {out_stl_1}")
    print(f"Bounds: min={full_model.bounds[0]}, max={full_model.bounds[1]}")
    print(f"Extents: {full_model.extents}")
    
    # Render preview
    fig = plt.figure(figsize=(18, 12), dpi=150)
    fig.suptitle('Rocket M3 Type 1 (Candidate 1 - Asymmetric 4-Fin Cross Model)', fontsize=16, fontweight='bold')
    
    verts = full_model.vertices
    faces = full_model.faces
    sub_idx = np.random.choice(len(faces), min(25000, len(faces)), replace=False)
    
    # 1. 3D Isometric View
    ax1 = fig.add_subplot(2, 2, 1, projection='3d')
    poly = Poly3DCollection(verts[faces[sub_idx]], alpha=0.35, edgecolor='teal', linewidths=0.2, facecolor='lightcyan')
    ax1.add_collection3d(poly)
    ax1.set_xlim([-75, 75])
    ax1.set_ylim([-75, 75])
    ax1.set_zlim([0, 260])
    ax1.view_init(elev=20, azim=45)
    ax1.set_title('3D Isometric View', fontsize=12)
    ax1.set_xlabel('X (mm)')
    ax1.set_ylabel('Y (mm)')
    ax1.set_zlabel('Z (mm)')
    
    # 2. Pitch plane (X vs Z) - Horizontal Main Fins
    ax2 = fig.add_subplot(2, 2, 2)
    ax2.scatter(verts[::4, 0], verts[::4, 2], s=0.5, c='navy', alpha=0.3)
    ax2.set_xlim([-75, 75])
    ax2.set_ylim([-10, 260])
    ax2.set_aspect('equal')
    ax2.set_title('Pitch View (X-Z plane: Main Fins 55x31mm & Motor Cavity)', fontsize=12)
    ax2.set_xlabel('X [Lateral] (mm)')
    ax2.set_ylabel('Z [Length] (mm)')
    ax2.grid(True, linestyle='--', alpha=0.5)
    
    # 3. Yaw plane (Y vs Z) - Vertical Sub Fins
    ax3 = fig.add_subplot(2, 2, 3)
    ax3.scatter(verts[::4, 1], verts[::4, 2], s=0.5, c='crimson', alpha=0.3)
    ax3.set_xlim([-75, 75])
    ax3.set_ylim([-10, 260])
    ax3.set_aspect('equal')
    ax3.set_title('Yaw View (Y-Z plane: Sub Fins 49.5x27.9mm, kv=0.90)', fontsize=12)
    ax3.set_xlabel('Y [Vertical] (mm)')
    ax3.set_ylabel('Z [Length] (mm)')
    ax3.grid(True, linestyle='--', alpha=0.5)
    
    # 4. Tail View (X vs Y) - Cross Fin Layout
    ax4 = fig.add_subplot(2, 2, 4)
    tail_pts = verts[verts[:, 2] < 45.0]
    ax4.scatter(tail_pts[::2, 0], tail_pts[::2, 1], s=1.0, c='darkgreen', alpha=0.5)
    ax4.set_xlim([-75, 75])
    ax4.set_ylim([-75, 75])
    ax4.set_aspect('equal')
    ax4.set_title('Tail View (X-Y plane: 4-Fin Cross Layout & Launch Lug)', fontsize=12)
    ax4.set_xlabel('X [Lateral] (mm)')
    ax4.set_ylabel('Y [Vertical] (mm)')
    ax4.grid(True, linestyle='--', alpha=0.5)
    ax4.axhline(0, color='gray', linestyle=':')
    ax4.axvline(0, color='gray', linestyle=':')
    
    plt.tight_layout()
    plt.savefig('output/rocket_m3type1_preview.png', dpi=150)
    plt.savefig(r'C:\Users\kuron.HX99G\.gemini\antigravity\brain\f5d3bd8b-8307-472d-83e6-9bd725805a5f\rocket_m3type1_preview.png', dpi=150)
    print("Preview saved to output/rocket_m3type1_preview.png")

if __name__ == '__main__':
    build_candidate_1_complete()
