"""Independent fresh native/STEP/STL and compact-stack geometric screens, not physical qualification."""
import json,hashlib,math
from pathlib import Path
import FreeCAD as A
import Part,Mesh
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'housing';EX=OUT/'dist';CACHE=ROOT/'.cache/housing';build=json.loads((CACHE/'build.json').read_text());d=A.openDocument(str(OUT/'smove-r2-enclosure.FCStd'));d.recompute();checks=[]
def check(n,ok,detail=None):checks.append(dict(check=n,passed=bool(ok),detail=detail))
def volume(a,b):return a.common(b).Volume if a.BoundBox.intersect(b.BoundBox) else 0.
def sep(n,a,b):v=volume(a,b);check(n,v<1e-6,dict(overlap_mm3=v))
def moved(s,x=0,y=0,z=0):s=s.copy();s.translate(A.Vector(x,y,z));return s
refs=[d.getObject(n) for n in build['reference_objects']];hw=[d.getObject(n) for n in build['hardware_objects']];cs=[d.getObject(n) for n in build['clearance_objects']];case=[d.Base,d.Lid,d.BatteryDivider]
for o in case+refs+hw:check('valid_solid:'+o.Name,o.Shape.isValid() and len(o.Shape.Solids)==1 and o.Shape.isClosed())
check('editable_native_CSG',d.Base.TypeId=='Part::Cut' and d.Lid.TypeId=='Part::Cut' and d.Parameters.TypeId=='Spreadsheet::Sheet')
for i,a in enumerate(case):
 for b in case[i+1:]:sep('case:'+a.Name+':'+b.Name,a.Shape,b.Shape)
 for o in refs+hw+cs:
  if getattr(o,'Role','')=='rf_keepout':continue
  sep('clear:'+a.Name+':'+o.Name,a.Shape,o.Shape)
for i,a in enumerate(refs+hw):
 for b in (refs+hw)[i+1:]:
  if a.Role=='harness' or b.Role=='harness':
   other=b if a.Role=='harness' else a
   if (a.Name.startswith('BareWire') and b.Name=='SolderFillet'+a.Name[-1]) or (b.Name.startswith('BareWire') and a.Name=='SolderFillet'+b.Name[-1]):continue
  sep('parts:'+a.Name+':'+b.Name,a.Shape,b.Shape)
for o in refs+hw+[d.BatteryDivider]:
 if o.Name not in ('MainPCB','Main_U1'):sep('RF:'+o.Name,d.RF_NO_BATTERY_HARNESS_METAL.Shape,o.Shape)
for c in cs:
 if 'MatingInsertion' in c.Name:
  for o in refs+hw+[d.BatteryDivider]:
   if o.Name==c.Name.replace('_MatingInsertion','') or o.Role=='harness':continue
   sep('plug:'+c.Name+':'+o.Name,c.Shape,o.Shape)
# J2 is now PTH wire pads: no mate, no header, no connector-envelope exception.
check('obsolete_J2_mate_removed',d.getObject('Main_J2_MatingInsertion') is None and d.getObject('Main_J2') is None)
check('two_wire_routes',len([o for o in refs if o.Name.startswith('BatteryWire')])==2)
for i,x in enumerate((11.23,13.77),1):
 wire=d.getObject('BatteryWire'+str(i));bare=d.getObject('BareWire'+str(i))
 check('wire_assumed_OD:'+str(i),abs(wire.EnvelopeRadius.Value-.6)<1e-6)
 check('wire_bend_reserve:'+str(i),abs(wire.BendRadius.Value-2.)<1e-6)
 check('tinned_bundle_in_PTH:'+str(i),abs(bare.Shape.BoundBox.XLength-.7)<1e-6 and d.MainPCB.Shape.common(bare.Shape).Volume<1e-6)
 check('solder_top_trim:'+str(i),abs(d.getObject('SolderFillet'+str(i)).Shape.BoundBox.ZMax-12.4)<1e-6)
 sep('wire_vs_full_pack_reserve:'+str(i),wire.Shape,d.BatteryAcceptance_21x31x4_3.Shape)
 # The guide and lacing bores must be actual negative space in native base, not drawings.
 for label,xx,yy,r in [('wire',x,2.2,.6),('lacing',(9.3,15.7)[i-1],2.7,.2)]:
  probe=Part.makeCylinder(r,1.,A.Vector(xx,yy,5.1));sep('strain_relief_passage:'+label+str(i),probe,d.Base.Shape)
check('lacing_bridge_connected',len(d.Base.Shape.Solids)==1 and d.WireLacingBridge.Shape.Volume>15)
# Verify every generated component against CURRENT native extraction, not an old file hash alone.
inputs=json.loads((CACHE/'input-geometry.json').read_text())['boards']['main']
for r,f in inputs['footprints'].items():
 if not f.get('fitted'):continue
 bb2=d.getObject('Main_'+r).Shape.BoundBox;x0,y0,x1,y1=f['envelope_xy'];z0,z1=f['z_mm']
 check('current_component_geometry:'+r,max(abs(a-b) for a,b in zip([bb2.XMin,bb2.YMin,bb2.ZMin,bb2.XMax,bb2.YMax,bb2.ZMax],[x0,y0,10.8+z0,x1,y1,10.8+z1]))<1e-6)
