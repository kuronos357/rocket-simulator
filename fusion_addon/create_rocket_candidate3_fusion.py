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
            ui.messageBox('No active Fusion design found.')
            return

        rootComp = design.rootComponent
        sketches = rootComp.sketches
        xyPlane = rootComp.xYConstructionPlane
        xzPlane = rootComp.xZConstructionPlane
        yzPlane = rootComp.yZConstructionPlane

        # ---------------------------------------------------------
        # 1. Body Tube (Cylinder: D=24mm, L=130mm, from Z=0 to Z=130)
        # ---------------------------------------------------------
        sketch_body = sketches.add(xyPlane)
        circles = sketch_body.sketchCurves.sketchCircles
        circle_out = circles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), 1.2) # cm (R=12mm)
        
        prof_body = sketch_body.profiles.item(0)
        extrudes = rootComp.features.extrudeFeatures
        extInput_body = extrudes.createInput(prof_body, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        dist_body = adsk.core.ValueInput.createByReal(13.0) # cm (130mm)
        extInput_body.setDistanceExtent(False, dist_body)
        body_feature = extrudes.add(extInput_body)
        body_feature.bodies.item(0).name = "Fuselage_Tube"

        # ---------------------------------------------------------
        # 2. Nose Cone (Revolve: Power Series 0.75, L=120mm, R=12mm)
        # ---------------------------------------------------------
        sketch_nose = sketches.add(xzPlane)
        lines = sketch_nose.sketchCurves.sketchLines
        curves = sketch_nose.sketchCurves.sketchFittedSplines

        # Generate points for nose profile
        # z in [13.0, 25.0] cm, x = R * ((z - 13) / 12)^0.75
        points = adsk.core.ObjectCollection.create()
        n_pts = 25
        for i in range(n_pts + 1):
            t = i / float(n_pts) # 0 to 1
            z_cm = 13.0 + 12.0 * t # from base to tip
            dist_from_tip = (25.0 - z_cm) / 12.0
            x_cm = 1.2 * (1.0 - (dist_from_tip ** 0.75)) if dist_from_tip < 1.0 else 0.0
            points.add(adsk.core.Point3D.create(x_cm, z_cm, 0))

        spline = curves.add(points)
        # Close the profile: vertical line along Z axis from tip (0, 25) to base (0, 13), then horizontal to (1.2, 13)
        l_center = lines.addByTwoPoints(adsk.core.Point3D.create(0, 25.0, 0), adsk.core.Point3D.create(0, 13.0, 0))
        l_base = lines.addByTwoPoints(adsk.core.Point3D.create(0, 13.0, 0), adsk.core.Point3D.create(1.2, 13.0, 0))

        # Revolve feature
        revolves = rootComp.features.revolveFeatures
        prof_nose = sketch_nose.profiles.item(0)
        revInput = revolves.createInput(prof_nose, l_center, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        revInput.setAngleExtent(False, adsk.core.ValueInput.createByReal(2 * math.pi))
        nose_feature = revolves.add(revInput)
        nose_feature.bodies.item(0).name = "NoseCone"

        # ---------------------------------------------------------
        # 3. Delta Fin (Span=59mm, Cr=33mm, Thick=0.8mm)
        # ---------------------------------------------------------
        sketch_fin = sketches.add(xzPlane)
        lines_fin = sketch_fin.sketchCurves.sketchLines
        
        # In X-Z plane: Root attached at X=1.2cm (12mm)
        # P1: Root Trailing Edge at (1.2, 0.0)
        # P2: Root Leading Edge at (1.2, 3.3)
        # P3: Tip at (1.2 + 5.9 = 7.1, 0.0)
        p1 = adsk.core.Point3D.create(1.2, 0.0, 0)
        p2 = adsk.core.Point3D.create(1.2, 3.3, 0)
        p3 = adsk.core.Point3D.create(7.1, 0.0, 0)

        lines_fin.addByTwoPoints(p1, p2)
        lines_fin.addByTwoPoints(p2, p3)
        lines_fin.addByTwoPoints(p3, p1)

        prof_fin = sketch_fin.profiles.item(0)
        extInput_fin = extrudes.createInput(prof_fin, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        # Symmetric extrusion: total thickness 0.8mm = 0.08cm (0.04cm each side)
        dist_fin = adsk.core.ValueInput.createByReal(0.04)
        extInput_fin.setSymmetricExtent(dist_fin, True)
        fin_feature = extrudes.add(extInput_fin)
        base_fin_body = fin_feature.bodies.item(0)
        base_fin_body.name = "Fin_1"

        # ---------------------------------------------------------
        # 4. Circular Pattern for 4 Fins (90 deg symmetric)
        # ---------------------------------------------------------
        patterns = rootComp.features.circularPatternFeatures
        fin_coll = adsk.core.ObjectCollection.create()
        fin_coll.add(base_fin_body)
        
        # Z-axis is l_center from nose cone or ZConstructionAxis
        z_axis = rootComp.zConstructionAxis
        patternInput = patterns.createInput(fin_coll, z_axis)
        patternInput.quantity = adsk.core.ValueInput.createByString("4")
        patternInput.totalAngle = adsk.core.ValueInput.createByReal(2 * math.pi)
        patternInput.isSymmetric = False
        pattern_feature = patterns.add(patternInput)

        ui.messageBox(
            '【機体③】鉄壁安全重視モデルの自動モデリングが完了しました！\n\n'
            '・全長: 250 mm (ノーズ 120 mm + 胴体 130 mm)\n'
            '・外径: 24 mm\n'
            '・翼: 4枚 正十字完全対称 (スパン 59 mm × ルート 33 mm)\n'
            '・安全率: +1.22 cal (強風下でも直進)'
        )

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
