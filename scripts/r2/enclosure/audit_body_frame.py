#!/usr/bin/python3
"""Inspect saved CAD placements and native U2 pads without modifying geometry.

This is NOT a FreeCAD recompute, BRep interference check, or a physical fit test.
The owner explicitly identified the flat base / main PCB bottom as body-facing.
In-plane +Y is chosen toward the main antenna; it is not anatomical up.
"""
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile
import pcbnew as p

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'docs/revision-r2/rgb-body/validation'


def rotation(q):
    x,y,z,w = q
    assert abs(sum(v*v for v in q)-1) < 1e-10
    return [[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
            [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
            [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]]


def matmul(a,b):
    return [[sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def main():
    file = ROOT/'housing/smove-r2-enclosure.FCStd'
    with zipfile.ZipFile(file) as z:
        assert z.testzip() is None
        doc = ET.fromstring(z.read('Document.xml'))
    objects = {o.get('name'):o for o in doc.find('ObjectData')}
    def prop(obj, name):
        return objects[obj].find(f"Properties/Property[@name='{name}']")
    rotations = {}
    placements = {}
    for name in ['MainPCB','CarrierPCB']:
        raw = prop(name,'Placement').find('PropertyPlacement').attrib
        q = [float(raw['Q'+str(i)]) for i in range(4)]
        rotations[name] = rotation(q)
        placements[name] = dict(translation_mm=[float(raw['P'+axis]) for axis in 'xyz'], quaternion_xyzw=q,
                               rotation=rotations[name])
    n_main = [row[2] for row in rotations['MainPCB']]
    n_carrier = [row[2] for row in rotations['CarrierPCB']]
    dot = sum(a*b for a,b in zip(n_main,n_carrier))
    b = p.LoadBoard(str(ROOT/'PCB/imu-carrier/smove-imu-carrier.kicad_pcb'))
    u = next(f for f in b.GetFootprints() if f.GetReference()=='U2')
    pads = {pad.GetNumber():[round(v,6) for v in p.ToMM(pad.GetPosition())] for pad in u.Pads()}
    # Independent DS-000189 Fig3 top-view numbering, 0.4mm pitch.
    expected = {}
    for i in range(6):
        expected[str(1+i)] = [108.0,102.8+i*.4]
        expected[str(7+i)] = [108.5+i*.4,105.3]
        expected[str(13+i)] = [111.0,104.8-i*.4]
        expected[str(19+i)] = [110.5-i*.4,102.3]
    pin_match = set(pads)==set(expected) and all(math.dist(pads[n],v)<1e-5 for n,v in expected.items())
    assert pin_match and not u.IsFlipped() and u.GetOrientationDegrees()==0
    assert math.dist(list(p.ToMM(u.GetPosition())),[109.5,103.8])<1e-6
    identity = [[1,0,0],[0,1,0],[0,0,1]]
    mag = [[1,0,0],[0,-1,0],[0,0,-1]]
    iface = json.loads((ROOT/'PCB/imu-carrier/interface.json').read_text())
    assert iface['axes']['accel_to_carrier']==iface['axes']['gyro_to_carrier']==identity
    assert iface['axes']['mag_to_carrier']==mag
    build = json.loads((ROOT/'housing/validation/build.json').read_text())
    assert build['body_frame']['Z'] == 'outward away from body'
    assert n_main == n_carrier == [0., 0., 1.]
    mainboard = p.LoadBoard(str(ROOT/'PCB/main/smove-r2-main.kicad_pcb'))
    led = next(f for f in mainboard.GetFootprints() if f.GetReference() == 'D1')
    assert not led.IsFlipped() and list(p.ToMM(led.GetPosition())) == [119.15, 122.7]
    report = dict(
        status='PASS_BODY_FRAME_AND_PACKAGE_SIGNS', geometry_changed=True, requirement_satisfied=True,
        requirement='Coplanar boards parallel to base contact plane; accel/gyro +Z outward; D1 top and unobstructed lid aperture.',
        body_frame=build['body_frame'],
        user_authority='Main BOTTOM faces body through housing base. Worn-up antenna/USB choice explicitly unimportant.',
        enclosure_to_body=identity, accel_gyro_to_body=identity, mag_to_body=mag,
        inspection_scope='Saved native placements plus actual U2 pads, pin-1 and D1 side. Fresh BRep/STEP/STL checks are housing/validation/mechanical.json.',
        saved_object_placements=placements,
        normals=dict(main=n_main,carrier=n_carrier,dot_product=dot,acute_angle_degrees=math.degrees(math.acos(min(1,abs(dot))))),
        substrates_z_mm=[4.,5.], body_contact_z_mm=0., main_bottom_toward_body=True, led_top_outward=True,
        sensor=dict(part='ICM-20948',reference='U2',top=True,rotation_deg=0,
                    anchor_native_mm=[109.5,103.8],all_24_pin_positions_match_datasheet=pin_match,pads_native_mm=pads,
                    evidence='../evidence/icm-pinout.png and ../evidence/icm-axes.png',
                    accel_to_carrier=identity,gyro_to_carrier=identity,mag_to_carrier=mag,
                    accel_gyro_to_current_enclosure=rotations['CarrierPCB'],
                    mag_to_current_enclosure=matmul(rotations['CarrierPCB'],mag),
                    positive_gyro_rotation='Manufacturer Fig12 signed rotations, right-hand convention; not Euler angle remapping'),
        limitations=['All axes use column vectors; do not apply accelerometer rotation blindly to raw magnetometer.',
                     'In-plane +Y toward antenna is a convenient device axis, not anatomical up.',
                     'Mechanical CAD cannot establish printed fit, clamp stiffness, true harness slack, screw material or magnetic/RF suitability.',
                     'Bench six-face acceleration, positive gyro rotation and finished-case magnetometer calibration still required.'],
        sources_sha256={path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in [
            'housing/smove-r2-enclosure.FCStd','scripts/r2/enclosure/generate.py',
            'PCB/imu-carrier/smove-imu-carrier.kicad_pcb','PCB/main/smove-r2-main.kicad_pcb','PCB/imu-carrier/interface.json']})
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'mechanical-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report['status'], 'PCB plane angle:',report['normals']['acute_angle_degrees'],
          'degrees; U2 signed axes, explicit body frame and outward LED PASS')


if __name__=='__main__':
    main()
