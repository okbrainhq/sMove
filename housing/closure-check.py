"""Independent nominal rigid lid-hook installation/removal path; no snap flex assumed.
Reverse of the sampled removal path installs the lid: tilt, slide south, lower,
then fit the single M3x8. No battery/PCB component may be forced to make it fit.
"""
import FreeCAD as A, Part, json, hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];d=A.openDocument(str(R/'housing/smove-r2-enclosure.FCStd'))
build=json.loads((R/'housing/validation/build.json').read_text())
obstacles=[d.Base,d.BatteryDivider]+[d.getObject(n) for n in build['reference_objects']]+[d.getObject(n) for n in build['hardware_objects'] if 'Screw' not in n]
collisions=[];poses=[]
# Deliberate three-stage rigid motion, not a straight lift through captured hooks.
for i in range(41):poses.append((i/4,0.,0.))
for i in range(1,41):poses.append((10.,i*.03,0.))
for i in range(1,61):poses.append((10.,1.2,i*.5))
for angle,y,z in poses:
 sh=d.Lid.Shape.copy();sh.rotate(A.Vector(0,1.8,18.4),A.Vector(1,0,0),angle);sh.translate(A.Vector(0,y,z))
 for o in obstacles:
  if sh.BoundBox.intersect(o.Shape.BoundBox):
   v=sh.common(o.Shape).Volume
   if v>1e-6:collisions.append(dict(pose=[angle,y,z],obstacle=o.Name,overlap_mm3=v))
report=dict(status='PASS_SAMPLED_RIGID_HOOK_PATH' if not collisions else 'FAIL',samples=len(poses),pivot_mm=[0,1.8,18.4],rotation_axis=[1,0,0],removal_stages='Remove M3 screw; raise north edge to 10 degrees, translate lid north 1.2mm, then lift 30mm. Install in reverse; never force.',collisions=collisions,scope='Nominal discrete rigid geometry, not continuous sweep, tolerance/strength/print/physical qualification.',native_sha256=hashlib.sha256((R/'housing/smove-r2-enclosure.FCStd').read_bytes()).hexdigest())
(R/'housing/validation/closure-insertion.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(bool(collisions))
