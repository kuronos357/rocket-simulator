import zipfile

path = "つくば＿ロケット.gcode.3mf"
with zipfile.ZipFile(path, 'r') as z:
    for name in ["Metadata/plate_1.png", "Metadata/top_1.png"]:
        if name in z.namelist():
            data = z.read(name)
            out_name = f"export/{name.replace('/', '_')}"
            with open(out_name, 'wb') as f:
                f.write(data)
            print(f"Extracted {name} to {out_name}")
