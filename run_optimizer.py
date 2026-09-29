"""
Interactive Rocket Fin Optimizer CLI
Inversely calculates optimal fin dimensions to achieve desired stability margin.

Usage:
    python run_optimizer.py
    python run_optimizer.py --preset tsukuba --target-margin 1.2 --shape trapezoid
    python run_optimizer.py --preset v9 --target-margin 1.0
"""

import sys
import os
import argparse
from typing import Dict, Any, List

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim_engine.optimizer import RocketSpec, FinOptimizer


PRESETS = {
    "tsukuba": {
        "name": "つくば＿ロケット (軽量機体)",
        "spec": RocketSpec(
            total_length_mm=190.0,
            body_diameter_mm=22.0,
            nose_length_mm=60.0,
            tail_length_mm=0.0,
            wall_thickness_mm=0.4,
            material="PLA",
            motor_type="1/2A6-2",
            dry_mass_override_g=11.5,
            ballast_mass_g=0.0
        ),
        "arrangement": "airplane_3fin",
        "taper_ratio": 0.0 # 三角翼
    },
    "v9": {
        "name": "ロケット本体 v9 (アビオニクス中型機)",
        "spec": RocketSpec(
            total_length_mm=363.0,
            body_diameter_mm=46.6,
            nose_length_mm=113.0,
            tail_length_mm=0.0,
            wall_thickness_mm=0.4,
            material="PLA",
            motor_type="C6-5",
            dry_mass_override_g=50.0,
            ballast_mass_g=35.0, # AtomS3R + LiPo + TFカード
            ballast_z_mm=260.0
        ),
        "arrangement": "symmetric_3fin", # 120度対称3枚
        "taper_ratio": 0.0 # 三角翼
    }
}


