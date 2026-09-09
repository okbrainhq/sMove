#!/usr/bin/python3
"""Read-only native board checks; writes evidence, never saves/regenerates the PCB.
Run after native CLI final ERC/DRC and netlist exports. Housing is deliberately not validated.
"""
import hashlib, json, math, subprocess as sp, sys
from pathlib import Path
import xml.etree.ElementTree as ET
import pcbnew as p
from sexp import parse, many, one, val, dump
R=Path(__file__).resolve().parents[3]; H=R/'PCB/main'; V=R/'docs/revision-r2/pcb-repair/validation'
BASE='554e4fe'; SELECTED='96e081b9b29db2bb852a43be9e6060a8a99aadf9'
checks=[]
def ck(n,ok,detail=None): checks.append(dict(check=n,passed=bool(ok),detail=detail))
def obj(rev,path): return sp.check_output(['git','show',rev+':'+str(path)])
def sha(data): return hashlib.sha256(data).hexdigest()
before=p.LoadBoard(str(R/'.cache/pcb-repair/baseline/smove-r2-main.kicad_pcb')); after=p.LoadBoard(str(H/'smove-r2-main.kicad_pcb'))
B={f.GetReference():f for f in before.GetFootprints()}; A={f.GetReference():f for f in after.GetFootprints()}
ck('same_references',set(A)==set(B))
def pins(b): return sorted((f.GetReference(),a.GetNumber(),a.GetNetname()) for f in b.GetFootprints() for a in f.Pads())
ck('baseline_final_native_pad_net_equivalence',pins(before)==pins(after),{'pad_count':len(pins(after))})
def netlist(path):
 root=ET.parse(path).getroot()
 return sorted((n.attrib['name'],sorted((v.attrib['ref'],v.attrib['pin']) for v in n.findall('node'))) for n in root.findall('nets/net'))
ck('baseline_final_schematic_net_equivalence',netlist(V/'baseline-netlist.xml')==netlist(V/'final-netlist.xml'))
protected=[H/'smove-r2-main.kicad_pro',H/'smove-r2-main.kicad_dru',*H.glob('*.kicad_sch'),*H.glob('*.kicad_sym')]
rule_hashes={}
for f in protected:
 rel=f.relative_to(R); data=f.read_bytes(); old=obj(BASE,rel)
 ck('unchanged_rules_or_schematic:'+f.name,data==old);rule_hashes[str(rel)]={'baseline':sha(old),'final':sha(data)}
for ref in sorted(A):
 a,b=A[ref],B[ref]
 ck('same_part_and_side:'+ref,a.GetValue()==b.GetValue() and (str(a.GetFPID().GetLibNickname()),str(a.GetFPID().GetLibItemName()))==(str(b.GetFPID().GetLibNickname()),str(b.GetFPID().GetLibItemName())) and a.IsFlipped()==b.IsFlipped())
 def pads(f): return sorted((a.GetNumber(),tuple(p.ToMM(a.GetSize())),tuple(p.ToMM(a.GetDrillSize())),int(a.GetAttribute()),a.GetLayerSet().FmtHex(),a.GetLocalSolderMaskMargin()) for a in f.Pads())
 ck('same_pad_geometry:'+ref,pads(a)==pads(b))
raw=parse((H/'smove-r2-main.kicad_pcb').read_text()); oldraw=parse(obj(BASE,'PCB/main/smove-r2-main.kicad_pcb').decode())
ck('unchanged_board_setup_and_stack',dump(one(raw,'setup'))==dump(one(oldraw,'setup')))
ck('exact_selected_native_pcb',(H/'smove-r2-main.kicad_pcb').read_bytes()==obj(SELECTED,'PCB/main/smove-r2-main.kicad_pcb'))
for name in ['final-drc.json','final-erc.json']:
 j=json.loads((V/name).read_text())
 issues=j.get('violations',[]) + j.get('unconnected_items',[]) + j.get('schematic_parity',[])
 if 'sheets' in j: issues += [v for sheet in j['sheets'] for v in sheet.get('violations',[])]
 ck('zero_issues:'+name,not issues,len(issues))
points=[p.ToMM(v) for e in after.GetDrawings() if e.GetLayer()==p.Edge_Cuts for v in [e.GetStart(),e.GetEnd()]]
size=[max(v[i] for v in points)-min(v[i] for v in points) for i in [0,1]]
ck('outline_25x30_no_growth',size==[25.,30.],size)
ck('In1_reference_has_no_signal_tracks',not any(not isinstance(t,p.PCB_VIA) and t.GetLayer()==p.In1_Cu for t in after.GetTracks()))
parts=json.loads((H/'parts-main.json').read_text());contract=json.loads((H/'native-layout-contract.json').read_text());interface=json.loads((H/'interface.json').read_text())
for r in A:
 pose=[*p.ToMM(A[r].GetPosition()),A[r].GetOrientationDegrees()]
 if r.startswith('H'):
  ck('source_mount:'+r,contract['mounting']['holes_native_xy_mm'][r]==pose[:2])
 else:
  ck('source_pose:'+r,parts[r]['placement']==pose and contract['placement'][r]==pose)
