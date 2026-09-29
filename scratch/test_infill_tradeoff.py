import sys
import os
import math
import numpy as np

sys.path.insert(0, os.path.abspath("."))
from sim_engine.optimizer import RocketSpec, FinOptimizer
from scratch.test_correct_physics import evaluate_physically_correct_fins

def check_infill_tradeoff():
    print("=" * 80)
    print("INVESTIGATING NOSE INFILL / BALLAST TRADEOFF")
    print("=" * 80)
    print("Question: Does adding slight infill/ballast to the nose reduce required fin size enough to improve hang time?")

    # Base specs for L=250mm, D=24mm, Nose=120mm
    # Let's test various nose infill ratios: 0.0%, 1.0%, 2.0%, 3.0%, 5.0%, 8.0%, 10.0%
    infill_levels = [0.0, 0.01, 0.02, 0.03, 0.05, 0.08, 0.10]
    
    streamer_area = 250.0 # 50x500mm
    streamer_mass = 1.2
    streamer_cd = 0.25

    print("\n--- Testing Target Margin >= 0.90 cal (4-fin + shape symmetric) ---")
    for inf in infill_levels:
        spec = RocketSpec(
            total_length_mm=250.0,
            body_diameter_mm=24.0,
            nose_length_mm=120.0,
            tail_length_mm=0.0,
            wall_thickness_mm=0.4,
            infill_ratio=inf,
            material="PLA",
            material_density=1.24,
            motor_type="1/2A6-2",
            recovery_mass_g=streamer_mass,
            recovery_area_cm2=streamer_area,
            recovery_cd=streamer_cd,
            descent_horizontal=True
        )
        opt = FinOptimizer(spec)
        best = None
        for span in range(40, 80, 1):
            for cr in range(25, 55, 1):
                if span > 1.8 * cr or span < 0.35 * cr:
                    continue
                r = evaluate_physically_correct_fins(opt, float(span), float(cr), 0.0, 0.0, 1.0, is_4fin=True)
                if r["margin_pitch"] >= 0.90 and r["margin_yaw"] >= 0.90:
                    if best is None or r["total_time_s"] > best["total_time_s"]:
                        best = r
        if best:
            print(f"Infill: {inf*100:4.1f}% | BodyDry: {opt.m_airframe_g:.2f}g, BaseCG: {opt.z_base_cg:.1f}mm | Best Fin: {best['span']}x{best['cr']}mm (FinMass={best['fin_mass_g']:.2f}g) | TotalMass: {best['total_mass_g']:.1f}g | Apogee: {best['apogee_m']:.1f}m | Time: {best['total_time_s']:.2f}s")

    print("\n--- Testing Target Margin >= 1.20 cal (L=250mm, Can infill unlock 1.2 cal?) ---")
    for inf in [0.0, 0.02, 0.05, 0.08, 0.10, 0.15, 0.20]:
        spec = RocketSpec(
            total_length_mm=250.0,
            body_diameter_mm=24.0,
            nose_length_mm=120.0,
            tail_length_mm=0.0,
            wall_thickness_mm=0.4,
            infill_ratio=inf,
            material="PLA",
            material_density=1.24,
            motor_type="1/2A6-2",
            recovery_mass_g=streamer_mass,
            recovery_area_cm2=streamer_area,
            recovery_cd=streamer_cd,
            descent_horizontal=True
        )
        opt = FinOptimizer(spec)
        best = None
        for span in range(40, 85, 1):
            for cr in range(25, 60, 1):
                if span > 1.8 * cr or span < 0.35 * cr:
                    continue
                r = evaluate_physically_correct_fins(opt, float(span), float(cr), 0.0, 0.0, 1.0, is_4fin=True)
                if r["margin_pitch"] >= 1.20 and r["margin_yaw"] >= 1.20:
                    if best is None or r["total_time_s"] > best["total_time_s"]:
                        best = r
        if best:
            print(f"Infill: {inf*100:4.1f}% | BodyDry: {opt.m_airframe_g:.2f}g, BaseCG: {opt.z_base_cg:.1f}mm | Best Fin: {best['span']}x{best['cr']}mm (FinMass={best['fin_mass_g']:.2f}g) | TotalMass: {best['total_mass_g']:.1f}g | Apogee: {best['apogee_m']:.1f}m | Time: {best['total_time_s']:.2f}s")
        else:
            print(f"Infill: {inf*100:4.1f}% | BodyDry: {opt.m_airframe_g:.2f}g, BaseCG: {opt.z_base_cg:.1f}mm | No solution for Margin >= 1.20 cal")

if __name__ == "__main__":
    check_infill_tradeoff()
