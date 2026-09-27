import json

for ver in ["v10", "v11"]:
    fn = f"export/つくば＿ロケット {ver}_params.json"
    with open(fn, encoding="utf-8") as f:
        d = json.load(f)
    print(f"=== {ver} ===")
    print("Assembly mass (CAD):", d["assembly_summary"]["total_mass_g"])
    print("Assembly volume (CAD):", d["assembly_summary"]["total_volume_cm3"])
    print("Assembly area (CAD):", d["assembly_summary"]["total_area_cm2"])
    print("Center of mass:", d["assembly_summary"]["center_of_mass_mm"])
    print("Bodies:")
    for b in d["bodies"]:
        print(f"  {b['name']}: vol={b['volume_cm3']:.3f}, mass={b['mass_g']:.2f}, size={b['size_mm']}")
    print()
