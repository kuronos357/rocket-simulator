import json

with open('output/final_three_models_full_specs.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

for k, v in d.items():
    fp = v['flight_performance']
    mb = v['mass_and_balance']
    fin = v['fins']
    print(f"{k}:")
    print(f"  Launch Mass: {mb['launch_mass_total_g']:.2f} g")
    print(f"  Stability Margin: {mb['margin_effective_cal']:.2f} cal (Pitch: {mb['margin_pitch_cal']:.2f}, Yaw: {mb['margin_yaw_cal']:.2f})")
    print(f"  Apogee: {fp['apogee_altitude_m']:.2f} m")
    print(f"  Burnout Speed: {fp['burnout_velocity_ms']:.2f} m/s")
    print(f"  Time to Apogee: {fp['time_to_apogee_s']:.2f} s")
    print(f"  Total Flight Time: {fp['total_flight_time_s']:.2f} s")
    print(f"  Descent Speed: {fp['descent_velocity_ms']:.2f} m/s")
    print("-" * 50)
