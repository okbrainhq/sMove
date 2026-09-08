#!/usr/bin/python3
"""Read-only native R2 MAIN invariant audit. Does not repair/reroute/edit any CAD.
Write only a compact report. Runs configured native ERC/DRC and net export first.
"""
from common import H,D,ROOT,PARTS,OUTLINE,RF_KEEPOUT,RETENTION
import pcbnew as p,json,hashlib,xml.etree.ElementTree as ET,collections,math,argparse
import subprocess
for args in [
 ['sch','erc','--format','json','--severity-all','--exit-code-violations','-o',str(D/'erc.json'),str(H/'smove-r2-main.kicad_sch')],
 ['sch','export','netlist','--format','kicadxml','-o',str(D/'netlist.xml'),str(H/'smove-r2-main.kicad_sch')],
 ['pcb','drc','--format','json','--severity-all','--all-track-errors','--schematic-parity','--exit-code-violations','-o',str(D/'routed-drc.json'),str(H/'smove-r2-main.kicad_pcb')]]:
 subprocess.run(['kicad-cli',*args],check=True)
not_applicable={'historical_preservation':'RETIRED, NOT PASSED; see docs/cleanup/README.md'}
b=p.LoadBoard(str(H/'smove-r2-main.kicad_pcb'));fps={f.GetReference():f for f in b.GetFootprints()};checks={}
def check(name,cond):
 checks[name]=bool(cond)
 if not cond:print('FAIL',name)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def point(v):return [round(p.ToMM(v.x),6),round(p.ToMM(v.y),6)]
xml=ET.parse(D/'netlist.xml');actual={}
for net in xml.findall('.//nets/net'):
 for node in net.findall('node'):actual[node.get('ref'),node.get('pin')]=net.get('name')
errors=[];pad_count=0
for r,f in fps.items():
 seen=set()
 for pad in f.Pads():
  n=pad.GetNumber()
  if not n:continue
  pad_count+=1;seen.add(n);name=pad.GetNetname();expected=PARTS[r]['pins'][n]
  if name!=actual.get((r,n)) or (expected is not None and name.lstrip('/')!=expected) or (expected is None and not name.startswith('unconnected-')):errors.append([r,n,name,expected])
 if seen!=set(PARTS[r]['pins']):errors.append([r,'physical pad set mismatch'])
check('all_schematic_physical_pad_and_handoff_nets_match',not errors)
check('exact_36_footprints_35_fitted',set(fps)==set(PARTS) and len(fps)==36 and sum(not bool(f.GetAttributes()&p.FP_EXCLUDE_FROM_BOM) for f in fps.values())==35)
check('top_smt_only_except_unpopulated_debug',all(f.GetLayer()==p.F_Cu for f in fps.values()) and bool(fps['J3'].GetAttributes()&p.FP_EXCLUDE_FROM_BOM))
check('four_copper_layers_one_mm',b.GetCopperLayerCount()==4 and b.GetDesignSettings().GetBoardThickness()==p.FromMM(1))
edges=[e for e in b.GetDrawings() if isinstance(e,p.PCB_SHAPE) and e.GetLayer()==p.Edge_Cuts]
check('outline_exact_25x35',len(edges)==4 and {tuple(point(e.GetStart())) for e in edges}=={tuple(x) for x in OUTLINE})
# Independent literal BQ pin functions; NOT taken from generator's symbol map.
truth={'1':'TS_NO_CELL_SENSING','2':'PACK_P','3':'PACK_P','4':'GND','5':'GND','6':'GND','7':'USB_POWER_N','8':'GND','9':None,'10':'SYS','11':'SYS','12':'CHG_ILIM','13':'VBUS','14':None,'15':None,'16':'CHG_ISET','17':'GND'}
physical={a.GetNumber():a for a in fps['U6'].Pads() if a.GetNumber()}
check('TI_BQ24074_all_17_functions_including_PGOOD7_VSS8_EP17',all((physical[n].GetNetname().lstrip('/')==net if net else physical[n].GetNetname().startswith('unconnected-')) for n,net in truth.items()))
# Primary RGT top-view numbering: left 1..4 downward, bottom 5..8 rightward,
# right 9..12 upward, top 13..16 leftward. Geometry independently calculated here.
expected={}
for i in range(4):
 expected[str(i+1)]=(-1.4,-.75+i*.5);expected[str(i+5)]=(-.75+i*.5,1.4);expected[str(i+9)]=(1.4,.75-i*.5);expected[str(i+13)]=(.75-i*.5,-1.4)
