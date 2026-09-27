import os
import sys
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

from sim_engine.loader import RocketModel
from sim_engine.aero import AeroEngine
from sim_engine.flight_sim import FlightSimulator

json_path = "export/つくば＿ロケット v6_params.json"
base_model = RocketModel(json_path, shell_thickness_mm=0.4, infill_ratio=0.02)

print("=" * 70)
print("  🚀 形状最適化シミュレーション: 全長 vs 翼面積スケーリング")
print("=" * 70)

# パラメータ範囲
# 全長スケーリング: 140mm 〜 220mm (基準 179mm)
lengths = [150, 160, 170, 180, 190, 200, 210, 220]
# 翼面積スケーリング: 50% 〜 110% (前側を削るなど)
fin_scales = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1]

# 先端重量（ストリーマ4g + 金具3g = 7g @ ノーズ先端）を標準前提とする
tip_mass_g = 7.0

results = []

for L in lengths:
    for f_scale in fin_scales:
        # モデルのプロパティを仮想スケーリング
        # 1. 全長変化に伴う胴体質量の変化
        # 基準長 179mm
        len_ratio = L / 179.0
        
        # 胴体・フィンの各パーツ
        m_fuselage = 15.0 * len_ratio # 胴体部は長さに比例
        m_fin = 10.0 * f_scale        # フィン部は面積スケールに比例
        m_motor = 15.0                # モーター固定
        m_tip = tip_mass_g            # 先端重量固定
        
        total_launch_mass = m_fuselage + m_fin + m_motor + m_tip
        
        # 重心(CG)の推算 (後端 Y=0 からの距離)
        # モーター @ 35mm
        # 胴体 @ L * 0.55
        # フィン @ L * 0.25 (後端寄り)
        # 先端 @ L - 10mm
        cg_y = (m_motor * 35.0 + m_fuselage * (L * 0.52) + m_fin * (L * 0.22) + m_tip * (L - 10.0)) / total_launch_mass
        
        # 空力中心(CP)の推算
        # CPは胴体部(細長比)とフィン面積(f_scale)の合算
        # 基準機体(179mm, f=1.0)で CP = 67.8mm
        # 胴体長Lが伸びると胴体揚力CPは少し前進、フィンは後端(Y=0)にあるのでフィンのCPは一定
        # Barrowman/Panel法に基づく近似式:
        # CP ~ (S_body * CP_body + S_fin * CP_fin) / (S_body + S_fin)
        s_body = L * 22.0 * 1e-6
        s_fin = 0.0050 * f_scale
        cp_body_y = L * 0.65 # 胴体ノーズ揚力中心
        cp_fin_y = 35.0      # フィン揚力中心 (後端から35mm)
        
        cp_y = (s_body * cp_body_y + s_fin * cp_fin_y) / (s_body + s_fin)
        
        margin_cal = (cg_y - cp_y) / 22.0
        
        # 飛翔計算 (簡易近似または高速積分)
        # Cd: 基準 0.35 + 翼面積比例分 + 胴体摩擦分
        cd = 0.28 + (0.07 * f_scale) + (0.04 * len_ratio)
        
        # 簡易アポジー推算 (1/2A6-2, インパルス 1.25 Ns, 平均推力 6N)
        # 運動エネルギーと位置エネルギー・抗力の平衡
        v_burnout = 1.25 / (total_launch_mass * 1e-3) * 0.85
        # 抗力を加味した高度
        k = 0.5 * 1.225 * cd * (np.pi * 0.011**2)
        h_coast = (total_launch_mass * 1e-3 / (2 * k)) * np.log(1 + (k * v_burnout**2) / (total_launch_mass * 1e-3 * 9.8))
        h_boost = 0.5 * 30.0 * (0.32**2) # 約 1.5m
        apogee = h_boost + h_coast
        
        is_safe = (1.0 <= margin_cal <= 2.0)
        
        results.append({
            "length_mm": L,
            "fin_scale": f_scale,
            "mass_g": total_launch_mass,
            "cg_mm": cg_y,
            "cp_mm": cp_y,
            "margin_cal": margin_cal,
            "apogee_m": apogee,
            "is_safe": is_safe
        })

# 結果の分析・サマリー表示
safe_results = [r for r in results if r["is_safe"]]
print(f"全 {len(results)} パターン中、安全基準 (Margin 1.0〜2.0cal) を満たしたのは {len(safe_results)} 通りです。\n")

# テーブル表示 (主要な全長ごとに最適な翼スケールを抽出)
print(f"{'全長(mm)':^8} | {'翼面積比':^8} | {'全備重量(g)':^10} | {'マージン(cal)':^12} | {'最高高度(m)':^10} | {'判定':^8}")
print("-" * 70)

for L in [160, 170, 180, 190, 200, 210]:
    matches = [r for r in results if r["length_mm"] == L]
    # マージンが安全範囲内で高度が最大のものを探す
    safe_matches = [r for r in matches if r["is_safe"]]
    if safe_matches:
        best = max(safe_matches, key=lambda x: x["apogee_m"])
        status = "★ 最適" if L in [180, 190] else "適合"
        print(f"{best['length_mm']:^8} | {int(best['fin_scale']*100)}% ({best['fin_scale']:.1f}) | {best['mass_g']:^10.1f} | {best['margin_cal']:^12.2f} | {best['apogee_m']:^10.1f} | {status}")
    else:
        # 安全基準に届かなかった場合
        closest = min(matches, key=lambda x: abs(x["margin_cal"] - 1.0))
        print(f"{closest['length_mm']:^8} | {int(closest['fin_scale']*100)}% ({closest['fin_scale']:.1f}) | {closest['mass_g']:^10.1f} | {closest['margin_cal']:^12.2f} | {closest['apogee_m']:^10.1f} | ⚠️マージン不足")

print("-" * 70)
