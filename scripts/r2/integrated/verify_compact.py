#!/usr/bin/python3
"""Read-only final PCB/placement/electrical comparison against f8c7ef6.
KiCad ERC/DRC and independent native FreeCAD solid checks are additional gates.
"""
import json, hashlib, subprocess as sp, math, sys, xml.etree.ElementTree as ET
from pathlib import Path
import pcbnew as p
from sexp import parse,many,one,val,prop
R=Path(__file__).resolve().parents[3];H=R/'PCB/main';E=R/'docs/revision-r2/compact-placement';V=E/'validation';C=R/'.cache/compact'
checks=[]
def ck(name,ok,detail=None):checks.append(dict(check=name,passed=bool(ok),detail=detail))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def old(path):return sp.check_output(['git','show','f8c7ef6:'+str(path.relative_to(R))])
base=C/'verify-baseline.kicad_pcb';base.write_bytes(old(H/'smove-r2-main.kicad_pcb'))
boards=[p.LoadBoard(str(base)),p.LoadBoard(str(H/'smove-r2-main.kicad_pcb'))];bf,af=[{f.GetReference():f for f in b.GetFootprints()} for b in boards]
ck('only_H2_mechanical_footprint_removed',set(bf)-set(af)=={'H2'} and not set(af)-set(bf))
ck('fitted_parts_46',sum(not f.IsExcludedFromBOM() for f in af.values())==46)
placements=[]
for r,f in af.items():
 before=bf[r]
 ck('same_part:'+r,f.GetValue()==before.GetValue() and (str(f.GetFPID().GetLibNickname()),str(f.GetFPID().GetLibItemName()))==(str(before.GetFPID().GetLibNickname()),str(before.GetFPID().GetLibItemName())) and f.IsFlipped()==before.IsFlipped())
 def pads(fp):
  return sorted([(a.GetNumber(),a.GetNetname(),tuple(p.ToMM(a.GetSize())),tuple(p.ToMM(a.GetDrillSize())),int(a.GetAttribute()),a.GetLocalSolderMaskMargin(),a.GetLayerSet().FmtHex()) for a in fp.Pads()])
 ck('same_pads_nets_drills_layers:'+r,pads(f)==pads(before))
 a=[*p.ToMM(f.GetPosition()),f.GetOrientationDegrees()];b=[*p.ToMM(before.GetPosition()),before.GetOrientationDegrees()]
 if a!=b:placements.append(dict(ref=r,before=b,after=a))
 ck('same_courtyard_area:'+r,abs(f.GetCourtyard(p.F_CrtYd).Area()-before.GetCourtyard(p.F_CrtYd).Area())<1e4)
for f in [H/'smove-r2-main.kicad_pro',H/'smove-r2-main.kicad_dru',*sorted(H.glob('*.kicad_sch')),*sorted(H.glob('*.kicad_sym'))]:ck('unchanged_rules_or_schematic:'+f.name,f.read_bytes()==old(f))
for r in ('U1','U2','U4','U5','U8','J1','C3','C4','C5','C6','C7','C8','C9','C10','C11','C13'):
 ck('critical_placement_retained:'+r,p.ToMM(af[r].GetPosition())==p.ToMM(bf[r].GetPosition()) and af[r].GetOrientationDegrees()==bf[r].GetOrientationDegrees())
for r in ('SW2','SW3'):
 f=af[r];x,y=p.ToMM(f.GetPosition());mapping={a.GetNumber():dict(net=a.GetNetname(),xy=list(p.ToMM(a.GetPosition()))) for a in f.Pads()}
 ck('switch_rotated_native_mapping:'+r,f.GetOrientationDegrees()==0 and mapping['1']['xy']==[x-2.225,y] and mapping['2']['xy']==[x+2.225,y] and mapping['2']['net']=='GND',mapping)
 ck('switch_contact_1_preserved:'+r,mapping['1']['net']==next(a.GetNetname() for a in bf[r].Pads() if a.GetNumber()=='1'))
j2={a.GetNumber():a for a in af['J2'].Pads()};pitch=(j2['1'].GetPosition()-j2['2'].GetPosition()).EuclideanNorm()/1e6
ck('J2_2_54mm_centre_pitch',abs(pitch-2.54)<1e-6,pitch)
ck('J2_two_1mm_PTH_2mm_pads',len(j2)==2 and all(a.GetAttribute()==p.PAD_ATTRIB_PTH and p.ToMM(a.GetDrillSize())==(1.,1.) and p.ToMM(a.GetSize())==(2.,2.) for a in j2.values()))
ck('J2_not_fitted_or_CPL',af['J2'].IsExcludedFromBOM() and af['J2'].IsExcludedFromPosFiles())
ck('no_UART_or_testpoints',not any(r.startswith('TP') or r in ('J3','J4','J5') or 'Debug' in str(f.GetFPID().GetLibItemName()) for r,f in af.items()))
ck('single_top_RGB',len([r for r in af if r.startswith('D')])==1 and not af['D1'].IsFlipped())
ck('In1_GND_reference_only',not any(type(t)==p.PCB_TRACK and t.GetLayer()==p.In1_Cu for t in boards[1].GetTracks()))
# No process change to filled/capped via-in-pad: vias stay clear of all SMT paste pads.
hits=[]
for via in boards[1].GetTracks():
 if type(via)!=p.PCB_VIA:continue
 for r,f in af.items():
  for pad in f.Pads():
   if pad.GetAttribute()==p.PAD_ATTRIB_SMD and p.SHAPE.Collide(via.GetEffectiveShape(),pad.GetEffectiveShape(p.F_Cu)):hits.append([r,pad.GetNumber(),list(p.ToMM(via.GetPosition()))])