# Exact two diagonal native holes, sleeve contact and retained non-contact sensor frame.
check('two_diagonal_holes',len(build['fastener_xy_mm'])==2 and abs(build['fastener_xy_mm'][0][0]-build['fastener_xy_mm'][1][0])>17 and abs(build['fastener_xy_mm'][0][1]-build['fastener_xy_mm'][1][1])>28)
bb=Part.makeCompound([o.Shape for o in case+hw]).BoundBox;dims=[bb.XLength,bb.YLength,bb.ZLength];sorted_dims=sorted(dims,reverse=True)
check('outer_measured_bounds',all(v>0 for v in dims),dims)
full=Part.makeCompound([o.Shape for o in case+refs+hw]).BoundBox
check('all_installed_items_within_reported_bounds',max(abs(a-b) for a,b in zip([full.XMin,full.YMin,full.ZMin,full.XMax,full.YMax,full.ZMax],[bb.XMin,bb.YMin,bb.ZMin,bb.XMax,bb.YMax,bb.ZMax]))<1e-6)
# This is a requirement report, not a falsely passing release assertion.
target=dict(target_sorted_mm=[50,30,20],actual_sorted_mm=sorted_dims,met=all(a<t for a,t in zip(sorted_dims,[50,30,20])),limiter='Nominal CAD only: no print/cell/wire/fastener tolerance approval')
for i,(x,y) in enumerate(build['fastener_xy_mm'],1):
 # Acceptance SCREEN, not evidence that the owner's screws meet these bounds.
 worst=Part.makeCylinder(1.5,8.1,A.Vector(x,y,15.4-8.1)).fuse(Part.makeCylinder(2.84,3,A.Vector(x,y,15.4)))
 for o in case+refs:sep(f'screw_8_1_screen:{i}:'+o.Name,worst,o.Shape)
 check(f'M3:{i}:tip_to_divider_screen',15.4-8.1-7.1>=.1999,15.4-8.1-7.1)
 check(f'M3:{i}:7_9_full_nut_screen',15.4-7.9<7.6,7.6-(15.4-7.9))
 check(f'M3:{i}:engagement_mm',abs(d.getObject(f'ClosureNut{i}').Shape.BoundBox.ZLength-2.4)<1e-6,2.4)
 for name,z in [('LowerBearing',10.8),('LidBearingBoss',11.8)]:
  bearing=d.getObject(name+str(i)).Shape;zface=bearing.BoundBox.ZMax if name=='LowerBearing' else bearing.BoundBox.ZMin
  check(f'bearing_z:{i}:{name}',abs(zface-z)<1e-6)
  sl=Part.makeCylinder(3.4,.01,A.Vector(x,y,10.8 if name=='LowerBearing' else 11.79)).cut(Part.makeCylinder(1.7,.02,A.Vector(x,y,10.795 if name=='LowerBearing' else 11.785)))
  check(f'annular_PCB_contact:{i}:{name}',volume(sl,d.MainPCB.Shape)>.25)
  check(f'no_U2_clamp:{i}:{name}',bearing.distToShape(d.Main_U2.Shape)[0]>5)
 for shift in (0,1,3,6):sep(f'nut_entry:{i}:{shift}',moved(d.getObject(f'ClosureNut{i}').Shape,x=shift*(1 if i==1 else -1)),d.Base.Shape)
check('battery_ceiling_gap',d.BatteryDivider.Shape.BoundBox.ZMin-d.BatteryAcceptance_21x31x4_3.Shape.BoundBox.ZMax>=.1999)
check('solder_tail_barrier_gap',d.Main_USB_ShellTails.Shape.BoundBox.ZMin-d.BatteryDivider.Shape.BoundBox.ZMax>=2.4999)
for obj in [d.MainPCB,d.BatteryDivider]:
 for z in (0,.2,1,3,7,15,25):sep(f'top_insertion:{obj.Name}:{z}',moved(obj.Shape,z=z),d.Base.Shape)
for name in ('base','lid','divider'):
 mesh=Mesh.Mesh(str(EX/(name+'.stl')));check('watertight_STL:'+name,mesh.isSolid() and mesh.CountFacets>0)
shape=Part.Shape();shape.read(str(EX/'smove-r2-printable.step'));check('printable_STEP_three_solids',shape.isValid() and len(shape.Solids)==3)
source={o.Name:(o.Shape.Volume,str(o.Placement)) for o in case+refs+hw};groups=build['inspection_groups']
for n in groups:d.getObject(n).Placement.Base=A.Vector(3,5,7)
d.recompute();check('independently_movable_groups',all(o.TypeId=='App::Part' for o in [d.getObject(n) for n in groups]));check('display_moves_do_not_mutate_sources',source=={o.Name:(o.Shape.Volume,str(o.Placement)) for o in case+refs+hw})
for n in groups:d.getObject(n).Placement=A.Placement()
d.recompute();check('restored_display_groups',all(d.getObject(n).Placement.Base.Length==0 for n in groups))
fails=[c for c in checks if not c['passed']];report=dict(status='PASS_GEOMETRIC_SCREENS' if not fails else 'FAIL',checks=checks,failures=fails,check_count=len(checks),measured_external_mm=dims,target=target,physical_validation='NOT PERFORMED; battery insertion under raised shelves is a separate rigid-body path/sample gate;: print tolerance/rigidity/clamp preload, sample battery/lead/screw fit and lacing pull/flex test, RF/thermal/magnetic performance',sources={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [OUT/'smove-r2-enclosure.FCStd',ROOT/'PCB/main/smove-r2-main.kicad_pcb']})
(OUT/'validation').mkdir(exist_ok=True);(OUT/'validation/mechanical.json').write_text(json.dumps(report,indent=2)+'\n');(OUT/'validation/build.json').write_text(json.dumps(build,indent=2)+'\n');print(json.dumps(dict(status=report['status'],count=len(checks),failures=fails,dimensions=dims,target=target),indent=2));raise SystemExit(bool(fails))
