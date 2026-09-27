import zipfile

path_gcode = "つくば＿ロケットm2.gcode.3mf"
with zipfile.ZipFile(path_gcode, 'r') as z:
    for name in ["Metadata/slice_info.config", "Metadata/plate_1.json"]:
        if name in z.namelist():
            print(f"=== {name} ===")
            print(z.read(name).decode('utf-8', errors='ignore'))
