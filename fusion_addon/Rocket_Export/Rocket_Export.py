import adsk.core, adsk.fusion, traceback
import json
import os
import re
from datetime import datetime

DEFAULT_PROJECT_DIR = r"D:\1_Stuff\0_programming\0_Project\ロケットシミュレーター\export"

def parse_part_metadata(name):
    """
    オブジェクト名からパーツ種別やパラメータを自動抽出
    例:
      - Motor_C6-5 -> type: motor, motor_id: C6-5
      - Parachute_30cm -> type: parachute, diameter_cm: 30
      - Ballast_10g -> type: ballast, mass_g_override: 10
    """
    lower = name.lower()
    meta = {
        "part_type": "structure",
        "detected_params": {}
    }
    
    # 1. モーター (Engine / Motor)
    if "motor" in lower or "engine" in lower:
        meta["part_type"] = "motor"
        # C6-5, A8-3, D12-5, E9 などの型番パターンを抽出
        m = re.search(r'([A-Oa-o]\d+(?:-\d+)?)', name)
        if m:
            meta["detected_params"]["motor_id"] = m.group(1).upper()
        else:
            meta["detected_params"]["motor_id"] = "C6-5"
            
    # 2. パラシュート (Parachute / Chute)
    elif "chute" in lower or "parachute" in lower:
        meta["part_type"] = "parachute"
        meta["detected_params"]["horizontal_descent"] = True  # 横向き降下ギミック有効
        meta["detected_params"]["shape"] = "flat"  # デフォルト: flat
        # 30cm, 450mm などの寸法抽出
        m_cm = re.search(r'(\d+)\s*cm', lower)
        m_mm = re.search(r'(\d+)\s*mm', lower)
        if m_cm:
            meta["detected_params"]["diameter_cm"] = float(m_cm.group(1))
        elif m_mm:
            meta["detected_params"]["diameter_cm"] = float(m_mm.group(1)) / 10.0
        else:
            meta["detected_params"]["diameter_cm"] = 30.0

    # 3. ストリーマ (Streamer)
    elif "streamer" in lower or "ribbon" in lower:
        meta["part_type"] = "streamer"
        meta["detected_params"]["width_cm"] = 5.0
        meta["detected_params"]["length_cm"] = 100.0

    # 4. バラスト・重り (Ballast / Weight / Payload)
    elif "ballast" in lower or "weight" in lower or "payload" in lower:
        meta["part_type"] = "ballast"
        m = re.search(r'(\d+(?:\.\d+)?)\s*g', lower)
        if m:
            meta["detected_params"]["mass_g_override"] = float(m.group(1))

    return meta


