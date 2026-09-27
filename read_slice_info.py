import zipfile

path = r"D:\1_Stuff\0_programming\0_Project\ロケットシミュレーター\つくば＿ロケット.gcode.3mf"
with zipfile.ZipFile(path, 'r') as z:
    for target in ["Metadata/slice_info.config", "Metadata/plate_1.json"]:
        if target in z.namelist():
            print(f"=== {target} ===")
            content = z.read(target).decode('utf-8', errors='ignore')
            print(content[:1000])
