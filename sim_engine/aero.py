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
        alpha_deg: Pitch angle of attack in degrees
        beta_deg: Yaw angle in degrees
        cg_z_mm: Center of Gravity Z coordinate in mm from tail
        """
        if cg_z_mm is None:
            cg_z_mm = (self.z_min + self.z_max) / 2.0
            
        alpha_rad = np.radians(alpha_deg)
        beta_rad = np.radians(beta_deg)
        
        air_density = 1.225 # kg/m3
        q = 0.5 * air_density * (velocity_m_s**2)
        
        # 3D 幾何学的コンポーネント分離 (標準Z軸座標系: +Zが進行軸、Z=0がテール)
        # r は胴体中心軸 (Z軸) からの半径距離
        centers = self.face_centers_mm
        normals = self.std_normals
        areas = self.face_areas_m2
        verts = self.std_vertices
        
        r_body = self.ref_diameter_mm / 2.0
        r_centers = np.sqrt(centers[:, 0]**2 + centers[:, 1]**2)
        
        # 1. ノーズコーン判定: 前方部で法線が前方(+Z)を向いている面
        is_nose = (centers[:, 2] >= (self.z_max - 65.0)) & (normals[:, 2] > 0.05)
        cna_nose = 2.0 # Slender-body theory
        if np.sum(is_nose) > 0 and np.sum(areas[is_nose]) > 0:
            cp_nose = float(np.sum(centers[is_nose, 2] * areas[is_nose]) / np.sum(areas[is_nose]))
        else:
            cp_nose = self.z_max - 0.466 * 60.0
            
        # 2. フィン判定 (テール付近で胴体外径より突出している面)
        # 水平主翼 (X軸方向へ広がり、法線が Y 方向を向く)
        is_h_fin = (r_centers > (r_body + 0.2)) & (centers[:, 2] <= (self.z_min + 75.0)) & (abs(normals[:, 1]) > 0.5)
        # 垂直尾翼 (Y軸方向へ広がり、法線が X 方向を向く)
        is_v_fin = (r_centers > (r_body + 0.2)) & (centers[:, 2] <= (self.z_min + 75.0)) & (abs(normals[:, 0]) > 0.5)
        
        # 水平主翼 (Pitch 軸に寄与)
        if np.sum(is_h_fin) > 0 and np.sum(areas[is_h_fin]) > 0:
            h_faces = self.mesh.faces[is_h_fin].flatten()
            v_h = verts[h_faces]
            span_h = max(1.0, float(np.abs(v_h[:, 0]).max() - r_body))
            area_1fin_h_m2 = np.sum(areas[is_h_fin]) / 4.0 # 2枚 x 表裏
            cr_h = float(v_h[:, 2].max() - self.z_min)
            ct_h = max(0.0, 2.0 * area_1fin_h_m2 * 1e6 / span_h - cr_h)
            sweep_h = cr_h - ct_h
            mid_sweep_h = sweep_h + (ct_h - cr_h) / 2.0
            Lf_h = np.sqrt(mid_sweep_h**2 + span_h**2)
            k_body_h = 1.0 + r_body / (r_body + span_h)
            denom_h = 1.0 + np.sqrt(1.0 + (2.0 * Lf_h / (cr_h + ct_h))**2) if (cr_h + ct_h) > 0 else 2.0
            cna_h = k_body_h * (4.0 * 2.0 * (span_h / self.ref_diameter_mm)**2) / denom_h
            cp_h = float(np.sum(centers[is_h_fin, 2] * areas[is_h_fin]) / np.sum(areas[is_h_fin]))
        else:
            cna_h = 0.0
            cp_h = self.z_min + 20.0
            
        # 垂直尾翼 (Yaw 軸に寄与)
        if np.sum(is_v_fin) > 0 and np.sum(areas[is_v_fin]) > 0:
            v_faces = self.mesh.faces[is_v_fin].flatten()
            v_v = verts[v_faces]
            span_v = max(1.0, float(v_v[:, 1].max() - r_body))
            area_1fin_v_m2 = np.sum(areas[is_v_fin]) / 2.0 # 1枚 x 表裏
            cr_v = float(v_v[:, 2].max() - self.z_min)
            ct_v = max(0.0, 2.0 * area_1fin_v_m2 * 1e6 / span_v - cr_v)
            sweep_v = cr_v - ct_v
            mid_sweep_v = sweep_v + (ct_v - cr_v) / 2.0
            Lf_v = np.sqrt(mid_sweep_v**2 + span_v**2)
            k_body_v = 1.0 + r_body / (r_body + span_v)
            denom_v = 1.0 + np.sqrt(1.0 + (2.0 * Lf_v / (cr_v + ct_v))**2) if (cr_v + ct_v) > 0 else 2.0
            cna_v = k_body_v * (4.0 * 1.0 * (span_v / self.ref_diameter_mm)**2) / denom_v
            cp_v = float(np.sum(centers[is_v_fin, 2] * areas[is_v_fin]) / np.sum(areas[is_v_fin]))
        else:
            cna_v = 0.0
            cp_v = self.z_min + 20.0
            
        # Pitch 方向 (主翼作動)
        cna_pitch = cna_nose + cna_h
        cp_pitch_mm = (cna_nose * cp_nose + cna_h * cp_h) / cna_pitch if cna_pitch > 0 else cg_z_mm
        margin_pitch_cal = (cg_z_mm - cp_pitch_mm) / self.ref_diameter_mm
        
        # Yaw 方向 (垂直尾翼作動)
        cna_yaw = cna_nose + cna_v
        cp_yaw_mm = (cna_nose * cp_nose + cna_v * cp_v) / cna_yaw if cna_yaw > 0 else cg_z_mm
        margin_yaw_cal = (cg_z_mm - cp_yaw_mm) / self.ref_diameter_mm
        
        # 3D 空間実効安定性 (合成)
        cna_eff = cna_nose + 0.5 * (cna_h + cna_v)
        cp_eff_mm = (cna_nose * cp_nose + 0.5 * cna_h * cp_h + 0.5 * cna_v * cp_v) / cna_eff if cna_eff > 0 else cg_z_mm
        margin_eff_cal = (cg_z_mm - cp_eff_mm) / self.ref_diameter_mm
        margin_eff_mm = cg_z_mm - cp_eff_mm
        
        # クリティカル（最も厳しい軸）
        critical_margin_cal = min(margin_pitch_cal, margin_yaw_cal)
        
        # ロール誘導トルク (面ごとのクロス積)
        wind_dir = np.array([0.0, np.sin(alpha_rad), -np.cos(alpha_rad)], dtype=float)
        cos_theta = -np.dot(normals, wind_dir)
        F_faces_dummy = -normals * (q * 2.0 * cos_theta[:, np.newaxis] * areas[:, np.newaxis])
        r_cg = (centers - np.array([0.0, 0.0, cg_z_mm])) * 1e-3
        roll_torque = float(np.sum(np.cross(r_cg, F_faces_dummy)[:, 2]))
        
        # Axial Drag (Hoerner breakdown)
        total_wet_area = np.sum(areas)
        Cd_fric = 0.0045 * (total_wet_area / self.ref_area_m2) if self.ref_area_m2 > 0 else 0.35
        base_area = np.sum(areas * np.maximum(0, -normals[:, 2]))
        Cd_base = 0.12 * (base_area / self.ref_area_m2) if self.ref_area_m2 > 0 else 0.10
        Cd_nose = 0.08
        
        # Induced drag
        cn_eff = cna_eff * np.sin(alpha_rad)
        Cd_induced = abs(cn_eff * np.sin(alpha_rad))
        
        Cd = Cd_fric + Cd_base + Cd_nose + Cd_induced
        Cd = max(0.35, min(1.2, float(Cd)))
        Drag = float(q * self.ref_area_m2 * Cd)
        Normal_force = float(q * self.ref_area_m2 * cna_eff * np.sin(alpha_rad))
        
        return {
            "Cd": round(float(Cd), 3),
            "Drag_N": round(float(Drag), 4),
            "Normal_N": round(float(Normal_force), 4),
            "Roll_Torque_Nm": float(roll_torque),
            "CP_z_mm": round(float(cp_eff_mm), 2),
            "CG_z_mm": round(float(cg_z_mm), 2),
            "margin_mm": round(float(margin_eff_mm), 2),
            "margin_cal": round(float(margin_eff_cal), 2),
            "pitch_cp_mm": round(float(cp_pitch_mm), 2),
            "pitch_margin_cal": round(float(margin_pitch_cal), 2),
            "yaw_cp_mm": round(float(cp_yaw_mm), 2),
            "yaw_margin_cal": round(float(margin_yaw_cal), 2),
            "critical_margin_cal": round(float(critical_margin_cal), 2),
            "is_stable": bool(margin_eff_cal >= 0.8)
        }
