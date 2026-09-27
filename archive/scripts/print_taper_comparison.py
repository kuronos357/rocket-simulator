import math
import numpy as np
import sys
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

from compare_taper_impact import analyze_configuration

res_current = analyze_configuration("現行 m2 モデル (180mm ロングテーパー)", 180.0)
res_mid     = analyze_configuration("中間案 (120mm テーパー)", 120.0)
res_recom   = analyze_configuration("修正モデル (75mm ノーズ + 175mm ストレート)", 75.0)

print(f"{'比較項目':<22} | {'現行 m2 (180mmテーパー)':<25} | {'修正案 (75mmノーズ)':<25} | {'変化・効果':<20}")
print("-" * 100)
print(f"{'胴体ストレート長':<22} | {res_current['tube_len']:<23.1f}mm | {res_recom['tube_len']:<23.1f}mm | +105.0 mm 拡大")
print(f"{'ノーズコーン長':<22} | {res_current['nose_len']:<23.1f}mm | {res_recom['nose_len']:<23.1f}mm | -105.0 mm 短縮")
print(f"{'ストリーマ格納容積':<20} | {res_current['streamer_vol']:<23.1f}cm3 | {res_recom['streamer_vol']:<23.1f}cm3 | +16.5 cm3 (2.4倍!)")
print(f"{'ストリーマ格納位置(Y)':<19} | {res_current['y_streamer']:<23.1f}mm | {res_recom['y_streamer']:<23.1f}mm | +55.0 mm 前進！")
print(f"{'重心 CG (後端から)':<21} | {res_current['cg_tail']:<23.2f}mm | {res_recom['cg_tail']:<23.2f}mm | +9.70 mm 前進！")
print(f"{'ノーズ部 局所CP':<22} | {res_current['cp_nose_tail']:<23.2f}mm | {res_recom['cp_nose_tail']:<23.2f}mm | +48.9 mm 前方へ")
print(f"{'全体 圧力中心 CP':<21} | {res_current['cp_tail']:<23.2f}mm | {res_recom['cp_tail']:<23.2f}mm | +6.37 mm (フィン比で安定)")
print(f"{'静安定マージン (mm)':<19} | {res_current['margin_mm']:<23.2f}mm | {res_recom['margin_mm']:<23.2f}mm | +3.32 mm 拡大")
print(f"{'静安定マージン (cal)':<18} | {res_current['margin_cal']:<+23.2f}cal | {res_recom['margin_cal']:<+23.2f}cal | +0.16 cal 向上")
print(f"{'横倒し投影面積':<21} | {res_current['side_area_cm2']:<23.1f}cm2 | {res_recom['side_area_cm2']:<23.1f}cm2 | +10.5 cm2 (+22% エアブレーキ増)")
print(f"{'横倒し終末降下速度':<20} | {res_current['v_term']:<23.2f}m/s | {res_recom['v_term']:<23.2f}m/s | -0.60 m/s (減速・滞空時間向上)")
print(f"{'最高到達高度':<22} | {res_current['apogee']:<23.1f}m | {res_recom['apogee']:<23.1f}m | -7.2 m (投影面積増による微減)")
print(f"{'総滞空時間 (機体のみ)':<19} | {res_current['flight_time']:<23.1f}s | {res_recom['flight_time']:<23.1f}s | +0.1 s")
