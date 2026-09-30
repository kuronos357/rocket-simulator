import os
import uuid
import zipfile
import subprocess

def create_ork_xml(
    rocket_name="Tsukuba Baseline Model",
    designer="Antigravity MDO",
    nose_length=0.08, # 80mm
    nose_radius=0.012, # 12mm
    nose_shape="power",
    nose_parameter=0.75,
    body_length=0.11, # 110mm
    body_radius=0.012, # 12mm
    fin_count=3,
    fin_root_chord=0.045, # 45mm
    fin_span=0.048, # 48mm
    fin_sweep=0.045, # 45mm
    fin_thickness=0.0004, # 0.4mm
    streamer_length=0.5, # 500mm
    streamer_width=0.05, # 50mm
    motor_mount_length=0.07, # 70mm
    motor_mount_radius=0.009, # 9mm (18mm motor)
    dry_mass_kg=0.01554, # dry mass without motor
    override_cg_m=0.1856, # from nose tip
):
    rocket_id = str(uuid.uuid4())
    stage_id = str(uuid.uuid4())
    config_id = str(uuid.uuid4())
    nose_id = str(uuid.uuid4())
    body_id = str(uuid.uuid4())
    mount_id = str(uuid.uuid4())
    streamer_id = str(uuid.uuid4())
    fin_id = str(uuid.uuid4())

    xml = f"""<?xml version='1.0' encoding='utf-8'?>
<openrocket version="1.10" creator="OpenRocket 24.12">
  <rocket>
    <name>{rocket_name}</name>
    <id>{rocket_id}</id>
    <axialoffset method="absolute">0.0</axialoffset>
    <position type="absolute">0.0</position>
    <designer>{designer}</designer>
    <designtype>original</designtype>
    <motorconfiguration configid="{config_id}" default="true">
      <stage number="0" active="true"/>
    </motorconfiguration>
    <referencetype>maximum</referencetype>

    <subcomponents>
      <stage>
        <name>Sustainer</name>
        <id>{stage_id}</id>

        <subcomponents>
          <nosecone>
            <name>Nose cone</name>
            <id>{nose_id}</id>
            <appearance>
              <paint red="240" green="180" blue="50" alpha="255"/>
              <shine>0.5</shine>
            </appearance>
            <finish>normal</finish>
            <material type="bulk" density="1240.0" group="Plastics">PLA (polylactide)</material>
            <length>{nose_length}</length>
            <thickness>0.0004</thickness>
            <shape>{nose_shape}</shape>
            <shapeparameter>{nose_parameter}</shapeparameter>
            <aftradius>{nose_radius}</aftradius>
            <aftshoulderradius>{nose_radius - 0.0004}</aftshoulderradius>
            <aftshoulderlength>0.015</aftshoulderlength>
            <aftshoulderthickness>0.0004</aftshoulderthickness>
            <aftshouldercapped>false</aftshouldercapped>
            <isflipped>false</isflipped>
          </nosecone>

          <bodytube>
            <name>Body tube</name>
            <id>{body_id}</id>
            <appearance>
              <paint red="230" green="230" blue="230" alpha="255"/>
              <shine>0.5</shine>
            </appearance>
            <finish>normal</finish>
            <material type="bulk" density="1240.0" group="Plastics">PLA (polylactide)</material>
            <length>{body_length}</length>
            <thickness>0.0004</thickness>
            <radius>auto {body_radius}</radius>

            <subcomponents>
              <innertube>
                <name>Motor Mount (18mm)</name>
                <id>{mount_id}</id>
                <appearance>
                  <paint red="120" green="80" blue="50" alpha="255"/>
                  <shine>0.0</shine>
                </appearance>
                <axialoffset method="bottom">0.0</axialoffset>
                <position type="bottom">0.0</position>
                <material type="bulk" density="680.0" group="PaperProducts">Cardboard</material>
                <length>{motor_mount_length}</length>
                <radialposition>0.0</radialposition>
                <radialdirection>0.0</radialdirection>
                <outerradius>{motor_mount_radius}</outerradius>
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
                    <delay>2.0</delay>
                  </motor>
                  <ignitionconfiguration configid="{config_id}">
                    <ignitionevent>automatic</ignitionevent>
                    <ignitiondelay>0.0</ignitiondelay>
                  </ignitionconfiguration>
                </motormount>
              </innertube>

              <streamer>
                <name>Recovery Streamer</name>
                <id>{streamer_id}</id>
                <axialoffset method="top">0.02</axialoffset>
                <position type="top">0.02</position>
                <packedlength>0.03</packedlength>
                <packedradius>{body_radius - 0.002}</packedradius>
                <radialposition>0.0</radialposition>
                <radialdirection>0.0</radialdirection>
                <cd>auto</cd>
                <material type="surface" density="0.067" group="Fabrics">Ripstop nylon</material>
                <deployevent>ejection</deployevent>
                <deployaltitude>200.0</deployaltitude>
                <deploydelay>0.0</deploydelay>
                <striplength>{streamer_length}</striplength>
                <stripwidth>{streamer_width}</stripwidth>
              </streamer>

              <trapezoidfinset>
                <name>Fin set</name>
                <id>{fin_id}</id>
                <appearance>
                  <paint red="220" green="50" blue="50" alpha="255"/>
                  <shine>0.3</shine>
                </appearance>
                <instancecount>{fin_count}</instancecount>
                <fincount>{fin_count}</fincount>
                <radiusoffset method="surface">0.0</radiusoffset>
                <angleoffset method="relative">0.0</angleoffset>
                <rotation>0.0</rotation>
                <axialoffset method="bottom">0.0</axialoffset>
                <position type="bottom">0.0</position>
                <finish>normal</finish>
                <material type="bulk" density="1240.0" group="Plastics">PLA (polylactide)</material>
                <thickness>{fin_thickness}</thickness>
                <crosssection>square</crosssection>
                <cant>0.0</cant>
                <filletradius>0.0</filletradius>
                <filletmaterial type="bulk" density="1240.0" group="Plastics">PLA (polylactide)</filletmaterial>
                <rootchord>{fin_root_chord}</rootchord>
                <tipchord>0.0</tipchord>
                <sweeplength>{fin_sweep}</sweeplength>
                <height>{fin_span}</height>
              </trapezoidfinset>
            </subcomponents>
          </bodytube>
        </subcomponents>
      </stage>
    </subcomponents>
  </rocket>

  <simulations>
    <simulation status="outdated">
      <name>Standard Launch (Estes 1/2A6-2)</name>
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

def save_ork(filepath, xml_content):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with zipfile.ZipFile(filepath, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('rocket.ork', xml_content)
    print(f"Generated ORK file: {filepath}")

if __name__ == "__main__":
    test_path = "output/ロケット_ベースライン.ork"
    xml = create_ork_xml(rocket_name="つくばモデルロケット (Baseline)")
    save_ork(test_path, xml)
