"""
Rocket Parameters and Geometry Loader
Loads params.json exported from Fusion 360, applies real material/3D-print densities,
and calculates composite mass properties (CG, Moments of Inertia) along the flight axis.
"""

import json
import os
import re
import numpy as np
from .motor_db import get_motor

MATERIAL_DENSITIES = {
    "PLA": 1.24,       # g/cm3
    "PETG": 1.27,
    "ABS": 1.04,
    "FILM": 0.92,      # Polyethylene / Mylar film
    "NYLON": 1.14
}

class RocketModel:
    def __init__(self, json_path, shell_thickness_mm=0.4, infill_ratio=0.02, default_material="PLA", airframe_mass_override_g=None):
        self.json_path = os.path.abspath(json_path)
        self.base_dir = os.path.dirname(self.json_path)
        
        with open(self.json_path, 'r', encoding='utf-8') as f:
            self.raw_data = json.load(f)
            
        self.design_name = self.raw_data.get("design_name", "Rocket")
        self.stl_filename = self.raw_data.get("stl_file", f"{self.design_name}.stl")
        self.stl_path = os.path.join(self.base_dir, self.stl_filename)
        
        self.shell_thickness_mm = shell_thickness_mm
        self.infill_ratio = infill_ratio
        self.default_material = default_material
        self.airframe_mass_override_g = airframe_mass_override_g
        
        # 1. 軸の自動判定 (X, Y, Z のうち寸法が最大のものを進行軸とする)
        self._detect_flight_axis()
        
        # 2. 各ボディの分類と質量・重心の再計算
        self.parts = []
        self.motor_part = None
        self.recovery_part = None
        
        self._process_bodies()
        
        # スライサー実測値による構造体質量のスケーリング
        self._apply_airframe_override()
        
        # 3. 機体全体の合成重心・慣性テンソルの計算
        self._calculate_composite_properties()

    def _apply_airframe_override(self):
        struct_parts = [p for p in self.parts if p.get("type") == "structure"]
        if not struct_parts:
            return
            
        target_mass = self.airframe_mass_override_g
        if target_mass is None:
            # プロジェクト直下の .gcode.3mf や .3mf があれば自動探索
            import zipfile
            import glob
            mf_candidates = (
                glob.glob(os.path.join(proj_dir, "*.gcode.3mf")) +
                glob.glob(os.path.join(proj_dir, "input", "*.gcode.3mf")) +
                glob.glob(os.path.join(proj_dir, "input", "*.3mf")) +
                glob.glob(os.path.join(self.base_dir, "*.gcode.3mf"))
            )
            if mf_candidates:
                # 最新の3MFから推定重量を取得 (ユーザー指定11.07g等)
                pass # ユーザー明示指定がない場合はデフォルト計算を優先
                
        if target_mass is not None:
            curr_mass = sum(p["mass_g"] for p in struct_parts)
            if curr_mass > 0:
                scale = target_mass / curr_mass
                for p in struct_parts:
                    p["mass_g"] = round(p["mass_g"] * scale, 3)
                    p["moi_g_cm2"] = {k: v * scale for k, v in p["moi_g_cm2"].items()}

    def _detect_flight_axis(self):
        """全体の寸法（全パーツのバウンディングボックス合成）からロケットの長軸（飛行軸）と全長を特定"""
        bodies = self.raw_data.get("bodies", [])
        min_coords = {"x": float('inf'), "y": float('inf'), "z": float('inf')}
        max_coords = {"x": float('-inf'), "y": float('-inf'), "z": float('-inf')}
        
        found = False
        for b in bodies:
            if not b.get("is_visible", True):
                continue
            b_min = b.get("bbox_min_mm", {})
            b_max = b.get("bbox_max_mm", {})
            for axis in ["x", "y", "z"]:
                if axis in b_min and axis in b_max:
                    found = True
                    if b_min[axis] < min_coords[axis]:
                        min_coords[axis] = b_min[axis]
                    if b_max[axis] > max_coords[axis]:
                        max_coords[axis] = b_max[axis]
                        
        if found:
            extents = {axis: max_coords[axis] - min_coords[axis] for axis in ["x", "y", "z"]}
            self.flight_axis = max(extents, key=extents.get)
            self.total_length_mm = extents[self.flight_axis]
            self.bbox_min_mm = min_coords
            self.bbox_max_mm = max_coords
        else:
            self.flight_axis = "y"
            self.total_length_mm = 250.0

    def _process_bodies(self):
        bodies = self.raw_data.get("bodies", [])
        
        for b in bodies:
            name = b.get("name", "")
            lower_name = name.lower()
            part_type = b.get("part_type", "structure")
            is_recovery = (part_type in ["streamer", "parachute"] or 
                           "ストリーマ" in name or "streamer" in lower_name or 
                           "chute" in lower_name or "parachute" in lower_name)
            is_motor = (part_type == "motor" or "motor" in lower_name or "engine" in lower_name)
            
            # 通常構造で非表示のものはスキップするが、モーターや回収装置などの内部機能パーツは読み込む
            if not b.get("is_visible", True) and not (is_recovery or is_motor):
                continue
                
            area_cm2 = b.get("area_cm2", 0.0)
            vol_cm3 = b.get("volume_cm3", 0.0)
            cad_mass_g = b.get("mass_g", 0.0)
            com = b.get("center_of_mass_mm", {"x": 0.0, "y": 0.0, "z": 0.0})
            com_vec = np.array([com.get("x", 0.0), com.get("y", 0.0), com.get("z", 0.0)])
            moi = b.get("moments_of_inertia_g_cm2", {})
            
            # --- 分類と実効質量の算定 ---
            # A. モーター
            if part_type == "motor" or "motor" in lower_name or "engine" in lower_name:
                part_type = "motor"
                custom = b.get("custom_params", {})
                motor_id = custom.get("motor_id", None)
                if not motor_id:
                    m = re.search(r'([A-Oa-o]\d+(?:-\d+)?)', name)
                    motor_id = m.group(1).upper() if m else "1/2A6-2"
                
                # 特殊ケース: 1/2A6 の正規化
                if "1/2A" in name:
                    motor_id = "1/2A6-2"
                    
                motor_data = get_motor(motor_id)
                self.motor_data = motor_data
                
                # モーター初期全重量で上書き
                real_mass_g = motor_data.total_mass_g
                scale = real_mass_g / max(0.001, cad_mass_g)
                real_moi = {k: v * scale for k, v in moi.items()}
                
                part_obj = {
                    "name": name,
                    "type": "motor",
                    "motor_id": motor_id,
                    "mass_g": real_mass_g,
                    "com_mm": com_vec,
                    "moi_g_cm2": real_moi,
                    "motor_data": motor_data
                }
                self.motor_part = part_obj
                self.parts.append(part_obj)

            # B. 回収装置 (ストリーマ / パラシュート)
            elif part_type in ["streamer", "parachute"] or "ストリーマ" in name or "streamer" in lower_name or "chute" in lower_name or "parachute" in lower_name:
                is_streamer = "ストリーマ" in name or "streamer" in lower_name
                dev_type = "streamer" if is_streamer else "parachute"
                
                # フィルム製ストリーマの典型質量: 約 1.5g
                real_mass_g = 1.5 if is_streamer else 8.0
                scale = real_mass_g / max(0.001, cad_mass_g)
                real_moi = {k: v * scale for k, v in moi.items()}
                
                part_obj = {
                    "name": name,
                    "type": dev_type,
                    "mass_g": real_mass_g,
                    "com_mm": com_vec,
                    "moi_g_cm2": real_moi,
                    "horizontal_descent": True if is_streamer else False
                }
                self.recovery_part = part_obj
                self.parts.append(part_obj)

            # C. バラスト / ペイロード
            elif part_type == "ballast" or b.get("mass_g_override") is not None:
                real_mass_g = float(b.get("mass_g_override", 10.0))
                scale = real_mass_g / max(0.001, cad_mass_g)
                real_moi = {k: v * scale for k, v in moi.items()}
                
                part_obj = {
                    "name": name,
                    "type": "ballast",
                    "mass_g": real_mass_g,
                    "com_mm": com_vec,
                    "moi_g_cm2": real_moi
                }
                self.parts.append(part_obj)

            # D. 機体構造 (PLA 1層 + インフィル2%)
            else:
                density = MATERIAL_DENSITIES.get(self.default_material, 1.24)
                # 表面積から外殻体積 (シェル厚 t [cm])
                shell_thickness_cm = self.shell_thickness_mm / 10.0
                shell_vol_cm3 = area_cm2 * shell_thickness_cm
                inner_vol_cm3 = max(0.0, vol_cm3 - shell_vol_cm3)
                
                eff_vol_cm3 = shell_vol_cm3 + (inner_vol_cm3 * self.infill_ratio)
                real_mass_g = round(eff_vol_cm3 * density, 3)
                
                scale = real_mass_g / max(0.001, cad_mass_g)
                real_moi = {k: v * scale for k, v in moi.items()}
                
                part_obj = {
                    "name": name,
                    "type": "structure",
                    "material": self.default_material,
                    "mass_g": real_mass_g,
                    "com_mm": com_vec,
                    "moi_g_cm2": real_moi,
                    "area_cm2": area_cm2,
                    "volume_cm3": vol_cm3
                }
                self.parts.append(part_obj)

    def _calculate_composite_properties(self):
        """平行軸の定理による打ち上げ時（点火時）の総合重心・慣性テンソルの合成"""
        total_mass = sum(p["mass_g"] for p in self.parts)
        if total_mass <= 0:
            total_mass = 1.0
            
        # 総合重心 (CG)
        cg = np.zeros(3)
        for p in self.parts:
            cg += p["mass_g"] * p["com_mm"]
        self.cg_mm = cg / total_mass
        
        # モーター抜きの機体乾燥質量 (Airframe + Payload + Streamer)
        self.airframe_mass_g = sum(p["mass_g"] for p in self.parts if p.get("type") != "motor")
        self.dry_mass_g = self.airframe_mass_g # モーター無しの機体乾燥質量
        
        # 推進剤質量
        prop_mass = self.motor_part["motor_data"].propellant_mass_g if self.motor_part else 0.0
        self.propellant_mass_g = prop_mass
        
        # 点火時総質量 (機体 + モーター全質量)
        self.launch_mass_g = total_mass
        
        # 燃焼終了時総質量 (機体 + モーター空ケース質量)
        self.burnout_mass_g = total_mass - prop_mass
        
        # 慣性モーメントの合成 (g*cm2)
        # 距離は mm なので cm に変換 ( / 10.0 )
        Ixx, Iyy, Izz = 0.0, 0.0, 0.0
        for p in self.parts:
            d_cm = (p["com_mm"] - self.cg_mm) / 10.0
            dx, dy, dz = d_cm[0], d_cm[1], d_cm[2]
            m = p["mass_g"]
            
            p_moi = p["moi_g_cm2"]
            Ixx += p_moi.get("Ixx", 0.0) + m * (dy**2 + dz**2)
            Iyy += p_moi.get("Iyy", 0.0) + m * (dx**2 + dz**2)
            Izz += p_moi.get("Izz", 0.0) + m * (dx**2 + dy**2)
            
        self.moi_g_cm2 = {"Ixx": Ixx, "Iyy": Iyy, "Izz": Izz}
