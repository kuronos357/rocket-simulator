import math
import sys
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# v14 baseline
L = 190.0
D = 22.0
R = 11.0
cg_v14 = 56.91
m_tot_v14 = 27.57
surf_density = 0.0346 # g/cm2 (PLA single perimeter ~0.4mm)

# Aerodynamic parameters
cna_nose = 2.0
cp_nose = L - 0.466 * 60.0 # from tail

def analyze(name, cr, ct, span, sweep_le, y_rear=0.0):
    area_1fin_mm2 = 0.5 * (cr + ct) * span
    area_1fin_cm2 = area_1fin_mm2 * 0.01
    
    # 2 horizontal fins mass
    m_fins_g = 2 * (2 * area_1fin_cm2) * surf_density
    
    # v14 fin mass (cr=51, ct=20, s=31)
    area_v14_mm2 = 0.5 * (51 + 20) * 31
    m_v14_fins = 2 * (2 * area_v14_mm2 * 0.01) * surf_density
    
    # Fin CG from tail
    y_fin_local = (cr**2 + cr*ct + ct**2) / (3.0 * (cr + ct)) if (cr + ct) > 0 else 0.0
    y_fin_cg = y_rear + y_fin_local
    
    m_tot = m_tot_v14 - m_v14_fins + m_fins_g
    cg = (m_tot_v14 * cg_v14 - m_v14_fins * 20.0 + m_fins_g * y_fin_cg) / m_tot
    
    # Barrowman CNA
    mid_sweep = sweep_le + (ct - cr) / 2.0
    Lf = math.sqrt(mid_sweep**2 + span**2)
    k_body = 1.0 + R / (R + span)
    denom = 1.0 + math.sqrt(1.0 + (2.0 * Lf / (cr + ct))**2)
    cna_fins = k_body * (4.0 * 2.0 * (span / D)**2) / denom
    
    # Fin CP
    term1 = sweep_le * (cr + 2*ct) / (3.0 * (cr + ct))
    term2 = (1.0 / 6.0) * (cr + ct - (cr * ct) / (cr + ct))
    cp_fin = cr - (term1 + term2) + y_rear
    
    # Top vertical fin (v14 constant)
    cna_top = 1.5 * (4.0 * 1.0 * (27 / D)**2) / (1.0 + math.sqrt(1.0 + (2.0 * 27 / 35.8)**2))
    cp_top = 15.0
    
    tot_cna = cna_nose + cna_fins + cna_top
    cp_tot = (cna_nose * cp_nose + cna_fins * cp_fin + cna_top * cp_top) / tot_cna
    
    margin_mm = cg - cp_tot
    margin_cal = margin_mm / D
    
    # Flight apogee prediction (flight_sim 相当の計算)
    S_ref = math.pi * (R * 1e-3)**2
    total_wet_cm2 = 330.0 - (area_v14_mm2 * 4 * 1e-2) + (area_1fin_mm2 * 4 * 1e-2)
    Cd = 0.0045 * (total_wet_cm2 * 1e-4 / S_ref) + 0.12 + 0.08
    m_avg = m_tot - 0.78
    v_bo = (1.25 / (m_avg * 1e-3)) - 9.8 * 0.32
    h_bo = 0.5 * v_bo * 0.32
    k_drag = 0.5 * 1.225 * Cd * S_ref / (m_tot * 1e-3)
    h_coast = (1.0 / (2.0 * k_drag)) * math.log(1.0 + k_drag * v_bo**2 / 9.8) if k_drag > 0 else 0
    apogee = h_bo + h_coast
    
    return {
        'name': name,
        'cr': cr, 'ct': ct, 'span': span, 'width': 2*(R+span),
        'area': area_1fin_cm2, 'mass': m_tot,
        'cg': cg, 'cp': cp_tot,
        'margin_cal': margin_cal, 'margin_mm': margin_mm,
        'apogee': apogee, 'Cd': Cd
    }

cases = [
    ('現行 v14 (台形翼)', 51, 20, 31, 31, 0),
    ('案1: 前縁延長デルタ翼 (スパン51mm・根元51mm)', 51, 0, 51, 51, 0),
    ('案2: スパン固定デルタ翼 (スパン31mm・根元31mm)', 31, 0, 31, 31, 0),
    ('案3: バランス型デルタ翼 (スパン40mm・根元40mm)', 40, 0, 40, 40, 0),
    ('案4: 前縁スパン維持デルタ (後縁前退・スパン31mm)', 51, 0, 31, 31, 20),
]

for c in cases:
    res = analyze(*c)
    print(f"[{res['name']}]")
    print(f"  翼寸法: 根元={res['cr']}mm, 翼端={res['ct']}mm, スパン={res['span']}mm (機体全幅: {res['width']:.0f}mm)")
    print(f"  片面面積: {res['area']:.1f} cm2, 機体総重量: {res['mass']:.2f} g")
    print(f"  CG(重心) = {res['cg']:.1f} mm, CP(空力中心) = {res['cp']:.1f} mm (テールから)")
    status = "OK: 安定" if res['margin_cal'] >= 0.8 else ("LOW: 弱安定" if res['margin_cal'] >= 0.2 else "NG: 不安定")
    print(f"  静安定マージン: {res['margin_cal']:+.2f} cal ({res['margin_mm']:+.1f} mm) -> [{status}]")
    print(f"  最高到達高度: 約 {res['apogee']:.1f} m (Cd={res['Cd']:.3f})")
    print()
