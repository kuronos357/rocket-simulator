"""
Fusion 360 Script: Parametric Nonlinear Rocket Wing Generator
============================================================
How to use in Fusion 360:
1. Open Fusion 360.
2. Go to: [Utilities] (ユーティリティ) -> [Add-Ins] (アドイン) -> [Scripts and Add-Ins] (スクリプトとアドイン).
3. Under [My Scripts] (マイスクリプト), click [Create] (作成) -> Select [Python].
4. Name it (e.g. 'GenerateRocketWing'), click [Create].
5. Select the created script, click [Edit] (編集), paste this code, and Save.
6. Click [Run] (実行). It will instantly create a closed sketch profile of the optimal wing!
"""

import adsk.core, adsk.fusion, traceback
import math

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        design = app.activeProduct
        if not design:
            ui.messageBox('アクティブなデザインを開いてから実行してください。')
            return
            
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        xyPlane = rootComp.xYConstructionPlane
        sketch = sketches.add(xyPlane)
        sketch.name = "Optimal_Rocket_Wing_Profile"

        # =====================================================================
        # 設計パラメータ [mm単位で指定 -> Fusion内部単位(cm)に自動変換]
        # 【実用第1位：ベストバランス機】デフォルト値
        # =====================================================================
        span_mm = 75.0      # スパン幅 (胴体からの飛び出し量)
        cr_mm   = 28.0      # 翼根コード長
        ct_mm   = 10.0      # 翼端コード長 (高強度10mm)
        te_deg  = 25.0      # 後退角 [deg]
        oh_mm   = 5.0       # 後端オーバーハング
        p_le    = 0.70      # 前縁曲率指数
        p_te    = 0.80      # 後縁曲率指数
        # =====================================================================

        # mm -> cm 変換 (Fusion 360 の内部単位は cm)
        scale = 0.1
        span = span_mm * scale
        cr = cr_mm * scale
        ct = ct_mm * scale
        oh = oh_mm * scale
        
        te_sweep = span * math.tan(math.radians(te_deg))
        le_sweep = cr - ct + te_sweep
        
        # 点群の生成 (スパン方向 30分割)
        n_pts = 30
        pts_te = adsk.core.ObjectCollection.create()
        pts_le = adsk.core.ObjectCollection.create()
        
        # 後縁 (Root -> Tip)
        for i in range(n_pts + 1):
            eta = i / float(n_pts)
            x = span * eta
            y = -oh - te_sweep * (eta ** p_te)
            pts_te.add(adsk.core.Point3D.create(x, y, 0))
            
        # 前縁 (Tip -> Root)
        for i in range(n_pts, -1, -1):
            eta = i / float(n_pts)
            x = span * eta
            y = -oh + cr - le_sweep * (eta ** p_le)
            pts_le.add(adsk.core.Point3D.create(x, y, 0))
            
        # スプライン曲線の描画
        spline_te = sketch.sketchCurves.sketchFittedSplines.add(pts_te)
        spline_le = sketch.sketchCurves.sketchFittedSplines.add(pts_le)
        
        # 翼根と翼端を直線で閉じてプロファイル化
        # 翼根: (0, -oh) から (0, -oh + cr)
        p_root_te = pts_te.item(0)
        p_root_le = pts_le.item(pts_le.count - 1)
        line_root = sketch.sketchCurves.sketchLines.addByTwoPoints(p_root_te, p_root_le)
        
        # 翼端: (span, y_tip_te) から (span, y_tip_le)
        p_tip_te = pts_te.item(pts_te.count - 1)
        p_tip_le = pts_le.item(0)
        line_tip = sketch.sketchCurves.sketchLines.addByTwoPoints(p_tip_te, p_tip_le)
        
        ui.messageBox(f'非線形翼スケッチの生成が完了しました！\nスパン: {span_mm}mm, 翼根: {cr_mm}mm, 翼端: {ct_mm}mm\nそのまま押し出し(Extrude)可能です。')

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
