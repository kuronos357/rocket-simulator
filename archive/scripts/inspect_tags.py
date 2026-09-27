import zipfile
import xml.etree.ElementTree as ET

path = "つくば＿ロケット.gcode.3mf"
with zipfile.ZipFile(path, 'r') as z:
    for name in z.namelist():
        if "model" in name.lower():
            data = z.read(name)
            root = ET.fromstring(data)
            tags = set(elem.tag for elem in root.iter())
            print(f"File {name}: tags found:")
            for t in sorted(tags):
                print(" ", t)
