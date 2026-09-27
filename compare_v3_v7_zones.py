import numpy as np
import trimesh
import sys
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

def compute_mesh_forces(stl_path, name):
    mesh = trimesh.load(stl_path)
    # y flight axis -> z
    verts = mesh.vertices[:, [0, 2, 1]]
    normals = mesh.face_normals[:, [0, 2, 1]]
    centers = mesh.triangles_center[:, [0, 2, 1]]
    areas = mesh.area_faces * 1e-6
    
    alpha_rad = np.radians(2.0)
    wind_dir = np.array([0, -np.sin(alpha_rad), -np.cos(alpha_rad)])
    cos_theta = np.dot(normals, -wind_dir)
    
    q = 0.5 * 1.225 * (40.0**2)
    Cp = np.zeros_like(cos_theta)
    windward = cos_theta > 0
    Cp[windward] = 1.8 * (cos_theta[windward]**1.5)
    
    F_faces = -normals * (q * Cp[:, np.newaxis] * areas[:, np.newaxis])
    cg_pos = np.array([0, 0, 69.0]) # 共通CG
    r_m = (centers - cg_pos) * 1e-3
    moments = np.cross(r_m, F_faces)
    
    # ゾーン別集計
    # ゾーン1: フィン部 (Z: 0 ~ 70mm)
    # ゾーン2: 胴体中央部 (Z: 70 ~ 175mm)
    # ゾーン3: 先端ノーズ部 (Z: 175 ~ 250mm)
    zones = [
        ("テール・フィン部 (0~70mm)", 0, 70),
        ("胴体中央部 (70~175mm)", 70, 175),
        ("先端ノーズ部 (175~250mm)", 175, 250),
    ]
    
    res = {}
    for z_name, z0, z1 in zones:
        mask = (centers[:, 2] >= z0) & (centers[:, 2] < z1)
        Fy = np.sum(F_faces[mask, 1])
        Mx = np.sum(moments[mask, 0])
        sub_area = np.sum(areas[mask]) * 1e4
        res[z_name] = {"Fy": Fy, "Mx": Mx, "area": sub_area}
        
    tot_Fy = np.sum(F_faces[:, 1])
    tot_Mx = np.sum(moments[:, 0])
    cp = 69.0 + (-tot_Mx / tot_Fy * 1000.0) if abs(tot_Fy) > 1e-5 else 0.0
    res["TOTAL"] = {"Fy": tot_Fy, "Mx": tot_Mx, "CP": cp, "total_area": np.sum(areas)*1e4}
    return res

v3 = compute_mesh_forces("export/つくば＿ロケットm2 v3.stl", "m2 v3 (旧 180mmテーパー)")
v7 = compute_mesh_forces("export/つくば＿ロケットm2 v7.stl", "m2 v7 (新 175mmストレート)")

print("="*85)
print("  テーパー修正の直接効果：ゾーン別 空力・モーメント比較 (迎角 α=2度)")
print("="*85)
print(f"{'ゾーン':<25} | {'m2 v3 (旧テーパー)':<25} | {'m2 v7 (新ストレート)':<25}")
print("-" * 85)

for z in ["胴体中央部 (70~175mm)", "先端ノーズ部 (175~250mm)", "テール・フィン部 (0~70mm)"]:
    d3 = v3[z]
    d7 = v7[z]
    print(f"■ {z}")
    print(f"  表面積 (cm2)            : {d3['area']:<23.1f} | {d7['area']:<23.1f} ({d7['area']-d3['area']:+.1f}cm2)")
    print(f"  法線力 Fy (N)           : {d3['Fy']:<23.4f} | {d7['Fy']:<23.4f} ({d7['Fy']-d3['Fy']:+.4f}N)")
    print(f"  ピッチモーメント Mx     : {d3['Mx']:<23.5f} | {d7['Mx']:<23.5f} ({d7['Mx']-d3['Mx']:+.5f}Nm)")

print("-" * 85)
print("■ 総合評価 (CG = 69.0mm 基準)")
print(f"  総法線力 Fy (N)         : {v3['TOTAL']['Fy']:<23.4f} | {v7['TOTAL']['Fy']:<23.4f}")
print(f"  頭上げモーメント Mx     : {v3['TOTAL']['Mx']:<23.5f} | {v7['TOTAL']['Mx']:<23.5f}")
print(f"  重心位置 CG             : 61.6 mm                 | 69.1 mm (+7.5mm 前進！)")
print(f"  ストリーマ格納容積      : 約 12 cm3               | 約 28 cm3 (2.3倍！)")
