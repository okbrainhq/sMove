"""Independent fresh FCStd/STEP/STL, insertion and hardware-envelope screens.
No printed-fit/load, cable-flexibility, waterproofing or magnetic-performance claim.
"""
import hashlib
import json
import math
from pathlib import Path
from collections import defaultdict
import FreeCAD as A
import Part
import Mesh
ROOT=Path(__file__).resolve().parents[3]; OUT=ROOT/'housing'; EX=OUT/'dist'; CACHE=ROOT/'.cache/housing'
CACHE.mkdir(parents=True,exist_ok=True)
build_path=CACHE/'build.json'
if not build_path.exists():build_path=OUT/'validation/build.json'
build=json.loads(build_path.read_text())
d=A.openDocument(str(OUT/'smove-r2-enclosure.FCStd')); d.recompute()
checks=[]; failures=[]
def check(name,ok,detail=None):
    row=dict(check=name,passed=bool(ok),detail=detail); checks.append(row)
    if not ok:failures.append(row)
def vol(a,b):
    if not a.BoundBox.intersect(b.BoundBox):return 0.
    return a.common(b).Volume
def separate(name,a,b):
    v=vol(a,b); check(name,v<1e-6,dict(intersection_mm3=v)); return v
def translated(shape,v):
    s=shape.copy(); s.translate(A.Vector(*v)); return s
base=d.Base.Shape; lid=d.Lid.Shape
refs=[d.getObject(n) for n in build['reference_objects']]
hardware=[d.getObject(n) for n in build['hardware_objects']]
clearances=[d.getObject(n) for n in build['clearance_objects']]
main=[o for o in refs if o.Name.startswith('Main')]
carrier=[o for o in refs if o.Name.startswith('Carrier')]
pack=d.ProtectedPack_ACCEPTANCE_ONLY
for o in [d.Base,d.Lid]+refs+hardware:
    check('native_closed_solid:'+o.Name,o.Shape.isValid() and len(o.Shape.Solids)==1 and o.Shape.isClosed(),dict(volume_mm3=o.Shape.Volume))
check('native_editable_CSG',d.Base.TypeId=='Part::Cut' and d.Lid.TypeId=='Part::Cut' and d.Parameters.TypeId=='Spreadsheet::Sheet')
separate('case:base_lid',base,lid)
for part in (d.Base,d.Lid):
    for obj in refs+hardware+clearances:
        if getattr(obj,'Role','')=='rf_keepout':continue # unfilled ordinary plastic is permitted, not RF isolation
        separate('case:'+part.Name+':'+obj.Name,part.Shape,obj.Shape)
for obj in refs+hardware:
    if obj.Name not in ('MainPCB','Main_U1'):
        separate('RF:'+obj.Name,d.RF_NO_BATTERY_HARNESS_CARRIER_METAL.Shape,obj.Shape)
for a in main:
    for b in carrier:separate('boards:'+a.Name+':'+b.Name,a.Shape,b.Shape)
for o in main+carrier:separate('battery:'+o.Name,o.Shape,pack.Shape)
for name in ('Main_J1_MatingInsertion','Main_J2_MatingInsertion','Main_J4_MatingInsertion'):
    for obj in carrier+[pack]+hardware:separate('plug:'+name+':'+obj.Name,d.getObject(name).Shape,obj.Shape)
for name in ('Carrier_aabb_mm','Carrier_wire_strain_relief_aabb_mm'):
    for obj in main+[pack]+hardware:separate('plug:'+name+':'+obj.Name,d.getObject(name).Shape,obj.Shape)
for obj in hardware:separate('no_sensor_support:'+obj.Name,obj.Shape,d.Carrier_NoSupport.Shape)
for wire,allowed,otherplug in [(d.PH4_1to1_LE50mm,{'Main_J4','Carrier_J5'},'Main_J2_MatingInsertion'),
                              (d.PH2_PairedProtectedPackLeads,{'Main_J2','ProtectedPack_ACCEPTANCE_ONLY'},'Main_J4_MatingInsertion')]:
    for obj in main+carrier+[pack]+hardware:
        if obj.Name not in allowed:separate('wire:'+wire.Name+':'+obj.Name,wire.Shape,obj.Shape)
    separate('wire:unrelated_plug:'+wire.Name,wire.Shape,d.getObject(otherplug).Shape)
separate('wires:mutual',d.PH4_1to1_LE50mm.Shape,d.PH2_PairedProtectedPackLeads.Shape)
for i,a in enumerate(hardware):
    for b in hardware[i+1:]:separate('hardware:mutual:'+a.Name+':'+b.Name,a.Shape,b.Shape)
    for b in main+carrier+[pack]:separate('hardware:electronics:'+a.Name+':'+b.Name,a.Shape,b.Shape)
