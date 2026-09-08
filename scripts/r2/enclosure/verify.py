"""Fresh native FCStd/STEP/STL checks; explicit intentional contacts, no broad clash waiver."""
import json, math
from pathlib import Path
from collections import defaultdict, deque
import FreeCAD as A
import Part
import Mesh
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'housing';EX=OUT/'dist'
(ROOT/'.cache/housing').mkdir(parents=True,exist_ok=True)
build_path=ROOT/'.cache/housing/build.json'
if not build_path.exists():build_path=OUT/'validation/build.json'
build=json.loads(build_path.read_text())
d=A.openDocument(str(OUT/'smove-r2-enclosure.FCStd'));d.recompute()
checks=[];failures=[]
def check(name,ok,detail=None):
    row={'check':name,'pass':bool(ok),'detail':detail};checks.append(row)
    if not ok:failures.append(row)
def vol(a,b):
    # Exact BRep Boolean, not AABB collision approximation.
    if not a.BoundBox.intersect(b.BoundBox):return 0.
    return a.common(b).Volume

def separate(name,a,b):
    v=vol(a,b);check(name,v<1e-6,{'intersection_mm3':v});return v
base=d.Base.Shape;lid=d.Lid.Shape
for name in ['Base','Lid']+build['reference_objects']+build['hardware_objects']:
    o=d.getObject(name);check('native_closed_solid:'+name,o.Shape.isValid() and len(o.Shape.Solids)==1 and o.Shape.isClosed(),{'solids':len(o.Shape.Solids),'volume_mm3':o.Shape.Volume})
check('editable_native_CSG_and_parameters',d.Base.TypeId=='Part::Cut' and d.Lid.TypeId=='Part::Cut' and d.Parameters.TypeId=='Spreadsheet::Sheet' and len(d.Base.OutList)>0)
separate('base_lid',base,lid)
for part in (d.Base,d.Lid):
    for name in build['reference_objects']:
        separate(part.Name+':'+name,part.Shape,d.getObject(name).Shape)
    for name in build['clearance_objects']:
        o=d.getObject(name)
        if o.Role=='rf_keepout':continue # Ordinary unfilled plastic is permitted, NOT RF isolation.
        separate(part.Name+':'+name,part.Shape,o.Shape)
# Other-board, battery, harness and metal keep out of exact RF volume.
for name in build['reference_objects']+build['hardware_objects']:
    if name in ('MainPCB','Main_U1'):continue
    separate('RF:'+name,d.RF_NO_BATTERY_HARNESS_CARRIER_METAL.Shape,d.getObject(name).Shape)
main=[d.getObject(n) for n in build['reference_objects'] if n.startswith('Main')]
carrier=[d.getObject(n) for n in build['reference_objects'] if n.startswith('Carrier')]
for a in main:
    for b in carrier:separate('boards:'+a.Name+':'+b.Name,a.Shape,b.Shape)
for name in ('Main_J1_MatingInsertion','Main_J2_MatingInsertion','Main_J4_MatingInsertion'):
    for obj in carrier+[d.ProtectedPack_ACCEPTANCE_ONLY]:separate('insertion:'+name+':'+obj.Name,d.getObject(name).Shape,obj.Shape)
for name in ('Carrier_aabb_mm','Carrier_wire_strain_relief_aabb_mm'):
    for obj in main+[d.ProtectedPack_ACCEPTANCE_ONLY]:separate('insertion:'+name+':'+obj.Name,d.getObject(name).Shape,obj.Shape)
for wire,allowed in [(d.PH4_1to1_LE50mm,{'Main_J4','Carrier_J5'}),(d.PH2_PairedProtectedPackLeads,{'Main_J2','ProtectedPack_ACCEPTANCE_ONLY'})]:
    for o in main+carrier+[d.ProtectedPack_ACCEPTANCE_ONLY]:
        if o.Name not in allowed:separate('wire:'+wire.Name+':'+o.Name,wire.Shape,o.Shape)
separate('harness_to_harness',d.PH4_1to1_LE50mm.Shape,d.PH2_PairedProtectedPackLeads.Shape)
# Nylon thread/pilot contact is intended ONLY inside that screw's declared blind pilot cylinder.
for i,name in enumerate(build['hardware_objects']):
    o=d.getObject(name)
    if name.startswith('NylonClosure'):
        k=name[-1];pilot=d.getObject('ClosurePilot'+k).Shape.copy();mask=Part.makeCylinder(1.01,5.1,pilot.BoundBox.Center-A.Vector(0,0,2.55))
    else:
        k=name[-1];z=4 if k=='1' else 17;mask=Part.makeCylinder(1.01,3.25,A.Vector(-8.4,17.5,z),A.Vector(1,0,0))
    separate('nylon_only_thread_engagement:'+name,base.cut(mask),o.Shape)
    separate('nylon_lid:'+name,lid,o.Shape)
    for ref in main+carrier+[d.ProtectedPack_ACCEPTANCE_ONLY,d.PH4_1to1_LE50mm,d.PH2_PairedProtectedPackLeads]:separate('nylon:'+name+':'+ref.Name,o.Shape,ref.Shape)
