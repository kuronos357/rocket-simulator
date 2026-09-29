"""
Fin Geometry Optimizer for Rocket Simulation Engine
Inversely calculates optimal fin dimensions (span, chord length, taper ratio)
to achieve target static stability margin (e.g. +1.2 cal).
Accounts for fin mass feedback on CG, boat tail, nose profile, and avionics ballast.
"""

import math
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple, List, Union
import numpy as np

from sim_engine.motor_db import BUILTIN_MOTORS, get_motor


@dataclass
class RocketSpec:
    total_length_mm: float
    body_diameter_mm: float
    nose_length_mm: float
    nose_shape_n: float = 0.75           # 1.0=Cone, 0.75=Ogive-like, 0.5=Parabola
    tail_length_mm: float = 0.0          # ボートテール長 (0ならストレート胴体)
    wall_thickness_mm: float = 0.4       # 3Dプリント外壁厚 (0.4mm, 0.8mm等)
    infill_ratio: float = 0.02           # インフィル率
    material: str = "PLA"
    material_density: float = 1.24       # g/cm3 (PLA: 1.24, PETG: 1.27, ABS: 1.04)
    dry_mass_override_g: Optional[float] = None # スライサー実測乾燥質量があれば直接指定
    
    # 内部パーツ
    motor_type: str = "1/2A6-2"
    ballast_mass_g: float = 0.0          # アビオニクス＋追加重り
    ballast_z_mm: Optional[float] = None # テール後端からの距離 (未指定ならノーズ内)
    recovery_mass_g: float = 0.5         # リカバリー質量 (ストリーマ 25x250mm + 糸)
    recovery_z_mm: Optional[float] = None# リカバリー位置 (未指定なら胴体中央)
    recovery_area_cm2: float = 62.5      # ストリーマー展開面積 (JAR規則最小 25mm x 250mm = 62.5cm2)
    recovery_cd: float = 0.25            # 抗力係数 (ストリーマー:0.2~0.3)
    descent_horizontal: bool = True      # 降下時に機体が横倒しになるか (空気抵抗が増す)


# Standard motor dimensions (outer diameter, length mm)
MOTOR_DIMENSIONS = {
    "1/4A": {"diameter_mm": 13.0, "length_mm": 45.0},
    "1/2A3": {"diameter_mm": 13.0, "length_mm": 45.0},
    "A3": {"diameter_mm": 13.0, "length_mm": 45.0},
    "A10": {"diameter_mm": 13.0, "length_mm": 45.0},
    "1/2A6": {"diameter_mm": 18.0, "length_mm": 70.0},
    "1/2A6-2": {"diameter_mm": 18.0, "length_mm": 70.0},
    "A8": {"diameter_mm": 18.0, "length_mm": 70.0},
    "A8-3": {"diameter_mm": 18.0, "length_mm": 70.0},
    "B6": {"diameter_mm": 18.0, "length_mm": 70.0},
    "B6-4": {"diameter_mm": 18.0, "length_mm": 70.0},
    "C6": {"diameter_mm": 18.0, "length_mm": 70.0},
    "C6-5": {"diameter_mm": 18.0, "length_mm": 70.0},
    "D12": {"diameter_mm": 24.0, "length_mm": 70.0},
    "E9": {"diameter_mm": 24.0, "length_mm": 95.0},
}


