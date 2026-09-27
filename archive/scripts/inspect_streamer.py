import json
import numpy as np

with open("export/つくば＿ロケット v8_params.json", encoding="utf-8") as f:
    d = json.load(f)

for b in d["bodies"]:
    if "ストリーマ" in b["name"] or "streamer" in b["name"].lower():
        print(f"Name: {b['name']}")
        print(f"Volume: {b['volume_cm3']} cm3")
        print(f"Area: {b['area_cm2']} cm2")
        print(f"Bbox: Y={b['bbox_min_mm']['y']} to {b['bbox_max_mm']['y']}")
        print(f"X: {b['bbox_min_mm']['x']} to {b['bbox_max_mm']['x']}")
        print(f"Z: {b['bbox_min_mm']['z']} to {b['bbox_max_mm']['z']}")