def extract_body_data(body, parent_name="RootComponent"):
    """BRepBody から形状・物理プロパティを抽出"""
    if not body.isSolid:
        return None

    # BoundingBox (cm -> mm)
    bbox = body.boundingBox
    min_pt = [bbox.minPoint.x * 10.0, bbox.minPoint.y * 10.0, bbox.minPoint.z * 10.0]
    max_pt = [bbox.maxPoint.x * 10.0, bbox.maxPoint.y * 10.0, bbox.maxPoint.z * 10.0]
    size_mm = [
        round(max_pt[0] - min_pt[0], 3),
        round(max_pt[1] - min_pt[1], 3),
        round(max_pt[2] - min_pt[2], 3)
    ]
    center_mm = [
        round((min_pt[0] + max_pt[0]) / 2.0, 3),
        round((min_pt[1] + max_pt[1]) / 2.0, 3),
        round((min_pt[2] + max_pt[2]) / 2.0, 3)
    ]

    # 物理プロパティ (質量、重心、慣性モーメント)
    mass_g = 0.0
    com_mm = center_mm
    moi = {"Ixx": 0.0, "Iyy": 0.0, "Izz": 0.0, "Ixy": 0.0, "Iyz": 0.0, "Ixz": 0.0}
    mat_name = "Unknown"

    try:
        if body.material:
            mat_name = body.material.name

        props = body.physicalProperties
        mass_g = round(props.mass * 1000.0, 3)  # kg -> g
        com = props.centerOfMass
        com_mm = [round(com.x * 10.0, 3), round(com.y * 10.0, 3), round(com.z * 10.0, 3)]

        # 慣性モーメント (kg*cm^2 -> g*cm^2)
        res, ixx, iyy, izz, ixy, iyz, ixz = props.getXYZMomentsOfInertia()
        if res:
            moi = {
                "Ixx": round(ixx * 1000.0, 3),
                "Iyy": round(iyy * 1000.0, 3),
                "Izz": round(izz * 1000.0, 3),
                "Ixy": round(ixy * 1000.0, 3),
                "Iyz": round(iyz * 1000.0, 3),
                "Ixz": round(ixz * 1000.0, 3)
            }
    except:
        pass

    # 名前から種別を自動判定
    meta = parse_part_metadata(body.name)

    body_info = {
        "name": body.name,
        "parent": parent_name,
        "part_type": meta["part_type"],
        "material": mat_name,
        "is_visible": body.isVisible,
        "mass_g": mass_g,
        "mass_g_override": meta["detected_params"].get("mass_g_override", None),
        "center_of_mass_mm": {"x": com_mm[0], "y": com_mm[1], "z": com_mm[2]},
        "size_mm": {"x": size_mm[0], "y": size_mm[1], "z": size_mm[2]},
        "bbox_min_mm": {"x": round(min_pt[0], 3), "y": round(min_pt[1], 3), "z": round(min_pt[2], 3)},
        "bbox_max_mm": {"x": round(max_pt[0], 3), "y": round(max_pt[1], 3), "z": round(max_pt[2], 3)},
        "volume_cm3": round(body.volume, 4),
        "area_cm2": round(body.area, 4),
        "moments_of_inertia_g_cm2": moi,
        "custom_params": meta["detected_params"]
    }
    return body_info


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)

        if not design:
            ui.messageBox('アクティブな Fusion 360 デザインが見つかりません。', 'ロケット解析エクスポート')
            return

        rootComp = design.rootComponent
        doc_name = design.parentDocument.name if design.parentDocument else "Rocket"
        safe_doc_name = re.sub(r'[\\/*?:"<>|]', "_", doc_name)

        # 1. 出力先フォルダの確認 / 選択
        folder_dlg = ui.createFolderDialog()
        folder_dlg.title = "ロケットシミュレータ用データの保存先フォルダを選択"
        if os.path.exists(DEFAULT_PROJECT_DIR):
            folder_dlg.initialDirectory = DEFAULT_PROJECT_DIR
        
        dialog_res = folder_dlg.showDialog()
        if dialog_res != adsk.core.DialogResults.DialogOK:
            return
        
        export_dir = folder_dlg.folder
        if not os.path.exists(export_dir):
            os.makedirs(export_dir, exist_ok=True)

        stl_filename = f"{safe_doc_name}.stl"
        json_filename = f"{safe_doc_name}_params.json"
        stl_path = os.path.join(export_dir, stl_filename)
        json_path = os.path.join(export_dir, json_filename)

        # 2. STL のエクスポート実行
        exportMgr = design.exportManager
        stlOptions = exportMgr.createSTLExportOptions(rootComp, stl_path)
        stlOptions.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        stlOptions.isBinaryFormat = True
        exportMgr.execute(stlOptions)

        # 2b. STEP のエクスポート実行 (精密解析用)
        step_filename = f"{safe_doc_name}.step"
        step_path = os.path.join(export_dir, step_filename)
        try:
            stepOptions = exportMgr.createSTEPExportOptions(step_path, rootComp)
            exportMgr.execute(stepOptions)
        except:
            pass

        # 3. アセンブリ全体の物理プロパティ
        asm_props = rootComp.physicalProperties
        asm_com = asm_props.centerOfMass
        res, a_ixx, a_iyy, a_izz, a_ixy, a_iyz, a_ixz = asm_props.getXYZMomentsOfInertia()
        
        assembly_summary = {
            "total_mass_g": round(asm_props.mass * 1000.0, 3),
            "total_volume_cm3": round(asm_props.volume, 4),
            "total_area_cm2": round(asm_props.area, 4),
            "center_of_mass_mm": {
                "x": round(asm_com.x * 10.0, 3),
                "y": round(asm_com.y * 10.0, 3),
                "z": round(asm_com.z * 10.0, 3)
            },
            "moments_of_inertia_g_cm2": {
                "Ixx": round(a_ixx * 1000.0, 3),
                "Iyy": round(a_iyy * 1000.0, 3),
                "Izz": round(a_izz * 1000.0, 3)
            }
        }

        # 4. 全ボディの走査
        bodies_data = []

        # Root 直下のボディ
        for b in rootComp.bRepBodies:
            b_info = extract_body_data(b, "RootComponent")
            if b_info:
                bodies_data.append(b_info)

        # 各コンポーネント（Occurrences）下のボディ
        for occ in rootComp.allOccurrences:
            if not occ.isLightweight:
                for b in occ.bRepBodies:
                    b_info = extract_body_data(b, occ.name)
                    if b_info:
                        # コンポーネント全体の可視性も反映
                        b_info["is_visible"] = b_info["is_visible"] and occ.isVisible
                        bodies_data.append(b_info)

        # 5. JSON データの構築
        export_data = {
            "design_name": doc_name,
            "export_time": datetime.now().isoformat(),
            "stl_file": stl_filename,
            "step_file": step_filename,
            "units": {
                "length": "mm",
                "mass": "g",
                "volume": "cm3",
                "area": "cm2",
                "moments_of_inertia": "g*cm2"
            },
            "assembly_summary": assembly_summary,
            "bodies": bodies_data
        }

        # JSON ファイル書き出し
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        # 完了メッセージ
        msg = f"エクスポートが完了しました！\n\n" \
              f"・STLファイル: {stl_filename}\n" \
              f"・STEPファイル: {step_filename}\n" \
              f"・JSONパラメータ: {json_filename}\n" \
              f"・検出ボディ数: {len(bodies_data)} 個\n" \
              f"・総重量(CAD上): {assembly_summary['total_mass_g']} g\n\n" \
              f"保存先:\n{export_dir}"
        ui.messageBox(msg, 'ロケット解析エクスポート成功')

    except:
        if ui:
            ui.messageBox(f'エラーが発生しました:\n{traceback.format_exc()}', 'エクスポート失敗')
