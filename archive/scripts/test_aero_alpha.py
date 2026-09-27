import numpy as np
import trimesh
from sim_engine.aero import AeroEngine

# m2v3 の STL を読み込んで、Barrowman と aero.py の差を検証
m = trimesh.load("export/つくば＿ロケットm2 v3.stl")
print("Total mesh bounds:", m.bounds)

aero = AeroEngine("export/つくば＿ロケットm2 v3.stl", flight_axis="y", ref_diameter_mm=20.0)

# alpha=0, 1, 2, 5度での力を計算
for alpha in [0.5, 1.0, 2.0, 5.0]:
    res = aero.compute_aerodynamics(velocity_m_s=40.0, alpha_deg=alpha, cg_z_mm=62.0)
    print(f"alpha={alpha}deg: Normal_F={res['Normal_N']:.4f}N, Pitch_M={res['Normal_N']*(res['CP_z_mm']-62.0)*1e-3:.5f}Nm, CP={res['CP_z_mm']:.2f}mm, Margin={res['margin_cal']:.2f}cal")
