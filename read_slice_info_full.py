import zipfile

path = r"D:\1_Stuff\0_programming\0_Project\ロケットシミュレーター\つくば＿ロケット.gcode.3mf"
with zipfile.ZipFile(path, 'r') as z:
    content = z.read("Metadata/slice_info.config").decode('utf-8', errors='ignore')
    print(content)
