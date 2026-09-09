"""Read-only CAD fit verification. No PCB or FCStd saves; fail on any failed check.
Geometric checks are NOT print, strength, insulation, pouch or RF qualification.
"""
import hashlib,json,math,sys
from pathlib import Path
import FreeCAD as A,Part,Mesh
R=Path(__file__).resolve().parents[3]; H=R/'housing'; V=H/'validation'
D=A.openDocument(str(H/'smove-r2-enclosure.FCStd')); B=json.loads((V/'build.json').read_text())
checks=[]
def ck(n,ok,detail=None):checks.append(dict(check=n,passed=bool(ok),detail=detail))
def sh(n):return D.getObject(n).Shape
def overlap(a,b):return a.common(b).Volume
def separated(n,a,b):
    vol=overlap(a,b);ck(n,vol<1e-6,round(vol,9));return vol
def moved(shape,x=0,y=0,z=0):
    q=shape.copy();q.translate(A.Vector(x,y,z));return q
def dist(a,b):return a.distToShape(b)[0]
def bounds(shape):
    b=shape.BoundBox;return [b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax]
base,lid,pcb=sh('Base'),sh('Lid'),sh('MainPCB')
physical=['Base','Lid']+B['reference_objects']+B['hardware_objects']
for n in physical:ck('valid_solid:'+n,sh(n).isValid() and len(sh(n).Solids)>=1,{'solids':len(sh(n).Solids),'volume':sh(n).Volume})
ck('exactly_two_printed_parts',B['printed_parts']==2 and sorted(o.Name for o in D.Objects if getattr(o,'Role','')=='print' and o.TypeId!='App::Link')==['Base','Lid'])
ck('no_removable_divider',D.getObject('BatteryDivider') is None and D.getObject('ViewDivider') is None)
ck('source_pcb_hash',hashlib.sha256((R/'PCB/main/smove-r2-main.kicad_pcb').read_bytes()).hexdigest()==B['input_hash'])
separated('base_lid_no_penetration',base,lid)
for n in B['reference_objects']+B['hardware_objects']:
    for case in ['Base','Lid']:separated(case+'_no_penetration:'+n,sh(case),sh(n))
components=[n for n in B['reference_objects'] if n.startswith('Main_')]
for n in ['BatteryWire1','BatteryWire2','BareWire1','BareWire2','ClosureScrew','ClosureNut']:
    separated('pcb_no_penetration:'+n,pcb,sh(n))
    for c in components:separated('component_clear:'+n+':'+c,sh(c),sh(n))
reserve=sh('BatteryAcceptance_21x31x4_3')
for n in ['Base','Lid','MainPCB','Main_USB_ShellTails','ClosureScrew','ClosureNut']:
    separated('pack_reserve_clear:'+n,reserve,sh(n))
# The two leads intentionally end at the pack's side boundary; do not pretend those terminals are pack geometry.
for i in (1,2):
    separated('cell_wire_no_penetration:'+str(i),sh('BatteryCandidate_UNQUALIFIED'),sh('BatteryWire'+str(i)))
separated('independent_insulated_leads',sh('BatteryWire1'),sh('BatteryWire2'))
rf=sh('RF_NO_BATTERY_HARNESS_METAL');rf_dist={}
for n in ['BatteryAcceptance_21x31x4_3','BatteryWire1','BatteryWire2','BareWire1','BareWire2','SolderFillet1','SolderFillet2','ClosureScrew','ClosureNut']:
    separated('RF_exclusion:'+n,rf,sh(n));rf_dist[n]=dist(rf,sh(n))
