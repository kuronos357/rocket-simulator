import json

with open('output/all_pattern_simulation_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total entries: {len(data)}")

# Let's inspect data keys
if data:
    print("Keys:", list(data[0].keys()))

# Filter PLA L=250
pla_250 = [d for d in data if d.get('material') == 'PLA' and d.get('L') == 250]
print(f"PLA L=250 count: {len(pla_250)}")

# Check points near margin 0.74, 0.925, 1.16
def find_near(m_target, m_tol=0.03):
    matches = [d for d in pla_250 if abs(d.get('margin_eff', 0) - m_target) <= m_tol]
    return sorted(matches, key=lambda x: x.get('total_time_s', 0), reverse=True)[:5]

print("\n--- Peak around 0.74 cal ---")
for p in find_near(0.74):
    print(f"Time: {p['total_time_s']:.3f}s, Margin: {p['margin_eff']:.3f}cal, Type: {p['wing_type']}, Span: {p['span_mm']}, Cr: {p['cr_mm']}, Nose: {p['nose_mm']}, Bal: {p['ballast_g']}")

print("\n--- Peak around 0.925 cal ---")
for p in find_near(0.925):
    print(f"Time: {p['total_time_s']:.3f}s, Margin: {p['margin_eff']:.3f}cal, Type: {p['wing_type']}, Span: {p['span_mm']}, Cr: {p['cr_mm']}, Nose: {p['nose_mm']}, Bal: {p['ballast_g']}")

print("\n--- Peak around 1.16 cal ---")
for p in find_near(1.16):
    print(f"Time: {p['total_time_s']:.3f}s, Margin: {p['margin_eff']:.3f}cal, Type: {p['wing_type']}, Span: {p['span_mm']}, Cr: {p['cr_mm']}, Nose: {p['nose_mm']}, Bal: {p['ballast_g']}")

print("\n--- 機体①, ②, ③ reference values ---")
c1_pts = [d for d in pla_250 if abs(d.get('margin_eff', 0) - 0.79) <= 0.02]
c2_pts = [d for d in pla_250 if abs(d.get('margin_eff', 0) - 0.86) <= 0.02]
c3_pts = [d for d in pla_250 if abs(d.get('margin_eff', 0) - 1.22) <= 0.02]
print("Near C1 (0.79):", sorted(c1_pts, key=lambda x: x['total_time_s'], reverse=True)[:1])
print("Near C2 (0.86):", sorted(c2_pts, key=lambda x: x['total_time_s'], reverse=True)[:1])
print("Near C3 (1.22):", sorted(c3_pts, key=lambda x: x['total_time_s'], reverse=True)[:1])
