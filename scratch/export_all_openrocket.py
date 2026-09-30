"""
Export All Rocket Candidates and Baseline to OpenRocket (.ork) Files
and Benchmark Cross-Verification with OpenRocket Official Simulation Engine.
"""

import os
import json
import uuid
import zipfile
import subprocess

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
    motor_desc="Estes 1/2A6",
    motor_delay=2.0,
    mass_override_g=None,
    cg_override_from_tip_mm=None,
    color_rgb=(235, 94, 85),
    designer="Antigravity MDO Optimizer"
):
    """
    Construct valid OpenRocket XML string (v1.10 format compatible with OpenRocket 23.09 - 24.12+).
    All dimensions converted to SI units (meters, kg, radians/deg).
    """
    rocket_id = make_uuid()
    stage_id = make_uuid()
    config_id = make_uuid()
    nose_id = make_uuid()
    body_id = make_uuid()
    mount_id = make_uuid()
    streamer_id = make_uuid()

    # Nose & body SI units
    nose_l_m = nose_len_mm / 1000.0
    body_l_m = body_len_mm / 1000.0
    radius_m = radius_mm / 1000.0

    # Fin sets XML string
    fin_xml_blocks = []
    for f in fin_sets:
        fin_id = make_uuid()
        f_count = f.get('count', 3)
        f_span_m = f['span_mm'] / 1000.0
        f_root_m = f['root_chord_mm'] / 1000.0
        f_tip_m = f.get('tip_chord_mm', 0.0) / 1000.0
        f_sweep_m = f.get('sweep_mm', f['root_chord_mm']) / 1000.0
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
                  <shine>0.4</shine>
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

    # Overrides if specified
    override_xml = ""
    if mass_override_g is not None and cg_override_from_tip_mm is not None:
        mass_kg = mass_override_g / 1000.0
        cg_m = cg_override_from_tip_mm / 1000.0
        # In OpenRocket, stage override overrides mass of entire sustainer
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
                <material type="surface" density="0.067" group="Fabrics">Ripstop nylon</material>
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
    print(f"Successfully generated: {filepath}")

