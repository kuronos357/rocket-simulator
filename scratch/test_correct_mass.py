import subprocess

# Let's test with Candidate 1 using dry mass = 15.54 g (0.01554 kg)
from export_all_openrocket import build_ork_xml, save_ork_file

c1_fins = [
    {
        'name': '主翼 (左右2枚 水平)',
        'count': 2,
        'span_mm': 55.0,
        'root_chord_mm': 31.0,
        'sweep_mm': 31.0,
        'tip_chord_mm': 0.0,
        'thickness_mm': 0.4,
        'rotation_deg': 0.0,
        'color_rgb': (230, 57, 70)
    },
    {
        'name': '垂直尾翼 (上下2枚 Kv=0.90)',
        'count': 2,
        'span_mm': 49.5,
        'root_chord_mm': 27.9,
        'sweep_mm': 27.9,
        'tip_chord_mm': 0.0,
        'thickness_mm': 0.4,
        'rotation_deg': 90.0,
        'color_rgb': (29, 53, 87)
    }
]

# Dry mass without motor = 30.54 - 15.0 = 15.54g
xml_test = build_ork_xml(
    rocket_name="機体①: 限界滞空型 (Cross Asym 4-Fin)",
    total_length_mm=250.0,
    nose_len_mm=120.0,
    body_len_mm=130.0,
    radius_mm=12.0,
    fin_sets=c1_fins,
    mass_override_g=15.54, # Dry mass without motor!
    cg_override_from_tip_mm=185.63,
    color_rgb=(230, 57, 70)
)
save_ork_file("scratch/test_c1_correct_mass.ork", xml_test)

# Now run simulation
res = subprocess.run([
    "java",
    "-cp", "C:\\Program Files\\OpenRocket\\jar\\OpenRocket-24.12.jar;scratch",
    "scratch/RunOrkSim.java",
    "scratch/test_c1_correct_mass.ork"
], capture_output=True, text=True)

for line in res.stdout.splitlines():
    if "APOGEE" in line or "VEL" in line or "TIME" in line or "FLIGHT" in line:
        print(line)
