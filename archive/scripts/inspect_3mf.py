import zipfile
import os

path = r"D:\1_Stuff\0_programming\0_Project\ロケットシミュレーター\つくば＿ロケット.gcode.3mf"
if os.path.exists(path):
    print("3MF file found! Size:", os.path.getsize(path))
    with zipfile.ZipFile(path, 'r') as z:
        print("Files inside 3MF:")
        for name in z.namelist():
            if "gcode" in name.lower() or "config" in name.lower() or "plate" in name.lower() or "slice" in name.lower():
                print(" -", name)
else:
    print("3MF file NOT found at:", path)
