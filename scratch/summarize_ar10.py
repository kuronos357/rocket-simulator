import json
import os

with open(os.path.join("scratch", "streamer_ar10_sweep_results.json"), "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Total data points: {len(data):,}")

streamer_lengths = sorted(list(set(d["streamer_L"] for d in data)))

print("\n--- 全体最高滞空時間 (マージン制約なし) ---")
print("| ストリーマー寸法 | 展開面積 | 重量 | 最高滞空時間 | 最高高度 | 降下速度 | 最適翼構成 | スパンxコード (ct, λ) | マージン |")
print("|---|---|---|---|---|---|---|---|---|")
for L in streamer_lengths:
    sub = [d for d in data if d["streamer_L"] == L]
    best = max(sub, key=lambda x: x["time"])
    W = best["streamer_W"]
    print(f"| {W:3.0f}x{L:4.0f} mm | {best['streamer_area']:6.1f} cm2 | {best['streamer_mass']:4.2f} g | {best['time']:5.2f} s | {best['apogee']:4.1f} m | {best['v_desc']:4.2f} m/s | {best['arch_name']:20s} | {best['span']}x{best['cr']}mm (ct={best['ct']}, λ={best['tr']:.2f}) | +{best['margin']:.2f} cal |")

print("\n--- 実戦基準: マージン >= 1.00 cal ---")
print("| ストリーマー寸法 | 展開面積 | 重量 | 最高滞空時間 | 最高高度 | 降下速度 | 最適翼構成 | スパンxコード (ct, λ) | マージン |")
print("|---|---|---|---|---|---|---|---|---|")
for L in streamer_lengths:
    sub = [d for d in data if d["streamer_L"] == L and d["margin"] >= 1.00]
    if not sub:
        continue
    best = max(sub, key=lambda x: x["time"])
    W = best["streamer_W"]
    print(f"| {W:3.0f}x{L:4.0f} mm | {best['streamer_area']:6.1f} cm2 | {best['streamer_mass']:4.2f} g | {best['time']:5.2f} s | {best['apogee']:4.1f} m | {best['v_desc']:4.2f} m/s | {best['arch_name']:20s} | {best['span']}x{best['cr']}mm (ct={best['ct']}, λ={best['tr']:.2f}) | +{best['margin']:.2f} cal |")
