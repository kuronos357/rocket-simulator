import os
import math
import uuid
import zipfile
import subprocess
import numpy as np

# Fin curve generator
def generate_fin_polygon(b, Cr, Ct, sweep_deg, p_le=1.0, p_te=1.0, n_points=25):
    """
    Generate polygon coordinates (x, y) along the contour of the fin.
    x is along the rocket axis (0 at leading edge of root), y is spanwise (distance from body surface).
    """
    deg_rad = math.radians(sweep_deg)
    delta_x_tip = b * math.tan(deg_rad)

    # 1. Leading edge from root (0, 0) to tip (delta_x_tip, b)
    # y from 0 to b
    y_le = np.linspace(0, b, n_points)
    eta_le = y_le / b
    x_le = delta_x_tip * (eta_le ** p_le)

    # 2. Tip edge from (delta_x_tip, b) to (delta_x_tip + Ct, b)
    x_tip = np.array([delta_x_tip, delta_x_tip + Ct])
    y_tip = np.array([b, b])

    # 3. Trailing edge from tip (delta_x_tip + Ct, b) back to root (Cr, 0)
    # y from b down to 0
    y_te = np.linspace(b, 0, n_points)
    eta_te = y_te / b
    # x_te(eta) = Cr + (delta_x_tip + Ct - Cr) * (eta ** p_te)
    x_te = Cr + (delta_x_tip + Ct - Cr) * (eta_te ** p_te)

    # Combine into a single closed loop of unique vertices
    # (x, y) in OpenRocket format (in meters)
    poly = []
    # Root leading edge
    for x, y in zip(x_le, y_le):
        poly.append((x / 1000.0, y / 1000.0))
    # Tip
    poly.append(((delta_x_tip + Ct) / 1000.0, b / 1000.0))
    # Trailing edge
    for x, y in zip(x_te[1:], y_te[1:]):
        poly.append((x / 1000.0, y / 1000.0))

    return poly

