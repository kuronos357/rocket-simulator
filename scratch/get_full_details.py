import sys, os
sys.path.insert(0, os.path.abspath('.'))
from sim_engine.optimizer import RocketSpec, FinOptimizer
from scratch.test_correct_physics import evaluate_physically_correct_fins

def get_full_details():
    spec_0 = RocketSpec(total_length_mm=250.0, body_diameter_mm=24.0, nose_length_mm=120.0,
                        tail_length_mm=0.0, wall_thickness_mm=0.4, infill_ratio=0.02,
                        material='PLA', material_density=1.24, motor_type='1/2A6-2',
                        ballast_mass_g=0.0, ballast_z_mm=245.0, recovery_mass_g=1.2,
                        recovery_area_cm2=250.0, recovery_cd=0.25, descent_horizontal=True)
    opt_0 = FinOptimizer(spec_0)

    # 1. 4-fin asym ~0.80 cal, 30.43s (or 30.37s)
    # Let's inspect span=55, cr=31, vs=0.9 and span=59, cr=33, vs=0.85
    r_4asym_1 = evaluate_physically_correct_fins(opt_0, 55.0, 31.0, 0.0, 0.0, 0.9, is_4fin=True)
    r_4asym_2 = evaluate_physically_correct_fins(opt_0, 59.0, 33.0, 0.0, 0.0, 0.85, is_4fin=True)

    # 2. 3-fin asym ~0.86 cal, 30.26s
    r_3asym = evaluate_physically_correct_fins(opt_0, 76.0, 44.0, 0.0, 35.0, 0.70, is_4fin=False)

    # 3. High stability 1.22 cal, 28.44s
    spec_122 = RocketSpec(total_length_mm=250.0, body_diameter_mm=24.0, nose_length_mm=120.0,
                          tail_length_mm=0.0, wall_thickness_mm=0.4, infill_ratio=0.02,
                          material='PLA', material_density=1.24, motor_type='1/2A6-2',
                          ballast_mass_g=1.0, ballast_z_mm=245.0, recovery_mass_g=1.2,
                          recovery_area_cm2=250.0, recovery_cd=0.25, descent_horizontal=True)
    opt_122 = FinOptimizer(spec_122)
    r_122 = evaluate_physically_correct_fins(opt_122, 59.0, 33.0, 0.0, 0.0, 1.0, is_4fin=True)

    models = {
        "4fin_asym_55x31": r_4asym_1,
        "4fin_asym_59x33": r_4asym_2,
        "3fin_asym_76x44": r_3asym,
        "122_high_stability": r_122
    }

    import json
    with open("scratch/final_three_models_detailed.json", "w", encoding="utf-8") as f:
        json.dump(models, f, indent=2, ensure_ascii=False)
    print("Exported complete model details!")

if __name__ == "__main__":
    get_full_details()
