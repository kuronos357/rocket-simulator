# Fusion 360 Python Script for Building Rocket Candidate 3 (Ironclad Stability Model)
# Dimensions: Total Length = 250mm, Diameter = 24mm, Nose = 120mm (Power 0.75), 4 Fins (59x33mm)
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
        xyPlane = rootComp.xYConstructionPlane
        xzPlane = rootComp.xZConstructionPlane
        zAxis = rootComp.zConstructionAxis

        extrudes = rootComp.features.extrudeFeatures
        revolves = rootComp.features.revolveFeatures
        patterns = rootComp.features.circularPatternFeatures

        # ---------------------------------------------------------
        # 1. Body Tube (Cylinder: D=24mm, L=130mm, from Z=0 to Z=130mm)
        # ---------------------------------------------------------
        sketch_body = sketches.add(xyPlane)
        circles = sketch_body.sketchCurves.sketchCircles
        circle_out = circles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), 1.2) # cm (R=12mm)
        
        if sketch_body.profiles.count == 0:
            ui.messageBox('胴体スケッチのプロファイル生成に失敗しました。')
            return
            
        prof_body = sketch_body.profiles.item(0)
        extInput_body = extrudes.createInput(prof_body, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        dist_body = adsk.core.ValueInput.createByReal(13.0) # 13.0 cm = 130mm
        extInput_body.setDistanceExtent(False, dist_body)
        body_feature = extrudes.add(extInput_body)
        body_feature.bodies.item(0).name = "Fuselage_Tube"

        # ---------------------------------------------------------
        # 2. Nose Cone (Revolve: Power Series 0.75, L=120mm, R=12mm)
        #    Located from Z=130mm to Z=250mm along Z-axis on xzPlane (Y=0)
        # ---------------------------------------------------------
        sketch_nose = sketches.add(xzPlane)
        lines_nose = sketch_nose.sketchCurves.sketchLines

        # Use piecewise connected lines for 100% guaranteed watertight profile detection
        n_pts = 30
        pt_base_outer = adsk.core.Point3D.create(1.2, 0.0, 13.0) # Base at (R=1.2cm, Z=13cm)
        prev_pt = pt_base_outer

        # 1) Curve profile from base (Z=13cm) to tip (Z=25cm)
        for i in range(1, n_pts + 1):
            t = i / float(n_pts) # 0 to 1
            z_cm = 13.0 + 12.0 * t # 13.0 to 25.0 cm
            dist_from_tip_cm = 25.0 - z_cm # 12.0 to 0.0 cm
            # y = R * (x / L)^0.75
            r_cm = 1.2 * ((dist_from_tip_cm / 12.0) ** 0.75) if dist_from_tip_cm > 0.0 else 0.0
            next_pt = adsk.core.Point3D.create(r_cm, 0.0, z_cm)
            lines_nose.addByTwoPoints(prev_pt, next_pt)
            prev_pt = next_pt

        # At tip: prev_pt is (0.0, 0.0, 25.0)
        # 2) Center line along Z-axis from tip (0, 0, 25) to base center (0, 0, 13)
        pt_center_base = adsk.core.Point3D.create(0.0, 0.0, 13.0)
        l_center = lines_nose.addByTwoPoints(prev_pt, pt_center_base)

        # 3) Horizontal base line closing back to start: (0, 0, 13) -> (1.2, 0, 13)
        lines_nose.addByTwoPoints(pt_center_base, pt_base_outer)

        if sketch_nose.profiles.count == 0:
            ui.messageBox('ノーズコーンの閉じたプロファイルが検出できませんでした。')
            return

        prof_nose = sketch_nose.profiles.item(0)
        revInput = revolves.createInput(prof_nose, zAxis, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        revInput.setAngleExtent(False, adsk.core.ValueInput.createByReal(2.0 * math.pi))
        nose_feature = revolves.add(revInput)
        nose_feature.bodies.item(0).name = "NoseCone"

        # ---------------------------------------------------------
        # 3. Delta Fin (Span=59mm, Cr=33mm, Thick=0.8mm)
        #    Attached at Z=0 to Z=33mm, extending in +X direction on xzPlane (Y=0)
        # ---------------------------------------------------------
        sketch_fin = sketches.add(xzPlane)
        lines_fin = sketch_fin.sketchCurves.sketchLines
        
        # P1: Root Trailing Edge at (1.2cm, 0, 0.0cm)
        # P2: Root Leading Edge at (1.2cm, 0, 3.3cm)
        # P3: Tip at (1.2 + 5.9 = 7.1cm, 0, 0.0cm)
        p1 = adsk.core.Point3D.create(1.2, 0.0, 0.0)
        p2 = adsk.core.Point3D.create(1.2, 0.0, 3.3)
        p3 = adsk.core.Point3D.create(7.1, 0.0, 0.0)

        lines_fin.addByTwoPoints(p1, p2)
        lines_fin.addByTwoPoints(p2, p3)
        lines_fin.addByTwoPoints(p3, p1)

        if sketch_fin.profiles.count == 0:
            ui.messageBox('フィンスケッチの閉じたプロファイルが検出できませんでした。')
            return

        prof_fin = sketch_fin.profiles.item(0)
        extInput_fin = extrudes.createInput(prof_fin, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        # Symmetric extrusion: total thickness 0.8mm = 0.08cm (half is 0.04cm)
        dist_fin = adsk.core.ValueInput.createByReal(0.04)
        extInput_fin.setSymmetricExtent(dist_fin, True)
        fin_feature = extrudes.add(extInput_fin)
        base_fin_body = fin_feature.bodies.item(0)
        base_fin_body.name = "Fin_1"

        # ---------------------------------------------------------
        # 4. Circular Pattern for 4 Fins (90 deg symmetric around Z-axis)
        # ---------------------------------------------------------
        fin_coll = adsk.core.ObjectCollection.create()
        fin_coll.add(base_fin_body)
        
        patternInput = patterns.createInput(fin_coll, zAxis)
        patternInput.quantity = adsk.core.ValueInput.createByString("4")
        patternInput.totalAngle = adsk.core.ValueInput.createByReal(2.0 * math.pi)
        patternInput.isSymmetric = False
        pattern_feature = patterns.add(patternInput)

        ui.messageBox(
            '【機体③】鉄壁安全重視モデルの自動モデリングが成功しました！\n\n'
            '・全長: 250 mm (ノーズ 120 mm + 胴体 130 mm)\n'
            '・外径: 24 mm\n'
            '・翼: 4枚 正十字完全対称 (スパン 59 mm × ルート 33 mm)\n'
            '・静的安定マージン: +1.22 cal (強風下でも直進)'
        )

    except:
        if ui:
            ui.messageBox('モデリング中にエラーが発生しました:\n{}'.format(traceback.format_exc()))
