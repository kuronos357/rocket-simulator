import itertools
import time
from typing import Dict, Any, List, Optional
from sim_engine.optimizer import RocketSpec, FinOptimizer

class FullRocketOptimizer:
    """
    Multidisciplinary Design Optimization (MDO) for Model Rockets.
    Optimizes both airframe parameters (total length, nose length) and fin parameters
    simultaneously to maximize Apogee, subject to a minimum stability margin.
    """
    def __init__(self, base_spec: RocketSpec):
        self.base_spec = base_spec

    def _evaluate_single(self, args_tuple):
        L, N, T, Sn, target_margin_cal, arrangement, shape_type, taper_ratios, fin_thickness_mm = args_tuple
        
        # モーターとペイロードが入る最小長さの確認
        # JAR公式競技規則: 全長250mm以上、かつ全長の50%以上が最小直径(基準直径)を下回ってはならない
        if L < 250.0 or L < self._get_minimum_length() or (L - N - T) < 0.50 * L:
            return None
            
        current_spec = RocketSpec(
            total_length_mm=L,
            body_diameter_mm=self.base_spec.body_diameter_mm,
            nose_length_mm=N,
            nose_shape_n=Sn,
            tail_length_mm=T,
            wall_thickness_mm=self.base_spec.wall_thickness_mm,
            infill_ratio=self.base_spec.infill_ratio,
            material=self.base_spec.material,
            material_density=self.base_spec.material_density,
            dry_mass_override_g=None,
            motor_type=self.base_spec.motor_type,
            ballast_mass_g=self.base_spec.ballast_mass_g,
            ballast_z_mm=self.base_spec.ballast_z_mm,
            recovery_mass_g=self.base_spec.recovery_mass_g,
            recovery_z_mm=self.base_spec.recovery_z_mm,
            recovery_area_cm2=self.base_spec.recovery_area_cm2,
            recovery_cd=self.base_spec.recovery_cd,
            descent_horizontal=self.base_spec.descent_horizontal
        )
        
        fin_opt = FinOptimizer(current_spec)
        res = fin_opt.optimize(
            target_margin_cal=target_margin_cal,
            arrangement=arrangement,
            shape_type=shape_type,
            taper_ratio=taper_ratios,
            fin_thickness_mm=fin_thickness_mm
        )
        
        if res is not None:
            res["arrangement"] = arrangement
            return {
                "apogee": res["apogee_m"],
                "body": {
                    "total_length_mm": L,
                    "nose_length_mm": N,
                    "nose_shape_n": Sn,
                    "tail_length_mm": T,
                    "airframe_mass_g": fin_opt.m_airframe_g
                },
                "fins": res
            }
        return None

    def optimize_design(self,
                        length_range: List[float],
                        nose_range: List[float],
                        tail_range: List[float],
                        shape_n_range: List[float] = [0.75],
                        target_margin_cal: float = 1.0,
                        arrangement: str = "symmetric_3fin",
                        shape_type: str = "trapezoid",
                        taper_ratios: List[float] = [0.0, 0.5, 1.0],
                        fin_thickness_mm: float = 0.4,
                        optimize_for: str = "apogee") -> List[Dict[str, Any]]:
        import multiprocessing
        
        tasks = []
        for L in length_range:
            for N in nose_range:
                for T in tail_range:
                    for Sn in shape_n_range:
                        tasks.append((L, N, T, Sn, target_margin_cal, arrangement, shape_type, taper_ratios, fin_thickness_mm))
                    
        total_evals = len(tasks)
        print(f"Starting MDO: {total_evals} body configurations... (Objective: {optimize_for})")
        
        t0 = time.perf_counter()
        
        # CPUコア数にあわせて並列処理
        with multiprocessing.Pool() as pool:
            raw_results = pool.map(self._evaluate_single, tasks)
            
        valid_results = [r for r in raw_results if r is not None]
                
        t1 = time.perf_counter()
        print(f"MDO finished in {t1-t0:.2f} seconds. Evaluated {total_evals} combinations.")
        return valid_results

    def _get_minimum_length(self) -> float:
        """Calculate the absolute minimum body length required to fit components."""
        motor_len = 70.0 # fallback
        from sim_engine.optimizer import MOTOR_DIMENSIONS
        for k, v in MOTOR_DIMENSIONS.items():
            if self.base_spec.motor_type.upper().startswith(k.upper()):
                motor_len = v["length_mm"]
                break
        # 最小でも モーター長 + パラシュート収納部(50mm) は必要とする
        return motor_len + 50.0