for case in ['Base','Lid']:separated('USB_plug_clear:'+case,sh('USBPlugReserve'),sh(case))
# Full translational sweep of maximum admitted pack through the south entry (lid OFF).
pack_sweep=Part.makeBox(21.,71.,4.3,A.Vector(2.,-33.5,1.8))
separated('pack_insertion_continuous_swept_volume',base,pack_sweep)
# Up/down PCB loading sampled at dense final approach plus larger heights. It is top-loaded, not slid over parts.
pcbgroup=Part.makeCompound([pcb]+[sh(n) for n in components])
for z in (0,.1,.25,.5,1,2,4,8,16,30):separated('PCB_vertical_insertion_z'+str(z),base,moved(pcbgroup,z=z))
# Actual lid sequence: down 1.5 mm south of final, then north 1.5 mm; screw fitted LAST.
fixed=Part.makeCompound([base,pcb]+[sh(n) for n in B['reference_objects'] if n!='MainPCB']+[sh('ClosureNut')])
for z in (12,6,3,1,.5,.2,0):separated('lid_lowering_z'+str(z),fixed,moved(lid,y=-1.5,z=z))
for y in (-1.5,-1.25,-1.,-.75,-.5,-.25,0):separated('lid_sliding_y'+str(y),fixed,moved(lid,y=y))
# Nut side-load BEFORE lid; seat against roof. Its entry is blocked by the lid door after assembly.
for x in (-8,-6,-4,-2,-1,0):separated('nut_side_insertion_x'+str(x),base,moved(sh('ClosureNut'),x=x))
# Assembly dimensions use physical objects only, not RF/USB reserves or display offsets.
bb=Part.makeCompound([sh(n) for n in physical]).BoundBox;dims=[bb.XLength,bb.YLength,bb.ZLength]
ck('actual_external_dimensions',all(abs(a-b)<1e-6 for a,b in zip(dims,[36.8,42.,16.6])),dims)
ck('pcb_size_and_body_frame',all(abs(a-b)<1e-6 for a,b in zip(bounds(pcb),[0,9,9.6,25,39,10.6])),bounds(pcb))
ck('IMU_above_PCB_outward',sh('Main_U2').BoundBox.ZMin>=10.6)
# Dimensional acceptance stack: not probabilistic, no RSS and no reliance on solder mask.
metrics={
 'battery_acceptance_mm':[31,21,4.3], 'battery_nominal_mm':[30,20,3],
 'battery_reserved_top_gap_mm':6.6-6.1,'barrier_thickness_mm':.8,
 'USB_tail_to_barrier_nominal_mm':8.4-7.4,'USB_tail_to_barrier_with_0_15_print_error_mm':8.4-7.4-.15,
 'groove_free_height_mm':11.15-9.6,'groove_min_no_clamp_play_mm':1.55-1.1-.15-.1,
 'XY_each_side_nominal_mm':.3,'XY_each_side_min_mm':.3-.15-.1,
 'H1_stop_gap_nominal_mm':9.6-9.25,'H1_stop_gap_min_mm':.35-.15-.15,
 'H1_stop_radius_mm':2.2,'H1_filled_copper_radius_mm':3.442612,
 'H1_stop_to_copper_nominal_mm':3.442612-2.2,
 'H1_stop_to_copper_adverse_stack_mm':3.442612-2.2-.3-.15-.15-.1,
 'screw_shank_clearance_radial_mm':1.8-1.5,'head_recess_clearance_radial_mm':3.5-2.84,
 'lid_bearing_thickness_mm':13.2-12.,'lid_bearing_min_mm':1.2-.15-.15,
 'nut_capture_roof_mm':12.-8.,'nut_full_thread_length_mm':2.4,'effective_thread_overlap_after_0_4_chamfer_reserve_mm':1.7,
 'screw_tip_z_mm':5.2,'screw_tip_min_floor_mm':5.2-4.2-.29-.15,
 'nut_engaged_nominal_mm':min(13.2,8.)-max(5.2,5.6),
 'nut_engaged_adverse_mm':min(13.2-.15,8.-.15)-max(5.2+.29+.15,5.6+.15),
 'screw_head_to_PCB_nominal_mm':dist(sh('ClosureScrew'),pcb),
 'hardware_to_pack_reserve_mm':min(dist(sh(n),reserve) for n in ('ClosureScrew','ClosureNut')),
 'RF_distances_mm':rf_dist,
 'button_access_diameter_mm':3.3,'RGB_access_diameter_mm':3.8,
 'lid_hook_nominal_engagement_mm':1.0,'lid_hook_adverse_engagement_mm':1.-.2-.15-.15,
 'PCB_groove_support_span_y_mm':28.,'PCB_groove_support_span_x_mm':24.7,
 'wire_OD_max_mm':1.2,'wire_centerline_bend_radius_mm':2.,
}
for n in ['battery_reserved_top_gap_mm','USB_tail_to_barrier_with_0_15_print_error_mm','groove_min_no_clamp_play_mm','XY_each_side_min_mm','H1_stop_gap_min_mm','H1_stop_to_copper_adverse_stack_mm','lid_bearing_min_mm','screw_tip_min_floor_mm','nut_engaged_adverse_mm','lid_hook_adverse_engagement_mm']:
    ck('positive_tolerance_stack:'+n,metrics[n]>0,metrics[n])
