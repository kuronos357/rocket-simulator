import zipfile

path = "つくば＿ロケット.gcode.3mf"
with zipfile.ZipFile(path, 'r') as z:
    xml_data = z.read("3D/3dmodel.model").decode('utf-8')
    print("--- First 500 chars of 3dmodel.model ---")
    print(xml_data[:500])
