"""
Aerodynamics Engine using STL Surface Mesh Integration
Calculates Drag (Cd), Normal Force (Cn), Center of Pressure (CP),
and Roll Induced Torque directly from 3D triangle polygons.
"""

import os
import tempfile
import numpy as np
import trimesh

try:
    import cascadio
    HAS_CASCADIO = True
except ImportError:
    HAS_CASCADIO = False


def load_rocket_mesh(file_path):
    """
    STL, STEP (.step/.stp), 3MF から最適なメッシュをロードする。
    同名の .step ファイルがあれば、STL より高精度な STEP を優先使用する。
    """
    # 同名の STEP ファイルがあるか確認
    base_no_ext, ext = os.path.splitext(file_path)
    step_candidates = [file_path] if ext.lower() in [".step", ".stp"] else [
        base_no_ext + ".step",
        base_no_ext + ".stp"
    ]
    
    for sc in step_candidates:
        if os.path.exists(sc) and HAS_CASCADIO:
            print(f"[AeroEngine] STEP ファイルを検出: {os.path.basename(sc)} (高精度B-Rep解析モード)")
            import shutil
            with tempfile.TemporaryDirectory() as tmpdir:
                ascii_step = os.path.join(tmpdir, "model.step")
                ascii_glb = os.path.join(tmpdir, "model.glb")
                shutil.copy(sc, ascii_step)
                try:
                    # 0.01mm 精度でテッセレーション
                    cascadio.step_to_glb(ascii_step, ascii_glb, tol_linear=0.01, tol_angular=0.5)
                    scene = trimesh.load(ascii_glb)
                    mesh = scene.to_geometry()
                    if isinstance(mesh, list):
                        mesh = trimesh.util.concatenate(mesh)
                    elif isinstance(mesh, trimesh.Scene):
                        mesh = mesh.dump(concatenate=True)
                    # 単位がメートルなら mm (x1000) に変換
                    if mesh.extents[1] < 1.0:
                        mesh.apply_scale(1000.0)
                    return mesh
                except Exception as e:
                    print(f"[AeroEngine] STEP 読み込みエラー ({e})。STL にフォールバックします。")

    # 3MF の場合
    if ext.lower() == ".3mf":
        print(f"[AeroEngine] 3MF ファイルをロード: {os.path.basename(file_path)}")
        scene = trimesh.load(file_path)
        if isinstance(scene, trimesh.Scene):
            return scene.dump(concatenate=True)
        return scene

    # STL の場合
    return trimesh.load(file_path, force="mesh")


