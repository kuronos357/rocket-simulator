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
    STL, STEP (.step/.stp), 3MF からメッシュをロードする。
    指定されたファイル形式を忠実に読み込み、極薄フィン（0.5mm等）の欠落を防ぐ。
    """
    base_no_ext, ext = os.path.splitext(file_path)
    
    # STEP が明示的に指定された場合
    if ext.lower() in [".step", ".stp"]:
        if HAS_CASCADIO:
            print(f"[AeroEngine] STEP ファイルをロード: {os.path.basename(file_path)}")
            import shutil
            with tempfile.TemporaryDirectory() as tmpdir:
                ascii_step = os.path.join(tmpdir, "model.step")
                ascii_glb = os.path.join(tmpdir, "model.glb")
                shutil.copy(file_path, ascii_step)
                try:
                    cascadio.step_to_glb(ascii_step, ascii_glb, tol_linear=0.005, tol_angular=0.2)
                    scene = trimesh.load(ascii_glb)
                    mesh = scene.to_geometry()
                    if isinstance(mesh, list):
                        mesh = trimesh.util.concatenate(mesh)
                    elif isinstance(mesh, trimesh.Scene):
                        mesh = mesh.dump(concatenate=True)
                    if mesh.extents[1] < 1.0:
                        mesh.apply_scale(1000.0)
                    return mesh
                except Exception as e:
                    print(f"[AeroEngine] STEP 読み込みエラー ({e})。STL があればそちらを使用してください。")
        else:
            print("[AeroEngine] cascadio がインストールされていません。STL を使用してください。")

    # 3MF の場合
    if ext.lower() == ".3mf":
        print(f"[AeroEngine] 3MF ファイルをロード: {os.path.basename(file_path)}")
        scene = trimesh.load(file_path)
        if isinstance(scene, trimesh.Scene):
            return scene.dump(concatenate=True)
        return scene

    # STL の場合 (デフォルト: Fusion 360 のハイメッシュ STL を忠実に読み込み)
    return trimesh.load(file_path, force="mesh")


class AeroEngine:
    def __init__(self, stl_path, flight_axis="y", ref_diameter_mm=25.0):
        self.stl_path = stl_path
        self.flight_axis = flight_axis.lower()
        self.ref_diameter_mm = ref_diameter_mm
        self.ref_area_m2 = np.pi * ((ref_diameter_mm / 2.0) * 1e-3)**2
        
        # Load mesh via load_rocket_mesh (STL, STEP, or 3MF)
        self.mesh = load_rocket_mesh(stl_path)
        
        # 内部パーツ（モーター、ストリーマ）の自動除外
        self._clean_internal_components()
        
        # Align mesh coordinates so that flight axis is Z-axis (forward = +Z)
        self._align_mesh_to_standard_z()

    def _clean_internal_components(self):
        """
        CADエクスポート時にSTL内に混入した内部パーツ（モーターやストリーマ）を自動検出し、
        純粋な外表面スキンメッシュだけを抽出する。
        """
        try:
            bodies = self.mesh.split(only_watertight=False)
            if len(bodies) <= 1:
                return

            clean_components = []
            removed_count = 0
            for b in bodies:
                r_max = float(np.sqrt(b.vertices[:, 0]**2 + b.vertices[:, 2]**2).max())
                # モーター判定 (直径18mm, 半径9mm以内, 長さ70mm)
                is_motor = bool(b.bounds[0][1] >= -1.0 and b.bounds[1][1] <= 75.0 and r_max <= 9.2 and len(b.faces) < 1000)
                # ストリーマ判定 (半径8.5mm以内, 胴体内部)
                is_streamer = bool(b.bounds[0][1] >= 65.0 and b.bounds[1][1] <= 180.0 and r_max <= 8.5)
                
                if is_motor or is_streamer:
                    removed_count += 1
                else:
                    clean_components.append(b)
                    
            if clean_components and removed_count > 0:
                print(f"[AeroEngine] 内部パーツ ({removed_count}個) を自動除外し、外表面スキンを抽出しました。")
                self.mesh = trimesh.util.concatenate(clean_components)
        except Exception:
            pass

    def _align_mesh_to_standard_z(self):
        """Standardize coordinates: +Z is flight direction (nose), origin at tail, maintaining right-handed chirality"""
        # Determine rotation matrix R (det(R) = +1) to orient flight axis to +Z
        if self.flight_axis == "y":
            # Map Y -> +Z, preserving right-handed frame (det = +1)
            # x_new = -x, y_new = z, z_new = y
            R = np.array([
                [-1.0,  0.0,  0.0],
                [ 0.0,  0.0,  1.0],
                [ 0.0,  1.0,  0.0]
            ], dtype=float)
        elif self.flight_axis == "x":
            # Map X -> +Z, preserving right-handed frame (det = +1)
            # x_new = z, y_new = y, z_new = -x
            R = np.array([
                [ 0.0,  0.0,  1.0],
                [ 0.0,  1.0,  0.0],
                [-1.0,  0.0,  0.0]
            ], dtype=float)
        else:
            R = np.eye(3, dtype=float)

        self.R = R
        self.std_vertices = np.dot(self.mesh.vertices, R.T)
        self.std_normals = np.dot(self.mesh.face_normals, R.T)
        self.face_centers_mm = np.dot(self.mesh.triangles_center, R.T)
        self.face_areas_m2 = self.mesh.area_faces * 1e-6 # mm2 -> m2

        # Determine orientation: min Z is tail (motor), max Z is nose
        self.z_min = float(np.min(self.std_vertices[:, 2]))
        self.z_max = float(np.max(self.std_vertices[:, 2]))
        self.total_length_m = (self.z_max - self.z_min) * 1e-3

    def compute_aerodynamics(self, velocity_m_s, alpha_deg=2.0, beta_deg=0.0, cg_z_mm=None):
        """
        Compute aerodynamic forces, roll torque, and CP at given velocity and angle of attack.
        velocity_m_s: Flight speed (e.g. 40 m/s)
        alpha_deg: Pitch angle of attack in degrees (nose pitches towards +Y)
        beta_deg: Yaw angle in degrees
        cg_z_mm: Center of Gravity Z coordinate in mm from tail
        """
        if cg_z_mm is None:
            cg_z_mm = (self.z_min + self.z_max) / 2.0
            
        alpha_rad = np.radians(alpha_deg)
        beta_rad = np.radians(beta_deg)
        
        # Inflow direction vector (direction air flows in body frame: mainly towards -Z, with +Y when pitched up)
        wind_dir = np.array([
            -np.sin(beta_rad),
             np.sin(alpha_rad),
            -np.cos(alpha_rad) * np.cos(beta_rad)
        ], dtype=float)
        wind_dir = wind_dir / np.linalg.norm(wind_dir)
        
        air_density = 1.225 # kg/m3
        q = 0.5 * air_density * (velocity_m_s**2)
        
        # Dot product with face normals: cos_theta > 0 means face is facing the oncoming wind
        normals = self.std_normals
        cos_theta = -np.dot(normals, wind_dir)
        
        # Panel normal force and moment integration
        normals = self.std_normals
        cos_theta = -np.dot(normals, wind_dir)
        
        # Subsonic linear differential pressure model for fins & lifting surfaces:
        # Windward faces: positive pressure (Cp ~ 2.0 * cos_theta)
        # Leeward faces: suction/depression (Cp ~ 1.0 * cos_theta)
        Cp_lat = np.zeros_like(cos_theta)
        windward = cos_theta > 0.0
        Cp_lat[windward] = 2.0 * cos_theta[windward]
        Cp_lat[~windward] = 1.0 * cos_theta[~windward]
        
        # Pressure forces (normal to face)
        F_faces = -normals * (q * Cp_lat[:, np.newaxis] * self.face_areas_m2[:, np.newaxis])
        
        # Aerodynamic moments around CG
        cg_pos = np.array([0.0, 0.0, cg_z_mm])
        r_vectors_m = (self.face_centers_mm - cg_pos) * 1e-3 # mm -> m
        moments = np.cross(r_vectors_m, F_faces)
        M_total = np.sum(moments, axis=0) # [Mx, My, Mz] (Mz is Roll torque!)
        
        Roll_torque = float(M_total[2])
        Pitch_moment = float(M_total[0])
        
        # Lateral normal force (Fy in pitch plane)
        F_total = np.sum(F_faces, axis=0)
        Fy_total = float(F_total[1])
        Normal_force = float(np.linalg.norm([F_total[0], F_total[1]]))
        
        # Calculate Center of Pressure (CP) Z coordinate
        # M_pitch = - (CP_z - CG_z) * Fy_total
        if abs(Fy_total) > 1e-4:
            cp_z_offset_m = -Pitch_moment / Fy_total
            cp_z_mm = cg_z_mm + (cp_z_offset_m * 1000.0)
        else:
            cp_z_mm = np.mean(self.face_centers_mm[:, 2])
            
        # Axial Drag Calculation (Hoerner subsonic aerodynamic breakdown):
        # 1. Skin friction (turbulent boundary layer over total wetted area)
        total_wet_area = np.sum(self.face_areas_m2)
        Cd_fric = 0.0045 * (total_wet_area / self.ref_area_m2) if self.ref_area_m2 > 0 else 0.35
        # 2. Base drag (flow separation at rear/tail area)
        base_area = np.sum(self.face_areas_m2 * np.maximum(0, -normals[:, 2]))
        Cd_base = 0.12 * (base_area / self.ref_area_m2) if self.ref_area_m2 > 0 else 0.10
        # 3. Nose form pressure drag
        Cd_nose = 0.08
        # 4. Induced drag due to lift/normal force: Cdi ~ (Cn^2) / (pi * AR) ~ Cn * sin(alpha)
        Cn = Fy_total / (q * self.ref_area_m2) if (q > 0 and self.ref_area_m2 > 0) else 0.0
        Cd_induced = abs(Cn * np.sin(alpha_rad))
        
        Cd = Cd_fric + Cd_base + Cd_nose + Cd_induced
        Cd = max(0.35, min(1.2, float(Cd)))
        Drag = float(q * self.ref_area_m2 * Cd)
        
        # Stability margin in Calibers (Reference diameter units)
        # Safe if CP is behind CG (cp_z_mm < cg_z_mm, closer to tail)
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
