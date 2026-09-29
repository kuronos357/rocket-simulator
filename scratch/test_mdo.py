import sys, time
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

sys.path.insert(0, r"d:\1_Stuff\0_programming\0_Project\ロケットシミュレーター")
from sim_engine.optimizer import RocketSpec
from sim_engine.mdo import FullRocketOptimizer

def test_mdo():
    print("=== MDO Test (Body + Fin Optimization) ===")
    
    # ユーザーの既存の「つくばロケット」をベースにする
    # ただし dry_mass_override を None にして物理質量計算を有効化
    spec = RocketSpec(
        total_length_mm=190.0, 
        body_diameter_mm=22.0, 
        nose_length_mm=60.0,
        motor_type="1/2A6-2",
        dry_mass_override_g=None, 
        infill_ratio=0.10, # ノーズコーン内部の10%が充填されているとする
        wall_thickness_mm=0.8 # プリント厚さ
    )
    
    mdo = FullRocketOptimizer(spec)
    
    # 全長の候補: 150mm から 300mm まで 10mm刻み
    length_range = [float(x) for x in range(150, 310, 10)]
    
    # ノーズ長さの候補: 40mm から 100mm まで 10mm刻み
    nose_range = [float(x) for x in range(40, 110, 10)]
    
    # ボートテールの長さ: 0mm (なし), 10mm, 20mm
    tail_range = [0.0, 10.0, 20.0]
    
    res = mdo.optimize_design(
        length_range=length_range,
        nose_range=nose_range,
        tail_range=tail_range,
        target_margin_cal=1.0,
        arrangement="airplane_3fin", # 水平尾翼＋垂直尾翼
        taper_ratios=[0.0, 0.5, 1.0] # デルタ翼, 半台形, 長方形
    )
    
    if res:
        b = res["body"]
        f = res["fins"]
        print("\n=== OPTIMAL DESIGN FOUND ===")
        print(f"Apogee: {f['apogee_m']:.1f} m (Velocity: {f['max_vel_km_h']:.1f} km/h)")
        print("\n[ Body Parameters ]")
        print(f"  Total Length: {b['total_length_mm']} mm")
        print(f"  Nose Length : {b['nose_length_mm']} mm")
        print(f"  Tail Length : {b['tail_length_mm']} mm")
        print(f"  Airframe Mass: {b['airframe_mass_g']:.1f} g")
        
        print("\n[ Fin Parameters ]")
        print(f"  Shape       : Taper Ratio {f['tip_chord_mm']/f['root_chord_mm'] if f['root_chord_mm']>0 else 0:.2f}")
        print(f"  Span        : {f['span_mm']} mm")
        print(f"  Root Chord  : {f['root_chord_mm']} mm")
        print(f"  Fin Mass    : {f['fin_mass_g']:.2f} g")
        print(f"  Margin      : {f['pitch_margin_cal']:+.2f} cal")
    else:
        print("No valid design found.")

if __name__ == "__main__":
    test_mdo()
