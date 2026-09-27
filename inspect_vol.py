import json

with open("export/つくば＿ロケット v8_params.json", encoding="utf-8") as f:
    d = json.load(f)

print("=== Bodies in v8 ===")
for b in d["bodies"]:
    print(f"Name: {b['name']}")
    print(f"  Visible: {b.get('is_visible')}")
    print(f"  Volume: {b.get('volume_cm3'):.3f} cm3")
    print(f"  Size (mm): {b.get('size_mm')}")
    print(f"  Bbox min: {b.get('bbox_min_mm')}")
    print(f"  Bbox max: {b.get('bbox_max_mm')}")
    print(f"  COM (mm): {b.get('center_of_mass_mm')}")
    print()
