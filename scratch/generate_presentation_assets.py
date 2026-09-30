"""
Presentation Visual Asset Generator:
1. presentation_3_candidates_planforms.png: High-resolution side-by-side planform profiles
2. presentation_horizontal_mylar_scatter.png: 4-panel comprehensive scatter analysis
"""

import os
import sys
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Japanese font settings
plt.rcParams['font.sans-serif'] = ['Yu Gothic', 'Meiryo', 'MS Gothic', 'TakaoPGothic', 'IPAexGothic', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

sys.path.insert(0, os.path.abspath("."))
from scratch.optimize_mylar_120x1200 import calc_flight, compute_fuselage_base

def generate_assets():
    print("Generating presentation dataset...")
    # Generate scatter dataset across horizontal landing space
    spans = np.arange(55.0, 95.1, 2.5)
    crs = np.arange(22.0, 44.1, 2.0)
    cts = np.array([2.5, 3.5, 5.0, 6.5, 8.0])
    te_angles = np.array([10.0, 15.0, 20.0, 25.0])
    overhangs = np.array([0.0, 2.5, 5.0, 10.0])
    p_les = np.array([0.5, 0.7, 0.85, 1.0])
    p_tes = np.array([0.8, 1.0, 1.2, 1.4])
    
    results = []
    for span in spans:
        for cr in crs:
            for ct in cts:
                if ct >= cr * 0.5: continue
                for te_ang in te_angles:
                    te_sw = span * math.tan(math.radians(te_ang))
                    for oh in overhangs:
                        for ple in p_les:
                            for pte in p_tes:
                                r = calc_flight(span, cr, ct, te_sw, oh, ple, pte, 0.0, 1.0, True, min_chord_mm=2.5)
                                if r and r["margin"] >= 0.90:
                                    r["te_ang"] = te_ang
                                    results.append(r)
                                    
    print(f"Dataset points: {len(results):,}")
    
    # Define Candidate 1, 2, 3
    cand1 = {
        "title": "【候補1】究極滞空・三日月フィレット機\n★総合性能トップ (滞空 18.52秒)",
        "span": 90.0, "cr": 40.0, "ct": 5.0, "te_ang": 25.0, "oh": 5.0,
        "p_le": 0.50, "p_te": 1.20, "margin": 1.05, "hang_time": 18.52,
        "apogee": 51.5, "v_desc": 3.39, "fin_mass": 1.39, "total_mass": 32.50,
        "color": "#1f77b4", "marker": "*", "sub": "最大滞空・三日月後退"
    }
    cand2 = {
        "title": "【候補2】完全ツライチ自立機\n★発射台・整備性最強 (滞空 18.30秒)",
        "span": 95.0, "cr": 34.0, "ct": 3.5, "te_ang": 25.0, "oh": 0.0,
        "p_le": 0.50, "p_te": 0.80, "margin": 1.04, "hang_time": 18.30,
        "apogee": 50.8, "v_desc": 3.39, "fin_mass": 1.59, "total_mass": 32.70,
        "color": "#2ca02c", "marker": "s", "sub": "後端ツライチ・机に自立"
    }
    cand3 = {
        "title": "【候補3】耐風・超安全マージン機\n★突風大会専用 (滞空 18.16秒)",
        "span": 95.0, "cr": 36.0, "ct": 4.0, "te_ang": 25.0, "oh": 5.0,
        "p_le": 0.50, "p_te": 0.80, "margin": 1.27, "hang_time": 18.16,
        "apogee": 50.4, "v_desc": 3.39, "fin_mass": 1.71, "total_mass": 32.82,
        "color": "#d62728", "marker": "^", "sub": "安全マージン+1.27cal"
    }
    candidates = [cand1, cand2, cand3]
    
    # -------------------------------------------------------------------------
    # Graphic 1: Presentation Planforms Plot
    # -------------------------------------------------------------------------
    fig, axes = plt.subplots(1, 3, figsize=(18, 7.5), sharey=True)
    R_fuselage = 12.0
    tail_len = 20.0
    
    for i, cand in enumerate(candidates):
        ax = axes[i]
        span = cand["span"]
        cr = cand["cr"]
        ct = cand["ct"]
        oh = cand["oh"]
        te_sw = span * math.tan(math.radians(cand["te_ang"]))
        le_sw = cr - ct + te_sw
        ple = cand["p_le"]
        pte = cand["p_te"]
        col = cand["color"]
        
        # Centerline & Fuselage
        ax.plot([0, 0], [-oh - 10, 80], 'k--', lw=1.2, alpha=0.5)
        z_body = np.linspace(-oh, 70, 100)
        r_body = np.where(z_body <= tail_len, 9.4 + (12.0 - 9.4)*(z_body/tail_len), 12.0)
        r_body = np.where(z_body < 0, 9.4, r_body)
        ax.plot(r_body, z_body, 'k-', lw=1.8, alpha=0.8)
        ax.fill_betweenx(z_body, 0, r_body, color='#ececec', alpha=0.6)
        
        # Wing outline
        n_pts = 80
        etas = np.linspace(0, 1, n_pts)
        y_pts = R_fuselage + span * etas
        z_te = -oh - te_sw * (etas ** pte)
        z_le = -oh + cr - le_sw * (etas ** ple)
        
        y_poly = np.concatenate([y_pts, y_pts[::-1]])
        z_poly = np.concatenate([z_te, z_le[::-1]])
        ax.fill(y_poly, z_poly, color=col, alpha=0.30, edgecolor=col, lw=2.5)
        
        # Reference lines
        ax.axhline(0, color='red', ls=':', lw=1.5, label='胴体後端 (z=0)')
        if oh > 0:
            ax.axhline(-oh, color='darkred', ls='--', lw=1.2, alpha=0.7, label=f'翼後端 (-{oh:.0f}mm)')
            
        # Root bonding callout line
        ax.plot([R_fuselage, R_fuselage], [-oh, -oh + cr], color='blue', lw=3.5, label=f'接着長: {cr:.0f}mm')
        
        # Title and Info card
        ax.set_title(cand["title"], fontsize=12, fontweight='bold', pad=12)
        info_txt = (
            f"【形状パラメータ】\n"
            f"  ・スパン $b$: {span:.1f} mm (全幅 {24+2*span:.0f}mm)\n"
            f"  ・翼根コード $C_r$: {cr:.1f} mm (接着長)\n"
            f"  ・翼端コード $C_t$: {ct:.1f} mm\n"
            f"  ・後退角: {cand['te_ang']:.0f}° / 突出し: {oh:.1f}mm\n"
            f"  ・前縁曲率 $p_{{le}}$: {ple:.2f} (凹フィレット)\n"
            f"  ・後縁曲率 $p_{{te}}$: {pte:.2f}\n"
            f"------------------------------------\n"
            f"【シミュレーション性能】\n"
            f"  ★総滞空時間: {cand['hang_time']:.2f} 秒\n"
            f"  ・最高到達高度: {cand['apogee']:.1f} m\n"
            f"  ・降下終端速度: {cand['v_desc']:.2f} m/s\n"
            f"  ・静安定マージン: {cand['margin']:.2f} cal\n"
            f"  ・翼合計質量: {cand['fin_mass']:.2f} g (4枚計)\n"
            f"  ・全備質量: {cand['total_mass']:.2f} g"
        )
        ax.text(0.04, 0.96, info_txt, transform=ax.transAxes, fontsize=10,
                verticalalignment='top', bbox=dict(boxstyle='round,pad=0.6', facecolor='white', alpha=0.9, edgecolor='gray', lw=1))
        
        ax.set_xlabel('Y [mm] (スパン方向・機体半径含む)', fontsize=11, fontweight='bold')
        if i == 0:
            ax.set_ylabel('Z [mm] (機首方向)', fontsize=11, fontweight='bold')
        ax.grid(True, linestyle=':', alpha=0.55)
        ax.set_xlim(-5, 115)
        ax.set_ylim(-55, 65)
        ax.set_aspect('equal')
        ax.legend(loc='lower left', fontsize=9, framealpha=0.85)
        
    plt.suptitle('【競技用ロケット翼 最適化プレゼン資料】アルミ蒸着フィルム (120×1200mm) 対応 厳選3候補 平面形比較',
                 fontsize=15, fontweight='bold', y=0.98)
    plt.tight_layout()
    os.makedirs('output', exist_ok=True)
    out_planforms = 'output/presentation_3_candidates_planforms.png'
    plt.savefig(out_planforms, dpi=300)
    print(f"Saved {out_planforms}")
    
    # -------------------------------------------------------------------------
    # Graphic 2: 4-Panel Presentation Scatter Plot
    # -------------------------------------------------------------------------
    fig, axes = plt.subplots(2, 2, figsize=(18, 14))
    
    margins = np.array([r["margin"] for r in results])
    hang_times = np.array([r["hang_time"] for r in results])
    apogees = np.array([r["apogee"] for r in results])
    fin_masses = np.array([r["fin_mass"] for r in results])
    spans_arr = np.array([r["span"] for r in results])
    crs_arr = np.array([r["cr"] for r in results])
    
    # Panel A: Margin vs Hang Time (Frontier & Candidates)
    ax1 = axes[0, 0]
    sc1 = ax1.scatter(margins, hang_times, c=fin_masses, cmap='viridis_r', s=12, alpha=0.45, rasterized=True)
    cbar1 = plt.colorbar(sc1, ax=ax1)
    cbar1.set_label('翼合計質量 [g]（軽量なほど黄色）', fontsize=10.5, fontweight='bold')
    
    for cand in candidates:
        ax1.scatter([cand["margin"]], [cand["hang_time"]], color=cand["color"], edgecolor='black',
                    s=260, marker=cand["marker"], zorder=10,
                    label=f"{cand['title'].splitlines()[0]}: {cand['hang_time']:.2f}s (+{cand['margin']:.2f}cal)")
    ax1.axvline(1.0, color='red', ls='--', lw=1.5, alpha=0.7, label='推奨静安定限界 (+1.0 cal)')
    ax1.axvline(1.25, color='blue', ls=':', lw=1.5, alpha=0.7, label='突風安全バッファ (+1.25 cal)')
    ax1.set_xlabel('静安定マージン [cal]', fontsize=11, fontweight='bold')
    ax1.set_ylabel('総滞空時間 [秒]', fontsize=11, fontweight='bold')
    ax1.set_title('(A) 静安定マージン vs 総滞空時間（パレートフロンティア上の配置）', fontsize=12, fontweight='bold')
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc='lower left', fontsize=9.5, framealpha=0.9)
    ax1.set_xlim(0.92, 1.45)
    ax1.set_ylim(16.5, 18.7)
    
    # Panel B: Margin vs Apogee (Altitude Peak)
    ax2 = axes[0, 1]
    sc2 = ax2.scatter(margins, apogees, c=hang_times, cmap='plasma', s=12, alpha=0.45, rasterized=True)
    cbar2 = plt.colorbar(sc2, ax=ax2)
    cbar2.set_label('総滞空時間 [秒]（長いほど黄色）', fontsize=10.5, fontweight='bold')
    for cand in candidates:
        ax2.scatter([cand["margin"]], [cand["apogee"]], color=cand["color"], edgecolor='black',
                    s=260, marker=cand["marker"], zorder=10,
                    label=f"{cand['title'].splitlines()[0]}: {cand['apogee']:.1f}m")
    ax2.axvline(1.0, color='red', ls='--', lw=1.5, alpha=0.7)
    ax2.set_xlabel('静安定マージン [cal]', fontsize=11, fontweight='bold')
    ax2.set_ylabel('最高到達高度 [m]', fontsize=11, fontweight='bold')
    ax2.set_title('(B) 静安定マージン vs 最高到達高度（軽量化による高度維持）', fontsize=12, fontweight='bold')
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(loc='lower left', fontsize=9.5, framealpha=0.9)
    ax2.set_xlim(0.92, 1.45)
    ax2.set_ylim(44.0, 52.5)
    
    # Panel C: Fin Mass vs Hang Time (Correlation with Wing Weight)
    ax3 = axes[1, 0]
    sc3 = ax3.scatter(fin_masses, hang_times, c=margins, cmap='coolwarm', s=12, alpha=0.45, rasterized=True)
    cbar3 = plt.colorbar(sc3, ax=ax3)
    cbar3.set_label('静安定マージン [cal]', fontsize=10.5, fontweight='bold')
    for cand in candidates:
        ax3.scatter([cand["fin_mass"]], [cand["hang_time"]], color=cand["color"], edgecolor='black',
                    s=260, marker=cand["marker"], zorder=10,
                    label=f"{cand['title'].splitlines()[0]}: {cand['fin_mass']:.2f}g")
    ax3.set_xlabel('翼合計質量 [g] (4枚合計)', fontsize=11, fontweight='bold')
    ax3.set_ylabel('総滞空時間 [秒]', fontsize=11, fontweight='bold')
    ax3.set_title('(C) 翼合計質量 vs 滞空時間（1.4g〜1.7gの超軽量領域の優位性）', fontsize=12, fontweight='bold')
    ax3.grid(True, linestyle=':', alpha=0.6)
    ax3.legend(loc='upper right', fontsize=9.5, framealpha=0.9)
    ax3.set_xlim(1.2, 3.2)
    ax3.set_ylim(16.5, 18.7)
    
    # Panel D: Span vs Root Chord (Structural Bonding Envelope)
    ax4 = axes[1, 1]
    sc4 = ax4.scatter(spans_arr, crs_arr, c=hang_times, cmap='viridis', s=12, alpha=0.45, rasterized=True)
    cbar4 = plt.colorbar(sc4, ax=ax4)
    cbar4.set_label('総滞空時間 [秒]（長いほど黄色）', fontsize=10.5, fontweight='bold')
    for cand in candidates:
        ax4.scatter([cand["span"]], [cand["cr"]], color=cand["color"], edgecolor='black',
                    s=260, marker=cand["marker"], zorder=10,
                    label=f"{cand['title'].splitlines()[0]}: Span {cand['span']:.0f}mm / 接着長 {cand['cr']:.0f}mm")
    ax4.set_xlabel('スパン幅 $b$ [mm]', fontsize=11, fontweight='bold')
    ax4.set_ylabel('翼根コード長 $C_r$ [mm]（胴体接着長）', fontsize=11, fontweight='bold')
    ax4.set_title('(D) スパン幅 vs 翼根コード長（横倒し着地耐荷重エンベロープ）', fontsize=12, fontweight='bold')
    ax4.grid(True, linestyle=':', alpha=0.6)
    ax4.legend(loc='upper left', fontsize=9.5, framealpha=0.9)
    ax4.set_xlim(52, 98)
    ax4.set_ylim(20, 46)
    
    plt.suptitle('【プレゼン用 散布図・相関解析】アルミ蒸着フィルム (120×1200mm) 対応 全探索パレートフロンティアと厳選3候補の配置',
                 fontsize=15, fontweight='bold', y=0.98)
    plt.tight_layout()
    out_scatter = 'output/presentation_horizontal_mylar_scatter.png'
    plt.savefig(out_scatter, dpi=300)
    print(f"Saved {out_scatter}")

if __name__ == "__main__":
    generate_assets()