# Full M3x8 tolerance envelope, not just a nominal screw. Model threads by major diameter.
# Source tables: ISO4762 length 7.71..8.29, head OD <=5.68, k<=3; nut thickness2.15..2.4.
for i,(x,y) in enumerate(build['fastener_xy_mm'],1):
    underhead=14.5; length_max=8.29; tip=underhead-length_max
    worst=Part.makeCylinder(1.5,length_max,A.Vector(x,y,tip)).fuse(Part.makeCylinder(2.84,3,A.Vector(x,y,underhead)))
    for obj in [d.Base,d.Lid]+refs:separate(f'screw_max:{i}:'+obj.Name,worst,obj.Shape)
    driver=Part.makeCylinder(3.,20.,A.Vector(x,y,17.5))
    for obj in [d.Base,d.Lid]+refs:separate(f'driver:{i}:'+obj.Name,driver,obj.Shape)
    check(f'M3:{i}:full_nut_engagement',underhead-7.71 < 10.5-2.4,dict(min_tip_beyond_nut_mm=(10.5-2.4)-(underhead-7.71),nut_threaded_thickness_mm=[2.15,2.4]))
    check(f'M3:{i}:blind_bottom_clearance',tip-5.8 >= .4,dict(worst_tip_to_bore_floor_mm=tip-5.8,tip_to_body_plane_mm=tip))
    check(f'M3:{i}:roof_and_lid',abs(d.getObject('ClosureBoss'+str(i)).Shape.BoundBox.ZMax-10.5-2.)<1e-6 and build['parameters_mm']['Roof']==2.)
    # Side-loaded nuts before boards/cell. No inaccessible top-entry nut that clamps only lid.
    nut=d.getObject('ClosureNut'+str(i)).Shape
    for shift in (0.,1.,3.,6.,8.):
        separate(f'nut_insertion:{i}:{shift}',translated(nut,(0,(1 if y<10 else -1)*shift,0)),base)
# Numerical contact checks at the actual board faces; surfaces are intentional contacts only.
for short,obj,bottom,top in [('Main',d.MainPCB,4.,5.),('Carrier',d.CarrierPCB,4.,5.)]:
    bb=obj.Shape.BoundBox
    check('planes:'+short,abs(bb.ZMin-bottom)<1e-6 and abs(bb.ZMax-top)<1e-6)
    normal=obj.Placement.Rotation.multVec(A.Vector(0,0,1))
    check('outward_normal:'+short,(normal-A.Vector(0,0,1)).Length<1e-8)
check('body_contact_floor_intact',abs(vol(base,Part.makeBox(109,48,1.6,A.Vector(-38,-5,0)))-109*48*1.6)<1e-5)
check('minimum_wall_and_mount_sections',build['parameters_mm']['Wall']==2. and 5.-6./math.sqrt(3)>1.5 and build['parameters_mm']['Floor']==1.6,
      dict(wall_mm=2.,floor_mm=1.6,nut_pocket_radial_wall_mm=5.-6./math.sqrt(3),nut_roof_mm=2.,carrier_seat_diameter_mm=3.2,
           main_bearing_width_mm=.7,main_bearing_note='Only existing 1.1x1.8mm copper-free lands; small bearings require a measured print/retention trial.'))
check('USB_tail_floor_reserve',d.Main_USB_ShellTails.Shape.BoundBox.ZMin-1.6>=1.2-1e-6)
check('PH4_centerline_plus_10mm_reserve_under_50',build['ph4_centerline_mm']+10<=50,dict(route_mm=build['ph4_centerline_mm'],budget_remaining_mm=50-build['ph4_centerline_mm'],bend_radius_mm=3.))
check('PH4_mating_endpoints',tuple(d.PH4_1to1_LE50mm.RoutePoints[0])==(.5,9.,8.) and tuple(d.PH4_1to1_LE50mm.RoutePoints[-1])==(-18.5,16.5,8.))
# Lid, both boards and pack all insert/remove vertically with power and loose cables removed.
# Samples plus a dense 0.5mm scan to clear the case height; NOT a continuous swept proof.
for dz in [i*.5 for i in range(31)]+[25.]:
    for obj in main+carrier+[pack]:separate('vertical_insertion:'+obj.Name+':'+str(dz),translated(obj.Shape,(0,0,dz)),base)
for dz in (.2,1.,3.,8.,16.,32.):
    sh=translated(lid,(0,0,dz))
    for obj in [d.Base]+refs:separate('lid_lift:'+str(dz)+':'+obj.Name,sh,obj.Shape)
