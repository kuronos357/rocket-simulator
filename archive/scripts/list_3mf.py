import zipfile

path = "つくば＿ロケット.gcode.3mf"
with zipfile.ZipFile(path, 'r') as z:
    for info in z.infolist():
        print(f"{info.filename:<40} : {info.file_size:>10} bytes")