def create_candidate_ork(
    name,
    candidate_id,
    b_mm, Cr_mm, Ct_mm, sweep_deg, oh_mm, p_le, p_te,
    dry_mass_kg=0.0155,
    override_cg_m=0.180
):
    rocket_id = str(uuid.uuid4())
    stage_id = str(uuid.uuid4())
    config_id = str(uuid.uuid4())
    nose_id = str(uuid.uuid4())
    body_id = str(uuid.uuid4())
    trans_id = str(uuid.uuid4())
    mount_id = str(uuid.uuid4())
    streamer_id = str(uuid.uuid4())
    fin_id = str(uuid.uuid4())

    # Fin points
    poly = generate_fin_polygon(b_mm, Cr_mm, Ct_mm, sweep_deg, p_le, p_te)
    fin_points_xml = "\n".join([f'                    <point x="{x:.6f}" y="{y:.6f}"/>' for x, y in poly])

    # Axial position of fins on body/transition:
    # Rocket total length = 0.125 (nose) + 0.105 (body) + 0.020 (tail) = 0.250 m
    # Fin trailing edge root relative to rocket aft end is -oh_mm / 1000.0
    # On the 105mm body tube + 20mm tail cone:
    # If fins are mounted on the body tube (length 105mm),
    # body tube bottom is at 0.125 + 0.105 = 0.230 m.
    # Tail cone is 0.230 to 0.250 m.
    # Mounting on body tube with axialoffset method="bottom":
    # Fin root chord length is Cr_mm.
    # Trailing edge root x on rocket is 0.250 - oh_mm/1000.
    # Body tube bottom is at 0.230.
    # So fin root leading edge on body tube:
    # Leading edge position from body tube bottom = (0.250 - oh_mm/1000 - Cr_mm/1000) - 0.230 = 0.020 - (oh_mm + Cr_mm)/1000
    # In OpenRocket, <position type="bottom"> offsets the fin set root chord leading edge from the parent tube bottom!
    # Specifically, positive offset from bottom means forward towards top.
    fin_offset_from_body_bottom = (0.020 - oh_mm / 1000.0)  # offset of fin root trailing edge from body bottom is 0.020 - oh
    # In OpenRocket, <position type="bottom">0.0</position> puts the LE of root chord at bottom, or root chord trailing edge at bottom?
    # OpenRocket convention: "bottom" offset is distance of component *front* from parent bottom, unless specified.
    # To be extremely clean and robust, we mount on BodyTube and use type="top" from body tube top:
    # Body tube top is at 0.125 m from nose tip.
    # Fin root leading edge on rocket is: 0.250 - (oh_mm + Cr_mm)/1000.0.
    # So fin root leading edge from body tube top is: (0.250 - (oh_mm + Cr_mm)/1000.0) - 0.125 = 0.125 - (oh_mm + Cr_mm)/1000.0.
    fin_pos_from_body_top = 0.125 - (oh_mm + Cr_mm) / 1000.0

    xml = f"""<?xml version='1.0' encoding='utf-8'?>
<openrocket version="1.10" creator="OpenRocket 24.12">
  <rocket>
    <name>{name}</name>
    <id>{rocket_id}</id>
    <axialoffset method="absolute">0.0</axialoffset>
    <position type="absolute">0.0</position>
    <designer>Antigravity MDO Team</designer>
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
            <name>Nose cone (Power 0.75)</name>
            <id>{nose_id}</id>
            <appearance>
              <paint red="240" green="180" blue="50" alpha="255"/>
              <shine>0.5</shine>
            </appearance>
            <finish>normal</finish>
            <material type="bulk" density="1240.0" group="Plastics">PLA (polylactide)</material>
            <length>0.125</length>
            <thickness>0.0004</thickness>
            <shape>power</shape>
            <shapeparameter>0.75</shapeparameter>
            <aftradius>0.012</aftradius>
            <aftshoulderradius>0.0116</aftshoulderradius>
            <aftshoulderlength>0.015</aftshoulderlength>
            <aftshoulderthickness>0.0004</aftshoulderthickness>
            <aftshouldercapped>false</aftshouldercapped>
            <isflipped>false</isflipped>
          </nosecone>

          <bodytube>
            <name>Body tube (24mm)</name>
            <id>{body_id}</id>
            <appearance>
              <paint red="235" green="235" blue="235" alpha="255"/>
              <shine>0.5</shine>
            </appearance>
            <finish>normal</finish>
            <material type="bulk" density="1240.0" group="Plastics">PLA (polylactide)</material>
            <length>0.105</length>
            <thickness>0.0004</thickness>
            <radius>auto 0.012</radius>

            <subcomponents>
              <innertube>
                <name>Motor Mount (18mm)</name>
                <id>{mount_id}</id>
                <appearance>
                  <paint red="130" green="90" blue="50" alpha="255"/>
                  <shine>0.0</shine>
                </appearance>
                <axialoffset method="bottom">0.020</axialoffset>
                <position type="bottom">0.020</position>
                <material type="bulk" density="680.0" group="PaperProducts">Cardboard</material>
                <length>0.070</length>
                <radialposition>0.0</radialposition>
                <radialdirection>0.0</radialdirection>
                <outerradius>0.0095</outerradius>
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
                    <length>0.070</length>
                    <delay>2.0</delay>
                  </motor>
                  <ignitionconfiguration configid="{config_id}">
                    <ignitionevent>automatic</ignitionevent>
                    <ignitiondelay>0.0</ignitiondelay>
                  </ignitionconfiguration>
                </motormount>
              </innertube>

              <streamer>
                <name>Mylar Streamer (120x1200mm)</name>
                <id>{streamer_id}</id>
                <axialoffset method="top">0.02</axialoffset>
                <position type="top">0.02</position>
                <packedlength>0.04</packedlength>
                <packedradius>0.010</packedradius>
                <radialposition>0.0</radialposition>
                <radialdirection>0.0</radialdirection>
                <cd>1.15</cd>
                <material type="surface" density="0.025" group="Plastics">Mylar</material>
                <deployevent>ejection</deployevent>
                <deployaltitude>200.0</deployaltitude>
                <deploydelay>0.0</deploydelay>
                <striplength>1.200</striplength>
                <stripwidth>0.120</stripwidth>
              </streamer>

              <freeformfinset>
                <name>Optimized Fin Set (4-Fin)</name>
                <id>{fin_id}</id>
                <appearance>
                  <paint red="30" green="120" blue="220" alpha="255"/>
                  <shine>0.4</shine>
                </appearance>
                <instancecount>4</instancecount>
                <fincount>4</fincount>
                <radiusoffset method="surface">0.0</radiusoffset>
                <angleoffset method="relative">0.0</angleoffset>
                <rotation>0.0</rotation>
                <axialoffset method="top">{fin_pos_from_body_top:.6f}</axialoffset>
                <position type="top">{fin_pos_from_body_top:.6f}</position>
                <finish>normal</finish>
                <material type="bulk" density="1240.0" group="Plastics">PLA (polylactide)</material>
                <thickness>0.0004</thickness>
                <crosssection>square</crosssection>
                <cant>0.0</cant>
                <filletradius>0.0</filletradius>
                <filletmaterial type="bulk" density="1240.0" group="Plastics">PLA (polylactide)</filletmaterial>
                <finpoints>
{fin_points_xml}
                </finpoints>
              </freeformfinset>
            </subcomponents>
          </bodytube>

          <transition>
            <name>Tail Boat-Tail Cone (20mm)</name>
            <id>{trans_id}</id>
            <appearance>
              <paint red="200" green="200" blue="200" alpha="255"/>
              <shine>0.5</shine>
            </appearance>
            <finish>normal</finish>
            <material type="bulk" density="1240.0" group="Plastics">PLA (polylactide)</material>
            <length>0.020</length>
            <thickness>0.0004</thickness>
            <shape>conical</shape>
            <foreradius>auto 0.012</foreradius>
            <aftradius>0.0095</aftradius>
            <foreshoulderradius>0.0116</foreshoulderradius>
            <foreshoulderlength>0.010</foreshoulderlength>
            <foreshoulderthickness>0.0004</foreshoulderthickness>
            <foreshouldercapped>false</foreshouldercapped>
            <aftshoulderradius>0.0</aftshoulderradius>
            <aftshoulderlength>0.0</aftshoulderlength>
            <aftshoulderthickness>0.0</aftshoulderthickness>
            <aftshouldercapped>false</aftshouldercapped>
          </transition>
        </subcomponents>
      </stage>
    </subcomponents>
  </rocket>

  <simulations>
    <simulation status="outdated">
      <name>Estes 1/2A6-2 Official Simulation</name>
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
    print(f"Generated ORK: {filepath}")

def main():
    candidates = [
        {
            "id": 1,
            "filename": "output/candidate_1_crescent_fillet.ork",
            "name": "Candidate 1: Ultimate Crescent-Fillet (18.52s)",
            "b": 90.0, "Cr": 40.0, "Ct": 5.0, "sweep": 25.0, "oh": 5.0, "p_le": 0.50, "p_te": 1.20
        },
        {
            "id": 2,
            "filename": "output/candidate_2_flush_standalone.ork",
            "name": "Candidate 2: Flush Standalone (18.30s)",
            "b": 95.0, "Cr": 34.0, "Ct": 3.5, "sweep": 25.0, "oh": 0.0, "p_le": 0.50, "p_te": 0.80
        },
        {
            "id": 3,
            "filename": "output/candidate_3_wind_robust.ork",
            "name": "Candidate 3: Wind-Robust High Margin (18.16s)",
            "b": 95.0, "Cr": 36.0, "Ct": 4.0, "sweep": 25.0, "oh": 5.0, "p_le": 0.50, "p_te": 0.80
        }
    ]

    for c in candidates:
        xml = create_candidate_ork(
            name=c["name"],
            candidate_id=c["id"],
            b_mm=c["b"],
            Cr_mm=c["Cr"],
            Ct_mm=c["Ct"],
            sweep_deg=c["sweep"],
            oh_mm=c["oh"],
            p_le=c["p_le"],
            p_te=c["p_te"]
        )
        save_ork(c["filename"], xml)

if __name__ == "__main__":
    main()