# Positive chamfer key: reversed carrier footprint would intersect the key at seated height.
reversed_pcb=d.CarrierPCB.Shape.copy()
reversed_pcb.rotate(A.Vector(-18.5,26.,5.),A.Vector(0,0,1),180)
check('carrier_wrong_way_key_rejection',vol(reversed_pcb,d.CarrierChamferKey.Shape)>0.01)
for i in (1,2):
    upper=d.getObject('CarrierUpperBearing'+str(i)).Shape.BoundBox
    lower=d.getObject('CarrierSeat'+str(i)).Shape.BoundBox
    check('carrier_contact_annulus:'+str(i),abs(upper.ZMin-5.)<1e-7 and abs(lower.ZMax-4.)<1e-7 and abs(lower.XLength-3.2)<1e-7)
for ref,radius,z in [('SW2',1.3,7.1),('SW3',1.3,7.1),('D1',1.0,5.7)]:
    a=json.loads((ROOT/'PCB/main/interface.json').read_text())['anchors'][ref]
    x,y=a['center_native_xy_mm']; probe=Part.makeCylinder(radius,14.,A.Vector(x-100,135-y,z))
    for obj in [d.Base,d.Lid]+hardware+[o for o in refs if o.Name!='Main_'+ref]:
        separate('outward_access:'+ref+':'+obj.Name,probe,obj.Shape)
# Service pads: no in-case header. Probe from bottom after lifting main; below-board reserve is open.
separate('J3_bottom_2mm',Part.makeBox(2.2,6.2,2.,A.Vector(20.9,28.1,2.)),base)
# Native movable groups reference all distinct source solids; default is ASSEMBLED.
source_shapes={o.Name:o.Shape.copy() for o in [d.Base,d.Lid]+refs+hardware}
for name in build['inspection_groups']:
    group=d.getObject(name)
    check('inspection_default:'+name,group.TypeId=='App::Part' and group.Placement.isIdentity())
    for link in group.Group:
        src=link.LinkedObject
        check('inspection_link:'+link.Name,src.Name in source_shapes and abs(link.Shape.Volume-src.Shape.Volume)<1e-6 and (link.Shape.BoundBox.Center-src.Shape.BoundBox.Center).Length<1e-6)
    group.Placement.Base=group.ExplodedOffset
    d.recompute()
    for link in group.Group:
        # App::Part placement is applied by global transform, not by rewriting fixed CSG.
        displayed=group.getSubObject(link.Name+'.')
        check('inspection_move:'+link.Name,(displayed.BoundBox.Center-link.LinkedObject.Shape.BoundBox.Center-group.ExplodedOffset).Length<1e-6)
    group.Placement=A.Placement(); d.recompute()
for name,sh in source_shapes.items():
    now=d.getObject(name).Shape
    check('inspection_restore_source:'+name,(now.BoundBox.Center-sh.BoundBox.Center).Length<1e-7 and abs(now.Volume-sh.Volume)<1e-7)
for file,expected in [('smove-r2-printable.step',2),('smove-r2-assembly.step',2+len(refs)+len(hardware))]:
    sh=Part.read(str(EX/file))
    check('STEP:'+file,sh.isValid() and len(sh.Solids)==expected and all(s.isClosed() for s in sh.Solids),dict(solids=len(sh.Solids),expected=expected))
    expected_vol=sum(o.Shape.Volume for o in ([d.Base,d.Lid] if expected==2 else [d.Base,d.Lid]+refs+hardware))
    check('STEP_volume:'+file,abs(sh.Volume-expected_vol)<.001)
    def signature(solid):
        bb=solid.BoundBox
        return (solid.Volume,bb.XMin,bb.YMin,bb.ZMin,bb.XMax,bb.YMax,bb.ZMax,*tuple(solid.CenterOfMass))
    native=[d.Base,d.Lid] if expected==2 else [d.Base,d.Lid]+refs+hardware
    unmatched=[signature(s) for s in sh.Solids];missing=[]
    for obj in native:
        wanted=signature(obj.Shape.Solids[0])
        # Compare absolute deltas, not rounded decimal strings at a halfway boundary.
        match=next((i for i,sig in enumerate(unmatched) if max(abs(a-b) for a,b in zip(sig,wanted))<1e-5),None)
        if match is None:missing.append(obj.Name)
        else:unmatched.pop(match)
    check('STEP_positions_and_each_solid:'+file,not missing and not unmatched,dict(missing=missing,unmatched_count=len(unmatched),absolute_tolerance_mm_and_mm3=1e-5))
