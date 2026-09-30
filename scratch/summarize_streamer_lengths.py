import json

with open('scratch/streamer_length_sweep_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total data points: {len(data):,}\n")

lengths = sorted(list(set(d['streamer_L'] for d in data)))
print("| ストリーマ長 | 展開面積 | ストリーマ重量 | 最大滞空時間 | 最高高度 | 降下速度 | 最適翼構成 | スパンxコード (ct, λ) | 安定マージン |")
print("|---|---|---|---|---|---|---|---|---|")

for L in lengths:
    sub = [d for d in data if d['streamer_L'] == L and d['margin'] >= 0.80]
    if sub:
        best = max(sub, key=lambda x: x['time'])
        print(f"| {L:4d} mm | {best['streamer_area']:6.1f} cm2 | {best['streamer_mass']:4.2f} g | {best['time']:5.2f} 秒 | {best['apogee']:4.1f} m | {best['v_desc']:4.2f} m/s | {best['arch_name']:22s} | {best['span']:2d}x{best['cr']:2d}mm (ct={best['ct']:3.1f}, λ={best['tr']:.2f}) | {best['margin']:+.2f} cal |")

print("\n--- 安定マージン >= 1.00 cal (本命帯) ---")
print("| ストリーマ長 | 展開面積 | ストリーマ重量 | 最大滞空時間 | 最高高度 | 降下速度 | 最適翼構成 | スパンxコード (ct, λ) | 安定マージン |")
print("|---|---|---|---|---|---|---|---|---|")
for L in lengths:
    sub = [d for d in data if d['streamer_L'] == L and d['margin'] >= 1.00]
    if sub:
        best = max(sub, key=lambda x: x['time'])
        print(f"| {L:4d} mm | {best['streamer_area']:6.1f} cm2 | {best['streamer_mass']:4.2f} g | {best['time']:5.2f} 秒 | {best['apogee']:4.1f} m | {best['v_desc']:4.2f} m/s | {best['arch_name']:22s} | {best['span']:2d}x{best['cr']:2d}mm (ct={best['ct']:3.1f}, λ={best['tr']:.2f}) | {best['margin']:+.2f} cal |")
