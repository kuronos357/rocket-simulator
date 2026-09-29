import os
import base64

def generate_html_deck():
    # Read embedded images as base64 for portable single-file offline presentation
    def to_b64(path):
        if os.path.exists(path):
            with open(path, "rb") as f:
                return "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")
        return ""

    scatter_path = "output/pareto_scatter_refined_minimal.png"
    if not os.path.exists(scatter_path):
        scatter_path = "output/pareto_scatter_presentation_clean.png"
    img_scatter = to_b64(scatter_path)
    img_c2 = to_b64("output/rocket_m3type2_preview.png")
    img_c1 = to_b64("output/rocket_m3type1_preview.png")

    html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>モデルロケット多目的設計最適化 (MDO) 発表スライド</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #090D16;
    color: #F8FAFC;
    font-family: 'Segoe UI', 'Meiryo', 'Hiragino Sans', sans-serif;
    overflow: hidden;
    height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
  }}
  .deck-container {{
    width: 100vw;
    height: 56.25vw; /* 16:9 */
    max-height: 100vh;
    max-width: 177.78vh; /* 16:9 */
    background: #0F172A;
    position: relative;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7);
    overflow: hidden;
  }}
  .slide {{
    display: none;
    width: 100%;
    height: 100%;
    padding: 3.5vw 4.5vw;
    position: absolute;
    top: 0; left: 0;
    flex-direction: column;
  }}
  .slide.active {{ display: flex; animation: fadeIn 0.35s cubic-bezier(0.16, 1, 0.3, 1); }}
  @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(12px); }} to {{ opacity: 1; transform: translateY(0); }} }}

  .category {{
    color: #2EC4B6;
    font-size: 1vw;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 0.4vw;
  }}
  .title {{
    color: #FFFFFF;
    font-size: 2.2vw;
    font-weight: 800;
    line-height: 1.25;
    margin-bottom: 2vw;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    padding-bottom: 0.8vw;
  }}
  .grid-3 {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.8vw; flex: 1; }}
  .grid-2 {{ display: grid; grid-template-columns: 1.35fr 1fr; gap: 2vw; flex: 1; align-items: center; }}

  .card {{
    background: #1E293B;
    border-radius: 0.8vw;
    padding: 1.5vw;
    border: 1px solid #334155;
    display: flex;
    flex-direction: column;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3);
  }}
  .card-title {{
    font-size: 1.25vw;
    font-weight: 700;
    margin-bottom: 1vw;
  }}
  .card-body {{
    font-size: 0.95vw;
    line-height: 1.65;
    color: #CBD5E1;
  }}
  .badge {{
    display: inline-block;
    padding: 0.2vw 0.6vw;
    border-radius: 0.3vw;
    font-size: 0.8vw;
    font-weight: 700;
    margin-bottom: 0.6vw;
  }}
  .stat-row {{
    display: flex;
    justify-content: space-between;
    padding: 0.35vw 0;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    font-size: 0.95vw;
  }}
  .stat-val {{ font-weight: 700; color: #FFF; }}

  .img-frame {{
    width: 100%;
    height: 100%;
    max-height: 30vw;
    object-fit: contain;
    background: #020617;
    border-radius: 0.8vw;
    border: 1px solid #334155;
  }}

  /* Controls */
  .controls {{
    position: fixed;
    bottom: 1.5vw;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    gap: 1vw;
    align-items: center;
    background: rgba(15, 23, 42, 0.85);
    padding: 0.5vw 1.2vw;
    border-radius: 2vw;
    backdrop-filter: blur(8px);
    border: 1px solid #334155;
    z-index: 100;
  }}
  .btn {{
    background: #334155;
    color: #FFF;
    border: none;
    padding: 0.4vw 0.9vw;
    border-radius: 0.4vw;
    cursor: pointer;
    font-size: 0.85vw;
    font-weight: 600;
    transition: all 0.2s;
  }}
  .btn:hover {{ background: #2EC4B6; color: #0F172A; }}
  .counter {{ font-size: 0.9vw; font-weight: 700; color: #94A3B8; min-width: 4vw; text-align: center; }}
</style>
</head>
<body>

<div class="deck-container" id="deck">

  <!-- SLIDE 1: Title -->
  <div class="slide active" style="justify-content: center; align-items: flex-start; padding-left: 8vw;">
    <div style="border-left: 0.5vw solid #2EC4B6; padding-left: 2vw;">
      <div style="color: #FFD166; font-size: 1.2vw; font-weight: 700; letter-spacing: 0.15em; margin-bottom: 0.8vw;">ESTES 1/2A6-2 COMPETITION ROCKET</div>
      <h1 style="font-size: 3.2vw; font-weight: 800; line-height: 1.2; margin-bottom: 1.2vw;">モデルロケット多目的設計最適化 (MDO)<br>＆ 3Dプリント実機開発</h1>
      <p style="color: #94A3B8; font-size: 1.3vw; margin-bottom: 2vw;">Barrowman法・1自由度非線形軌道シミュレーションに基づく パレート最適解の導出とCAD統合</p>
      <div style="background: #1E293B; border: 1px solid #334155; padding: 0.6vw 1.4vw; border-radius: 0.5vw; display: inline-block; font-size: 0.95vw; color: #E2E8F0;">
        JAR公式50%ルール準拠 ｜ 0.44mm単層薄膜造形 ｜ アンバランス翼解析
      </div>
    </div>
  </div>

  <!-- SLIDE 2: Constraints -->
  <div class="slide">
    <div class="category">01. CONSTRAINTS & CHALLENGES</div>
    <div class="title">設計課題と制約条件（レギュレーション＆造形）</div>
    <div class="grid-3">
      <div class="card" style="border-top: 0.3vw solid #E63946;">
        <div class="card-title" style="color: #E63946;">推進系制約 (Estes 1/2A6-2)</div>
        <div class="card-body">
          ・総重量: 15.0 g / 推進薬 1.56 g<br>
          ・総力積: 1.99 Ns (燃焼時間 0.32秒)<br>
          ・推力ピーク: 約 14 N<br><br>
          <b>【設計の要点】</b><br>
          極小インパルスエンジンのため、わずか1gの重量差が到達高度と滞空時間を大きく左右する。
        </div>
      </div>
      <div class="card" style="border-top: 0.3vw solid #FFD166;">
        <div class="card-title" style="color: #FFD166;">JAR公式競技規則</div>
        <div class="card-body">
          ・全長: 250 mm 以上<br>
          ・<b>50%ルール</b>: 全長の50%以上が基準外径(24mm)のストレート円筒であること<br><br>
          <b>【幾何的制約】</b><br>
          ノーズを120mmまで伸ばすと円筒部は130mm(52%)しか残らず、ボートテールは5mmすら配置不能。
        </div>
      </div>
      <div class="card" style="border-top: 0.3vw solid #2EC4B6;">
        <div class="card-title" style="color: #2EC4B6;">3Dプリント構造制約</div>
        <div class="card-body">
          ・フィン厚み: <b>0.44 mm</b> (単一外壁ライン)<br>
          ・内部インフィル: <b>2.0%</b> (超軽量シェル)<br>
          ・翼根フィレット: <b>R1.5 mm</b><br><br>
          <b>【目から鱗の物理】</b><br>
          コーナーを円弧に置換すると重い外壁周長が削られ、強度激増と同時に<b>さらなる軽量化</b>を達成！
        </div>
      </div>
    </div>
  </div>

  <!-- SLIDE 3: Pareto Frontier -->
  <div class="slide">
    <div class="category">02. PARETO OPTIMAL FRONTIER</div>
    <div class="title">多目的設計最適化：パレートフロンティア（散布図）</div>
    <div class="grid-2">
      <img src="{img_scatter}" class="img-frame" alt="Pareto Scatter">
      <div class="card" style="height: 100%; border-left: 0.3vw solid #FFD166;">
        <div class="card-title" style="color: #FFD166;">12万通りの探索から見えた真理</div>
        <div class="card-body">
          <p style="margin-bottom: 0.8vw;"><b style="color: #E63946;">■ 赤線：パレート最適フロンティア</b><br>いかなるパラメータ変更でもこれ以上右上には行けない理論限界線。</p>
          <p style="margin-bottom: 0.8vw;"><b style="color: #FFF;">■ 右肩下がりの物理限界</b><br>安全率（安定マージン）を稼ぐほどフィンが大型化・重量増となり、滞空時間が削られる。</p>
          <p style="margin-bottom: 0.8vw;"><b style="color: #2EC4B6;">■ 3大最適候補点（丸印）</b><br>
          ・水色点：機体① (+0.80 cal / 30.43s / 最高高度)<br>
          ・黄色点：機体② (+0.86 cal / 30.13s / 最長滞空)<br>
          ・青色点：機体③ (+1.22 cal / 28.44s / 強風直進)
          </p>
        </div>
      </div>
    </div>
  </div>

  <!-- SLIDE 4: Three Candidates -->
  <div class="slide">
    <div class="category">03. CANDIDATE SELECTION</div>
    <div class="title">選定された3大最適化モデルの性能比較</div>
    <div class="grid-3">
      <div class="card" style="border-top: 0.3vw solid #2EC4B6;">
        <span class="badge" style="background: rgba(46,196,182,0.2); color: #2EC4B6;">CHAMPION: 高度＆滞空</span>
        <div class="card-title" style="color: #2EC4B6;">機体①：アンバランス4枚翼</div>
        <div class="stat-row"><span>静的安定マージン</span><span class="stat-val">+0.791 cal</span></div>
        <div class="stat-row"><span>最高到達高度</span><span class="stat-val">145.6 m</span></div>
        <div class="stat-row"><span>降下速度</span><span class="stat-val">5.78 m/s</span></div>
        <div class="stat-row"><span>合計滞空時間</span><span class="stat-val">30.43 秒</span></div>
        <p style="font-size: 0.85vw; color: #94A3B8; margin-top: 1vw;">
          主翼55×31mm(水平2枚) ＋ 尾翼49.5×27.9mm(垂直2枚, kv=0.90)。最高高度を叩き出す最軽量モデル。
        </p>
      </div>

      <div class="card" style="border-top: 0.3vw solid #FFD166;">
        <span class="badge" style="background: rgba(255,209,102,0.2); color: #FFD166;">SWEET SPOT: 最遅降下</span>
        <div class="card-title" style="color: #FFD166;">機体②：逆Y字3枚翼 (35°)</div>
        <div class="stat-row"><span>静的安定マージン</span><span class="stat-val">+0.858 cal</span></div>
        <div class="stat-row"><span>最高到達高度</span><span class="stat-val">140.5 m</span></div>
        <div class="stat-row"><span>降下速度</span><span class="stat-val">5.59 m/s (全機最遅)</span></div>
        <div class="stat-row"><span>合計滞空時間</span><span class="stat-val">30.13 秒</span></div>
        <p style="font-size: 0.85vw; color: #94A3B8; margin-top: 1vw;">
          主翼76×44mm(35°下反角2枚) ＋ 尾翼53.2mm(垂直1枚)。大面積主翼が空気を受け止めて最長滞空。
        </p>
      </div>

      <div class="card" style="border-top: 0.3vw solid #3B82F6;">
        <span class="badge" style="background: rgba(59,130,246,0.2); color: #3B82F6;">HIGH STABILITY: 強風直進</span>
        <div class="card-title" style="color: #3B82F6;">機体③：完全対称4枚翼</div>
        <div class="stat-row"><span>静的安定マージン</span><span class="stat-val">+1.220 cal</span></div>
        <div class="stat-row"><span>最高到達高度</span><span class="stat-val">133.4 m</span></div>
        <div class="stat-row"><span>降下速度</span><span class="stat-val">6.02 m/s</span></div>
        <div class="stat-row"><span>合計滞空時間</span><span class="stat-val">28.44 秒</span></div>
        <p style="font-size: 0.85vw; color: #94A3B8; margin-top: 1vw;">
          十字翼59×33mm(完全対称4枚)。強風コンディション下でも風見鶏効果に流されず矢のように直進。
        </p>
      </div>
    </div>
  </div>

  <!-- SLIDE 5: Candidate 2 Breakdown -->
  <div class="slide">
    <div class="category">04. AERODYNAMIC BREAKTHROUGH</div>
    <div class="title">機体②の数理的ブレイクスルー（なぜ下反角35°なのか）</div>
    <div class="grid-2">
      <img src="{img_c2}" class="img-frame" alt="Candidate 2 Preview">
      <div class="card" style="height: 100%; border-left: 0.3vw solid #FFD166;">
        <div class="card-title" style="color: #FFD166;">直感と逆を行く「35°下反角」の必然性</div>
        <div class="card-body">
          <p style="margin-bottom: 0.7vw;"><b>1. 垂直尾翼の30%小型化 (kv=0.70)</b><br>軽量化と減抵抗のため上部尾翼を縮小。だがそのままではヨー安定性が破綻する。</p>
          <p style="margin-bottom: 0.7vw;"><b>2. 下反角35°による横風シェア</b><br>左右主翼を水平から35°へ深く倒すことで、横風復元力(sin²θ)が0.25→0.33へ<b>約1.32倍増大</b>！</p>
          <p style="margin-bottom: 0.7vw;"><b>3. 奇跡の1:1縦横完全対称</b><br>
          ピッチ +0.866 cal ＝ ヨー +0.858 cal<br>
          誤差わずか0.008 calで完全調和を達成！</p>
          <p><b>4. 最遅降下 5.59 m/s</b><br>2枚の大面積主翼が空気を受け止め、全機体中最もゆっくりと降下。</p>
        </div>
      </div>
    </div>
  </div>

  <!-- SLIDE 6: Candidate 1 Breakdown -->
  <div class="slide">
    <div class="category">05. DETAILED ARCHITECTURE</div>
    <div class="title">機体①の構造と実機作り込み（CAD＆3Dプリント）</div>
    <div class="grid-2">
      <img src="{img_c1}" class="img-frame" alt="Candidate 1 Preview">
      <div class="card" style="height: 100%; border-left: 0.3vw solid #2EC4B6;">
        <div class="card-title" style="color: #2EC4B6;">実プリント対応の細部設計</div>
        <div class="card-body">
          <p style="margin-bottom: 0.7vw;"><b>1. 0.44mm 単層外壁フィン</b><br>0.4mmノズルの1ライン幅に完全適合。余分な樹脂を削ぎ落とした超軽量ブレード。</p>
          <p style="margin-bottom: 0.7vw;"><b>2. 翼根フィレット (R1.5 mm)</b><br>薄膜フィンの着地もぎ取れを防止。角周長を短縮して外壁体積を削減(軽量化)。</p>
          <p style="margin-bottom: 0.7vw;"><b>3. 18mm Estesモーター室 ＆ ストッパー</b><br>テールからZ=70mmまで内径18mm空間。Z=70〜75mmにスラスト受圧リングを一体化。</p>
          <p><b>4. 一体型ランチラグ</b><br>フィンと干渉しない-45°位置(Z=40〜48mm)に内径3.2mmのガイドパイプを配置。</p>
        </div>
      </div>
    </div>
  </div>

  <!-- SLIDE 7: Material PP-CF -->
  <div class="slide">
    <div class="category">06. COMPOSITE MATERIAL UPGRADE</div>
    <div class="title">素材アップグレード：PP-CF（炭素繊維PP）の威力</div>
    <div class="grid-3" style="flex: 0 0 auto; margin-bottom: 1.5vw;">
      <div class="card" style="border-top: 0.3vw solid #2EC4B6;">
        <div class="card-title" style="color: #2EC4B6;">比重 0.95 (水に浮く軽さ)</div>
        <div class="card-body">
          ・PLA(1.24)比で約 <b>23% 軽量化</b><br>
          ・機体全体で <b>-3.3〜3.5g</b> の劇的減量<br>
          ・発射総重量の1割以上が軽くなる
        </div>
      </div>
      <div class="card" style="border-top: 0.3vw solid #FFD166;">
        <div class="card-title" style="color: #FFD166;">最高高度 +15.0 m UP</div>
        <div class="card-body">
          ・機体①: 145.6 m → <b>162.0 m</b><br>
          ・機体②: 140.5 m → <b>156.0 m</b><br>
          ・燃焼終了速度が 64m/s → <b>71m/s (時速256km)</b> へ跳ね上がる
        </div>
      </div>
      <div class="card" style="border-top: 0.3vw solid #3B82F6;">
        <div class="card-title" style="color: #3B82F6;">滞空時間 +3.6〜5.8 秒</div>
        <div class="card-body">
          ・軽くなったことで降下速度が約0.35m/s減速 (5.59→<b>5.25m/s</b>)<br>
          ・「高く上がる」×「ゆっくり降りる」の相乗効果で<b>36秒超え</b>へ
        </div>
      </div>
    </div>
    <div class="card" style="border-left: 0.3vw solid #2EC4B6;">
      <div class="card-title" style="font-size: 1.1vw; margin-bottom: 0.4vw;">【安定性への影響】オモリなしで安全基準（+0.5 cal以上）をクリア</div>
      <div class="card-body" style="font-size: 0.9vw;">
        前方のノーズ・胴体が軽くなるため重心(CG)が後方へ約3〜4mmシフトしますが、機体①で +0.63 cal、機体②で +0.71 cal を確保。バラストなしでそのまま安全にフライト可能です。
      </div>
    </div>
  </div>

  <!-- SLIDE 8: Summary -->
  <div class="slide">
    <div class="category">07. CONCLUSION & NEXT STEPS</div>
    <div class="title">総括：シミュレーションから実機フライトへ</div>
    <div class="card" style="flex: 1; border-left: 0.4vw solid #2EC4B6; padding: 2.5vw;">
      <div style="display: flex; flex-direction: column; gap: 1.5vw;">
        <div>
          <div style="font-size: 1.25vw; font-weight: 700; color: #FFD166; margin-bottom: 0.3vw;">1. 理論最適化の完結</div>
          <p style="font-size: 1vw; color: #CBD5E1;">12万通りを超える探索から、目的（高度特化／滞空特化／安全直進）に応じた明確なパレート最適解を導出。</p>
        </div>
        <div>
          <div style="font-size: 1.25vw; font-weight: 700; color: #2EC4B6; margin-bottom: 0.3vw;">2. アンバランス翼の幾何学的勝利</div>
          <p style="font-size: 1vw; color: #CBD5E1;">機体①の4枚翼アンバランス、機体②の35°下反角逆Y字翼により、従来対称翼の限界を突破。</p>
        </div>
        <div>
          <div style="font-size: 1.25vw; font-weight: 700; color: #3B82F6; margin-bottom: 0.3vw;">3. 実機CAD・3Dプリントデータの完成</div>
          <p style="font-size: 1vw; color: #CBD5E1;">内径18mmモーター室、スラストリング、ランチラグ、0.44mm薄膜フィレットを含むSTL・Fusion360スクリプトを完全整備。</p>
        </div>
        <div>
          <div style="font-size: 1.25vw; font-weight: 700; color: #E2E8F0; margin-bottom: 0.3vw;">4. 次のステップ（フライト検証）</div>
          <p style="font-size: 1vw; color: #CBD5E1;">スライサーでの単層スライス・実機印刷を行い、地上重心測定および打ち上げ滞空時間の実測へ！</p>
        </div>
      </div>
    </div>
  </div>

</div>

<!-- Navigation Controls -->
<div class="controls">
  <button class="btn" onclick="prevSlide()">◀ 前へ</button>
  <span class="counter" id="counter">1 / 8</span>
  <button class="btn" onclick="nextSlide()">次へ ▶</button>
  <button class="btn" onclick="toggleFullscreen()" style="background: #2EC4B6; color: #0F172A;">全画面表示</button>
</div>

<script>
  let cur = 0;
  const slides = document.querySelectorAll('.slide');
  const counter = document.getElementById('counter');

  function update() {{
    slides.forEach((s, i) => {{
      s.classList.toggle('active', i === cur);
    }});
    counter.textContent = `${{cur + 1}} / ${{slides.length}}`;
  }}

  function nextSlide() {{
    if (cur < slides.length - 1) {{ cur++; update(); }}
  }}
  function prevSlide() {{
    if (cur > 0) {{ cur--; update(); }}
  }}
  function toggleFullscreen() {{
    if (!document.fullscreenElement) {{
      document.documentElement.requestFullscreen();
    }} else {{
      document.exitFullscreen();
    }}
  }}

  document.addEventListener('keydown', (e) => {{
    if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown') nextSlide();
    if (e.key === 'ArrowLeft' || e.key === 'PageUp') prevSlide();
    if (e.key === 'f' || e.key === 'F') toggleFullscreen();
  }});
</script>

</body>
</html>
"""
    out_html = "output/presentation_slides.html"
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Interactive HTML presentation saved to: {out_html}")

if __name__ == "__main__":
    generate_html_deck()
