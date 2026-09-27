import numpy as np

# 決定版推奨モデル: 全長 L = 225 mm (250mm制限内で完璧な +1.05 cal を達成)
# モーター後端面中心を原点 (0, 0, 0) とする。
# X: 左右 (3時 = +X, 9時 = -X)
# Y: 飛行軸 (後端 = 0, 先端 = +225)
# Z: 上下 (12時 = +Z, 6時 = -Z)

L = 225.0
R_body = 11.0 # 胴体半径

# --- 1. 3時フィン (X > 0, Z = 0) ---
# 根元: Y=0 から Y=45 (cr = 45mm)
# 翼端: スパン S = 36mm (X = 11 + 36 = 47mm)
# 翼端コード: ct = 18mm (Y=0 から Y=18)
# T字エンドプレート: 翼端 X=47mm において、Z方向に +/- 5mm (幅10mm)
fin_3oclock = {
    "root_leading_edge": (R_body, 45.0, 0.0),
    "root_trailing_edge": (R_body, 0.0, 0.0),
    "tip_leading_edge": (R_body + 36.0, 18.0, 0.0),
    "tip_trailing_edge": (R_body + 36.0, 0.0, 0.0),
    "t_plate_z_extent": (-5.0, 5.0)
}

# --- 2. 9時フィン (X < 0, Z = 0) ---
fin_9oclock = {
    "root_leading_edge": (-R_body, 45.0, 0.0),
    "root_trailing_edge": (-R_body, 0.0, 0.0),
    "tip_leading_edge": (-(R_body + 36.0), 18.0, 0.0),
    "tip_trailing_edge": (-(R_body + 36.0), 0.0, 0.0),
    "t_plate_z_extent": (-5.0, 5.0)
}

# --- 3. 12時フィン (X = 0, Z > 0) ---
# 根元: Y=0 から Y=35 (cr = 35mm)
# 翼端: スパン S = 24mm (Z = 11 + 24 = 35mm)
# 翼端コード: ct = 15mm (Y=0 から Y=15)
# T字エンドプレート: 翼端 Z=35mm において、X方向に +/- 4mm (幅8mm)
fin_12oclock = {
    "root_leading_edge": (0.0, 35.0, R_body),
    "root_trailing_edge": (0.0, 0.0, R_body),
    "tip_leading_edge": (0.0, 15.0, R_body + 24.0),
    "tip_trailing_edge": (0.0, 0.0, R_body + 24.0),
    "t_plate_x_extent": (-4.0, 4.0)
}

# 胴体分割
# モーター室: Y = 0 ~ 70 mm
# ランチラグ: Y = 40 ~ 47 mm (Z = -11mm, 6時側)
# ストリーマ格納庫: Y = 73 ~ 175 mm (長さ約 102mm, 容積約 8.5~9 cm3)
# ノーズコーン (蓋): Y = 170 ~ 225 mm (長さ 55mm)

print("=== Recommended Final Architecture (L = 225 mm) ===")
print(f"Total Length: {L} mm (Margin from 250mm limit: 25 mm)")
print(f"Fuselage Tube: Y = 0 to 170 mm")
print(f"Nose Cone / Hatch: Y = 170 to 225 mm (Length = 55 mm)\n")

print("--- 3時フィン (X > 0) ---")
for k, v in fin_3oclock.items():
    print(f"  {k}: {v}")

print("\n--- 9時フィン (X < 0) ---")
for k, v in fin_9oclock.items():
    print(f"  {k}: {v}")

print("\n--- 12時フィン (Z > 0) ---")
for k, v in fin_12oclock.items():
    print(f"  {k}: {v}")
