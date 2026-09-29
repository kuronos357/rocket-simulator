import os
import pptx
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

def create_deck():
    prs = Presentation()
    # 16:9 Widescreen (13.333 x 7.5 inches)
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    
    blank_layout = prs.slide_layouts[6] # Blank
    
    # Color Palette: Deep Navy & Modern Tech
    C_BG = RGBColor(15, 23, 42)          # #0F172A (Slate 900)
    C_CARD = RGBColor(30, 41, 59)        # #1E293B (Slate 800)
    C_CARD_LIGHT = RGBColor(51, 65, 85)  # #334155 (Slate 700)
    C_TEXT = RGBColor(248, 250, 252)     # #F8FAFC (Slate 50)
    C_SUBTEXT = RGBColor(148, 163, 184)  # #94A3B8 (Slate 400)
    C_PRIMARY = RGBColor(46, 196, 182)   # #2EC4B6 (Teal)
    C_ACCENT = RGBColor(255, 209, 102)   # #FFD166 (Gold)
    C_RED = RGBColor(230, 57, 70)        # #E63946 (Red)
    C_BLUE = RGBColor(59, 130, 246)      # #3B82F6 (Blue)
    
    def set_bg(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = C_BG
        bg.line.fill.background()
        return bg

    def add_header(slide, title_text, category_text="MODEL ROCKET MDO PROJECT"):
        tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.7), Inches(1.1))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        
        p0 = tf.paragraphs[0]
        p0.text = category_text.upper()
        p0.font.size = Pt(11)
        p0.font.bold = True
        p0.font.color.rgb = C_PRIMARY
        p0.space_after = Pt(4)
        
        p1 = tf.add_paragraph()
        p1.text = title_text
        p1.font.size = Pt(24)
        p1.font.bold = True
        p1.font.color.rgb = C_TEXT

    # =========================================================================
    # SLIDE 1: Title Slide
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_bg(s1)
    
    # Decorative accent bar
    bar = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.2), Inches(2.0), Inches(0.15), Inches(3.2))
    bar.fill.solid()
    bar.fill.fore_color.rgb = C_PRIMARY
    bar.line.fill.background()
    
    tb = s1.shapes.add_textbox(Inches(1.6), Inches(1.9), Inches(10.5), Inches(3.5))
    tf = tb.text_frame
    tf.word_wrap = True
    
    p = tf.paragraphs[0]
    p.text = "ESTES 1/2A6-2 COMPETITION ROCKET"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = C_ACCENT
    p.space_after = Pt(10)
    
    p2 = tf.add_paragraph()
    p2.text = "モデルロケット多目的設計最適化 (MDO)\n＆ 3Dプリント実機開発"
    p2.font.size = Pt(36)
    p2.font.bold = True
    p2.font.color.rgb = C_TEXT
    p2.space_after = Pt(16)
    
    p3 = tf.add_paragraph()
    p3.text = "Barrowman法・1自由度軌道シミュレーションに基づく パレート最適解の導出とCAD統合"
    p3.font.size = Pt(16)
    p3.font.color.rgb = C_SUBTEXT

    # Footer badge
    badge = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(5.8), Inches(6.5), Inches(0.7))
    badge.fill.solid()
    badge.fill.fore_color.rgb = C_CARD
    badge.line.color.rgb = C_CARD_LIGHT
    btf = badge.text_frame
    btf.vertical_anchor = MSO_ANCHOR.MIDDLE
    bp = btf.paragraphs[0]
    bp.alignment = PP_ALIGN.CENTER
    bp.text = "JAR公式50%ルール準拠 ｜ 0.44mm単層薄膜造形 ｜ アンバランス翼解析"
    bp.font.size = Pt(12)
    bp.font.color.rgb = C_TEXT

    # =========================================================================
    # SLIDE 2: Background & Constraints
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_bg(s2)
    add_header(s2, "設計課題と制約条件（レギュレーション＆造形）", "01. CONSTRAINTS & CHALLENGES")

    cards_data = [
        ("推進系制約 (Estes 1/2A6-2)", "・総重量: 15.0 g / 推進薬 1.56 g\n・総力積: 1.99 Ns (燃焼 0.32秒)\n・極小インパルスのため、1gの軽量化が到達高度と滞空時間を大きく左右する", C_RED),
        ("JAR公式競技規則 (レギュレーション)", "・全長: 250 mm 以上\n・50%ルール: 全長の50%以上が基準外径(24mm)のストレート円筒であること\n・ノーズ120mm採用時はボートテール不可", C_ACCENT),
        ("3Dプリント構造制約 (FDM PLA/PP-CF)", "・フィン厚み: 0.44 mm (単一外壁ライン)\n・内部インフィル: 2.0% (軽量シェル構造)\n・翼根フィレット: R1.5mm (接着強度UP＆外壁周長短縮による軽量化)", C_PRIMARY),
    ]

    for i, (title, desc, color) in enumerate(cards_data):
        x = Inches(0.8 + i * 4.0)
        card = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(2.0), Inches(3.7), Inches(4.7))
        card.fill.solid()
        card.fill.fore_color.rgb = C_CARD
        card.line.color.rgb = color
        card.line.width = Pt(1.5)
        
        ctf = card.text_frame
        ctf.margin_left = ctf.margin_right = Inches(0.25)
        ctf.margin_top = Inches(0.3)
        cp0 = ctf.paragraphs[0]
        cp0.text = title
        cp0.font.size = Pt(15)
        cp0.font.bold = True
        cp0.font.color.rgb = color
        cp0.space_after = Pt(16)
        
        cp1 = ctf.add_paragraph()
        cp1.text = desc
        cp1.font.size = Pt(12)
        cp1.font.color.rgb = C_TEXT
        cp1.space_before = Pt(8)

    # =========================================================================
    # SLIDE 3: Pareto Frontier (Scatter Plot Focused)
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_bg(s3)
    add_header(s3, "多目的最適化：パレートフロンティア（散布図）", "02. PARETO OPTIMAL FRONTIER")

    # Embed Refined Clean Scatter Plot (No Clutter)
    img_path = "output/pareto_scatter_refined_minimal.png"
    if not os.path.exists(img_path):
        img_path = "output/pareto_scatter_presentation_clean.png"
    if os.path.exists(img_path):
        s3.shapes.add_picture(img_path, Inches(0.8), Inches(1.8), width=Inches(8.5))

    # Right side commentary card
    rcard = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(9.6), Inches(1.8), Inches(2.9), Inches(5.0))
    rcard.fill.solid()
    rcard.fill.fore_color.rgb = C_CARD
    rcard.line.color.rgb = C_CARD_LIGHT
    
    rtf = rcard.text_frame
    rtf.margin_left = rtf.margin_right = Inches(0.2)
    rtf.margin_top = Inches(0.25)
    
    rp0 = rtf.paragraphs[0]
    rp0.text = "12万回の全探索結果"
    rp0.font.size = Pt(15)
    rp0.font.bold = True
    rp0.font.color.rgb = C_ACCENT
    rp0.space_after = Pt(10)
    
    points = [
        "■ 赤線：最高性能限界線\n(パレートフロンティア)",
        "■ 右肩下がりの物理限界\n安全率(マージン)を増やすほど翼が巨大化・重量増となり滞空時間が削られる",
        "■ 3大候補点の存在\n① 0.80 cal (水色点)\n② 0.86 cal (黄色点)\n③ 1.22 cal (青色点)",
        "■ アンバランス翼の優位\n通常対称翼を上回る効率を達成"
    ]
    for pt in points:
        p = rtf.add_paragraph()
        p.text = pt
        p.font.size = Pt(11)
        p.font.color.rgb = C_TEXT
        p.space_before = Pt(8)

    # =========================================================================
    # SLIDE 4: Three Candidates Comparison
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_bg(s4)
    add_header(s4, "選定された3大最適化モデルの比較", "03. THREE CANDIDATE DESIGNS")

    cand_cards = [
        ("機体①：最高高度特化", "アンバランス 4枚翼", "+0.79 cal", "145.6 m", "5.78 m/s", "30.43 秒", "主翼 55×31 mm (水平2枚)\n尾翼 49.5×27.9 mm (垂直2枚)\n最高到達高度・最長滞空チャンピオン", C_PRIMARY),
        ("機体②：最長滞空本命", "逆Y字 3枚翼 (35°下反角)", "+0.86 cal", "140.5 m", "5.59 m/s", "30.13 秒", "主翼 76×44 mm (35°下反角2枚)\n尾翼 53.2×30.8 mm (垂直1枚)\n最遅降下・滞空スイートスポット", C_ACCENT),
        ("機体③：鉄壁安全直進", "完全対称 4枚翼", "+1.22 cal", "133.4 m", "6.02 m/s", "28.44 秒", "十字翼 59×33 mm (完全対称4枚)\n強風下でも風見鶏効果に負けず\n矢のように直進する安全重視型", C_BLUE),
    ]

    for i, (name, arch, margin, apo, desc_v, hang, desc_text, col) in enumerate(cand_cards):
        x = Inches(0.8 + i * 4.0)
        c = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(1.8), Inches(3.7), Inches(5.1))
        c.fill.solid()
        c.fill.fore_color.rgb = C_CARD
        c.line.color.rgb = col
        c.line.width = Pt(2.0)
        
        ctf = c.text_frame
        ctf.margin_left = ctf.margin_right = Inches(0.25)
        ctf.margin_top = Inches(0.25)
        
        p = ctf.paragraphs[0]
        p.text = name
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = col
        p.space_after = Pt(2)
        
        p_sub = ctf.add_paragraph()
        p_sub.text = arch
        p_sub.font.size = Pt(12)
        p_sub.font.color.rgb = C_SUBTEXT
        p_sub.space_after = Pt(12)
        
        stats = [
            f"静的安定マージン: {margin}",
            f"最高到達高度: {apo}",
            f"降下速度: {desc_v}",
            f"合計滞空時間: {hang}"
        ]
        for st in stats:
            sp = ctf.add_paragraph()
            sp.text = "・" + st
            sp.font.size = Pt(12)
            sp.font.bold = True
            sp.font.color.rgb = C_TEXT
            sp.space_after = Pt(3)
            
        dp = ctf.add_paragraph()
        dp.text = "\n" + desc_text
        dp.font.size = Pt(11)
        dp.font.color.rgb = C_SUBTEXT

    # =========================================================================
    # SLIDE 5: Candidate 2 Breakdown (3-Fin Inverted-Y with 35 deg)
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_bg(s5)
    add_header(s5, "機体②の数理的ブレイクスルー（なぜ下反角35°なのか）", "04. CANDIDATE 2 BREAKTHROUGH")

    img_c2 = "output/rocket_m3type2_preview.png"
    if os.path.exists(img_c2):
        s5.shapes.add_picture(img_c2, Inches(0.8), Inches(1.8), width=Inches(7.2))

    c2_box = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.3), Inches(1.8), Inches(4.2), Inches(5.1))
    c2_box.fill.solid()
    c2_box.fill.fore_color.rgb = C_CARD
    c2_box.line.color.rgb = C_ACCENT
    c2_box.line.width = Pt(1.5)
    
    c2_tf = c2_box.text_frame
    c2_tf.margin_left = c2_tf.margin_right = Inches(0.25)
    c2_tf.margin_top = Inches(0.25)
    
    p = c2_tf.paragraphs[0]
    p.text = "直感と逆を行く「35°下反角」の物理"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_ACCENT
    p.space_after = Pt(8)
    
    c2_points = [
        "1. 垂直尾翼の30%小型化 (kv=0.70)\n軽量化と摩擦抵抗低減のため、上部の垂直尾翼を小型化。",
        "2. ヨー安定性の不足危機\n主翼を水平(0°)に寝かせると横風を素通りさせてしまい、ヨー安定性が破綻する。",
        "3. 下反角35°による横風シェア\n左右の主翼を水平から35°へ深く倒すことで、横風復元力(sin²θ)が0.25→0.33へ1.32倍増大！",
        "4. 奇跡の1:1縦横完全対称\nピッチ +0.866 cal ＝ ヨー +0.858 cal\n誤差わずか0.008 calで完全調和を達成！",
        "5. 最遅降下 5.59 m/s\n巨大な2枚の主翼が空気を受け止め、全機体中最もゆっくりと降下。"
    ]
    for cpt in c2_points:
        cp = c2_tf.add_paragraph()
        cp.text = cpt
        cp.font.size = Pt(11)
        cp.font.color.rgb = C_TEXT
        cp.space_before = Pt(6)

    # =========================================================================
    # SLIDE 6: Candidate 1 Breakdown (4-Fin Asym)
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_bg(s6)
    add_header(s6, "機体①の構造と実機作り込み（CAD＆3Dプリント）", "05. CANDIDATE 1 ARCHITECTURE")

    img_c1 = "output/rocket_m3type1_preview.png"
    if os.path.exists(img_c1):
        s6.shapes.add_picture(img_c1, Inches(0.8), Inches(1.8), width=Inches(7.2))

    c1_box = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.3), Inches(1.8), Inches(4.2), Inches(5.1))
    c1_box.fill.solid()
    c1_box.fill.fore_color.rgb = C_CARD
    c1_box.line.color.rgb = C_PRIMARY
    c1_box.line.width = Pt(1.5)
    
    c1_tf = c1_box.text_frame
    c1_tf.margin_left = c1_tf.margin_right = Inches(0.25)
    c1_tf.margin_top = Inches(0.25)
    
    p = c1_tf.paragraphs[0]
    p.text = "実プリント対応の細部設計"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_PRIMARY
    p.space_after = Pt(8)
    
    c1_points = [
        "1. 0.44mm 単層外壁フィン\n0.4mmノズルの1ライン幅に完全一致。余分な樹脂を削ぎ落とした超軽量ブレード。",
        "2. 翼根フィレット (R1.5mm)\n薄膜フィンの着地もぎ取れを防止。角周長を短縮して外壁体積を削減(軽量化)。",
        "3. 18mm Estesモーターマウント\nテールからZ=70mmまで内径18mm空間。Z=70〜75mmにスラスト受圧リングを一体化。",
        "4. 一体型ランチラグ\nフィンと干渉しない-45°位置(Z=40〜48mm)に内径3.2mmのガイドパイプを配置。",
        "5. べき乗則ノーズコーン\n指数0.75の滑らかなスプライン曲線により、前面造波抗力を極限まで低減。"
    ]
    for pt in c1_points:
        cp = c1_tf.add_paragraph()
        cp.text = pt
        cp.font.size = Pt(11)
        cp.font.color.rgb = C_TEXT
        cp.space_before = Pt(6)

    # =========================================================================
    # SLIDE 7: Material Upgrade (PP-CF)
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_bg(s7)
    add_header(s7, "素材アップグレード：PP-CF（炭素繊維PP）の威力", "06. ADVANCED COMPOSITE UPGRADE")

    mat_cards = [
        ("比重 0.95（水に浮く軽さ）", "・PLA(1.24)比で約 23% 軽量化\n・機体全体で -3.3〜3.5g の劇的減量\n・発射時総重量の1割以上が軽くなる", C_PRIMARY),
        ("最高高度 +15.0 m UP", "・機体①: 145.6 m → 162.0 m\n・機体②: 140.5 m → 156.0 m\n・燃焼終了速度が 64m/s → 71m/s (時速256km) へ跳ね上がる", C_ACCENT),
        ("滞空時間 +3.6〜5.8 秒 延長", "・軽くなったことでストリーマー降下速度が約 0.35m/s 減速 (5.59→5.25m/s)\n・「高く上がる」×「ゆっくり降りる」の相乗効果で 36秒超えへ", C_BLUE),
    ]

    for i, (title, desc, col) in enumerate(mat_cards):
        x = Inches(0.8 + i * 4.0)
        c = s7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(1.8), Inches(3.7), Inches(3.2))
        c.fill.solid()
        c.fill.fore_color.rgb = C_CARD
        c.line.color.rgb = col
        c.line.width = Pt(1.5)
        
        ctf = c.text_frame
        ctf.margin_left = ctf.margin_right = Inches(0.25)
        ctf.margin_top = Inches(0.25)
        cp0 = ctf.paragraphs[0]
        cp0.text = title
        cp0.font.size = Pt(15)
        cp0.font.bold = True
        cp0.font.color.rgb = col
        cp0.space_after = Pt(10)
        
        cp1 = ctf.add_paragraph()
        cp1.text = desc
        cp1.font.size = Pt(12)
        cp1.font.color.rgb = C_TEXT

    # Bottom summary box on stability
    sbox = s7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(5.3), Inches(11.7), Inches(1.6))
    sbox.fill.solid()
    sbox.fill.fore_color.rgb = C_CARD
    sbox.line.color.rgb = C_CARD_LIGHT
    
    stf = sbox.text_frame
    stf.margin_left = stf.margin_right = Inches(0.3)
    stf.margin_top = Inches(0.2)
    sp0 = stf.paragraphs[0]
    sp0.text = "【安定性への影響】バラスト不要で安全基準をクリア"
    sp0.font.size = Pt(13)
    sp0.font.bold = True
    sp0.font.color.rgb = C_TEXT
    sp0.space_after = Pt(4)
    
    sp1 = stf.add_paragraph()
    sp1.text = "前方のノーズ・胴体が軽くなるため重心(CG)が後方へ約3〜4mmシフトしますが、機体①で +0.63 cal、機体②で +0.71 cal を確保。\nロケットの安全飛行基準（+0.50 cal 以上）をオモリなしで余裕で維持します。"
    sp1.font.size = Pt(11)
    sp1.font.color.rgb = C_SUBTEXT

    # =========================================================================
    # SLIDE 8: Conclusion & Summary
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_bg(s8)
    add_header(s8, "総括：シミュレーションから実機製作へ", "07. CONCLUSION & ROADMAP")

    summary_box = s8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(11.7), Inches(5.1))
    summary_box.fill.solid()
    summary_box.fill.fore_color.rgb = C_CARD
    summary_box.line.color.rgb = C_PRIMARY
    summary_box.line.width = Pt(1.5)

    stf8 = summary_box.text_frame
    stf8.margin_left = stf8.margin_right = Inches(0.4)
    stf8.margin_top = Inches(0.35)

    s_items = [
        ("1. 理論最適化の完結", "12万通りを超える探索から、目的（高度特化／滞空特化／安全直進）に応じた明確なパレート最適解を導出。"),
        ("2. アンバランス翼の幾何学的勝利", "機体①の4枚翼アンバランス、機体②の35°下反角逆Y字翼により、従来対称翼の限界を突破。"),
        ("3. 実機CAD・3Dプリントデータの完成", "内径18mmモーター室、スラストリング、ランチラグ、0.44mm薄膜フィレットを含むSTL・Fusion360スクリプトを完全整備。"),
        ("4. 次のステップ（フライト検証）", "スライサーでの単層スライス・実機印刷を行い、地上重心測定および打ち上げ滞空時間の実測へ！")
    ]

    for i, (head, body) in enumerate(s_items):
        hp = stf8.paragraphs[0] if i == 0 else stf8.add_paragraph()
        hp.text = head
        hp.font.size = Pt(15)
        hp.font.bold = True
        hp.font.color.rgb = C_ACCENT if i == 1 else C_TEXT
        hp.space_before = Pt(12) if i > 0 else Pt(0)
        hp.space_after = Pt(2)

        bp = stf8.add_paragraph()
        bp.text = body
        bp.font.size = Pt(12)
        bp.font.color.rgb = C_SUBTEXT

    paths = [
        "output/rocket_mdo_presentation.pptx",
        "output/モデルロケット多目的最適化_発表スライド.pptx"
    ]
    saved = []
    for p in paths:
        try:
            prs.save(p)
            saved.append(p)
            print(f"Presentation successfully saved to: {p}")
        except PermissionError:
            alt = p.replace(".pptx", "_v2.pptx")
            prs.save(alt)
            saved.append(alt)
            print(f"File locked, saved alternative to: {alt}")

if __name__ == "__main__":
    create_deck()
