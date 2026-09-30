"""
Generate OpenRocket (.ork) models for Setting A and Setting B.
- Setting A: 3-fin Asymmetric Inverted-Y (Theta=35 deg, V-scale=0.70)
- Setting B: 4-fin Symmetric Cross (+)
Streamer: 50 x 500 mm (Ripstop nylon / Mylar, 1.27 g)
Nose: 125.0 mm (Power n=0.75, Wall=0.4 mm)
Body: 125.0 mm (Outer D=24.0 mm, Wall=0.4 mm)
Motor: Estes 1/2A6-2
"""

import os
import uuid
import zipfile

def make_uuid():
    return str(uuid.uuid4())

def build_ork_xml(
    rocket_name,
    total_length_mm,
    nose_len_mm,
    body_len_mm,
    radius_mm,
    fin_sets,
    streamer_len_mm=500.0,
    streamer_width_mm=50.0,
    streamer_mass_g=1.27,
    motor_desc="Estes 1/2A6",
    motor_delay=2.0,
    mass_override_g=None,
    cg_override_from_tip_mm=None,
    color_rgb=(44, 160, 44),
    designer="Antigravity MDO Optimizer"
):
    rocket_id = make_uuid()
    stage_id = make_uuid()
    config_id = make_uuid()
    nose_id = make_uuid()
    body_id = make_uuid()
    mount_id = make_uuid()
    streamer_id = make_uuid()

    nose_l_m = nose_len_mm / 1000.0
    body_l_m = body_len_mm / 1000.0
    radius_m = radius_mm / 1000.0

    fin_xml_blocks = []
    for f in fin_sets:
        fin_id = make_uuid()
        f_count = f.get('count', 1)
        f_span_m = f['span_mm'] / 1000.0
        f_root_m = f['root_chord_mm'] / 1000.0
        f_tip_m = f.get('tip_chord_mm', 0.0) / 1000.0
        f_sweep_m = f.get('sweep_mm', f['root_chord_mm'] - f.get('tip_chord_mm', 0.0)) / 1000.0
        f_thick_m = f.get('thickness_mm', 0.4) / 1000.0
        f_rot = f.get('rotation_deg', 0.0)
        f_name = f.get('name', 'Fins')
        f_color = f.get('color_rgb', color_rgb)

        fin_xml = f"""
              <trapezoidfinset>
                <name>{f_name}</name>
                <id>{fin_id}</id>
                <appearance>
                  <paint red="{f_color[0]}" green="{f_color[1]}" blue="{f_color[2]}" alpha="255"/>
                  <shine>0.5</shine>
                </appearance>
                <instancecount>{f_count}</instancecount>
                <fincount>{f_count}</fincount>
                <radiusoffset method="surface">0.0</radiusoffset>
                <angleoffset method="relative">{f_rot}</angleoffset>
                <rotation>{f_rot}</rotation>
                <axialoffset method="bottom">0.0</axialoffset>
                <position type="bottom">0.0</position>
                <finish>normal</finish>
                <material type="bulk" density="1240.0" group="Plastics">PLA (polylactide)</material>
                <thickness>{f_thick_m}</thickness>
                <crosssection>square</crosssection>
                <cant>0.0</cant>
                <filletradius>0.0</filletradius>
                <filletmaterial type="bulk" density="1240.0" group="Plastics">PLA (polylactide)</filletmaterial>
                <rootchord>{f_root_m}</rootchord>
                <tipchord>{f_tip_m}</tipchord>
                <sweeplength>{f_sweep_m}</sweeplength>
                <height>{f_span_m}</height>
              </trapezoidfinset>"""
        fin_xml_blocks.append(fin_xml)

    all_fins_xml = "\n".join(fin_xml_blocks)

    override_xml = ""
    if mass_override_g is not None and cg_override_from_tip_mm is not None:
        mass_kg = mass_override_g / 1000.0
        cg_m = cg_override_from_tip_mm / 1000.0
        override_xml = f"""
        <overridemass>{mass_kg}</overridemass>
        <overridecg>{cg_m}</overridecg>
        <overridesubcomponents>true</overridesubcomponents>"""

    xml = f"""<?xml version='1.0' encoding='utf-8'?>
<openrocket version="1.10" creator="OpenRocket 24.12">
  <rocket>
    <name>{rocket_name}</name>
    <id>{rocket_id}</id>
    <axialoffset method="absolute">0.0</axialoffset>
    <position type="absolute">0.0</position>
    <designer>{designer}</designer>
    <designtype>competition</designtype>
    <motorconfiguration configid="{config_id}" default="true">
      <stage number="0" active="true"/>
    </motorconfiguration>
    <referencetype>maximum</referencetype>

    <subcomponents>
      <stage>
        <name>Sustainer</name>
        <id>{stage_id}</id>{override_xml}

        <subcomponents>
          <nosecone>
            <name>Nose cone (Power n=0.75)</name>
            <id>{nose_id}</id>
            <appearance>
              <paint red="{color_rgb[0]}" green="{color_rgb[1]}" blue="{color_rgb[2]}" alpha="255"/>
              <shine>0.6</shine>
            </appearance>
            <finish>normal</finish>
            <material type="bulk" density="1240.0" group="Plastics">PLA (polylactide)</material>
            <length>{nose_l_m}</length>
            <thickness>0.0004</thickness>
            <shape>power</shape>
            <shapeparameter>0.75</shapeparameter>
            <aftradius>{radius_m}</aftradius>
            <aftshoulderradius>{radius_m - 0.0004}</aftshoulderradius>
            <aftshoulderlength>0.015</aftshoulderlength>
            <aftshoulderthickness>0.0004</aftshoulderthickness>
            <aftshouldercapped>false</aftshouldercapped>
            <isflipped>false</isflipped>
          </nosecone>

          <bodytube>
            <name>Body tube (24mm)</name>
            <id>{body_id}</id>
            <appearance>
              <paint red="245" green="245" blue="245" alpha="255"/>
              <shine>0.4</shine>
            </appearance>
            <finish>normal</finish>
            <material type="bulk" density="1240.0" group="Plastics">PLA (polylactide)</material>
            <length>{body_l_m}</length>
            <thickness>0.0004</thickness>
            <radius>auto {radius_m}</radius>

            <subcomponents>
              <innertube>
                <name>Motor Mount (18mm Standard)</name>
                <id>{mount_id}</id>
                <appearance>
                  <paint red="130" green="90" blue="50" alpha="255"/>
                  <shine>0.0</shine>
                </appearance>
                <axialoffset method="bottom">0.0</axialoffset>
                <position type="bottom">0.0</position>
                <material type="bulk" density="680.0" group="PaperProducts">Cardboard</material>
                <length>0.07</length>
                <radialposition>0.0</radialposition>
                <radialdirection>0.0</radialdirection>
                <outerradius>0.009</outerradius>
                <thickness>0.0005</thickness>
                <clusterconfiguration>single</clusterconfiguration>
                <clusterscale>1.0</clusterscale>
                <clusterrotation>0.0</clusterrotation>
                <motormount>
                  <ignitionevent>automatic</ignitionevent>
                  <ignitiondelay>0.0</ignitiondelay>
                  <overhang>0.003</overhang>
                  <motor configid="{config_id}">
                    <type>single</type>
                    <manufacturer>Estes</manufacturer>
                    <designation>1/2A6</designation>
                    <diameter>0.018</diameter>
                    <length>0.07</length>
                    <delay>{motor_delay}</delay>
                  </motor>
                  <ignitionconfiguration configid="{config_id}">
                    <ignitionevent>automatic</ignitionevent>
                    <ignitiondelay>0.0</ignitiondelay>
                  </ignitionconfiguration>
                </motormount>
              </innertube>

              <streamer>
                <name>Recovery Streamer (50x500mm)</name>
                <id>{streamer_id}</id>
                <axialoffset method="top">0.02</axialoffset>
                <position type="top">0.02</position>
                <packedlength>0.03</packedlength>
                <packedradius>{radius_m - 0.002}</packedradius>
                <radialposition>0.0</radialposition>
                <radialdirection>0.0</radialdirection>
                <cd>auto</cd>
                <material type="surface" density="0.0508" group="Fabrics">Ripstop nylon</material>
                <deployevent>apogee</deployevent>
                <deployaltitude>200.0</deployaltitude>
                <deploydelay>0.0</deploydelay>
                <striplength>{streamer_len_mm / 1000.0}</striplength>
                <stripwidth>{streamer_width_mm / 1000.0}</stripwidth>
              </streamer>
{all_fins_xml}
            </subcomponents>
          </bodytube>
        </subcomponents>
      </stage>
    </subcomponents>
  </rocket>

  <simulations>
    <simulation status="outdated">
      <name>Standard Launch ({motor_desc}-{motor_delay})</name>
      <simulator>RK4Simulator</simulator>
      <calculator>BarrowmanCalculator</calculator>
      <conditions>
        <configid>{config_id}</configid>
        <launchrodlength>1.0</launchrodlength>
        <launchintowind>true</launchintowind>
        <launchrodangle>0.0</launchrodangle>
        <launchroddirection>90.0</launchroddirection>
        <windaverage>0.0</windaverage>
        <windturbulence>0.0</windturbulence>
        <winddirection>0.0</winddirection>
        <windmodeltype>Average</windmodeltype>
        <launchaltitude>0.0</launchaltitude>
        <launchlatitude>45.0</launchlatitude>
        <launchlongitude>0.0</launchlongitude>
        <geodeticmethod>flat</geodeticmethod>
        <atmosphere model="isa"/>
        <timestep>0.05</timestep>
        <maxtime>1200.0</maxtime>
      </conditions>
    </simulation>
  </simulations>
</openrocket>
"""
    return xml