ck('no_via_copper_overlap_with_SMT_pads',not hits,hits)
# Exact RF rule geometry/permissions retained, not only visual outline.
def rule(b,name):
 z=next(z for z in b.Zones() if z.GetZoneName()==name);poly=z.Outline().COutline(0)
 return dict(points=[list(p.ToMM(poly.CPoint(i))) for i in range(poly.PointCount())],layers=z.GetLayerSet().FmtHex(),tracks=z.GetDoNotAllowTracks(),vias=z.GetDoNotAllowVias(),copper=z.GetDoNotAllowCopperPour())
ck('RF_all_layer_exclusion_unchanged',rule(boards[0],'ANTENNA_ALL_LAYERS')==rule(boards[1],'ANTENNA_ALL_LAYERS'))
ck('M3_copper_exclusion_unchanged',rule(boards[0],'H1_M3_NO_COPPER')==rule(boards[1],'H1_M3_NO_COPPER'))
for name in ('SW_KEY_NO_COPPER','SE_KEY_NO_COPPER'):ck('positive_key_copper_exclusion:'+name,all(rule(boards[1],name)[k] for k in ('tracks','vias','copper')))
interface=json.loads((H/'interface.json').read_text());orig=json.loads(old(H/'interface.json'))
for key in ('accel_gyro_to_body','mag_to_body','accel_gyro_to_board','magnetometer_to_board'):
 if key in orig['sensor_frame']:ck('sensor_transform:'+key,orig['sensor_frame'][key]==interface['sensor_frame'][key])
ck('actual_ICM_top_orientation',af['U2'].GetValue()=='ICM-20948' and not af['U2'].IsFlipped() and af['U2'].GetOrientationDegrees()==-90)
ck('sensor_width_centre_central_region',interface['sensor_frame']['centre_offset_native_mm']==[0,2.5],interface['sensor_frame'])
# Every baseline endpoint set is retained; no net migration in this placement-only revision.
sp.run(['kicad-cli','sch','export','netlist','--format','kicadxml','-o',str(V/'post-netlist.xml'),str(H/'smove-r2-main.kicad_sch')],check=True,stdout=sp.DEVNULL)
def nets(path):return {n.get('name'):sorted((x.get('ref'),x.get('pin')) for x in n.findall('node')) for n in ET.parse(path).findall('.//nets/net')}
nb,na=nets(V/'baseline-netlist.xml'),nets(V/'post-netlist.xml');ck('exact_net_endpoint_equivalence',nb==na,dict(baseline_nets=len(nb),post_nets=len(na),endpoints=sum(len(v) for v in na.values())))
ck('current_interface_hash',interface['geometry_sha256']==sha(H/'smove-r2-main.kicad_pcb'))
for r,rec in interface['components'].items():ck('interface_current_pose:'+r,rec['anchor_native_xy_mm']==list(p.ToMM(af[r].GetPosition())) and rec['rotation_ccw_deg']==af[r].GetOrientationDegrees())
# Straight-line pad-to-pad proximity is a placement metric, not a routed-loop/SI certification.
decoupling=[]
for c,u in [('C1','U6'),('C2','U6'),('C3','U4'),('C4','U1'),('C5','U5'),('C6','U5'),('C7','U2'),('C8','U2'),('C9','U2')]:
 values=[]
 for fs in (bf,af):
  ds=[(a.GetPosition()-b.GetPosition()).EuclideanNorm()/1e6 for a in fs[c].Pads() for b in fs[u].Pads() if a.GetNetname()==b.GetNetname() and a.GetNetname()!='GND'];values.append(min(ds) if ds else None)
 decoupling.append(dict(cap=c,IC=u,nearest_matching_nonground_pad_mm_before_after=values))
 if None not in values:ck('decoupling_proximity_not_worse:'+c,values[1]<=values[0]+.01,values)
outline=interface['outline_native_xy_mm'];area=abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(outline,outline[1:]+outline[:1])))/2
ck('PCB_25x30x1',interface['board_size_mm']==[25,30] and abs(boards[1].GetDesignSettings().GetBoardThickness()/1e6-1)<1e-6)
dims=dict(PCB_before_mm=[25,35.5,1],PCB_after_mm=[25,30,1],bbox_area_reduction_pct=100*(1-30/35.5),outline_area_before_mm2=881.67,outline_area_after_mm2=area,lower_region_native_y_start_mm=122,lower_region_before_mm2=337.5,lower_region_after_mm2=200,lower_region_reduction_pct=100*(1-200/337.5),housing_before_LWH_mm=[46.8,29.4,19.6],housing_after_LWH_mm=[44.8,29.4,19.6],includes_recessed_M3x8=True,PCB_limit='Dense lower courtyard/routing, fixed upper USB/module/IMU. Three arrangements screened; not a global optimum claim.',housing_limit='Independent battery reserve 21x31x4.3, wire/lacing bay, RF/module overhang, walls and retained M3x8 vertical stack; nominal pouch 30x20x3 not compressed.')
(V/'dimensions.json').write_text(json.dumps(dims,indent=2)+'\n')
report=dict(status='PASS' if all(c['passed'] for c in checks) else 'FAIL',baseline='f8c7ef6',checks=checks,check_count=len(checks),failures=[c for c in checks if not c['passed']],changed_placements=placements,decoupling_placement_metrics=decoupling,routing_adjustment='After pre-route study, R22 translated 0.95mm left to permit U6.7 escape without via-in-pad; same outline and courtyard. All new vias ordinary, outside SMT pads.',manufacturing_release=False)
(V/'electrical.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(status=report['status'],checks=len(checks),failures=report['failures'],moved=len(placements)),indent=2));raise SystemExit(bool(report['failures']))
