import sys
import os
sys.path.insert(0, os.path.abspath("."))
from sim_engine.optimizer import RocketSpec, FinOptimizer

for b in [0.0, 1.0, 2.0, 3.0, 4.0]:
    spec = RocketSpec(
        total_length_mm=250.0,
        body_diameter_mm=24.0,
        nose_length_mm=60.0,
        tail_length_mm=0.0,
        wall_thickness_mm=0.4,
        infill_ratio=0.02,
        material="PLA",
        material_density=1.24,
        motor_type="1/2A6-2",
        ballast_mass_g=b,
        recovery_mass_g=0.5,
        recovery_area_cm2=62.5,
        recovery_cd=0.25,
        descent_horizontal=True
    )
    opt = FinOptimizer(spec)
    res = opt.optimize(target_margin_cal=1.20, arrangement="auto")
    if res:
        print(f"L=250mm, Ballast={b:3.1f}g -> Arr: {'4fin' if res['is_4fin'] else '3fin'}, theta={res['theta_deg']}°, span={res['span_mm']}mm, cr={res['root_chord_mm']}mm, fin_mass={res['fin_mass_g']:.2f}g, total={res['total_mass_g']:.1f}g | Apogee={res['apogee_m']:.1f}m, Time={res['total_flight_time_s']:.2f}s | margin={res['margin_cal']:+.2f}cal")
    else:
        print(f"L=250mm, Ballast={b:3.1f}g -> None")