def save_ork_file(filepath, xml_content):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with zipfile.ZipFile(filepath, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('rocket.ork', xml_content)
    print(f"Generated: {filepath}")

def main():
    # -------------------------------------------------------------
    # Setting A: 3-fin Asymmetric Inverted-Y (Theta=35 deg, Scale=0.70)
    # -------------------------------------------------------------
    # Main fins: 2 fins angled downwards at 35 deg from horizontal
    # Right-down: -35 deg (or 325 deg), Left-down: 215 deg (or 180 + 35)
    # Vertical fin: 1 fin pointing straight up (90 deg), scaled to 0.70
    setting_a_fins = [
        {
            'name': '主翼 (右下 35°下反角)',
            'count': 1,
            'span_mm': 66.0,
            'root_chord_mm': 30.0,
            'tip_chord_mm': 3.6,
            'sweep_mm': 26.4,
            'thickness_mm': 0.4,
            'rotation_deg': 325.0, # -35 deg
            'color_rgb': (44, 160, 44) # Green
        },
        {
            'name': '主翼 (左下 35°下反角)',
            'count': 1,
            'span_mm': 66.0,
            'root_chord_mm': 30.0,
            'tip_chord_mm': 3.6,
            'sweep_mm': 26.4,
            'thickness_mm': 0.4,
            'rotation_deg': 215.0, # 180 + 35 deg
            'color_rgb': (44, 160, 44) # Green
        },
        {
            'name': '垂直尾翼 (上向き 0.70倍)',
            'count': 1,
            'span_mm': 46.2,
            'root_chord_mm': 21.0,
            'tip_chord_mm': 2.52,
            'sweep_mm': 18.48,
            'thickness_mm': 0.4,
            'rotation_deg': 90.0,
            'color_rgb': (31, 119, 180) # Accent blue
        }
    ]

    xml_a_raw = build_ork_xml(
        rocket_name="設定A: 限界滞空型 (3枚非対称 逆Y字35°)",
        total_length_mm=250.0,
        nose_len_mm=125.0,
        body_len_mm=125.0,
        radius_mm=12.0,
        fin_sets=setting_a_fins,
        streamer_len_mm=500.0,
        streamer_width_mm=50.0,
        streamer_mass_g=1.27,
        color_rgb=(44, 160, 44),
        designer="Setting A (Inv-Y 35 deg)"
    )
    save_ork_file("output/設定A_3枚逆Y字_50x500_geom.ork", xml_a_raw)
    save_ork_file("output/setting_a_geom.ork", xml_a_raw)

    # Setting A with calibrated mass and CG matching custom optimizer
    xml_a_cal = build_ork_xml(
        rocket_name="設定A: 限界滞空型 (3枚非対称 逆Y字35°) [諸元同期版]",
        total_length_mm=250.0,
        nose_len_mm=125.0,
        body_len_mm=125.0,
        radius_mm=12.0,
        fin_sets=setting_a_fins,
        streamer_len_mm=500.0,
        streamer_width_mm=50.0,
        streamer_mass_g=1.27,
        mass_override_g=15.3, # Dry mass (30.3g launch mass - 15.0g motor)
        cg_override_from_tip_mm=185.9,
        color_rgb=(44, 160, 44),
        designer="Setting A (Calibrated)"
    )
    save_ork_file("output/設定A_3枚逆Y字_50x500_calibrated.ork", xml_a_cal)
    save_ork_file("output/setting_a_cal.ork", xml_a_cal)

    # -------------------------------------------------------------
    # Setting B: 4-fin Symmetric Cross (+)
    # -------------------------------------------------------------
    # 4 fins equally spaced at 90 deg (0, 90, 180, 270)
    setting_b_fins = [
        {
            'name': '4枚対称 十字翼 (+)',
            'count': 4,
            'span_mm': 56.0,
            'root_chord_mm': 26.0,
            'tip_chord_mm': 3.12,
            'sweep_mm': 22.88,
            'thickness_mm': 0.4,
            'rotation_deg': 0.0,
            'color_rgb': (127, 127, 127) # Grey
        }
    ]

    xml_b_raw = build_ork_xml(
        rocket_name="設定B: 実戦本命 (4枚対称 十字翼+)",
        total_length_mm=250.0,
        nose_len_mm=125.0,
        body_len_mm=125.0,
        radius_mm=12.0,
        fin_sets=setting_b_fins,
        streamer_len_mm=500.0,
        streamer_width_mm=50.0,
        streamer_mass_g=1.27,
        color_rgb=(100, 100, 100),
        designer="Setting B (Cross +)"
    )
    save_ork_file("output/設定B_4枚十字_50x500_geom.ork", xml_b_raw)
    save_ork_file("output/setting_b_geom.ork", xml_b_raw)

    xml_b_cal = build_ork_xml(
        rocket_name="設定B: 実戦本命 (4枚対称 十字翼+) [諸元同期版]",
        total_length_mm=250.0,
        nose_len_mm=125.0,
        body_len_mm=125.0,
        radius_mm=12.0,
        fin_sets=setting_b_fins,
        streamer_len_mm=500.0,
        streamer_width_mm=50.0,
        streamer_mass_g=1.27,
        mass_override_g=15.6, # Dry mass (30.6g launch mass - 15.0g motor)
        cg_override_from_tip_mm=186.4,
        color_rgb=(100, 100, 100),
        designer="Setting B (Calibrated)"
    )
    save_ork_file("output/設定B_4枚十字_50x500_calibrated.ork", xml_b_cal)
    save_ork_file("output/setting_b_cal.ork", xml_b_cal)

if __name__ == '__main__':
    main()
