import json
import sys

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

with open('export/ロケット本体 v9_params.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

# テールは X = 233.0 mm、ノーズ先端は X = -130.0 mm
# z_tail = 233.0 - x
print(f"{'ボディ名':<10} | {'CAD X座標 [mm]':<18} | {'テールからの位置 Z [mm]':<26} | {'重心 Z [mm]':<12} | {'寸法 (X x Y x Z) [mm]'}")
print("-" * 105)

for b in d['bodies']:
    x_min, x_max = b['bbox_min_mm']['x'], b['bbox_max_mm']['x']
    z_tail_min = 233.0 - x_max
    z_tail_max = 233.0 - x_min
    cg_x = b['center_of_mass_mm']['x']
    cg_z_tail = 233.0 - cg_x
    sz = b['size_mm']
    sz_str = f"{sz['x']:.1f} x {sz['y']:.1f} x {sz['z']:.1f}"
    print(f"{b['name']:<10} | [{x_min:6.1f} ~ {x_max:6.1f}] | [{z_tail_min:5.1f} ~ {z_tail_max:5.1f}] mm (L={z_tail_max-z_tail_min:.0f}) | {cg_z_tail:6.1f} mm   | {sz_str}")
