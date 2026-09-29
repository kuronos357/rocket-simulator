import sys
import os
sys.path.insert(0, os.path.abspath("."))
from sim_engine.optimizer import RocketSpec, FinOptimizer
from scratch.test_correct_physics import evaluate_physically_correct_fins

print("Investigating L=250mm vs L=330mm physics:")
for L, nose in [(250.0, 60.0), (250.0, 100.0), (280.0, 110.0), (330.0, 80.0)]:
    spec = RocketSpec(
        total_length_mm=L,
        body_diameter_mm=24.0,
        nose_length_mm=nose,
        tail_length_mm=0.0,
        wall_thickness_mm=0.4,
        infill_ratio=0.02,
        material="PLA",
        material_density=1.24,
        motor_type="1/2A6-2",
        recovery_mass_g=1.2,
        recovery_area_cm2=250.0,
        recovery_cd=0.25,
        descent_horizontal=True
    )
    opt = FinOptimizer(spec)
    print(f"\n--- L = {L}mm, Nose = {nose}mm (Airframe mass = {opt.m_airframe_g:.1f}g, Launch mass without fins = {opt.m_base_launch:.1f}g, Base CG = {opt.z_base_cg:.1f}mm from tail) ---")
    print(f"Motor: 15.0g at tail (0~70mm)")
    
    # Try various fin spans up to 120mm
    found = False
    for span in [30, 45, 60, 75, 90, 110]:
        cr = int(span * 0.7)
        r = evaluate_physically_correct_fins(opt, span, cr, 0.0, 30.0, 1.0, is_4fin=False)
        p_mar = r["margin_pitch"]
        y_mar = r["margin_yaw"]
        m_eff = r["margin_eff"]
        # In evaluate_physically_correct_fins, CG is from tail or nose?
        # Let's inspect CG and CP
        print(f"  Span={span:3d}mm, Cr={cr:2d}mm: FinMass={r['fin_mass_g']:.2f}g, TotalMass={r['total_mass_g']:.1f}g | PitchMar={p_mar:+.2f}cal, YawMar={y_mar:+.2f}cal | Apogee={r['apogee_m']:.1f}m, Time={r['total_time_s']:.2f}s")
        if m_eff >= 1.20 and not found:
            found = True
            print(f"    --> FIRST PASSES MARGIN >= 1.20 at span={span}mm!")
