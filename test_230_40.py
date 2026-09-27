from search_positive_margin import calc_detailed

# L=230mm, cr1=45, ct1=18, span1=40, sweep1=27, cr2=35, ct2=15, span2=25, sweep2=20
res = calc_detailed(
    L=230.0,
    cr1=45.0, ct1=18.0, span1=40.0, sweep1=27.0,
    cr2=35.0, ct2=15.0, span2=25.0, sweep2=20.0,
    m_streamer=2.5, m_nose_tip=1.0
)

print("=== Simulation Results for L=230mm Model (Span 40mm) ===")
print(f"Total Length            : {res['L']:.1f} mm (<= 250 mm)")
print(f"Gross Launch Mass       : {res['total_mass']:.2f} g")
print(f"Center of Gravity (CG)  : {res['cg_tail']:.2f} mm (from tail)")
print(f"Center of Pressure (CP) : {res['cp_tail']:.2f} mm (from tail)")
print(f"Static Margin           : +{res['margin_cal']:.2f} cal ({(res['margin_cal']*100):.1f} %D)")
print(f"Apogee Altitude         : {res['apogee']:.1f} m")
print(f"Terminal Descent Speed  : {res['v_term']:.2f} m/s")
print(f"Estimated Flight Time   : {res['flight_time']:.1f} s")
print(f"Side Projected Area     : {res['area_side_cm2']:.1f} cm2")