ck('interface_geometry_hash',interface['geometry_sha256']==sha((H/'smove-r2-main.kicad_pcb').read_bytes()))
ck('top_IMU_orientation',not A['U2'].IsFlipped() and A['U2'].GetOrientationDegrees()==-90)
ck('no_debug_testpoints',not any(r.startswith('TP') or r in ['J3','J4'] for r in A))
j2=sorted(A['J2'].Pads(),key=lambda a:a.GetNumber());pitch=(j2[0].GetPosition()-j2[1].GetPosition()).EuclideanNorm()/1e6
ck('BAT_pitch_drill_polarity',abs(pitch-2.54)<1e-6 and all(p.ToMM(a.GetDrillSize())==(1.,1.) for a in j2) and [a.GetNetname() for a in j2]==['/Power/PACK_P','GND'])
rf=next(z for z in after.Zones() if z.GetZoneName()=='ANTENNA_ALL_LAYERS')
rf_gap=min(rf.Outline().Distance(a.GetPosition())/1e6-max(p.ToMM(a.GetSize()))/2 for a in j2)
ck('BAT_copper_outside_RF_keepout',rf_gap>0,rf_gap)
pt=A['H1'].GetPosition();filled=[]
for z in after.Zones():
 if not z.GetIsRuleArea():
  for l in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]:
   if z.IsOnLayer(l):filled.append({'zone':z.GetZoneName(),'layer':after.GetLayerName(l),'radius_mm':z.GetFilledPolysList(l).Distance(pt)/1e6})
nearest=min(t.GetEffectiveShape().Distance(pt)/1e6 for t in after.GetTracks());hole_imu=(pt-A['U2'].GetPosition()).EuclideanNorm()/1e6
bearing_gap=min(x['radius_mm'] for x in filled)-3.4
# Deliberately record a failed release gate, not a DRC exclusion or nominal-mechanical PASS.
release={'manufacturing_release':False,'robust_insulation_approved':False,'legacy_bearing_radius_mm':3.4,'minimum_bearing_to_filled_copper_mm':bearing_gap,'blocker':'0.042612mm nominal margin is not a tolerance-qualified insulation design. H1/bearing/case assembly must be reviewed before manufacture/assembly.'}
ck('housing_marked_incompatible',interface['housing_compatibility']['status']=='INCOMPATIBLE_UNVALIDATED')
net_stats={}
for net in ['/USB_DP','/USB_DM','/Compute/USB_DP_MCU','/Compute/USB_DM_MCU','/Power/PACK_P','/Power/SYS','/VBUS','/3V3_MAIN','/IMU/1V8_IMU','/IMU/SCL_1V8','/IMU/SDA_1V8']:
 ts=[t for t in after.GetTracks() if t.GetNetname()==net and not isinstance(t,p.PCB_VIA)]
 net_stats[net]={'segments':len(ts),'min_width_mm':min((p.ToMM(t.GetWidth()) for t in ts),default=None),'length_mm':sum(t.GetLength()/1e6 for t in ts)}
# Compare USB geometry independent of UUID/net-code ordering.
def traces(b,net):
 return sorted((tuple(p.ToMM(t.GetStart())),tuple(p.ToMM(t.GetEnd())),t.GetLayerName(),p.ToMM(t.GetWidth()),isinstance(t,p.PCB_VIA)) for t in b.GetTracks() if t.GetNetname()==net)
usb={n:traces(before,n)==traces(after,n) for n in net_stats if 'USB_' in n}
result={'electrical_geometric_checks_passed':all(c['passed'] for c in checks),'checks':checks,'rule_hashes':rule_hashes,'net_geometry':net_stats,'USB_geometry_equal_baseline':usb,'measurements':{'board_size_mm':size,'BAT_pads_mm':[list(p.ToMM(a.GetPosition())) for a in j2],'BAT_to_RF_mm':rf_gap,'H1_mm':list(p.ToMM(pt)),'H1_IMU_distance_mm':hole_imu,'nearest_track_to_H1_center_mm':nearest,'filled_copper':filled},'release':release}
(V/'final-checks.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'checks':len(checks),'failed':[c['check'] for c in checks if not c['passed']],'USB_geometry_equal_baseline':usb,'release':release},indent=2))
if not result['electrical_geometric_checks_passed']: sys.exit(1)
