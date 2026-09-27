import zipfile
import re

path = r"D:\1_Stuff\0_programming\0_Project\ロケットシミュレーター\つくば＿ロケット.gcode.3mf"
with zipfile.ZipFile(path, 'r') as z:
    gcode = z.read("Metadata/plate_1.gcode").decode('utf-8', errors='ignore')
    for line in gcode.split('\n'):
        if any(k in line.lower() for k in ["filament", "weight", "model_settings", "flush", "waste", "support"]):
            if "filament_density" not in line and "additional" not in line and "ams" not in line and "temperature" not in line:
                print(line)