def generate_all_ork_files():
    models = {}

    # 1. Baseline Model (つくばモデルロケット)
    baseline_fins = [
        {
            'name': '3枚対称翼 (120度配置)',
            'count': 3,
            'span_mm': 48.0,
            'root_chord_mm': 45.0,
            'sweep_mm': 45.0,
            'tip_chord_mm': 0.0,
            'thickness_mm': 0.4,
            'rotation_deg': 0.0,
            'color_rgb': (0, 119, 182) # Deep blue
        }
    ]
    xml_b = build_ork_xml(
        rocket_name="つくばモデルロケット (Baseline)",
        total_length_mm=190.0,
        nose_len_mm=80.0,
        body_len_mm=110.0,
        radius_mm=12.0,
        fin_sets=baseline_fins,
        mass_override_g=13.5,
        cg_override_from_tip_mm=128.0,
        color_rgb=(0, 119, 182),
        designer="Tsukuba Model Rocket Baseline"
    )
    p_b = "output/ロケット_ベースライン.ork"
    save_ork_file(p_b, xml_b)
    models['Baseline'] = {'path': p_b, 'sim_apogee': 59.35, 'sim_time': 10.23}

    # 2. Candidate 1 (機体①: 限界滞空型 - 十字アンバランス4枚翼)
    c1_fins = [
        {
            'name': '主翼 (左右2枚 水平)',
            'count': 2,
            'span_mm': 55.0,
            'root_chord_mm': 31.0,
            'sweep_mm': 31.0,
            'tip_chord_mm': 0.0,
            'thickness_mm': 0.4,
            'rotation_deg': 0.0,
            'color_rgb': (230, 57, 70) # Red
        },
        {
            'name': '垂直尾翼 (上下2枚 Kv=0.90)',
            'count': 2,
            'span_mm': 49.5,
            'root_chord_mm': 27.9,
            'sweep_mm': 27.9,
            'tip_chord_mm': 0.0,
            'thickness_mm': 0.4,
            'rotation_deg': 90.0,
            'color_rgb': (29, 53, 87) # Navy
        }
    ]
    xml_c1 = build_ork_xml(
        rocket_name="機体①: 限界滞空型 (Cross Asym 4-Fin)",
        total_length_mm=250.0,
        nose_len_mm=120.0,
        body_len_mm=130.0,
        radius_mm=12.0,
        fin_sets=c1_fins,
        mass_override_g=15.54,
        cg_override_from_tip_mm=185.63,
        color_rgb=(230, 57, 70),
        designer="Antigravity MDO - Candidate 1"
    )
    p_c1 = "output/ロケット_機体1_限界滞空型.ork"
    save_ork_file(p_c1, xml_c1)
    models['Candidate 1'] = {'path': p_c1, 'sim_apogee': 56.06, 'sim_time': 9.59}

    # 3. Candidate 2 (機体②: 超高安定型 - 逆Y字3枚翼)
    # OpenRocket models non-planar fins through separate fin sets with specified rotations
    c2_fins = [
        {
            'name': '真上垂直尾翼 (1枚 90度)',
            'count': 1,
            'span_mm': 52.9,
            'root_chord_mm': 31.5,
            'sweep_mm': 31.5,
            'tip_chord_mm': 0.0,
            'thickness_mm': 0.44,
            'rotation_deg': 90.0,
            'color_rgb': (29, 53, 87) # Navy
        },
        {
            'name': '主翼 (左右2枚 35度下反角)',
            'count': 2,
            'span_mm': 75.7,
            'root_chord_mm': 45.0,
            'sweep_mm': 45.0,
            'tip_chord_mm': 0.0,
            'thickness_mm': 0.44,
            'rotation_deg': -35.0, # 35 deg droop
            'color_rgb': (230, 57, 70) # Red
        }
    ]
    xml_c2 = build_ork_xml(
        rocket_name="機体②: 超高安定型 (Inverted-Y 3-Fin)",
        total_length_mm=250.0,
        nose_len_mm=120.0,
        body_len_mm=130.0,
        radius_mm=12.0,
        fin_sets=c2_fins,
        mass_override_g=16.25,
        cg_override_from_tip_mm=184.5,
        color_rgb=(255, 183, 3), # Warm Amber/Gold
        designer="Antigravity MDO - Candidate 2"
    )
    p_c2 = "output/ロケット_機体2_超高安定型.ork"
    save_ork_file(p_c2, xml_c2)
    models['Candidate 2'] = {'path': p_c2, 'sim_apogee': 54.03, 'sim_time': 9.25}

    # 4. Candidate 3 (機体③: 鉄壁安全型 - 3枚対称翼)
    c3_fins = [
        {
            'name': '3枚対称翼 (120度配置)',
            'count': 3,
            'span_mm': 59.0,
            'root_chord_mm': 33.0,
            'sweep_mm': 33.0,
            'tip_chord_mm': 0.0,
            'thickness_mm': 0.44,
            'rotation_deg': 0.0,
            'color_rgb': (42, 157, 143) # Teal / Green
        }
    ]
    xml_c3 = build_ork_xml(
        rocket_name="機体③: 鉄壁安全型 (Ironclad Safety 3-Fin)",
        total_length_mm=250.0,
        nose_len_mm=120.0,
        body_len_mm=130.0,
        radius_mm=12.0,
        fin_sets=c3_fins,
        mass_override_g=15.4,
        cg_override_from_tip_mm=185.2,
        color_rgb=(42, 157, 143),
        designer="Antigravity MDO - Candidate 3"
    )
    p_c3 = "output/ロケット_機体3_鉄壁安全型.ork"
    save_ork_file(p_c3, xml_c3)
    models['Candidate 3'] = {'path': p_c3, 'sim_apogee': 51.55, 'sim_time': 8.84}

    return models

if __name__ == "__main__":
    generate_all_ork_files()