class FinOptimizer:
    def __init__(self, spec: RocketSpec):
        self.spec = spec
        self._init_rocket_components()

    def _init_rocket_components(self):
        """Calculate base airframe mass, CG, and nose/tail aerodynamics without fins."""
        s = self.spec
        
        # 1. モーター情報の取得
        motor_obj = get_motor(s.motor_type)
        self.motor_id = motor_obj.motor_id if motor_obj else s.motor_type
        self.motor_mass_g = motor_obj.total_mass_g if motor_obj else 15.0
        self.motor_burnout_mass_g = motor_obj.burnout_mass_g if motor_obj else 13.4
        
        # モーター寸法
        clean_id = s.motor_type.upper()
        dim_info = None
        for k, v in MOTOR_DIMENSIONS.items():
            if clean_id.startswith(k.upper()):
                dim_info = v
                break
        if not dim_info:
            dim_info = {"diameter_mm": 18.0, "length_mm": 70.0}
            
        self.motor_diameter_mm = dim_info["diameter_mm"]
        self.motor_length_mm = dim_info["length_mm"]
        
        # テール直径 (モーター外径 + 2 * 外壁厚)
        self.tail_diameter_mm = self.motor_diameter_mm + 2.0 * s.wall_thickness_mm
        if s.tail_length_mm <= 0.0:
            self.tail_diameter_mm = s.body_diameter_mm
            
        self.cyl_length_mm = max(10.0, s.total_length_mm - s.nose_length_mm - s.tail_length_mm)
        
        # 2. 胴体外殻の質量と重心 (3Dプリント実効構造)
        r_body = s.body_diameter_mm / 2.0
        r_tail = self.tail_diameter_mm / 2.0
        t_wall = s.wall_thickness_mm
        rho = s.material_density
        n = s.nose_shape_n
        
        # ジョイント・ショルダー・内部構造の重なりを考慮した実効面積係数 (約1.65倍)
        area_mult = 1.65
        
        # ノーズ計算: Power Series y = R * (x/L)^n
        # 表面積とシェルの重心を数値積分で概算
        slices = 50
        dx = s.nose_length_mm / slices
        area_nose_mm2 = 0.0
        moment_nose_shell = 0.0
        for i in range(slices):
            x = (i + 0.5) * dx
            y = r_body * (x / s.nose_length_mm)**n
            # 傾き dy/dx = R/L * n * (x/L)^(n-1)
            dydx = (r_body / s.nose_length_mm) * n * ((x / s.nose_length_mm)**(n - 1)) if x > 0 else 0
            ds = math.sqrt(1.0 + dydx**2) * dx
            dA = 2.0 * math.pi * y * ds
            area_nose_mm2 += dA
            moment_nose_shell += dA * x # 先端からの距離
            
        cg_nose_shell_from_tip = moment_nose_shell / area_nose_mm2 if area_nose_mm2 > 0 else 0
        
        # 外壁の質量 (Shell)
        area_nose_cm2 = area_nose_mm2 * 0.01 * area_mult
        m_nose_shell_g = area_nose_cm2 * (t_wall * 0.1) * rho
        
        # ノーズ内部のインフィルの質量 (Solid volume)
        # べき乗則の体積 = pi * R^2 * L * (1 / (2n + 1))
        vol_nose_cm3 = (math.pi * r_body**2 * s.nose_length_mm * (1.0 / (2.0 * n + 1.0))) * 0.001
        m_nose_infill_g = vol_nose_cm3 * s.infill_ratio * rho
        # ボリューム重心 = 先端から L * (2n+1)/(2n+2)
        cg_nose_infill_from_tip = s.nose_length_mm * (2.0 * n + 1.0) / (2.0 * n + 2.0)
        
        m_nose_g = m_nose_shell_g + m_nose_infill_g
        z_nose_cg_from_tip = (m_nose_shell_g * cg_nose_shell_from_tip + m_nose_infill_g * cg_nose_infill_from_tip) / m_nose_g if m_nose_g > 0 else 0
        z_nose_cg = s.total_length_mm - z_nose_cg_from_tip # テールからの位置
        
        # 胴体の質量 (パイプ)
        area_cyl_cm2 = (math.pi * s.body_diameter_mm * self.cyl_length_mm) * 0.01 * area_mult
        m_cyl_g = area_cyl_cm2 * (t_wall * 0.1) * rho
        z_cyl_cg = s.tail_length_mm + self.cyl_length_mm / 2.0
        
        # ボートテールの質量
        if s.tail_length_mm > 0.0:
            slant_h = math.sqrt(s.tail_length_mm**2 + (r_body - r_tail)**2)
            area_tail_cm2 = (math.pi * (r_body + r_tail) * slant_h) * 0.01 * area_mult
            m_tail_g = area_tail_cm2 * (t_wall * 0.1) * rho
            z_tail_cg = s.tail_length_mm * (s.body_diameter_mm + 2.0 * self.tail_diameter_mm) / (3.0 * (s.body_diameter_mm + self.tail_diameter_mm))
        else:
            area_tail_cm2 = 0.0
            m_tail_g = 0.0
            z_tail_cg = 0.0
            
        calc_airframe_g = m_nose_g + m_cyl_g + m_tail_g
        z_airframe_cg = (m_nose_g * z_nose_cg + m_cyl_g * z_cyl_cg + m_tail_g * z_tail_cg) / calc_airframe_g if calc_airframe_g > 0 else 50.0
        
        # 3D真の濡れ面積 (ノーズ積分曲面 + 円筒 + ボートテール円錐台) cm^2
        raw_tail_area_cm2 = (area_tail_cm2 / area_mult) if s.tail_length_mm > 0 else 0.0
        self.wet_area_body_cm2 = (area_nose_mm2 * 0.01) + ((math.pi * s.body_diameter_mm * self.cyl_length_mm) * 0.01) + raw_tail_area_cm2
        
        # ユーザーによる乾燥重量オーバーライドがあれば優先
        self.m_airframe_g = s.dry_mass_override_g if s.dry_mass_override_g is not None else calc_airframe_g
        self.z_airframe_cg = z_airframe_cg
        
        # 3. 内部パーツ
        z_motor_cg = self.motor_length_mm / 2.0
        z_ballast = s.ballast_z_mm if s.ballast_z_mm is not None else (s.total_length_mm - 0.4 * s.nose_length_mm)
        z_recovery = s.recovery_z_mm if s.recovery_z_mm is not None else (s.tail_length_mm + self.cyl_length_mm / 2.0)
        
        self.m_base_launch = self.m_airframe_g + self.motor_mass_g + s.ballast_mass_g + s.recovery_mass_g
        self.mom_base_launch = (self.m_airframe_g * self.z_airframe_cg + 
                                self.motor_mass_g * z_motor_cg + 
                                s.ballast_mass_g * z_ballast + 
                                s.recovery_mass_g * z_recovery)
        self.z_base_cg = self.mom_base_launch / self.m_base_launch
        
        # 4. ベース空力特性 (ノーズ & ボートテール)
        self.cna_nose = 2.0
        # Barrowman CP for power series nose: X_N = L * 2n / (2n + 1)  (distance from tip)
        cp_nose_from_tip = s.nose_length_mm * (2.0 * n) / (2.0 * n + 1.0)
        self.cp_nose = s.total_length_mm - cp_nose_from_tip
        
        if s.tail_length_mm > 0.0 and s.body_diameter_mm > self.tail_diameter_mm:
            self.cna_tail = -2.0 * (s.body_diameter_mm**2 - self.tail_diameter_mm**2) / (s.body_diameter_mm**2)
            self.cp_tail = s.tail_length_mm * (s.body_diameter_mm + 2.0 * self.tail_diameter_mm) / (3.0 * (s.body_diameter_mm + self.tail_diameter_mm))
        else:
            self.cna_tail = 0.0
            self.cp_tail = 0.0
            
        self.cna_body_base = self.cna_nose + self.cna_tail
        self.cp_body_base = (self.cna_nose * self.cp_nose + self.cna_tail * self.cp_tail) / self.cna_body_base if self.cna_body_base != 0 else self.cp_nose

    def evaluate_fins(self, 
                      span_mm: float, 
                      cr_mm: float, 
                      arrangement: str = "auto",
                      shape_type: str = "trapezoid", 
                      taper_ratio: float = 0.0,
                      fin_thickness_mm: float = 0.4,
                      root_offset_mm: float = 0.0,
                      theta_deg: Optional[float] = None,
                      v_scale: Optional[float] = None,
                      is_4fin: Optional[bool] = None,
                      v_span_mm: Optional[float] = None,
                      v_cr_mm: Optional[float] = None) -> Dict[str, Any]:
        """
        Evaluate full aerodynamics, mass feedback, CG, CP, pitch/yaw margins,
        and flight performance for given fin dimensions, dihedral angle theta, and vertical scale.
        """
        s = self.spec
        D = s.body_diameter_mm
        R = D / 2.0
        rho = s.material_density
        
        # 1. フィン配置パラメータの解決
        if theta_deg is not None:
            th = float(theta_deg)
        elif arrangement == "airplane_3fin":
            th = 0.0
        elif arrangement in ["symmetric_3fin", "3"]:
            th = 30.0
        elif arrangement in ["symmetric_4fin", "4"]:
            th = 0.0
        else:
            th = 30.0
            
        if is_4fin is not None:
            b_4fin = bool(is_4fin)
        elif arrangement in ["symmetric_4fin", "4"]:
            b_4fin = True
        else:
            b_4fin = False
            
        if v_scale is not None:
            vs = float(v_scale)
        elif v_span_mm is not None and span_mm > 0:
            vs = float(v_span_mm / span_mm)
        elif arrangement == "airplane_3fin":
            vs = 0.85
        elif arrangement in ["symmetric_3fin", "3"]:
            vs = 1.0
        elif arrangement in ["symmetric_4fin", "4"]:
            vs = 1.0
        else:
            vs = 1.0
            
        theta_rad = math.radians(th)
        
        # 2. 水平/傾斜主翼 (2枚)
        if shape_type == "ellipse":
            ct_mm = 0.0
            area_1side_cm2 = (math.pi / 4.0 * cr_mm * span_mm) * 0.01
            z_fin_local_cg_h = 0.424 * cr_mm
            k_body_h = 1.0 + R / (R + span_mm)
            denom_h = 1.0 + math.sqrt(1.0 + (2.0 * span_mm / cr_mm)**2)
            cna_1pair_h = k_body_h * (4.0 * 2.0 * (span_mm / D)**2) / denom_h
            # 楕円翼の空力中心は前縁から 0.25*cr (後縁から 0.75*cr)
            cp_fin_h = root_offset_mm + 0.75 * cr_mm
        else: # trapezoid / delta
            ct_mm = taper_ratio * cr_mm
            area_1side_cm2 = (0.5 * (cr_mm + ct_mm) * span_mm) * 0.01
            denom_cg_h = 3.0 * (cr_mm + ct_mm) if (cr_mm + ct_mm) > 0 else 1.0
            # 後縁直角固定の台形コード方向図心 (後縁からの距離)
            z_fin_local_cg_h = (cr_mm**2 + cr_mm * ct_mm + ct_mm**2) / denom_cg_h
            
            sweep_h = cr_mm - ct_mm
            mid_sweep_h = sweep_h + (ct_mm - cr_mm) / 2.0
            Lf_h = math.sqrt(mid_sweep_h**2 + span_mm**2)
            k_body_h = 1.0 + R / (R + span_mm)
            denom_h = 1.0 + math.sqrt(1.0 + (2.0 * Lf_h / (cr_mm + ct_mm))**2) if (cr_mm + ct_mm) > 0 else 2.0
            cna_1pair_h = k_body_h * (4.0 * 2.0 * (span_mm / D)**2) / denom_h
            
            denom_ch = (cr_mm + ct_mm) if (cr_mm + ct_mm) > 0 else 1.0
            xf_h_from_le = ((cr_mm - ct_mm) / 3.0) * ((cr_mm + 2.0 * ct_mm) / denom_ch) + (1.0 / 6.0) * (cr_mm + ct_mm - (cr_mm * ct_mm) / denom_ch)
            cp_fin_h = (root_offset_mm + cr_mm) - xf_h_from_le
            
        z_fin_cg_h = root_offset_mm + z_fin_local_cg_h
        
        # 3. 垂直尾翼 (3枚翼なら上部1枚、4枚翼なら上下2枚)
        span_v = span_mm * vs
        cr_v = cr_mm * vs
        ct_v = ct_mm * vs
        num_v = 2.0 if b_4fin else 1.0
        num_total_fins = 2.0 + num_v
        
        if shape_type == "ellipse":
            area_1v_cm2 = (math.pi / 4.0 * cr_v * span_v) * 0.01
            z_fin_local_cg_v = 0.424 * cr_v
            k_body_v = 1.0 + R / (R + span_v)
            denom_v = 1.0 + math.sqrt(1.0 + (2.0 * span_v / cr_v)**2)
            cna_1v = k_body_v * (4.0 * 1.0 * (span_v / D)**2) / denom_v
            cp_fin_v = root_offset_mm + 0.75 * cr_v
        else:
            area_1v_cm2 = (0.5 * (cr_v + ct_v) * span_v) * 0.01
            denom_cg_v = 3.0 * (cr_v + ct_v) if (cr_v + ct_v) > 0 else 1.0
            z_fin_local_cg_v = (cr_v**2 + cr_v * ct_v + ct_v**2) / denom_cg_v if (cr_v + ct_v) > 0 else 0.0
            
            mid_sweep_v = (cr_v - ct_v) + (ct_v - cr_v) / 2.0
            Lf_v = math.sqrt(mid_sweep_v**2 + span_v**2)
            k_body_v = 1.0 + R / (R + span_v)
            denom_v = 1.0 + math.sqrt(1.0 + (2.0 * Lf_v / (cr_v + ct_v))**2) if (cr_v + ct_v) > 0 else 2.0
            cna_1v = k_body_v * (4.0 * 1.0 * (span_v / D)**2) / denom_v
            
            denom_cv = (cr_v + ct_v) if (cr_v + ct_v) > 0 else 1.0
            xf_v_from_le = ((cr_v - ct_v) / 3.0) * ((cr_v + 2.0 * ct_v) / denom_cv) + (1.0 / 6.0) * (cr_v + ct_v - (cr_v * ct_v) / denom_cv)
            cp_fin_v = (root_offset_mm + cr_v) - xf_v_from_le
            
        z_fin_cg_v = root_offset_mm + z_fin_local_cg_v
        cna_v_total = num_v * cna_1v
        
        # 4. フィン合計面積・質量・合成重心
        total_fin_area_cm2 = 2.0 * area_1side_cm2 + num_v * area_1v_cm2
        fin_mass_g = total_fin_area_cm2 * (fin_thickness_mm * 0.1) * rho
        if total_fin_area_cm2 > 0:
            z_fin_cg = (2.0 * area_1side_cm2 * z_fin_cg_h + num_v * area_1v_cm2 * z_fin_cg_v) / total_fin_area_cm2
        else:
            z_fin_cg = root_offset_mm
            
        # 5. ピッチ & ヨー空力特性 (Barrowman厳密理論に基づく任意角度合成)
        cos2_theta = math.cos(theta_rad)**2
        sin2_theta = math.sin(theta_rad)**2
        
        cna_pitch_fins = cos2_theta * cna_1pair_h
        cna_yaw_fins = sin2_theta * cna_1pair_h + cna_v_total
        
        cna_pitch = self.cna_body_base + cna_pitch_fins
        cp_pitch = (self.cna_body_base * self.cp_body_base + cna_pitch_fins * cp_fin_h) / cna_pitch if cna_pitch > 0 else cp_fin_h
        
        yaw_fins_moment = sin2_theta * cna_1pair_h * cp_fin_h + cna_v_total * cp_fin_v
        cna_yaw = self.cna_body_base + cna_yaw_fins
        cp_yaw = (self.cna_body_base * self.cp_body_base + yaw_fins_moment) / cna_yaw if cna_yaw > 0 else cp_fin_v
        
        # 3D実効空間安定性
        cna_eff = 0.5 * (cna_pitch + cna_yaw)
        cp_eff = (cna_pitch * cp_pitch + cna_yaw * cp_yaw) / (2.0 * cna_eff) if cna_eff > 0 else cp_pitch
        
        # 6. フィン質量フィードバック後の全備質量と重心 CG
        total_launch_mass_g = self.m_base_launch + fin_mass_g
        total_cg_mm = (self.mom_base_launch + fin_mass_g * z_fin_cg) / total_launch_mass_g
        
        # 7. 静安定マージン (両軸とも厳格にチェック)
        margin_pitch_cal = (total_cg_mm - cp_pitch) / D
        margin_yaw_cal = (total_cg_mm - cp_yaw) / D
        margin_eff_cal = min(margin_pitch_cal, margin_yaw_cal)
        margin_eff_mm = margin_eff_cal * D
        
        total_span_width_mm = D + 2.0 * span_mm * math.cos(theta_rad)
        
        # 8. 飛翔予測 (上昇時)
        S_ref = math.pi * (R * 1e-3)**2
        wet_area_m2 = (self.wet_area_body_cm2 + total_fin_area_cm2 * 2.0) * 1e-4
        cd_interference = 0.005 * num_total_fins
        Cd = 0.0045 * (wet_area_m2 / S_ref) + (0.05 if s.tail_length_mm > 0 else 0.10) + 0.08 + cd_interference
        
        motor_obj = get_motor(self.motor_id)
        if motor_obj:
            avg_thrust = motor_obj.total_impulse / motor_obj.burn_time if motor_obj.burn_time > 0 else 5.0
            burn_t = motor_obj.burn_time
            m_avg_kg = (total_launch_mass_g - motor_obj.propellant_mass_g * 0.5) * 1e-3
            v_bo = max(0.0, (avg_thrust / m_avg_kg - 9.8) * burn_t)
            h_bo = 0.5 * v_bo * burn_t
            
            burnout_mass_g = total_launch_mass_g - motor_obj.propellant_mass_g
            k_drag = 0.5 * 1.225 * Cd * S_ref / (burnout_mass_g * 1e-3)
            
            if k_drag > 0 and v_bo > 0:
                h_coast = (1.0 / (2.0 * k_drag)) * math.log(1.0 + k_drag * v_bo**2 / 9.8)
                t_coast = (1.0 / math.sqrt(9.8 * k_drag)) * math.atan(v_bo * math.sqrt(k_drag / 9.8))
            else:
                h_coast = 0.0
                t_coast = 0.0
                
            apogee_m = h_bo + h_coast
            max_vel_km_h = v_bo * 3.6
            
            # 9. 降下フェーズ (3D濡れ面積 + 翼面角度投影による横倒し降下モデル)
            streamer_cd_A = s.recovery_cd * (s.recovery_area_cm2 * 1e-4) # m^2
            
            if s.descent_horizontal:
                wet_body_m2 = self.wet_area_body_cm2 * 1e-4
                body_cd_A = (1.1 / math.pi) * wet_body_m2
                # 主翼は傾斜角thetaに応じた正対投影面積、垂直尾翼は横流端面寄与 (0.15)
                proj_fins_m2 = (2.0 * area_1side_cm2 * math.cos(theta_rad) + 0.15 * num_v * area_1v_cm2) * 1e-4
                fins_cd_A = 1.25 * proj_fins_m2
                total_cd_A = streamer_cd_A + body_cd_A + fins_cd_A
            else:
                total_cd_A = streamer_cd_A + (Cd * S_ref)
                
            if total_cd_A > 0:
                v_descent = math.sqrt((2.0 * (burnout_mass_g * 1e-3) * 9.8) / (1.225 * total_cd_A))
                t_descent = apogee_m / v_descent if v_descent > 0 else 0.0
            else:
                v_descent = 0.0
                t_descent = 0.0
                
            total_flight_time_s = burn_t + t_coast + t_descent
        else:
            apogee_m = 0.0
            max_vel_km_h = 0.0
            total_flight_time_s = 0.0
            v_descent = 0.0

        return {
            "span_mm": round(span_mm, 1),
            "root_chord_mm": round(cr_mm, 1),
            "tip_chord_mm": round(ct_mm, 1),
            "total_width_mm": round(total_span_width_mm, 1),
            "theta_deg": round(th, 1),
            "v_scale": round(vs, 2),
            "is_4fin": b_4fin,
            "v_span_mm": round(span_v, 1),
            "v_cr_mm": round(cr_v, 1),
            "v_ct_mm": round(ct_v, 1),
            "fin_area_1side_cm2": round(area_1side_cm2, 2),
            "fin_mass_g": round(fin_mass_g, 2),
            "total_mass_g": round(total_launch_mass_g, 1),
            "cg_mm": round(total_cg_mm, 1),
            "cp_mm": round(cp_eff, 1),
            "margin_cal": round(margin_eff_cal, 2),
            "margin_mm": round(margin_eff_mm, 1),
            "pitch_margin_cal": round(margin_pitch_cal, 2),
            "yaw_margin_cal": round(margin_yaw_cal, 2),
            "Cd": round(Cd, 3),
            "apogee_m": round(apogee_m, 1),
            "max_vel_km_h": round(max_vel_km_h, 1),
            "total_flight_time_s": round(total_flight_time_s, 2),
            "v_descent_m_s": round(v_descent, 2)
        }

    def optimize(self, 
                 target_margin_cal: float = 1.2,
                 arrangement: str = "auto",
                 shape_type: str = "trapezoid",
                 taper_ratio: Union[float, List[float]] = 0.0,
                 fin_thickness_mm: float = 0.4,
                 theta_deg: Optional[Union[float, List[float]]] = None,
                 v_scale: Optional[Union[float, List[float]]] = None) -> Optional[Dict[str, Any]]:
        """
        Find (span, cr, taper_ratio, theta_deg, v_scale) that achieves target_margin_cal
        with minimum total fin mass.
        """
        if isinstance(taper_ratio, (float, int)):
            taper_ratios = np.array([float(taper_ratio)], dtype=np.float64)
        else:
            taper_ratios = np.array(taper_ratio, dtype=np.float64)
            
        step = 1.0  # mm
        min_cr = max(20.0, self.spec.body_diameter_mm * 0.8)
        max_cr = min(self.cyl_length_mm, 100.0)
        min_span = 10.0
        max_span = min(80.0, self.spec.body_diameter_mm * 3.5)
        root_offset_mm = self.spec.tail_length_mm
        
        # 探索する角度 theta と垂直尾翼スケール v_scale の設定
        from sim_engine.numba_opt import _fast_generalized_search
        
        configs_to_try = [] # list of (thetas, v_scales, is_4fin)
        
        if theta_deg is not None and v_scale is not None:
            ths = np.array([float(theta_deg)] if isinstance(theta_deg, (int, float)) else theta_deg, dtype=np.float64)
            vss = np.array([float(v_scale)] if isinstance(v_scale, (int, float)) else v_scale, dtype=np.float64)
            is_4 = (arrangement in ["symmetric_4fin", "4"])
            configs_to_try.append((ths, vss, is_4))
        elif arrangement == "airplane_3fin":
            ths = np.array([0.0], dtype=np.float64)
            vss = np.array([0.5, 0.7, 0.85, 1.0, 1.2], dtype=np.float64)
            configs_to_try.append((ths, vss, False))
        elif arrangement in ["symmetric_3fin", "3"]:
            ths = np.array([30.0], dtype=np.float64)
            vss = np.array([1.0], dtype=np.float64)
            configs_to_try.append((ths, vss, False))
        elif arrangement in ["symmetric_4fin", "4"]:
            ths = np.array([0.0], dtype=np.float64)
            vss = np.array([1.0], dtype=np.float64)
            configs_to_try.append((ths, vss, True))
        else: # "auto" - 全自由度探索 (3枚翼の任意角度 + 4枚翼十字)
            ths_3 = np.array([0.0, 10.0, 15.0, 20.0, 30.0, 45.0], dtype=np.float64)
            vss_3 = np.array([0.5, 0.7, 0.85, 1.0, 1.2], dtype=np.float64)
            configs_to_try.append((ths_3, vss_3, False))
            
            ths_4 = np.array([0.0], dtype=np.float64)
            vss_4 = np.array([0.5, 0.7, 0.85, 1.0], dtype=np.float64)
            configs_to_try.append((ths_4, vss_4, True))
            
        global_best = None
        global_best_mass = 999999.0
        
        for (ths, vss, is_4) in configs_to_try:
            best_coarse = _fast_generalized_search(
                min_span, max_span, step,
                min_cr, max_cr,
                taper_ratios,
                ths,
                vss,
                is_4,
                target_margin_cal,
                self.spec.body_diameter_mm,
                root_offset_mm,
                fin_thickness_mm,
                self.spec.material_density,
                self.cna_body_base,
                self.cp_body_base,
                self.m_base_launch,
                self.mom_base_launch
            )
            
            if best_coarse[0] >= 0 and best_coarse[5] < global_best_mass:
                coarse_span, coarse_cr, best_tr, best_th, best_vs, mass = best_coarse
                
                # 0.1mm 刻みの精密探索
                fine_step = 0.1
                s_min = max(min_span, coarse_span - step)
                s_max = min(max_span, coarse_span + step)
                c_min = max(min_cr, coarse_cr - step)
                c_max = min(max_cr, coarse_cr + step)
                
                best_fine = _fast_generalized_search(
                    s_min, s_max, fine_step,
                    c_min, c_max,
                    np.array([best_tr], dtype=np.float64),
                    np.array([best_th], dtype=np.float64),
                    np.array([best_vs], dtype=np.float64),
                    is_4,
                    target_margin_cal,
                    self.spec.body_diameter_mm,
                    root_offset_mm,
                    fin_thickness_mm,
                    self.spec.material_density,
                    self.cna_body_base,
                    self.cp_body_base,
                    self.m_base_launch,
                    self.mom_base_launch
                )
                
                if best_fine[0] >= 0:
                    final_span, final_cr, final_tr, final_th, final_vs, final_mass = best_fine
                else:
                    final_span, final_cr, final_tr, final_th, final_vs, final_mass = best_coarse
                    
                global_best_mass = final_mass
                global_best = (final_span, final_cr, final_tr, final_th, final_vs, is_4)
                
        if global_best is None:
            return None
            
        f_span, f_cr, f_tr, f_th, f_vs, f_is4 = global_best
        
        # 最終結果の評価
        arr_str = "symmetric_4fin" if f_is4 else ("airplane_3fin" if f_th == 0.0 else f"dihedral_{f_th:.0f}deg")
        res = self.evaluate_fins(
            span_mm=f_span,
            cr_mm=f_cr,
            arrangement=arr_str,
            shape_type=shape_type,
            taper_ratio=f_tr,
            fin_thickness_mm=fin_thickness_mm,
            root_offset_mm=root_offset_mm,
            theta_deg=f_th,
            v_scale=f_vs,
            is_4fin=f_is4
        )
        
        # 厳格な安定性マージンチェック: 目標マージン未満は完全に切る (除外)
        if res is not None and res["margin_cal"] < target_margin_cal:
            return None
            
        return res

