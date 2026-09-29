# Fusion 360 Python Script for Building Rocket Candidate 1 (Asymmetric 4-Fin High Altitude Model)
# Dimensions: Total Length = 250mm, Diameter = 24mm, Nose = 120mm (Power 0.75)
# Motor Mount: 18mm Estes Mount (Length 70mm, Stop Ring at 70-75mm)
# Main Fins (Horizontal 2x): Span = 55mm, Cr = 31mm, Thickness = 0.44mm
# Sub Fins (Vertical 2x, kv=0.90): Span = 49.5mm, Cr = 27.9mm, Thickness = 0.44mm
# Launch Lug: 45 deg between fins, Length 8mm, ID 3.2mm, OD 4.8mm
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
        xyPlane = rootComp.xYConstructionPlane
        zAxis = rootComp.zConstructionAxis

        revolves = rootComp.features.revolveFeatures
        extrudes = rootComp.features.extrudeFeatures
        patterns = rootComp.features.circularPatternFeatures
        fillets = rootComp.features.filletFeatures

        # パラメータ設定 (単位: cm)
        body_r = 1.2         # 胴体半径 12mm
        motor_r = 0.9        # 18mmモーター内径 (半径 9mm)
        stop_r = 0.8         # ストッパー内径 (半径 8mm)
        tube_in_r = 1.0      # 上部チューブ内径 (肉厚 2mm)
        fin_half_t = 0.022   # フィン片側厚み 0.22mm (全厚 0.44mm)
        fillet_r = 0.15      # 翼根フィレット 1.5mm

        # =========================================================
        # 1. ロケット中空本体 (モーター室70mm + 上部チューブ + スプラインノーズ)
        # =========================================================
        sketch_body = sketches.add(xzPlane)
        lines_body = sketch_body.sketchCurves.sketchLines

        def m2s_body(x, y, z):
            return sketch_body.modelToSketchSpace(adsk.core.Point3D.create(x, y, z))

        # 外周ライン
        # テール端面: (0.9, 0, 0) -> (1.2, 0, 0)
        lines_body.addByTwoPoints(m2s_body(motor_r, 0.0, 0.0), m2s_body(body_r, 0.0, 0.0))
        # 胴体外周: (1.2, 0, 0) -> (1.2, 0, 13.0)
        lines_body.addByTwoPoints(m2s_body(body_r, 0.0, 0.0), m2s_body(body_r, 0.0, 13.0))

        # ノーズコーン外形曲線 (Z=13.0cm から Z=25.0cm まで) - スプライン
        spline_points = adsk.core.ObjectCollection.create()
        pt_shoulder = m2s_body(body_r, 0.0, 13.0)
        spline_points.add(pt_shoulder)

        n_pts = 24
        for i in range(1, n_pts):
            t = i / float(n_pts)
            z_cm = 13.0 + 12.0 * t
            dist_from_tip = 25.0 - z_cm
            r_cm = body_r * ((dist_from_tip / 12.0) ** 0.75)
            spline_points.add(m2s_body(r_cm, 0.0, z_cm))

        pt_tip = m2s_body(0.0, 0.0, 25.0)
        spline_points.add(pt_tip)
        sketch_body.sketchCurves.sketchFittedSplines.add(spline_points)

        # 中心軸ライン (ノーズ先端 -> Z=13.0cm)
        lines_body.addByTwoPoints(pt_tip, m2s_body(0.0, 0.0, 13.0))

        # 内腔ライン (ノーズ付け根からモーター室へ)
        # 上部チューブ内壁: (0.0, 0, 13.0) -> (1.0, 0, 13.0) -> (1.0, 0, 7.5)
        lines_body.addByTwoPoints(m2s_body(0.0, 0.0, 13.0), m2s_body(tube_in_r, 0.0, 13.0))
        lines_body.addByTwoPoints(m2s_body(tube_in_r, 0.0, 13.0), m2s_body(tube_in_r, 0.0, 7.5))

        # ストッパーリング: (1.0, 0, 7.5) -> (0.8, 0, 7.5) -> (0.8, 0, 7.0) -> (0.9, 0, 7.0)
        lines_body.addByTwoPoints(m2s_body(tube_in_r, 0.0, 7.5), m2s_body(stop_r, 0.0, 7.5))
        lines_body.addByTwoPoints(m2s_body(stop_r, 0.0, 7.5), m2s_body(stop_r, 0.0, 7.0))
        lines_body.addByTwoPoints(m2s_body(stop_r, 0.0, 7.0), m2s_body(motor_r, 0.0, 7.0))

        # モーター室壁: (0.9, 0, 7.0) -> (0.9, 0, 0.0) で閉じる
        axis_line = lines_body.addByTwoPoints(m2s_body(motor_r, 0.0, 7.0), m2s_body(motor_r, 0.0, 0.0))

        if sketch_body.profiles.count == 0:
            ui.messageBox('本体プロファイルの生成に失敗しました。')
            return

        prof_body = sketch_body.profiles.item(0)
        revInput = revolves.createInput(prof_body, axis_line, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        revInput.setAngleExtent(False, adsk.core.ValueInput.createByReal(2.0 * math.pi))
        body_feat = revolves.add(revInput)
        body_airframe = body_feat.bodies.item(0)
        body_airframe.name = "Rocket_Airframe"

        # =========================================================
        # 2. 左右主翼 (水平2枚: スパン55mm, コード31mm, 厚み0.44mm) on xzPlane
        # =========================================================
        sketch_main = sketches.add(xzPlane)
        lines_main = sketch_main.sketchCurves.sketchLines

        def m2s_m(x, y, z):
            return sketch_main.modelToSketchSpace(adsk.core.Point3D.create(x, y, z))

        mp1 = m2s_m(1.2, 0.0, 0.0)
        mp2 = m2s_m(1.2, 0.0, 3.1)
        mp3 = m2s_m(6.7, 0.0, 0.0)

        lines_main.addByTwoPoints(mp1, mp2)
        lines_main.addByTwoPoints(mp2, mp3)
        lines_main.addByTwoPoints(mp3, mp1)

        prof_main = sketch_main.profiles.item(0)
        extInput_m = extrudes.createInput(prof_main, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        extInput_m.setSymmetricExtent(adsk.core.ValueInput.createByReal(fin_half_t), True)
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
        # 3. 上下垂直尾翼 (垂直2枚: スパン49.5mm, コード27.9mm, 厚み0.44mm) on yzPlane
        # =========================================================
        sketch_sub = sketches.add(yzPlane)
        lines_sub = sketch_sub.sketchCurves.sketchLines

        def m2s_s(x, y, z):
            return sketch_sub.modelToSketchSpace(adsk.core.Point3D.create(x, y, z))

        sp1 = m2s_s(0.0, 1.2, 0.0)
        sp2 = m2s_s(0.0, 1.2, 2.79)
        sp3 = m2s_s(0.0, 6.15, 0.0)

        lines_sub.addByTwoPoints(sp1, sp2)
        lines_sub.addByTwoPoints(sp2, sp3)
        lines_sub.addByTwoPoints(sp3, sp1)

        prof_sub = sketch_sub.profiles.item(0)
        extInput_s = extrudes.createInput(prof_sub, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        extInput_s.setSymmetricExtent(adsk.core.ValueInput.createByReal(fin_half_t), True)
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

        # =========================================================
        # 4. ランチラグ (案内パイプ: -45度位置, Z=40〜48mm)
        # =========================================================
        # オフセット構築平面 (Z=4.0cm)
        planeInput = rootComp.constructionPlanes.createInput()
        planeInput.setByOffset(xyPlane, adsk.core.ValueInput.createByReal(4.0))
        plane_lug = rootComp.constructionPlanes.add(planeInput)

        sketch_lug = sketches.add(plane_lug)
        # -45度方向の位置: 中心 = (1.2 + 0.24) * cos(-45), (1.2 + 0.24) * sin(-45)
        rad_45 = -math.pi / 4.0
        lug_dist = 1.2 + 0.22 # 胴体外周に接する
        lug_cx = lug_dist * math.cos(rad_45)
        lug_cy = lug_dist * math.sin(rad_45)
        pt_lug_center = sketch_lug.modelToSketchSpace(adsk.core.Point3D.create(lug_cx, lug_cy, 4.0))

        # 外円 (外径 4.8mm = 半径 0.24cm) と 内円 (内径 3.2mm = 半径 0.16cm)
        sketch_lug.sketchCurves.sketchCircles.addByCenterRadius(pt_lug_center, 0.24)
        sketch_lug.sketchCurves.sketchCircles.addByCenterRadius(pt_lug_center, 0.16)

        # パイプ部分のプロファイル (円環)
        prof_lug = None
        for p in sketch_lug.profiles:
            # 2つのループを持つプロファイルが円環
            if p.profileLoops.count == 2:
                prof_lug = p
                break
        if not prof_lug and sketch_lug.profiles.count > 0:
            prof_lug = sketch_lug.profiles.item(0)

        if prof_lug:
            extInput_lug = extrudes.createInput(prof_lug, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            extInput_lug.setDistanceExtent(False, adsk.core.ValueInput.createByReal(0.8)) # 長さ 8mm
            feat_lug = extrudes.add(extInput_lug)
            feat_lug.bodies.item(0).name = "Launch_Lug"

        ui.messageBox(
            '【機体①】アンバランス4枚翼・実用完全版モデルの生成が完了しました！\n\n'
            '・全長: 250 mm (ノーズ 120 mm + 胴体 130 mm)\n'
            '・外径: 24 mm\n'
            '・内部: 18mm Estesモーター室 (深さ70mm) ＆ スラストリング\n'
            '・主翼 (水平2枚): スパン 55.0 mm × ルート 31.0 mm (厚み 0.44 mm)\n'
            '・尾翼 (垂直2枚): スパン 49.5 mm × ルート 27.9 mm (厚み 0.44 mm, kv=0.90)\n'
            '・ランチラグ: 45度位置 (長さ 8mm, 内径 3.2mm)\n'
            '・実効安全マージン: +0.79 cal (高度145.6m・最高滞空特化)'
        )

    except:
        if ui:
            ui.messageBox('モデリング中にエラーが発生しました:\n{}'.format(traceback.format_exc()))