mesh_results={}
for name in ('base','lid'):
    mesh=Mesh.Mesh(str(EX/(name+'.stl'))); verts,faces=mesh.Topology; edges=defaultdict(list); adj=defaultdict(set); signed_volume=0
    for i,(a,b,c) in enumerate(faces):
        signed_volume+=verts[a].dot(verts[b].cross(verts[c]))/6
        for p,q in ((a,b),(b,c),(c,a)):edges[tuple(sorted((p,q)))].append((i,p<q))
    for vals in edges.values():
        if len(vals)==2:adj[vals[0][0]].add(vals[1][0]); adj[vals[1][0]].add(vals[0][0])
    seen=set(); todo=[0]
    while todo:
        i=todo.pop()
        if i in seen:continue
        seen.add(i); todo.extend(adj[i]-seen)
    manifold=all(len(v)==2 for v in edges.values()); normals=all(len(v)==2 and v[0][1]!=v[1][1] for v in edges.values())
    self_intersects=mesh.hasSelfIntersections() if hasattr(mesh,'hasSelfIntersections') else None
    mesh_results[name]=dict(facets=len(faces),watertight=manifold,consistent_normals=normals,connected=len(seen)==len(faces),signed_volume_mm3=signed_volume,self_intersects=self_intersects)
    check('STL:'+name,mesh.isSolid() and manifold and normals and len(seen)==len(faces) and signed_volume>0 and self_intersects is not True,mesh_results[name])
    check('STL_volume:'+name,abs(signed_volume-build['parts'][name]['volume_mm3'])/signed_volume<.002)
# Positive distances independently complement common-volume classification.
clearance_metrics={
    'board_edge_to_board_edge_mm':d.MainPCB.Shape.distToShape(d.CarrierPCB.Shape)[0],
    'RF_boundary_to_carrier_mm':d.RF_NO_BATTERY_HARNESS_CARRIER_METAL.Shape.distToShape(d.CarrierPCB.Shape)[0],
    'USB_plug_reserve_to_lid_mm':d.Main_J1_MatingInsertion.Shape.distToShape(lid)[0],
    'PH4_plug_reserve_to_lid_mm':min(d.Main_J4_MatingInsertion.Shape.distToShape(lid)[0],d.Carrier_aabb_mm.Shape.distToShape(lid)[0]),
    'PH4_bundle_to_case_mm':min(d.PH4_1to1_LE50mm.Shape.distToShape(sh)[0] for sh in (base,lid)),
    'PH2_bundle_to_case_mm':min(d.PH2_PairedProtectedPackLeads.Shape.distToShape(sh)[0] for sh in (base,lid)),
    'hardware_to_electronics_mm':min(a.Shape.distToShape(b.Shape)[0] for a in hardware for b in main+carrier+[pack]),
    'hardware_to_IMU_package_mm':min(a.Shape.distToShape(d.Carrier_U2.Shape)[0] for a in hardware),
}
for name,value in clearance_metrics.items():check('positive_clearance:'+name,value>1e-6,dict(mm=value))
report=dict(status='PASS' if not failures else 'FAIL',checks_count=len(checks),failures=failures,meshes=mesh_results,checks=checks,
            clearance_metrics=clearance_metrics,method='Fresh FCStd recompute and exact BRep common volumes; fresh STEP import; mesh topology. All individual interference pairs retained in cache.',
            intentional_contacts='Zero-volume PCB reserved annuli/lands, floor/bay boundaries and screw/nut thread major diameter contacts. Harness overlaps own mating interfaces only.',
            limitations=['NOT physical fit or structural/torque/preload validation','Insertion samples, not a full continuous sweep','Contract envelopes, not measured plugs or flexing wires',
                         'No magnetic/current/RF/thermal/skin qualification','Printer tolerances, nut bridging and main clamp rigidity must be tested'])
(CACHE/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
# Compact deliverable: retain all key checks/failures and category counts rather than thousands of zero rows.
summary={k:v for k,v in report.items() if k!='checks'}
summary['categories']={prefix:dict(tested=sum(r['check'].startswith(prefix+':') for r in checks),failed=sum(r['check'].startswith(prefix+':') and not r['passed'] for r in checks)) for prefix in sorted({r['check'].split(':')[0] for r in checks})}
summary['key_checks']=[r for r in checks if r['check'].startswith(('M3:','planes:','outward_normal:','PH4_','minimum_','body_','USB_','carrier_wrong','STL','STEP'))]
summary['inputs_sha256']={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [Path(__file__),OUT/'smove-r2-enclosure.FCStd',EX/'smove-r2-assembly.step',EX/'smove-r2-printable.step',EX/'base.stl',EX/'lid.stl']}
(OUT/'validation').mkdir(exist_ok=True)
(OUT/'validation/mechanical.json').write_text(json.dumps(summary,indent=2)+'\n')
(OUT/'validation/build.json').write_text(json.dumps(build,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k in ('status','checks_count','failures','meshes')},indent=2))
if failures:raise SystemExit(1)