ck('screw_is_not_at_H1',B['screw_xy_mm']!=B['H1_xy_mm'])
ck('nut_effective_engagement_min',metrics['nut_engaged_adverse_mm']>=2.)
# Gauge requirements cover eccentricity as well as printer error.
ck('head_recess_tolerance_stack',3.5-2.84-.3-.15-.15>0,3.5-2.84-.3-.15-.15)
ck('blind_bore_tolerance_stack',metrics['screw_tip_min_floor_mm']>=.5)
# Individual STEP/STL consistency, solid closure/manifold and volume.
exports={}
for name in ('base','lid'):
    mesh=Mesh.Mesh(str(H/'dist'/f'{name}.stl'))
    nonmanifold=mesh.hasNonManifolds();solid=mesh.isSolid();consistent=not mesh.hasNonUniformOrientedFacets()
    ck('STL_closed_manifold:'+name,solid and not nonmanifold and consistent,{'solid':solid,'nonmanifolds':nonmanifold,'consistent_orientation':consistent})
    vol=abs(mesh.Volume);native=sh(name.capitalize()).Volume
    ck('STL_volume_matches:'+name,abs(vol-native)/native<.005,{'native':native,'stl':vol})
    exports[name]={'facets':mesh.CountFacets,'stl_volume_mm3':vol,'native_volume_mm3':native,'closed_manifold':solid and not nonmanifold,'consistent_orientation':consistent}
step=Part.Shape();step.read(str(H/'dist/smove-r2-printable.step'))
ck('STEP_two_valid_solids',step.isValid() and len(step.Solids)==2,len(step.Solids))
ck('STEP_volume_matches_native',abs(step.Volume-base.Volume-lid.Volume)<1e-4)
assembly_step=Part.Shape();assembly_step.read(str(H/'dist/smove-r2-assembly.step'))
ck('assembly_STEP_valid_matching_solid_count',assembly_step.isValid() and len(assembly_step.Solids)==sum(len(sh(n).Solids) for n in physical))
ck('assembly_STEP_volume_matches_native',abs(assembly_step.Volume-sum(sh(n).Volume for n in physical))<1e-3)
for n in B['inspection_groups']:ck('movable_native_group:'+n,D.getObject(n).TypeId=='App::Part')
result={'status':'PASS_GEOMETRIC_PROTOTYPE' if all(c['passed'] for c in checks) else 'FAIL','manufacturing_release':False,
        'measured_external_mm':dims,'metrics':metrics,'exports':exports,'checks':checks,'failed':[c for c in checks if not c['passed']],
        'method':'Open saved FCStd, native BRep intersections/distances, pack continuous translation swept solid, sampled PCB/lid/nut insertion, independent STEP and STL imports. No FEA or physical qualification.',
        'pcb_hash':B['input_hash']}
(V/'mechanical.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':result['status'],'checks':len(checks),'failed':result['failed'],'external_mm':dims},indent=2))
if result['failed']:sys.exit(1)
