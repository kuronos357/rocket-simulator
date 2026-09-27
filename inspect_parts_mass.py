from sim_engine.loader import RocketModel

model = RocketModel("export/つくば＿ロケット v12_params.json")
print("=== Parts in v12 Model ===")
for p in model.parts:
    print(f"{p['name']} ({p['type']}): mass = {p['mass_g']} g, COM = {p['com_mm']}")
print(f"Total launch mass: {model.launch_mass_g} g")
print(f"Dry mass: {model.dry_mass_g} g")
