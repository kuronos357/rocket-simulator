from optimize_stable_rocket import calc_rocket_properties

margins = []
for L in [190, 210, 230, 245]:
    for span1 in [25, 30, 35, 40]:
        for cr1 in [40, 50, 60]:
            ct1 = 20
            sweep1 = cr1 - ct1
            res = calc_rocket_properties(L, cr1, ct1, span1, sweep1, 35, 15, 25, 20)
            margins.append((res["margin_cal"], res["cg_tail"], res["cp_tail"], L, span1, cr1))

margins.sort(key=lambda x: x[0], reverse=True)
print("Top 10 highest margins:")
for m in margins[:10]:
    print(f"Margin: {m[0]:.2f} cal | CG: {m[1]:.1f} mm | CP: {m[2]:.1f} mm | L: {m[3]} mm | Span1: {m[4]} mm | Cr1: {m[5]} mm")
print("\nLowest 5 margins:")
for m in margins[-5:]:
    print(f"Margin: {m[0]:.2f} cal | CG: {m[1]:.1f} mm | CP: {m[2]:.1f} mm | L: {m[3]} mm")
