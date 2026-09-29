import os
import sys
sys.path.insert(0, os.path.abspath("."))
import shutil
import numpy as np
import trimesh
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

plt.rcParams['font.sans-serif'] = ['Yu Gothic', 'Meiryo', 'DejaVu Sans', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

art_dir = r"C:\Users\kuron.HX99G\.gemini\antigravity\brain\f5d3bd8b-8307-472d-83e6-9bd725805a5f"
os.makedirs("output", exist_ok=True)
os.makedirs("input", exist_ok=True)

# =============================================================================
# 1. GENERATE PREVIEW FOR CANDIDATE 2 (機体②: 35°下反角逆Y字翼)
# Matches exact style of Candidate 1 and Candidate 3 (3-panel)
# =============================================================================
def generate_candidate_2_preview():
    print("Generating rocket_candidate_2_preview.png...")
    total_len = 250.0
    nose_len = 120.0
    body_len = 130.0
    radius = 12.0
    main_span = 75.7
    main_cr = 45.0
    v_span = 52.9
    v_cr = 31.5
    droop_deg = 35.0
    droop_rad = np.radians(droop_deg)
    fin_thick = 0.44

    cg_z = 65.5
    cp_z = 44.8
    margin_cal = 0.86
    margin_mm = 20.7

    fig = plt.figure(figsize=(18, 7.5), dpi=200)
    fig.patch.set_facecolor('#ffffff')

    ax1 = fig.add_subplot(131, projection='3d')
    ax2 = fig.add_subplot(132)
    ax3 = fig.add_subplot(133)

    # 1. 3D Isometric View
    # Body mesh from revolution
    z_body = np.linspace(0, body_len, 40)
    theta = np.linspace(0, 2*np.pi, 36)
    Z_b, T_b = np.meshgrid(z_body, theta)
    X_b = radius * np.cos(T_b)
    Y_b = radius * np.sin(T_b)
    ax1.plot_surface(X_b, Y_b, Z_b, color='#ffd166', alpha=0.35, edgecolor='#d4a373', lw=0.3)

    # Nose mesh
    z_nose = np.linspace(body_len, total_len, 50)
    Z_n, T_n = np.meshgrid(z_nose, theta)
    dist = total_len - Z_n
    R_n = radius * (np.maximum(0.0, dist) / nose_len)**0.75
    X_n = R_n * np.cos(T_n)
    Y_n = R_n * np.sin(T_n)
    ax1.plot_surface(X_n, Y_n, Z_n, color='#ffd166', alpha=0.55, edgecolor='#b5838d', lw=0.3)

    # 3 Fins 3D
    # Right droop fin
    fin_r_verts = [
        [radius * np.cos(-droop_rad), radius * np.sin(-droop_rad), main_cr],
        [(radius + main_span) * np.cos(-droop_rad), (radius + main_span) * np.sin(-droop_rad), 0.0],
        [radius * np.cos(-droop_rad), radius * np.sin(-droop_rad), 0.0]
    ]
    poly_r = Poly3DCollection([fin_r_verts], color='#e63946', alpha=0.75, edgecolor='#9e2a2b', lw=1.2)
    ax1.add_collection3d(poly_r)

    # Left droop fin
    fin_l_verts = [
        [-radius * np.cos(-droop_rad), radius * np.sin(-droop_rad), main_cr],
        [-(radius + main_span) * np.cos(-droop_rad), (radius + main_span) * np.sin(-droop_rad), 0.0],
        [-radius * np.cos(-droop_rad), radius * np.sin(-droop_rad), 0.0]
    ]
    poly_l = Poly3DCollection([fin_l_verts], color='#e63946', alpha=0.75, edgecolor='#9e2a2b', lw=1.2)
    ax1.add_collection3d(poly_l)

    # Vertical fin (+Y)
    fin_v_verts = [
        [0.0, radius, v_cr],
        [0.0, radius + v_span, 0.0],
        [0.0, radius, 0.0]
    ]
    poly_v = Poly3DCollection([fin_v_verts], color='#1d3557', alpha=0.75, edgecolor='#03045e', lw=1.2)
    ax1.add_collection3d(poly_v)

    ax1.set_xlim(-85, 85)
    ax1.set_ylim(-85, 85)
    ax1.set_zlim(0, 260)
    ax1.set_box_aspect([1, 1, 2.2])
    ax1.view_init(elev=20, azim=45)
    ax1.set_title("3D アイソメトリック外観\n(全長250mm, 35°下反角逆Y字翼)", fontsize=11, fontweight="bold")
    ax1.set_xlabel("X [mm]")
    ax1.set_ylabel("Y [mm]")
    ax1.set_zlabel("Z [mm]")

    # 2. Side View (X-Z)
    xs_nose = np.linspace(0, nose_len, 100)
    rs_nose = radius * (xs_nose / nose_len)**0.75
    zs_nose = 250.0 - xs_nose

    ax2.plot(rs_nose, zs_nose, '#d4a373', lw=2)
    ax2.plot(-rs_nose, zs_nose, '#d4a373', lw=2)
    ax2.plot([radius, radius], [0, body_len], '#d4a373', lw=2)
    ax2.plot([-radius, -radius], [0, body_len], '#d4a373', lw=2)
    ax2.plot([-radius, radius], [0, 0], '#d4a373', lw=2)

    # Main fins in side projection (projected span = span * cos(35 deg))
    proj_span = main_span * np.cos(droop_rad)
    ax2.plot([radius, radius + proj_span, radius], [main_cr, 0, 0], '#e63946', lw=2.2, label=f"主翼 (75.7×45mm, 下垂35°)")
    ax2.plot([-radius, -(radius + proj_span), -radius], [main_cr, 0, 0], '#e63946', lw=2.2)

    # Stability marks
    ax2.axhline(cg_z, color='green', ls='--', lw=1.8, label=f"重心 CG (Z={cg_z:.1f}mm)")
    ax2.axhline(cp_z, color='purple', ls=':', lw=2.0, label=f"風圧中心 CP (Z={cp_z:.1f}mm)")

    ax2.set_xlim(-85, 85)
    ax2.set_ylim(-10, 260)
    ax2.set_aspect('equal')
    ax2.grid(True, ls='--', alpha=0.5)
    ax2.legend(loc='upper right', fontsize=8.5)
    ax2.set_title(f"側面断面・バランス図 (Side View)\n実効安全率: +{margin_cal:.2f} cal (余裕度 {margin_mm:.1f}mm)", fontsize=11, fontweight="bold")
    ax2.set_xlabel("X [mm]")
    ax2.set_ylabel("Z (長軸高さ) [mm]")

    # 3. Rear View (X-Y)
    circle_body = plt.Circle((0, 0), radius, color='#ffd166', alpha=0.4, ec='#d4a373', lw=2, label="胴体 (D=24mm)")
    circle_motor = plt.Circle((0, 0), 9.0, color='darkorange', alpha=0.4, ec='brown', lw=1.5, label="モーター (18mm)")
    ax3.add_patch(circle_body)
    ax3.add_patch(circle_motor)

    # Fins in rear view
    # Vertical fin (+Y)
    ax3.plot([0, 0], [radius, radius + v_span], color='#1d3557', lw=3.0, label=f"垂直尾翼 (52.9×31.5mm, Kv=0.7)")
    # Right droop fin
    x_r_end = (radius + main_span) * np.cos(-droop_rad)
    y_r_end = (radius + main_span) * np.sin(-droop_rad)
    x_r_root = radius * np.cos(-droop_rad)
    y_r_root = radius * np.sin(-droop_rad)
    ax3.plot([x_r_root, x_r_end], [y_r_root, y_r_end], color='#e63946', lw=3.0, label=f"主翼 (75.7mm, 35°下反角)")

    # Left droop fin
    ax3.plot([-x_r_root, -x_r_end], [y_r_root, y_r_end], color='#e63946', lw=3.0)

    # Reference horizontal dashed line
    ax3.axhline(0, color='#999999', ls=':', lw=1.0)
    ax3.scatter([0], [0], color='black', s=30, label="中心軸")

    ax3.set_xlim(-85, 85)
    ax3.set_ylim(-85, 85)
    ax3.set_aspect('equal')
    ax3.grid(True, ls='--', alpha=0.5)
    ax3.legend(loc='upper right', fontsize=8.5)
    ax3.set_title("後方視界・翼配置図 (Rear View)\n3枚逆Y字配置 (下反角35° / 垂直Kv=0.70)", fontsize=11, fontweight="bold")
    ax3.set_xlabel("X [mm]")
    ax3.set_ylabel("Y [mm]")

    plt.suptitle("【機体②】超高安定・逆Y字3枚翼機 (0.86 cal, 30.13s) 3D CAD形状＆配置図", fontsize=14, fontweight="bold", y=0.98)
    p_path = "output/rocket_candidate_2_preview.png"
    plt.tight_layout(rect=[0.02, 0.02, 0.98, 0.93])
    plt.savefig(p_path, dpi=200)
    plt.close(fig)
    shutil.copy(p_path, os.path.join(art_dir, "rocket_candidate_2_preview.png"))
    print(f"Saved {p_path} and artifact copy.")

# =============================================================================
# 2. GENERATE PREVIEW FOR BASELINE ROCKET (機体⓪: つくばモデルロケット)
# =============================================================================
def generate_baseline_preview():
    print("Generating rocket_candidate_0_baseline_preview.png...")
    total_len = 190.0
    nose_len = 80.0
    body_len = 110.0
    radius = 12.0
    fin_span = 48.0
    fin_cr = 45.0
    cg_z = 62.0
    cp_z = 42.0

    fig = plt.figure(figsize=(18, 7.5), dpi=200)
    fig.patch.set_facecolor('#ffffff')

    ax1 = fig.add_subplot(131, projection='3d')
    ax2 = fig.add_subplot(132)
    ax3 = fig.add_subplot(133)

    # 1. 3D Isometric View
    z_body = np.linspace(0, body_len, 30)
    theta = np.linspace(0, 2*np.pi, 36)
    Z_b, T_b = np.meshgrid(z_body, theta)
    X_b = radius * np.cos(T_b)
    Y_b = radius * np.sin(T_b)
    ax1.plot_surface(X_b, Y_b, Z_b, color='#90e0ef', alpha=0.35, edgecolor='#0077b6', lw=0.3)

    z_nose = np.linspace(body_len, total_len, 40)
    Z_n, T_n = np.meshgrid(z_nose, theta)
    dist = total_len - Z_n
    R_n = radius * (np.maximum(0.0, dist) / nose_len)**0.75
    X_n = R_n * np.cos(T_n)
    Y_n = R_n * np.sin(T_n)
    ax1.plot_surface(X_n, Y_n, Z_n, color='#90e0ef', alpha=0.55, edgecolor='#0096c7', lw=0.3)

    # 3 symmetric 120 deg fins
    for ang_deg in [90, 210, 330]:
        rad = np.radians(ang_deg)
        f_verts = [
            [radius * np.cos(rad), radius * np.sin(rad), fin_cr],
            [(radius + fin_span) * np.cos(rad), (radius + fin_span) * np.sin(rad), 0.0],
            [radius * np.cos(rad), radius * np.sin(rad), 0.0]
        ]
        poly = Poly3DCollection([f_verts], color='#0077b6', alpha=0.75, edgecolor='#03045e', lw=1.2)
        ax1.add_collection3d(poly)

    ax1.set_xlim(-85, 85)
    ax1.set_ylim(-85, 85)
    ax1.set_zlim(0, 210)
    ax1.set_box_aspect([1, 1, 1.8])
    ax1.view_init(elev=20, azim=45)
    ax1.set_title("3D アイソメトリック外観\n(初期機体: 全長190mm, 120°対称3枚翼)", fontsize=11, fontweight="bold")
    ax1.set_xlabel("X [mm]")
    ax1.set_ylabel("Y [mm]")
    ax1.set_zlabel("Z [mm]")

    # 2. Side View
    xs_nose = np.linspace(0, nose_len, 80)
    rs_nose = radius * (xs_nose / nose_len)**0.75
    zs_nose = total_len - xs_nose

    ax2.plot(rs_nose, zs_nose, '#0077b6', lw=2)
    ax2.plot(-rs_nose, zs_nose, '#0077b6', lw=2)
    ax2.plot([radius, radius], [0, body_len], '#0077b6', lw=2)
    ax2.plot([-radius, -radius], [0, body_len], '#0077b6', lw=2)
    ax2.plot([-radius, radius], [0, 0], '#0077b6', lw=2)

    proj_s = fin_span * np.cos(np.radians(30))
    ax2.plot([radius, radius + proj_s, radius], [fin_cr, 0, 0], '#0077b6', lw=2.2, label=f"対称翼 (48×45mm)")
    ax2.plot([-radius, -(radius + proj_s), -radius], [fin_cr, 0, 0], '#0077b6', lw=2.2)

    ax2.axhline(cg_z, color='green', ls='--', lw=1.8, label=f"重心 CG (Z={cg_z:.1f}mm)")
    ax2.axhline(cp_z, color='purple', ls=':', lw=2.0, label=f"風圧中心 CP (Z={cp_z:.1f}mm)")

    ax2.set_xlim(-85, 85)
    ax2.set_ylim(-10, 210)
    ax2.set_aspect('equal')
    ax2.grid(True, ls='--', alpha=0.5)
    ax2.legend(loc='upper right', fontsize=8.5)
    ax2.set_title("側面断面・バランス図 (Side View)\n実効安全率: +0.83 cal (滞空 22.40s)", fontsize=11, fontweight="bold")
    ax2.set_xlabel("X [mm]")
    ax2.set_ylabel("Z (長軸高さ) [mm]")

    # 3. Rear View
    circle_body = plt.Circle((0, 0), radius, color='#90e0ef', alpha=0.4, ec='#0077b6', lw=2, label="胴体 (D=24mm)")
    circle_motor = plt.Circle((0, 0), 9.0, color='darkorange', alpha=0.4, ec='brown', lw=1.5, label="モーター (18mm)")
    ax3.add_patch(circle_body)
    ax3.add_patch(circle_motor)

    for i, ang_deg in enumerate([90, 210, 330]):
        rad = np.radians(ang_deg)
        x_end = (radius + fin_span) * np.cos(rad)
        y_end = (radius + fin_span) * np.sin(rad)
        x_root = radius * np.cos(rad)
        y_root = radius * np.sin(rad)
        lbl = "対称3枚翼 (120°等配)" if i == 0 else None
        ax3.plot([x_root, x_end], [y_root, y_end], color='#0077b6', lw=3.0, label=lbl)

    ax3.scatter([0], [0], color='black', s=30, label="中心軸")
    ax3.set_xlim(-85, 85)
    ax3.set_ylim(-85, 85)
    ax3.set_aspect('equal')
    ax3.grid(True, ls='--', alpha=0.5)
    ax3.legend(loc='upper right', fontsize=8.5)
    ax3.set_title("後方視界・翼配置図 (Rear View)\n正120°等角度 完全対称配置", fontsize=11, fontweight="bold")
    ax3.set_xlabel("X [mm]")
    ax3.set_ylabel("Y [mm]")

    plt.suptitle("【機体⓪】初期ベースライン機（つくばモデルロケット）3D CAD形状＆配置図", fontsize=14, fontweight="bold", y=0.98)
    p_path = "output/rocket_candidate_0_baseline_preview.png"
    plt.tight_layout(rect=[0.02, 0.02, 0.98, 0.93])
    plt.savefig(p_path, dpi=200)
    plt.close(fig)
    shutil.copy(p_path, os.path.join(art_dir, "rocket_candidate_0_baseline_preview.png"))
    print(f"Saved {p_path} and artifact copy.")

# =============================================================================
# 3. BUILD CANDIDATE 3 3D PRINTABLE STL AND 4-PANEL PREVIEW (ロケットM3type3.stl)
# =============================================================================
def build_candidate_3_full():
    print("Generating input/ロケットM3type3.stl and output/rocket_m3type3_preview.png...")
    from scratch.generate_rocket_1_final import create_hollow_airframe, create_filleted_fin_mesh, create_launch_lug

    airframe = create_hollow_airframe(n_radial=64, n_z_steps=80)

    # 4 Fins (59 span x 33 root chord, symmetric cross)
    cr = 33.0
    span = 59.0
    thick = 0.44
    fillet_r = 1.5

    fin_base = create_filleted_fin_mesh(span=span, root_chord=cr, thickness=thick, fillet_r=fillet_r, body_r=12.0)
    
    fin_0 = fin_base.copy()
    
    rot_90 = trimesh.transformations.rotation_matrix(np.pi / 2.0, [0, 0, 1])
    fin_90 = fin_base.copy()
    fin_90.apply_transform(rot_90)

    rot_180 = trimesh.transformations.rotation_matrix(np.pi, [0, 0, 1])
    fin_180 = fin_base.copy()
    fin_180.apply_transform(rot_180)

    rot_270 = trimesh.transformations.rotation_matrix(3.0 * np.pi / 2.0, [0, 0, 1])
    fin_270 = fin_base.copy()
    fin_270.apply_transform(rot_270)

    lug = create_launch_lug(z_start=40.0, length=8.0, r_inner=1.6, r_outer=2.4, body_r=12.0, angle_deg=-45.0)

    full_rocket = trimesh.util.concatenate([airframe, fin_0, fin_90, fin_180, fin_270, lug])
    stl_path = "input/ロケットM3type3.stl"
    full_rocket.export(stl_path)
    print(f"Saved complete 3D STL to: {stl_path} (Faces: {len(full_rocket.faces)})")

    # Render 4-Panel Mesh Preview (same style as rocket_m3type1 and rocket_m3type2)
    fig = plt.figure(figsize=(18, 12), dpi=200)
    fig.patch.set_facecolor('#ffffff')

    ax1 = fig.add_subplot(221, projection='3d')
    ax2 = fig.add_subplot(222)
    ax3 = fig.add_subplot(223)
    ax4 = fig.add_subplot(224)

    verts = full_rocket.vertices
    faces = full_rocket.faces

    # 1. 3D Isometric View
    mesh_col = Poly3DCollection(verts[faces], alpha=0.15, facecolor='#2a9d8f', edgecolor='#264653', linewidths=0.2)
    ax1.add_collection3d(mesh_col)
    ax1.set_xlim(-70, 70)
    ax1.set_ylim(-70, 70)
    ax1.set_zlim(0, 255)
    ax1.set_box_aspect([1, 1, 1.8])
    ax1.view_init(elev=22, azim=45)
    ax1.set_title("3D Isometric View (Candidate 3)", fontsize=13, fontweight="bold")
    ax1.set_xlabel("X (mm)")
    ax1.set_ylabel("Y (mm)")
    ax1.set_zlabel("Z (mm)")

    # Sample points for 2D projections
    sub_indices = np.random.choice(len(verts), size=min(4500, len(verts)), replace=False)
    sub_v = verts[sub_indices]

    # 2. Pitch View (X-Z)
    ax2.scatter(sub_v[:, 0], sub_v[:, 2], s=1.2, color='#1d3557', alpha=0.55)
    ax2.set_xlim(-75, 75)
    ax2.set_ylim(-10, 255)
    ax2.set_aspect('equal')
    ax2.grid(True, ls='--', alpha=0.5)
    ax2.set_title("Side / Pitch View (X-Z plane: 4-Fin Cross 59x33mm)", fontsize=12, fontweight="bold")
    ax2.set_xlabel("X [Lateral] (mm)")
    ax2.set_ylabel("Z [Length] (mm)")

    # 3. Yaw View (Y-Z)
    ax3.scatter(sub_v[:, 1], sub_v[:, 2], s=1.2, color='#e63946', alpha=0.55)
    ax3.set_xlim(-75, 75)
    ax3.set_ylim(-10, 255)
    ax3.set_aspect('equal')
    ax3.grid(True, ls='--', alpha=0.5)
    ax3.set_title("Yaw View (Y-Z plane: Symmetric 4-Fin Cross)", fontsize=12, fontweight="bold")
    ax3.set_xlabel("Y [Vertical] (mm)")
    ax3.set_ylabel("Z [Length] (mm)")

    # 4. Tail View (X-Y)
    ax4.scatter(sub_v[:, 0], sub_v[:, 1], s=1.5, color='#2a9d8f', alpha=0.6)
    ax4.set_xlim(-75, 75)
    ax4.set_ylim(-75, 75)
    ax4.set_aspect('equal')
    ax4.grid(True, ls='--', alpha=0.5)
    ax4.axhline(0, color='#666', ls=':', lw=1.0)
    ax4.axvline(0, color='#666', ls=':', lw=1.0)
    ax4.set_title("Tail View (X-Y plane: 4-Fin Cross Layout & Launch Lug)", fontsize=12, fontweight="bold")
    ax4.set_xlabel("X [Lateral] (mm)")
    ax4.set_ylabel("Y [Vertical] (mm)")

    plt.suptitle("Rocket M3 Type 3 (Candidate 3 - High Stability 4-Fin Cross Model)", fontsize=16, fontweight="bold", y=0.98)
    p_path = "output/rocket_m3type3_preview.png"
    plt.tight_layout(rect=[0.02, 0.02, 0.98, 0.94])
    plt.savefig(p_path, dpi=200)
    plt.close(fig)
    shutil.copy(p_path, os.path.join(art_dir, "rocket_m3type3_preview.png"))
    print(f"Saved {p_path} and artifact copy.")

if __name__ == "__main__":
    generate_candidate_2_preview()
    generate_baseline_preview()
    build_candidate_3_full()
    print("ALL MISSING PREVIEWS SUCCESSFULLY GENERATED!")