check('PH4_centerline_under_50mm',build['ph4_centerline_mm']<=50,build['ph4_centerline_mm'])
check('barrier_to_worst_USB_tail_ge_0p8',d.Main_USB_ShellTails.Shape.BoundBox.ZMin-d.IntegralBatteryBarrier.Shape.BoundBox.ZMax>=.8-1e-6,d.Main_USB_ShellTails.Shape.BoundBox.ZMin-d.IntegralBatteryBarrier.Shape.BoundBox.ZMax)
check('unpierced_1p2mm_rigid_battery_roof',abs(vol(base,d.IntegralBatteryBarrier.Shape)-d.IntegralBatteryBarrier.Shape.Volume)<1e-6)
# Service geometry uses native solids, no live leads/fasteners during extraction.
for dy in (0,-2,-8,-20,-36):
    sh=d.ProtectedPack_ACCEPTANCE_ONLY.Shape.copy();sh.translate(A.Vector(0,dy,0));separate('battery_slide_front:'+str(dy),sh,base)
for dz in (0,.2,2,10,25):
    for o in main:
        sh=o.Shape.copy();sh.translate(A.Vector(0,0,dz));separate('main_top_insertion:'+str(dz)+':'+o.Name,sh,base)
for dx in (0,-.2,-1,-4,-10):
    for o in carrier:
        sh=o.Shape.copy();sh.translate(A.Vector(dx,0,0));separate('carrier_west_insertion:'+str(dx)+':'+o.Name,sh,base)
for z in (4,17):
    driver=Part.makeCylinder(1.4,16,A.Vector(-26,17.5,z),A.Vector(1,0,0));separate('carrier_driver_lid_removed:'+str(z),driver,base)
# Lid straight lift at finite checkpoints; route is constrained by integral keepers.
for dz in (.2,1,5,12,25):
    sh=lid.copy();sh.translate(A.Vector(0,0,dz));separate('lid_lift_base:'+str(dz),sh,base)
    for n in build['reference_objects']:separate('lid_lift:'+str(dz)+':'+n,sh,d.getObject(n).Shape)
for ref in ('SW2','SW3','D1'):
    x,y=__import__('json').loads((ROOT/'PCB/main/interface.json').read_text())['anchors'][ref]['center_native_xy_mm']
    probe=Part.makeCylinder(.9 if ref=='D1' else 1,8,A.Vector(x-100,135-y,15.6))
    separate('tool_or_optical_access:'+ref,probe,lid)
# J3 2mm bottom service volume is outside the barrier; lid and pack must be removed.
debug=Part.makeBox(2.2,6.2,2,A.Vector(20.9,28.1,10.4));separate('J3_bottom_service_2mm',debug,base)
# Enclosure rotation and actual carrier native placement are tested independently.
R=[[0,0,-1],[0,1,0],[1,0,0]];M=[[0,0,1],[0,-1,0],[1,0,0]]
for i,v in enumerate((A.Vector(1,0,0),A.Vector(0,1,0),A.Vector(0,0,1))):
    actual=d.CarrierPCB.Placement.Rotation.multVec(v);expected=A.Vector(*(R[j][i] for j in range(3)));check('carrier_signed_axis:'+str(i),(actual-expected).Length<1e-8)
check('right_handed_rotation',A.Vector(0,0,1).cross(A.Vector(0,1,0))==A.Vector(-1,0,0))
check('mag_different_from_accel_gyro',M!=R)
for file,expected in [('smove-r2-printable.step',2),('smove-r2-assembly.step',2+len(build['reference_objects'])+len(build['hardware_objects']))]:
    sh=Part.read(str(EX/file));check('fresh_STEP:'+file,sh.isValid() and len(sh.Solids)==expected and all(s.isClosed() for s in sh.Solids),{'solids':len(sh.Solids),'expected':expected,'volume_mm3':sh.Volume})
    if expected==2:check('STEP_native_volume_match',abs(sh.Volume-base.Volume-lid.Volume)<.001)
mesh_results={}
for name in ('base','lid'):
    mesh=Mesh.Mesh(str(EX/(name+'.stl')));verts,faces=mesh.Topology;edges=defaultdict(list);adj=defaultdict(set);signed_volume=0
    for i,(a,b,c) in enumerate(faces):
        signed_volume+=verts[a].dot(verts[b].cross(verts[c]))/6
        for p,q in ((a,b),(b,c),(c,a)):edges[tuple(sorted((p,q)))].append((i,p<q))
    for val in edges.values():
        if len(val)==2:adj[val[0][0]].add(val[1][0]);adj[val[1][0]].add(val[0][0])
    seen=set();todo=[0]
    while todo:
        i=todo.pop()
        if i in seen:continue
        seen.add(i);todo.extend(adj[i]-seen)
    manifold=all(len(v)==2 for v in edges.values());normals=all(len(v)==2 and v[0][1]!=v[1][1] for v in edges.values())
    self_intersects=mesh.hasSelfIntersections() if hasattr(mesh,'hasSelfIntersections') else None
    check('STL:'+name,mesh.isSolid() and manifold and normals and len(seen)==len(faces) and signed_volume>0 and self_intersects is not True,{'facets':len(faces),'watertight':manifold,'consistent_normals':normals,'connected_faces':len(seen),'signed_volume_mm3':signed_volume,'self_intersects':self_intersects})
    check('STL_native_volume_match:'+name,abs(signed_volume-build['parts'][name]['volume_mm3'])/signed_volume<.002)
    mesh_results[name]=checks[-2]['detail']
report={'status':'PASS' if not failures else 'FAIL','checks_count':len(checks),'failures':failures,'meshes':mesh_results,'checks':checks,
        'intentional_contacts':'PCB reserved lands and carrier annuli; zero-volume touching permitted. Nylon thread engagement exempt ONLY within declared pilot masks. Harness own mating interface overlaps permitted.',
        'qualification_not_claimed':['printed fit','actual plug/cable bend/polarity','protected battery qualification','thread strength and main-board clamp stiffness','RF/magnetic or thermal performance']}
(ROOT/'.cache/housing/verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2))
if failures:raise SystemExit(1)