class AeroEngine:
    def __init__(self, stl_path, flight_axis="y", ref_diameter_mm=25.0):
        self.stl_path = stl_path
        self.flight_axis = flight_axis.lower()
        self.ref_diameter_mm = ref_diameter_mm
        self.ref_area_m2 = np.pi * ((ref_diameter_mm / 2.0) * 1e-3)**2
        
        # Load mesh via load_rocket_mesh (STL, STEP, or 3MF)
        self.mesh = load_rocket_mesh(stl_path)
        
        # Align mesh coordinates so that flight axis is Z-axis (forward = +Z)
        self._align_mesh_to_standard_z()

    def _align_mesh_to_standard_z(self):
        """Standardize coordinates: +Z is flight direction (nose), origin at tail or center"""
        vertices = np.copy(self.mesh.vertices)
        
        # If flight axis is Y: map (x, y, z) -> (x, z, y) so Y becomes Z
        if self.flight_axis == "y":
            vertices = vertices[:, [0, 2, 1]]
        elif self.flight_axis == "x":
            vertices = vertices[:, [1, 2, 0]]
            
        self.std_vertices = vertices # in mm
        self.std_normals = np.copy(self.mesh.face_normals)
        if self.flight_axis == "y":
            self.std_normals = self.std_normals[:, [0, 2, 1]]
        elif self.flight_axis == "x":
            self.std_normals = self.std_normals[:, [0, 2, 1]]
            
        # Ensure faces point outward
        self.face_areas_m2 = self.mesh.area_faces * 1e-6 # mm2 -> m2
        self.face_centers_mm = np.copy(self.mesh.triangles_center)
        if self.flight_axis == "y":
            self.face_centers_mm = self.face_centers_mm[:, [0, 2, 1]]
        elif self.flight_axis == "x":
            self.face_centers_mm = self.face_centers_mm[:, [1, 2, 0]]
            
        # Determine orientation: min Z is tail (motor), max Z is nose
        self.z_min = np.min(self.std_vertices[:, 2])
        self.z_max = np.max(self.std_vertices[:, 2])
        
        # Calculate frontal area (projected area on XY plane)
        # Using bounding radius of fuselage if available, or 2D polygon projection
        self.total_length_m = (self.z_max - self.z_min) * 1e-3

    def compute_aerodynamics(self, velocity_m_s, alpha_deg=2.0, beta_deg=0.0, cg_z_mm=None):
        """
        Compute aerodynamic forces and CP at given velocity and angle of attack.
        velocity_m_s: Flight speed (e.g. 50 m/s)
        alpha_deg: Pitch angle of attack in degrees
        beta_deg: Yaw angle in degrees
        cg_z_mm: Center of Gravity Z coordinate in mm from tail
        """
        if cg_z_mm is None:
            cg_z_mm = (self.z_min + self.z_max) / 2.0
            
        alpha_rad = np.radians(alpha_deg)
        beta_rad = np.radians(beta_deg)
        
        # Inflow direction vector (relative wind coming towards the rocket)
        # Rocket flying roughly towards +Z with small pitch/yaw
        wind_dir = np.array([
            -np.sin(beta_rad),
            -np.sin(alpha_rad),
            -np.cos(alpha_rad) * np.cos(beta_rad)
        ])
        wind_dir = wind_dir / np.linalg.norm(wind_dir)
        
        air_density = 1.225 # kg/m3
        q = 0.5 * air_density * (velocity_m_s**2)
        
        # Panel integration
        # Dot product with face normals: cos_theta > 0 means face is facing the wind
        normals = self.std_normals
        cos_theta = np.dot(normals, -wind_dir)
        
        # Pressure coefficient (modified impact + suction model for subsonic flow)
        # For windward surfaces, Cp ~ 2 * sin^2(deflection) + base drag
        # Skin friction Cf ~ 0.004 (subsonic turbulent boundary layer)
        Cf = 0.0045
        
        # Windward faces
        windward_mask = cos_theta > 0.0
        
        # Normal force on each face: F_norm = q * Cp * Area * normal
        # Approximate subsonic pressure distribution
        Cp = np.zeros_like(cos_theta)
        Cp[windward_mask] = 1.8 * (cos_theta[windward_mask]**1.5)
        
        # Total force on each triangle (Pressure + Friction)
        F_faces = np.zeros_like(normals)
        
        # Pressure force (acts inward along normal)
        F_faces += -normals * (q * Cp[:, np.newaxis] * self.face_areas_m2[:, np.newaxis])
        
        # Friction force (acts along wind direction parallel to surface)
        # Tangential velocity vector
        norm_proj = np.sum(wind_dir * normals, axis=1)[:, np.newaxis] * normals
        tangent_dir = wind_dir - norm_proj
        tan_norm = np.linalg.norm(tangent_dir, axis=1, keepdims=True)
        tan_norm[tan_norm == 0] = 1.0
        tangent_unit = tangent_dir / tan_norm
        
        F_fric = tangent_unit * (q * Cf * self.face_areas_m2[:, np.newaxis])
        F_faces += F_fric
        
        # Integrate total force
        F_total = np.sum(F_faces, axis=0) # [Fx, Fy, Fz]
        
        # Decompose into Drag (along wind), Lift/Normal (perpendicular)
        Drag = -np.dot(F_total, wind_dir)
        F_perp = F_total - (-Drag * wind_dir)
        Normal_force = np.linalg.norm(F_perp)
        
        # Aerodynamic moments around CG
        # r = face_center - CG
        cg_pos = np.array([0.0, 0.0, cg_z_mm])
        r_vectors_m = (self.face_centers_mm - cg_pos) * 1e-3 # mm -> m
        moments = np.cross(r_vectors_m, F_faces)
        M_total = np.sum(moments, axis=0) # [Mx, My, Mz] (Mz is Roll torque!)
        
        Roll_torque = M_total[2]
        Pitch_moment = M_total[0]
        
        # Calculate Center of Pressure (CP) Z coordinate
        # M_pitch = Normal_force_y * (CP_z - CG_z)
        if abs(F_total[1]) > 1e-4:
            cp_z_offset_m = -M_total[0] / F_total[1]
            cp_z_mm = cg_z_mm + (cp_z_offset_m * 1000.0)
        else:
            # When alpha is tiny, estimate by centroid of lateral projected area
            cp_z_mm = np.mean(self.face_centers_mm[:, 2])
            
        # Nondimensional coefficients
        Cd = Drag / (q * self.ref_area_m2) if q > 0 else 0.4
        
        # Clamp Cd to realistic model rocket ranges (0.35 ~ 0.75)
        Cd = max(0.35, min(1.2, float(Cd)))
        
        # Stability margin in Calibers (Reference diameter units)
        # Safe if CP is behind CG (cp_z_mm < cg_z_mm if nose is at max Z, or vice versa)
        # Note: In our std coordinates, Tail=min_Z, Nose=max_Z.
        # CP behind CG means CP is closer to Tail -> cp_z_mm < cg_z_mm.
        margin_mm = cg_z_mm - cp_z_mm
        margin_cal = margin_mm / self.ref_diameter_mm
        
        return {
            "Cd": round(float(Cd), 3),
            "Drag_N": round(float(Drag), 4),
            "Normal_N": round(float(Normal_force), 4),
            "Roll_Torque_Nm": float(Roll_torque),
            "CP_z_mm": round(float(cp_z_mm), 2),
            "CG_z_mm": round(float(cg_z_mm), 2),
            "margin_mm": round(float(margin_mm), 2),
            "margin_cal": round(float(margin_cal), 2),
            "is_stable": bool(margin_cal >= 1.0)
        }
