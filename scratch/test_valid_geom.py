import numpy as np

# Let's verify valid geometry check
def check_geom(cr, ct, te_sweep, p_le, p_te, c_min=1.5):
    le_sweep = cr - ct + te_sweep
    eta = np.linspace(0, 1, 21)
    c = cr + te_sweep * (eta ** p_te) - le_sweep * (eta ** p_le)
    return np.all(c >= c_min)

print("Self-intersecting case:", check_geom(16, 4.8, 52, 0.7, 1.4))
print("Ogive case:", check_geom(25, 2.0, 20, 2.2, 1.0))
print("Crescent case:", check_geom(25, 2.0, 20, 2.0, 1.4))