def print_result_card(res: Dict[str, Any], arrangement: str, shape_type: str, target_margin: float):
    print("\n" + "=" * 68)
    print(f"       [ 最適フィン寸法 逆算結果 (目標マージン: {target_margin:+.2f} cal) ]")
    print("=" * 68)
    
    print("\n【 1. Fusion 360 スケッチ入力寸法 】")
    print("-" * 68)
    shape_desc = "直角三角翼 (デルタ翼)" if res.get('tip_chord_mm', 0) == 0 else ("楕円翼" if shape_type == "ellipse" else "台形翼")
    
    th = res.get('theta_deg', 30.0)
    is_4 = res.get('is_4fin', False)
    vs = res.get('v_scale', 1.0)
    
    if is_4:
        arr_desc = f"4枚十字翼 (+型配置, 仰角 0°)" if th == 0 else f"4枚X字翼 (傾斜 {th:.1f}°)"
    elif th == 0.0:
        arr_desc = f"飛行機型T字翼 (水平主翼 0° + 垂直尾翼 1枚)"
    elif abs(th - 30.0) < 0.1 and abs(vs - 1.0) < 0.05:
        arr_desc = "対称3枚翼 (120°等間隔配置)"
    else:
        arr_desc = f"3枚V字/逆Y字翼 (水平から傾斜 {th:.1f}°, 尾翼比率 {vs:.2f})"
        
    print(f"  - 翼の形状タイプ         : {shape_desc}")
    print(f"  - フィン配置構成         : {arr_desc}")
    print(f"  - 主翼 取り付け傾斜角(θ) : 水平から {th:4.1f}° (左右対称2枚)")
    print(f"  - 主翼 スパン (張り出し) : {res['span_mm']:5.1f} mm  (機体全幅: {res['total_width_mm']:.1f} mm)")
    print(f"  - 主翼 根元コード長 (高) : {res['root_chord_mm']:5.1f} mm")
    if shape_type != "ellipse":
        print(f"  - 主翼 翼端コード長       : {res['tip_chord_mm']:5.1f} mm")
    print(f"  - 主翼 後縁の配置         : ロケット最後端と直角 (90° 面一)")
    
    if res.get("v_span_mm") is not None:
        v_label = "垂直尾翼 (上下2枚)" if is_4 else "垂直尾翼 (12時方向 1枚)"
        print(f"\n  [ {v_label} の寸法 (主翼比 {vs:.2f}) ]")
        print(f"    * 尾翼 スパン (高さ)   : {res['v_span_mm']:5.1f} mm")
        print(f"    * 尾翼 根元コード長     : {res['v_cr_mm']:5.1f} mm")
        if shape_type != "ellipse":
            print(f"    * 尾翼 翼端コード長     : {res.get('v_ct_mm', 0.0):5.1f} mm")
            
    print("\n【 2. 安定性 & 質量バランス予測 】")
    print("-" * 68)
    print(f"  - フィン単体重量 (全枚数) : {res['fin_mass_g']:5.2f} g (片面面積: {res['fin_area_1side_cm2']:.1f} cm²)")
    print(f"  - 点火時 全備質量         : {res['total_mass_g']:5.1f} g")
    print(f"  - 重心 (CG)               : {res['cg_mm']:5.1f} mm (テールから)")
    print(f"  - 空力中心 (CP)           : {res['cp_mm']:5.1f} mm (テールから)")
    print(f"  - 総合実効静安定マージン  : {res['margin_cal']:+5.2f} cal ({res['margin_mm']:+5.1f} mm) -> [OK] 安定合格")
    print(f"    * Pitch 安定マージン    : {res['pitch_margin_cal']:+5.2f} cal")
    print(f"    * Yaw 安定マージン      : {res['yaw_margin_cal']:+5.2f} cal")

    print("\n【 3. フライト性能予測 】")
    print("-" * 68)
    print(f"  - 抗力係数 (Cd)           : {res['Cd']:.3f}")
    print(f"  - 最高到達高度            : 約 {res['apogee_m']:.1f} m")
    print(f"  - 最高速度                : 約 {res['max_vel_km_h']:.1f} km/h")
    if 'total_flight_time_s' in res:
        print(f"  - 総滞空時間 (Hang Time)  : 約 {res['total_flight_time_s']:.1f} 秒")
        print(f"  - 終端降下速度            : 約 {res.get('v_descent_m_s', 0):.1f} m/s")
    print("=" * 68 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Rocket Fin Geometry Inverse Optimizer")
    parser.add_argument("--preset", choices=["tsukuba", "v9"], help="Load predefined rocket preset")
    parser.add_argument("--target-margin", type=float, default=1.2, help="Target stability margin in calibers (default: 1.2)")
    parser.add_argument("--shape", choices=["trapezoid", "ellipse"], default="trapezoid", help="Fin shape type (default: trapezoid)")
    parser.add_argument("--taper", type=str, default="0.0", help="Taper ratio(s) to optimize over, comma-separated (default: '0.0' for delta wing)")
    parser.add_argument("--thickness", type=float, default=0.4, help="Fin thickness in mm (default: 0.4)")
    parser.add_argument("--arrangement", default="auto", help="Fin arrangement ('auto', 'airplane_3fin', 'symmetric_3fin', 'symmetric_4fin')")
    parser.add_argument("--theta", type=str, default=None, help="Dihedral angle(s) in degrees (e.g. '0,15,30' or 'auto')")
    parser.add_argument("--v-scale", type=str, default=None, help="Vertical fin scale(s) (e.g. '0.6,0.8,1.0' or 'auto')")
    parser.add_argument("--ballast", type=float, default=0.0, help="Nose ballast mass in grams (default: 0.0)")
    
    parser.add_argument("--mdo", action="store_true", help="Run Multi-Disciplinary Optimization (MDO) over full body parameters")
    
    parser.add_argument("--length", type=str, default="250-380-10", help="Total length search range 'min-max-step' or value (MDO only, min 250 for JAR)")
    parser.add_argument("--nose", type=str, default="50-100-10", help="Nose length search range 'min-max-step' or value (MDO only)")
    parser.add_argument("--tail", type=str, default="0", help="Tail length list '0,10' or range (MDO only)")
    parser.add_argument("--shape-n", type=str, default="0.75", help="Nose shape parameter 'n' (1.0=Cone, 0.75=Ogive, 0.5=Parabola)")
    
    parser.add_argument("--optimize-for", type=str, choices=["apogee", "time"], default="time", help="Objective function (apogee = 最高高度, time = 滞空時間)")
    parser.add_argument("--rec-area", type=float, default=62.5, help="リカバリー展開面積 cm^2 (JAR規則最小 25x250mm = 62.5cm2)")
    parser.add_argument("--rec-cd", type=float, default=0.25, help="リカバリーの抗力係数 (Cd) ストリーマーなら0.2~0.3")
    parser.add_argument("--fin-count", type=str, default="3", help="Number of fins for symmetric arrangement")
    parser.add_argument("--horizontal-descent", action="store_true", default=True, help="Calculate drag assuming the rocket falls horizontally")
    
    parser.add_argument("--diameter", type=float, default=24.0, help="Body diameter in mm (default: 24.0 for JAR rules)")
    parser.add_argument("--wall", type=float, default=0.4, help="Wall thickness in mm (default: 0.4)")
    parser.add_argument("--infill", type=float, default=0.02, help="Infill ratio (0.0 to 1.0, default: 0.02)")
    
    args = parser.parse_args()
    
    def parse_range(arg_str: str, default_step: float = 10.0) -> List[float]:
        arg_str = arg_str.strip()
        if "," in arg_str:
            return [float(x.strip()) for x in arg_str.split(",")]
        elif "-" in arg_str:
            parts = [float(x) for x in arg_str.split("-")]
            if len(parts) == 2:
                parts.append(default_step)
            if len(parts) == 3:
                start, end, step = parts
                res = []
                v = start
                while v <= end:
                    res.append(v)
                    v += step
                return res
        return [float(arg_str)]
    
    # パース
    try:
        taper_ratios = parse_range(args.taper, 0.1)
        length_range = parse_range(args.length, 10.0)
        nose_range = parse_range(args.nose, 10.0)
        tail_range = parse_range(args.tail, 10.0)
        shape_n_range = parse_range(args.shape_n, 0.25)
    except ValueError as e:
        print("❌ 引数の指定が不正です。カンマ区切りまたは min-max-step 形式で数値を指定してください。")
        sys.exit(1)
    
    # プリセットが指定されている場合
    if args.preset:
        p = PRESETS[args.preset]
        spec = p["spec"]
        arrangement = args.arrangement or p["arrangement"]
        taper_ratios = taper_ratios if args.taper != "0.0" else [p.get("taper_ratio", 0.0)]
        print(f"Loaded Preset: {p['name']}")
    else:
        # デフォルトは つくば＿ロケット
        p = PRESETS["tsukuba"]
        spec = p["spec"]
        arrangement = args.arrangement or p["arrangement"]
        print("Using Default: つくば＿ロケット")

    if args.mdo:
        from sim_engine.mdo import FullRocketOptimizer
        print("\n" + "=" * 65)
        print("🚀 [ MDO : 全体最適化モード ] を開始します...")
        print("=" * 65)
        
        # MDOモード時は物理ベース質量計算を強制するため override を解除
        spec.dry_mass_override_g = None
        
        # ユーザー指定のCLIパラメータを適用
        spec.body_diameter_mm = args.diameter
        spec.wall_thickness_mm = args.wall
        spec.infill_ratio = args.infill
        spec.recovery_area_cm2 = args.rec_area
        spec.recovery_cd = args.rec_cd
        spec.descent_horizontal = args.horizontal_descent
        spec.ballast_mass_g = args.ballast
        spec.motor_type = "1/2A6-2" # 固定要求
        
        mdo = FullRocketOptimizer(spec)
        
        # 候補とするフィン構成
        if args.arrangement == "auto":
            candidate_arrangements = ["auto", "airplane_3fin", "symmetric_3fin", "symmetric_4fin"]
        elif "," in args.arrangement:
            candidate_arrangements = [a.strip() for a in args.arrangement.split(",")]
        else:
            candidate_arrangements = [args.arrangement]
            
        import itertools
        from sim_engine.mdo import FullRocketOptimizer as mdo_class
        all_results = []
        for arr in candidate_arrangements:
            if arr == "auto":
                desc = "全自動探索 (任意傾斜角θ + 尾翼比率kv)"
            elif arr == "airplane_3fin":
                desc = "飛行機型T字翼 (水平主翼0° + 垂直尾翼)"
            elif arr in ["symmetric_3fin", "3"]:
                desc = "対称3枚翼 (120°等間隔)"
            elif arr in ["symmetric_4fin", "4"]:
                desc = "対称4枚翼 (90°十字)"
            else:
                desc = f"配置: {arr}"
            print(f"探索空間 ({desc}) - 全長: {length_range[0]}...{length_range[-1]}mm, ノーズ長: {nose_range[0]}...{nose_range[-1]}mm, テール長: {tail_range[0]}...{tail_range[-1]}mm, 形状n: {shape_n_range}")
            results = mdo.optimize_design(
                length_range=length_range,
                nose_range=nose_range,
                tail_range=tail_range,
                shape_n_range=shape_n_range,
                target_margin_cal=args.target_margin,
                arrangement=arr,
                shape_type=args.shape,
                taper_ratios=taper_ratios,
                fin_thickness_mm=args.thickness,
                optimize_for=args.optimize_for
            )
            all_results.extend(results)
            
        results = all_results
        
        if not results:
            print("❌ 条件を満たす組み合わせが見つかりませんでした。")
            sys.exit(1)
            
        print(f"\n有効な設計パターン数: {len(results)} 件")
        
        # 特徴別ピックアップ (Hall of Fame)
        def print_top(sorted_list, title):
            print(f"\n■ {title} トップ3")
            for i, r in enumerate(sorted_list[:3]):
                b = r["body"]
                f = r["fins"]
                print(f" {i+1}位: 全長 {b['total_length_mm']}mm | ノーズ {b['nose_length_mm']}mm | 形状n {b['nose_shape_n']} | テール {b['tail_length_mm']}mm "
                      f"-> 質量: {f['total_mass_g']}g | マージン: {f['margin_cal']:+.2f}cal | 滞空: {f['total_flight_time_s']}秒 | 高度: {f['apogee_m']}m")
        
        # 1. 滞空時間
        time_sorted = sorted(results, key=lambda x: x["fins"]["total_flight_time_s"], reverse=True)
        print_top(time_sorted, "最長滞空時間")
        
        # 2. 最高高度
        apogee_sorted = sorted(results, key=lambda x: x["fins"]["apogee_m"], reverse=True)
        print_top(apogee_sorted, "最高到達高度")
        
        # 3. 最軽量 (マージンを満たしつつ)
        light_sorted = sorted(results, key=lambda x: x["fins"]["total_mass_g"])
        print_top(light_sorted, "最軽量設計")
        
        # 4. 最も安定 (マージン大)
        margin_sorted = sorted(results, key=lambda x: x["fins"]["margin_cal"], reverse=True)
        print_top(margin_sorted, "高安定設計 (マージン最大)")
        
        # 総合1位の詳細を出力
        best_overall = time_sorted[0] if args.optimize_for == "time" else apogee_sorted[0]
        
        b = best_overall["body"]
        obj_str = "最高到達高度" if args.optimize_for == "apogee" else "最長滞空時間"
        print(f"\n★★★ 総合1位の詳細 ({obj_str}) ★★★")
        print(f"[ 機体寸法の最適解 ]")
        print(f"  - 全長        : {b['total_length_mm']} mm")
        print(f"  - ノーズ長さ  : {b['nose_length_mm']} mm")
        print(f"  - ノーズ形状 n: {b['nose_shape_n']} (1.0=コーン, 0.5=パラボラ)")
        print(f"  - ボートテール: {b['tail_length_mm']} mm")
        print(f"  - 機体乾燥質量: {b['airframe_mass_g']:.1f} g (※フィン除く)")
        
        fin_arr = best_overall["fins"].get("arrangement", arrangement)
        print_result_card(best_overall["fins"], arrangement=fin_arr, shape_type=args.shape, target_margin=args.target_margin)
        
        # グラフ生成
        try:
            import matplotlib.pyplot as plt
            masses = [r["fins"]["total_mass_g"] for r in results]
            times = [r["fins"]["total_flight_time_s"] for r in results]
            apogees = [r["fins"]["apogee_m"] for r in results]
            margins = [r["fins"]["margin_cal"] for r in results]
            
            plt.figure(figsize=(10, 6))
            if args.optimize_for == "time":
                sc = plt.scatter(masses, times, c=margins, cmap="viridis", alpha=0.7, edgecolors="k")
                plt.ylabel("Hang Time [s]")
                plt.title("Mass vs Hang Time (Color: Stability Margin)")
            else:
                sc = plt.scatter(masses, apogees, c=margins, cmap="plasma", alpha=0.7, edgecolors="k")
                plt.ylabel("Apogee [m]")
                plt.title("Mass vs Apogee (Color: Stability Margin)")
                
            plt.xlabel("Total Launch Mass [g]")
            plt.colorbar(sc, label="Static Margin [cal]")
            plt.grid(True, linestyle="--", alpha=0.6)
            
            out_file = "mdo_scatter.png"
            plt.savefig(out_file, dpi=150, bbox_inches="tight")
            print(f"📊 散布図グラフを保存しました: {os.path.abspath(out_file)}")
            
        except ImportError:
            print("matplotlib がインストールされていないため、グラフの保存をスキップしました。")
    else:
        spec.body_diameter_mm = args.diameter
        spec.ballast_mass_g = args.ballast
        spec.recovery_area_cm2 = args.rec_area
        spec.recovery_cd = args.rec_cd
        spec.descent_horizontal = args.horizontal_descent
        
        opt = FinOptimizer(spec)
        
        theta_arg = parse_range(args.theta) if (args.theta and args.theta != "auto") else None
        v_scale_arg = parse_range(args.v_scale) if (args.v_scale and args.v_scale != "auto") else None
        
        print(f"最適化を実行中... (目標マージン: {args.target_margin:+.2f} cal, 形状: {args.shape}, 探索テーパー比: {taper_ratios})")
        res = opt.optimize(
            target_margin_cal=args.target_margin,
            arrangement=arrangement,
            shape_type=args.shape,
            taper_ratio=taper_ratios,
            fin_thickness_mm=args.thickness,
            theta_deg=theta_arg,
            v_scale=v_scale_arg
        )
        
        if res:
            res_arr = res.get("arrangement", arrangement)
            print_result_card(res, arrangement=res_arr, shape_type=args.shape, target_margin=args.target_margin)
        else:
            print("❌ 条件を満たすフィン寸法が見つかりませんでした。胴体長さやバラスト重量を見直してください。")


if __name__ == "__main__":
    main()
