import sys, os, math
sys.path.insert(0, r"d:\1_Stuff\0_programming\0_Project\ロケットシミュレーター")
from sim_engine.optimizer import RocketSpec, FinOptimizer

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
D = spec.body_diameter_mm
R = D / 2.0

# 尾翼で yaw_margin >= +0.5 cal を満たすための探索
# 尾翼 1 枚 (N=1)
# cna_v = (1 + R/(R+span_v)) * (4 * 1 * (span_v/D)^2) / denom_v
# 尾翼の面積中心 cp_v = cr_v / 3 (三角翼)
print("Testing fin optimization with dual-axis decoupling...")

# 垂直尾翼の探索テスト
target_yaw = 0.5
best_v = None
min_v_area = 9999
for ratio in [0.7, 0.8, 0.9, 1.0, 1.2]:
    low_s, high_s = 15.0, 60.0
    found_s = None
    for _ in range(25):
        s = (low_s + high_s) / 2.0
        cr = s / ratio
        Lf = math.sqrt((cr/2.0)**2 + s**2)
        denom = 1.0 + math.sqrt(1.0 + (2.0 * Lf / cr)**2)
        k_b = 1.0 + R / (R + s)
        cna_v = k_b * (4.0 * 1.0 * (s / D)**2) / denom
        cp_v = cr / 3.0
        cna_yaw = opt.cna_body_base + cna_v
        cp_yaw = (opt.cna_body_base * opt.cp_body_base + cna_v * cp_v) / cna_yaw
        yaw_margin = (opt.z_base_cg - cp_yaw) / D
        if yaw_margin < target_yaw:
            low_s = s
        else:
            found_s = s
            high_s = s
    if found_s:
        cr = found_s / ratio
        area = 0.5 * found_s * cr
        if area < min_v_area:
            min_v_area = area
            best_v = (found_s, cr, area)

print(f"Optimal Vertical Fin for Yaw +{target_yaw:.1f} cal: span={best_v[0]:.1f}mm, cr={best_v[1]:.1f}mm, area={best_v[2]:.1f}mm2")
