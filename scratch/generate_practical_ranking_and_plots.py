"""
Comprehensive Practical & Realistic Wing Ranking Script
======================================================
Explores realistic parameter ranges:
  - Span: 55 to 85 mm
  - Root chord Cr: 28 to 48 mm
  - Tip chord Ct: 8 to 18 mm (Ct >= 8mm ensures 0.4mm nozzle durability)
  - Min local chord >= 8.0 mm everywhere (no thin waists!)
  - Overhang: 0.0, 5.0, 10.0 mm
  - Margin: >= 1.00 cal (with specific tiers for >= 1.00, >= 1.20, >= 1.30)
"""

import os
import sys
import math
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Japanese font setup
plt.rcParams['font.sans-serif'] = ['Yu Gothic', 'Meiryo', 'MS Gothic', 'TakaoPGothic', 'IPAexGothic', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

sys.path.insert(0, os.path.abspath("."))
from scratch.run_practical_ranking import calc_practical_flight, compute_fuselage_base

def run_ranking_search():
    spans = np.arange(55.0, 85.1, 2.5) # 13 values
    crs = np.arange(28.0, 48.1, 2.0)   # 11 values
    cts = np.array([8.0, 10.0, 12.0, 14.0, 16.0, 18.0]) # 6 values
    te_angles = np.array([0.0, 10.0, 15.0, 20.0, 25.0]) # 5 values
    overhangs = np.array([0.0, 5.0, 10.0]) # 3 values
    p_les = np.array([0.7, 0.85, 1.0, 1.2]) # 4 values
    p_tes = np.array([0.8, 1.0, 1.2])      # 3 values
    configs = [
        (35.0, 0.80, False, "3枚逆Y字35° (v=0.80)"),
        (35.0, 1.00, False, "3枚逆Y字35° (v=1.00)"),
        (0.0,  1.00, True,  "4枚十字 (+)"),
    ]
    
    total = (len(spans) * len(crs) * len(cts) * len(te_angles) * 
             len(overhangs) * len(p_les) * len(p_tes) * len(configs))
    print(f"Searching practical grid: {total:,} configurations...")
    
    results = []
    
    for span in spans:
        for cr in crs:
            for ct in cts:
                if ct >= cr * 0.65:
                    continue
                for te_ang in te_angles:
                    te_sw = span * math.tan(math.radians(te_ang))
                    for oh in overhangs:
                        for p_le in p_les:
                            for p_te in p_tes:
                                for theta, v_sc, is_4f, cfg_name in configs:
                                    r = calc_practical_flight(
                                        span, cr, ct, te_sw, oh,
                                        p_le, p_te,
                                        theta, v_sc, is_4f,
                                        min_chord_mm=8.0
                                    )
                                    if r is not None and r["margin"] >= 0.95:
                                        r["config_name"] = cfg_name
                                        r["te_angle"] = te_ang
                                        results.append(r)
                                        
    print(f"Found {len(results):,} valid practical configurations.")
    
    # -------------------------------------------------------------
    # 5 Key Realistic Archetypes:
    # -------------------------------------------------------------
    # 1. 【実用総合第1位：ベストバランス機】 (Ct >= 10mm, Overhang <= 5mm, Margin >= 1.05 cal, Span <= 75mm)
    c1 = [r for r in results if r["ct"] >= 10.0 and r["overhang"] <= 5.0 and r["margin"] >= 1.05 and r["span"] <= 75.0]
    c1.sort(key=lambda x: x["hang_time"], reverse=True)
    best_balance = c1[0]
    
    # 2. 【完全ツライチ自立機（発射台・整備性最優先）】 (Overhang == 0.0mm, Ct >= 10mm, Margin >= 1.00 cal)
    c2 = [r for r in results if r["overhang"] == 0.0 and r["ct"] >= 10.0 and r["margin"] >= 1.00]
    c2.sort(key=lambda x: x["hang_time"], reverse=True)
    best_flush = c2[0]
    
    # 3. 【直線クリップトデルタ（シンプル造形・高剛性）】 (p_le == 1.0, p_te == 1.0, Ct >= 10mm, Overhang <= 5mm, Margin >= 1.05 cal)
    c3 = [r for r in results if abs(r["p_le"] - 1.0) < 0.05 and abs(r["p_te"] - 1.0) < 0.05 and r["ct"] >= 10.0 and r["overhang"] <= 5.0 and r["margin"] >= 1.05]
    c3.sort(key=lambda x: x["hang_time"], reverse=True)
    best_straight = c3[0]
    
    # 4. 【強風耐性・超安定機（突風安全マージン重視）】 (Margin >= 1.30 cal, Ct >= 10mm, Overhang <= 10mm)
    c4 = [r for r in results if r["margin"] >= 1.30 and r["ct"] >= 10.0]
    c4.sort(key=lambda x: x["hang_time"], reverse=True)
    best_stable = c4[0]
    
    # 5. 【コンパクト高剛性機（小型スパン 65mm以下）】 (Span <= 65mm, Ct >= 10mm, Margin >= 1.00 cal)
    c5 = [r for r in results if r["span"] <= 65.0 and r["ct"] >= 10.0 and r["margin"] >= 1.00]
    c5.sort(key=lambda x: x["hang_time"], reverse=True)
    best_compact = c5[0]
    
    archetypes = [
        ("【実用第1位】ベストバランス機 (Span 75mm / OH 5mm)", best_balance, '#1f77b4'),
        ("【完全ツライチ自立機】(OH 0mm / 整備性最強)", best_flush, '#2ca02c'),
        ("【直線クリップトデルタ】(直線テーパー / 造形最容易)", best_straight, '#ff7f0e'),
        ("【耐風超安定機】(Margin +1.32cal / 突風耐性)", best_stable, '#9467bd'),
        ("【コンパクト機】(Span 65mm / 高剛性・収納性)", best_compact, '#d62728'),
    ]
    
    print("\n" + "="*80)
    print("実用・現実的トップランキング スペック一覧")
    print("="*80)
    for title, r, _ in archetypes:
        print(f"\n{title}")
        print(f"  形態: {r['config_name']}")
        print(f"  スパン: {r['span']:.1f} mm, 翼根コード: {r['cr']:.1f} mm, 翼端コード: {r['ct']:.1f} mm")
        print(f"  後退角: {r['te_angle']:.1f}°, オーバーハング: {r['overhang']:.1f} mm")
        print(f"  曲率: p_le={r['p_le']:.2f}, p_te={r['p_te']:.2f}")
        print(f"  性能: 静安定マージン={r['margin']:.2f} cal, 滞空時間={r['hang_time']:.2f} s, 最高高度={r['apogee']:.1f} m, 翼質量={r['fin_mass']:.2f} g")

    # -------------------------------------------------------------
    # Plot 1: Planform Comparison of 5 Practical Archetypes
    # -------------------------------------------------------------
    fig, axes = plt.subplots(1, 5, figsize=(22, 7), sharey=True)
    
    tail_len = 20.0
    R_fuselage = 12.0
    
    for i, (title, r, col) in enumerate(archetypes):
        ax = axes[i]
        span = r["span"]
        cr = r["cr"]
        ct = r["ct"]
        te_sw = r["te_sweep"]
        oh = r["overhang"]
        p_le = r["p_le"]
        p_te = r["p_te"]
        le_sw = cr - ct + te_sw
        
        # Fuselage outline
        # Tail cone from z=0 to 20, Body tube from z=20 to 120
        ax.plot([0, 0], [-oh - 10, 110], 'k--', lw=1, alpha=0.5)
        # Fuselage wall
        z_body = np.linspace(-oh, 100, 100)
        r_body = np.where(z_body <= tail_len, 9.4 + (12.0 - 9.4)*(z_body/tail_len), 12.0)
        r_body = np.where(z_body < 0, 9.4, r_body)
        ax.plot(r_body, z_body, 'k-', lw=1.5, alpha=0.7)
        ax.fill_betweenx(z_body, 0, r_body, color='#e0e0e0', alpha=0.5)
        
        # Wing outline
        n_pts = 60
        etas = np.linspace(0, 1, n_pts)
        y_pts = R_fuselage + span * etas
        # z coordinates from tail (z=0)
        # Root is attached from z = -oh to z = -oh + cr
        # Local TE and LE:
        # z_te(eta) = -oh + te_sw * (eta**p_te)
        # z_le(eta) = -oh + cr - le_sw * (eta**p_le)
        # Wait, in the earlier code:
        # xf_from_le was defined with root at x=0, tip at x=le_sw.
        # Let's be consistent: z axis points forward (nose is positive z).
        # Root TE is at z = -oh.
        # Root LE is at z = -oh + cr.
        # Tip TE is at z = -oh - te_sw (if sweep is backwards) or z = -oh + te_sw.
        # Let's check sign of te_sweep: te_sweep = span * tan(te_angle).
        # If te_angle > 0, tip moves backwards (more overhang).
        # So z_te(eta) = -oh - te_sw * (eta**p_te).
        # z_le(eta) = -oh + cr - le_sw * (eta**p_le).
        z_te = -oh - te_sw * (etas**p_te)
        z_le = -oh + cr - le_sw * (etas**p_le)
        
        # Plot fin polygon
        y_poly = np.concatenate([y_pts, y_pts[::-1]])
        z_poly = np.concatenate([z_te, z_le[::-1]])
        ax.fill(y_poly, z_poly, color=col, alpha=0.35, edgecolor=col, lw=2.5)
        
        # Motor exhaust line (z = 0)
        ax.axhline(0, color='red', ls=':', lw=1.5, label='胴体後端 (z=0)')
        if oh > 0:
            ax.axhline(-oh, color='darkred', ls='--', lw=1.0, alpha=0.7, label=f'翼後端 (-{oh}mm)')
            
        # Text details
        ax.set_title(f"{title.split('(')[0]}\n{r['config_name']}", fontsize=11, fontweight='bold')
        info_txt = (
            f"スパン $b$: {span:.1f} mm\n"
            f"翼根 $C_r$: {cr:.1f} mm\n"
            f"翼端 $C_t$: {ct:.1f} mm (高強度)\n"
            f"後退角: {r['te_angle']:.0f}° / 突出し: {oh:.1f}mm\n"
            f"前縁 $p_{{le}}$: {p_le:.2f} / 後縁: {p_te:.2f}\n"
            f"------------------\n"
            f"静安定: {r['margin']:.2f} cal\n"
            f"滞空: {r['hang_time']:.2f} 秒\n"
            f"高度: {r['apogee']:.1f} m\n"
            f"翼質量: {r['fin_mass']:.2f} g"
        )
        ax.text(0.05, 0.95, info_txt, transform=ax.transAxes, fontsize=9.5,
                verticalalignment='top', bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.85, edgecolor='gray'))
        
        ax.set_xlabel('Y [mm] (スパン方向)', fontsize=10.5, fontweight='bold')
        if i == 0:
            ax.set_ylabel('Z [mm] (機首方向)', fontsize=11, fontweight='bold')
        ax.grid(True, linestyle=':', alpha=0.5)
        ax.set_xlim(-5, 105)
        ax.set_ylim(-35, 80)
        ax.set_aspect('equal')
        
    plt.suptitle('【実用・現実的フォーカス】3Dプリント耐破損・発射台運用性・突風安定性を両立する実用最適翼ランキング', 
                 fontsize=14, fontweight='bold', y=0.98)
    plt.tight_layout()
    os.makedirs('output', exist_ok=True)
    plt.savefig('output/practical_optimal_wings.png', dpi=300)
    print("Saved output/practical_optimal_wings.png")
    
    # -------------------------------------------------------------
    # Plot 2: Practical Pareto & Trade-off Plot
    # -------------------------------------------------------------
    fig, (ax_p1, ax_p2) = plt.subplots(1, 2, figsize=(16, 7))
    
    # Scatter of all valid practical designs
    margins = np.array([r["margin"] for r in results])
    hang_times = np.array([r["hang_time"] for r in results])
    fin_masses = np.array([r["fin_mass"] for r in results])
    spans = np.array([r["span"] for r in results])
    
    # Panel 1: Margin vs Hang Time
    sc1 = ax_p1.scatter(margins, hang_times, c=fin_masses, cmap='viridis_r', s=16, alpha=0.5, rasterized=True)
    cbar1 = plt.colorbar(sc1, ax=ax_p1)
    cbar1.set_label('翼合計質量 [g]（軽量なほど黄色）', fontsize=10.5, fontweight='bold')
    
    # Mark the 5 archetypes
    markers = ['*', 's', '^', 'D', 'o']
    for idx, (title, r, col) in enumerate(archetypes):
        ax_p1.scatter([r["margin"]], [r["hang_time"]], color=col, edgecolor='black', s=220, marker=markers[idx], zorder=10,
                     label=f"{title.split('(')[0]}: {r['hang_time']:.2f}s (+{r['margin']:.2f}cal)")
        
    ax_p1.axvline(1.0, color='red', ls='--', lw=1.5, alpha=0.7, label='理論下限 (+1.0 cal)')
    ax_p1.axvline(1.3, color='blue', ls=':', lw=1.5, alpha=0.7, label='推奨実用安全圏 (+1.3 cal)')
    ax_p1.set_xlabel('静安定マージン [cal]', fontsize=11, fontweight='bold')
    ax_p1.set_ylabel('総滞空時間 [秒]', fontsize=11, fontweight='bold')
    ax_p1.set_title('(A) 実用制約下でのマージン vs 滞空時間トレードオフ', fontsize=12, fontweight='bold')
    ax_p1.grid(True, linestyle=':', alpha=0.6)
    ax_p1.legend(loc='lower left', fontsize=9.5, framealpha=0.9)
    ax_p1.set_xlim(0.95, 1.45)
    ax_p1.set_ylim(12.5, 13.6)
    
    # Panel 2: Span vs Fin Mass
    sc2 = ax_p2.scatter(spans, fin_masses, c=hang_times, cmap='plasma', s=16, alpha=0.5, rasterized=True)
    cbar2 = plt.colorbar(sc2, ax=ax_p2)
    cbar2.set_label('総滞空時間 [秒]（長いほど黄色）', fontsize=10.5, fontweight='bold')
    
    for idx, (title, r, col) in enumerate(archetypes):
        ax_p2.scatter([r["span"]], [r["fin_mass"]], color=col, edgecolor='black', s=220, marker=markers[idx], zorder=10,
                     label=f"{title.split('(')[0]}: b={r['span']:.0f}mm, {r['fin_mass']:.2f}g")
        
    ax_p2.set_xlabel('翼スパン幅 $b$ [mm]', fontsize=11, fontweight='bold')
    ax_p2.set_ylabel('翼合計質量 [g]', fontsize=11, fontweight='bold')
    ax_p2.set_title('(B) 翼スパン幅 vs 翼合計質量（剛性と重量のバランス）', fontsize=12, fontweight='bold')
    ax_p2.grid(True, linestyle=':', alpha=0.6)
    ax_p2.legend(loc='upper left', fontsize=9.5, framealpha=0.9)
    ax_p2.set_xlim(52, 88)
    ax_p2.set_ylim(1.8, 4.5)
    
    plt.suptitle('【実用設計空間のトレードオフ解析】実用・耐破損制約を満たす解の分布とトップランキング解の配置', 
                 fontsize=14, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.savefig('output/practical_pareto_ranking.png', dpi=300)
    print("Saved output/practical_pareto_ranking.png")
    
    # Export full JSON
    top_export = {
        "archetypes": [
            {
                "name": title,
                "specs": r
            } for title, r, _ in archetypes
        ]
    }
    with open("output/practical_top_archetypes.json", "w", encoding="utf-8") as f:
        json.dump(top_export, f, indent=2, ensure_ascii=False)
    print("Saved output/practical_top_archetypes.json")

if __name__ == "__main__":
    run_ranking_search()
