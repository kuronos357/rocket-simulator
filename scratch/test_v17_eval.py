import sys, os
sys.path.insert(0, r"d:\1_Stuff\0_programming\0_Project\ロケットシミュレーター")

from sim_engine.optimizer import RocketSpec, FinOptimizer

# つくば＿ロケットスペック
spec = RocketSpec(
    total_length_mm=190.0,
    body_diameter_mm=22.0,
    nose_length_mm=60.0,
    tail_length_mm=0.0,
    wall_thickness_mm=0.4,
    material="PLA",
    motor_type="1/2A6-2",
    dry_mass_override_g=11.5,
    ballast_mass_g=0.0
)

opt = FinOptimizer(spec)

# 実験: 水平主翼を pitch = +1.0 cal にしつつ、垂直尾翼を yaw = +0.5 ~ +1.0 cal にするにはどのサイズが必要か？
print("Base airframe mass:", opt.m_airframe_g, "Base CG:", opt.z_base_cg)
print("Base CP:", opt.cp_body_base, "Base CNa:", opt.cna_body_base)

# v17 の寸法で評価してみる (主翼: span 40, cr 58, 尾翼: span 27, cr 50)
res = opt.evaluate_fins(span_mm=40.0, cr_mm=58.0, arrangement="airplane_3fin", taper_ratio=0.0)
print("v17-like evaluation:")
for k, v in res.items():
    print(f"  {k}: {v}")
