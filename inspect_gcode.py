import zipfile

path = r"D:\1_Stuff\0_programming\0_Project\ロケットシミュレーター\つくば＿ロケット.gcode.3mf"
with zipfile.ZipFile(path, 'r') as z:
    gcode = z.read("Metadata/plate_1.gcode").decode('utf-8', errors='ignore')
    lines = gcode.split('\n')
    print("Total gcode lines:", len(lines))
    print("--- First 40 lines ---")
    for l in lines[:40]:
        print(l)
    print("--- Last 40 lines ---")
    for l in lines[-40:]:
        print(l)
