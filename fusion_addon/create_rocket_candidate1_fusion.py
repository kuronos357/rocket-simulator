# Fusion 360 Python Script for Building Rocket Candidate 1 (Asymmetric 4-Fin High Altitude Model)
# Dimensions: Total Length = 250mm, Diameter = 24mm, Nose = 120mm (Power 0.75)
# Main Fins (Horizontal 2x): Span = 55mm, Cr = 31mm
# Sub Fins (Vertical 2x, kv=0.90): Span = 49.5mm, Cr = 27.9mm
import adsk.core, adsk.fusion, traceback
import math

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        design = app.activeProduct
        if not design:
            ui.messageBox('アクティブなデザインが開かれていません。新規デザインを開いて実行してください。')
            return

        rootComp = design.rootComponent
        sketches = rootComp.sketches
        xzPlane = rootComp.xZConstructionPlane
        yzPlane = rootComp.yZConstructionPlane
        zAxis = rootComp.zConstructionAxis

        revolves = rootComp.features.revolveFeatures
        extrudes = rootComp.features.extrudeFeatures
        patterns = rootComp.features.circularPatternFeatures

        # =========================================================
        # 1. ロケット本体 (胴体 130mm + スプラインノーズ 120mm 一体回転成形)
        # =========================================================
        sketch_body = sketches.add(xzPlane)
        lines_body = sketch_body.sketchCurves.sketchLines

        def m2s_body(x, y, z):
            return sketch_body.modelToSketchSpace(adsk.core.Point3D.create(x, y, z))

        # テール中心 (0,0,0) -> テール外周 (1.2,0,0)
        lines_body.addByTwoPoints(m2s_body(0.0, 0.0, 0.0), m2s_body(1.2, 0.0, 0.0))
        # テール外周 (1.2,0,0) -> 胴体肩 (1.2,0,13.0)
        lines_body.addByTwoPoints(m2s_body(1.2, 0.0, 0.0), m2s_body(1.2, 0.0, 13.0))

        # ノーズコーン曲線 (Z=13.0cm から Z=25.0cm まで) - スプライン曲線
        spline_points = adsk.core.ObjectCollection.create()
        pt_shoulder = m2s_body(1.2, 0.0, 13.0)
        spline_points.add(pt_shoulder)

        n_pts = 24
        for i in range(1, n_pts):
            t = i / float(n_pts)
            z_cm = 13.0 + 12.0 * t
            dist_from_tip = 25.0 - z_cm
            r_cm = 1.2 * ((dist_from_tip / 12.0) ** 0.75)
            spline_points.add(m2s_body(r_cm, 0.0, z_cm))

        pt_tip = m2s_body(0.0, 0.0, 25.0)
        spline_points.add(pt_tip)
        sketch_body.sketchCurves.sketchFittedSplines.add(spline_points)

        # 中心軸 (ノーズ先端 -> テール中心) でプロファイルを閉じる
        axis_line = lines_body.addByTwoPoints(pt_tip, m2s_body(0.0, 0.0, 0.0))

        if sketch_body.profiles.count == 0:
            ui.messageBox('本体プロファイルの生成に失敗しました。')
            return

        prof_body = sketch_body.profiles.item(0)
        revInput = revolves.createInput(prof_body, axis_line, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        revInput.setAngleExtent(False, adsk.core.ValueInput.createByReal(2.0 * math.pi))
        body_feat = revolves.add(revInput)
        body_feat.bodies.item(0).name = "Rocket_Airframe"

        # =========================================================
        # 2. 左右主翼 (水平2枚: スパン55mm, コード31mm, 厚み0.8mm) on xzPlane
        # =========================================================
        sketch_main = sketches.add(xzPlane)
        lines_main = sketch_main.sketchCurves.sketchLines

        def m2s_m(x, y, z):
            return sketch_main.modelToSketchSpace(adsk.core.Point3D.create(x, y, z))

        # P1: (1.2cm, 0, 0.0cm)
        # P2: (1.2cm, 0, 3.1cm)
        # P3: (1.2 + 5.5 = 6.7cm, 0, 0.0cm)
        mp1 = m2s_m(1.2, 0.0, 0.0)
        mp2 = m2s_m(1.2, 0.0, 3.1)
        mp3 = m2s_m(6.7, 0.0, 0.0)

        lines_main.addByTwoPoints(mp1, mp2)
        lines_main.addByTwoPoints(mp2, mp3)
        lines_main.addByTwoPoints(mp3, mp1)

        prof_main = sketch_main.profiles.item(0)
        extInput_m = extrudes.createInput(prof_main, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        extInput_m.setSymmetricExtent(adsk.core.ValueInput.createByReal(0.04), True)
        feat_main = extrudes.add(extInput_m)
        body_main = feat_main.bodies.item(0)
        body_main.name = "MainFin_Horizontal"

        # 左右180度に対称配置 (合計2枚)
        coll_m = adsk.core.ObjectCollection.create()
        coll_m.add(body_main)
        pat_m = patterns.createInput(coll_m, zAxis)
        pat_m.quantity = adsk.core.ValueInput.createByString("2")
        pat_m.totalAngle = adsk.core.ValueInput.createByReal(2.0 * math.pi)
        pat_m.isSymmetric = False
        patterns.add(pat_m)

        # =========================================================
        # 3. 上下垂直尾翼 (垂直2枚: スパン49.5mm, コード27.9mm, kv=0.90) on yzPlane
        # =========================================================
        sketch_sub = sketches.add(yzPlane)
        lines_sub = sketch_sub.sketchCurves.sketchLines

        def m2s_s(x, y, z):
            return sketch_sub.modelToSketchSpace(adsk.core.Point3D.create(x, y, z))

        # P1: (0, 1.2cm, 0.0cm)
        # P2: (0, 1.2cm, 2.79cm)
        # P3: (0, 1.2 + 4.95 = 6.15cm, 0.0cm)
        sp1 = m2s_s(0.0, 1.2, 0.0)
        sp2 = m2s_s(0.0, 1.2, 2.79)
        sp3 = m2s_s(0.0, 6.15, 0.0)

        lines_sub.addByTwoPoints(sp1, sp2)
        lines_sub.addByTwoPoints(sp2, sp3)
        lines_sub.addByTwoPoints(sp3, sp1)

        prof_sub = sketch_sub.profiles.item(0)
        extInput_s = extrudes.createInput(prof_sub, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        extInput_s.setSymmetricExtent(adsk.core.ValueInput.createByReal(0.04), True)
        feat_sub = extrudes.add(extInput_s)
        body_sub = feat_sub.bodies.item(0)
        body_sub.name = "SubFin_Vertical"

        # 上下180度に対称配置 (合計2枚)
        coll_s = adsk.core.ObjectCollection.create()
        coll_s.add(body_sub)
        pat_s = patterns.createInput(coll_s, zAxis)
        pat_s.quantity = adsk.core.ValueInput.createByString("2")
        pat_s.totalAngle = adsk.core.ValueInput.createByReal(2.0 * math.pi)
        pat_s.isSymmetric = False
        patterns.add(pat_s)

        ui.messageBox(
            '【機体①】アンバランス4枚翼モデルのモデリングが成功しました！\n\n'
            '・全長: 250 mm (ノーズ 120 mm + 胴体 130 mm)\n'
            '・外径: 24 mm\n'
            '・主翼 (水平2枚): スパン 55.0 mm × ルート 31.0 mm\n'
            '・尾翼 (垂直2枚): スパン 49.5 mm × ルート 27.9 mm (kv=0.90)\n'
            '・実効安全率: +0.79 cal (高度145.6m・最高滞空特化)'
        )

    except:
        if ui:
            ui.messageBox('モデリング中にエラーが発生しました:\n{}'.format(traceback.format_exc()))
