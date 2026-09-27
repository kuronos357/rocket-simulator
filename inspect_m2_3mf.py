import zipfile
import os

path_m2 = "つくば＿ロケットm2.3mf"
if os.path.exists(path_m2):
    print(f"Found {path_m2}! Size: {os.path.getsize(path_m2)} bytes")
    with zipfile.ZipFile(path_m2, 'r') as z:
        print("\nFiles in 3MF:")
        for info in z.infolist():
            print(f"  {info.filename:<40} : {info.file_size:>10} bytes")
else:
    print(f"File NOT found: {path_m2}")