expected['17']=(0,0);ox,oy=point(fps['U6'].GetPosition())
check('TI_RGT_physical_numbering_not_legacy_symbol_labels',all(math.dist(point(physical[n].GetPosition()),[ox+x,oy+y])<1e-5 for n,(x,y) in expected.items()))
check('J4_frozen_pinout_no_host_pullups',all(actual['J4',n].lstrip('/')==net for n,net in {'1':'3V3_MAIN','2':'GND','3':'SDA_HOST','4':'SCL_HOST'}.items()) and not any(r.startswith('R') and any(v in ['SDA_HOST','SCL_HOST'] for v in c['pins'].values()) for r,c in PARTS.items()))
check('local_PHY_series_resistors',all(math.dist(point(fps[r].GetPosition()),point(next(a for a in fps['U1'].Pads() if a.GetNumber()==n).GetPosition()))<3 for r,n in [('R3','26'),('R4','27')]))
check('L2_no_signal_tracks',not any(not isinstance(t,p.PCB_VIA) and t.GetLayer()==p.In1_Cu for t in b.GetTracks()))
# Independent antenna test: physical copper bboxes must all be south of the exact RF boundary;
# all filled polygons independently checked, not merely trusting the rule-area declaration.
check('all_pad_track_via_copper_outside_antenna',all(p.ToMM(t.GetBoundingBox().GetY())>=100 for t in b.GetTracks()) and all(p.ToMM(a.GetBoundingBox().GetY())>=100 for f in fps.values() for a in f.Pads() if a.GetNumber()))
polys=[]
for z in b.Zones():
 if z.GetIsRuleArea():continue
 for layer in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]:
  if z.IsOnLayer(layer):polys.append((layer,z.GetFilledPolysList(layer)))
check('filled_copper_outside_antenna_all_layers',all(po.OutlineCount() and p.ToMM(po.BBox().GetY())>=100 for layer,po in polys))
# Rule zones exact on all four copper layers; independent dense retention-point coverage.
rules={z.GetZoneName():z for z in b.Zones() if z.GetIsRuleArea()}
check('RF_and_retention_rules_active_all_layers',len(rules)==3 and all(z.GetDoNotAllowPads() and z.GetDoNotAllowTracks() and z.GetDoNotAllowVias() and z.GetDoNotAllowCopperPour() and all(z.IsOnLayer(l) for l in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]) for z in rules.values()))
ret_clear=True
for ret in RETENTION:
 x0,y0=ret['xy'][0];x1,y1=ret['xy'][2]
 for layer,po in polys:
  for ix in range(11):
   for iy in range(11):
    if po.Contains(p.VECTOR2I(p.FromMM(x0+(x1-x0)*(ix+.5)/11),p.FromMM(y0+(y1-y0)*(iy+.5)/11))):ret_clear=False
check('retention_pour_voids_all_layers',ret_clear)
interface=json.loads((H/'interface.json').read_text())
check('interface_component_centers_and_rotations_match_native',all(point(f.GetPosition())==interface['components'][r]['anchor_native_xy_mm'] and abs((f.GetOrientationDegrees()-interface['components'][r]['rotation_ccw_deg'])%360)<1e-5 for r,f in fps.items()))
erc=json.loads((D/'erc.json').read_text());drc=json.loads((D/'routed-drc.json').read_text())
check('native_ERC_zero_errors_zero_warnings',not any(sh['violations'] for sh in erc['sheets']))
check('native_DRC_zero_violations_zero_opens_zero_parity',not drc['violations'] and not drc['unconnected_items'] and not drc['schematic_parity'])
tracks=collections.Counter(b.GetLayerName(t.GetLayer()) for t in b.GetTracks() if not isinstance(t,p.PCB_VIA));usb={n:round(sum(p.ToMM(t.GetLength()) for t in b.GetTracks() if not isinstance(t,p.PCB_VIA) and t.GetNetname()==n),3) for n in ['/USB_DM','/USB_DP','/USB_DM_MCU','/USB_DP_MCU']}
result={'status':'PASS' if all(checks.values()) else 'FAIL','scope':'Native CAD checks only. Exact-part screens and primary pin/footprint audit recorded in ../electrical-completion; no manufacture/charging approval.','checks':checks,'not_applicable':not_applicable,'physical_numbered_pads':pad_count,'fitted':35,'0402_count':sum(c['fp'].startswith(('R_0402','C_0402')) for c in PARTS.values()),'track_segments_by_layer':dict(tracks),'via_count':sum(isinstance(t,p.PCB_VIA) for t in b.GetTracks()),'usb_total_copper_lengths_mm_including_branches':usb,'pad_errors':errors,'pcb_sha256':sha(H/'smove-r2-main.kicad_pcb'),'schematic_sha256':sha(H/'smove-r2-main.kicad_sch'),'interface_sha256':sha(H/'interface.json'),'geometry_sha256':interface['geometry_sha256'],'cleanup_design_changes':'none'}
(D/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'],len(checks),'checks; 35 fitted,',result['0402_count'],'0402;',result['via_count'],'vias;',dict(tracks));print('USB lengths (branched copper)',usb)
raise SystemExit(0 if all(checks.values()) else 1)
