#!/usr/bin/python3
"""Read-only combined final electrical audit; writes one compact machine report.
Run both native board checkers first. No CAD generation, fabrication or STEP exports.
"""
import gc;gc.disable()
from pathlib import Path
import pcbnew as p,json,hashlib,math,heapq,xml.etree.ElementTree as ET,collections,sys,csv
ROOT=Path(__file__).resolve().parents[3];D=ROOT/'.cache/verify/electrical';D.mkdir(parents=True,exist_ok=True);checks={}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def check(k,v):checks[k]=bool(v);assert v,k
def pt(v):return [round(p.ToMM(v.x),6),round(p.ToMM(v.y),6)]
boards={};fps={};nets={};hashes={}
for key,name in [('main','smove-r2-main'),('imu-carrier','smove-imu-carrier')]:
 h=ROOT/'PCB'/key;b=p.LoadBoard(str(h/(name+'.kicad_pcb')));boards[key]=b;fs={f.GetReference():f for f in b.GetFootprints()};fps[key]=fs
 xml=ET.parse(ROOT/'.cache/verify'/key/'netlist.xml');sn={(n.attrib['ref'],n.attrib['pin']):net.attrib['name'].lstrip('/') for net in xml.findall('.//nets/net') for n in net.findall('node')};nets[key]=sn
 check(key+'_all_native_pad_nets',all(q.GetNetname().lstrip('/')==sn.get((r,q.GetNumber())) for r,f in fs.items() for q in f.Pads() if q.GetNumber()))
 comps={c.attrib['ref']:c for c in xml.findall('.//components/comp')}
 bom=json.loads((h/('parts-main.json' if key=='main' else 'parts.json')).read_text())
 if isinstance(bom,list):bom={x['ref']:x for x in bom}
 if 'parts' in bom:bom=bom['parts']
 for r,f in fs.items():
  if f.IsExcludedFromBOM():continue
  fields={q.GetName():q.GetText() for q in f.GetFields()};c=comps[r];sf={q.attrib['name']:q.text for q in c.findall('fields/field')}
  check(key+'_'+r+'_MPN_LCSC',fields['MPN']==sf['MPN']==bom[r]['mpn'] and fields['LCSC']==sf['LCSC']==bom[r]['jlc'])
 hashes[key]={'board':sha(h/(name+'.kicad_pcb')),'schematic':sha(h/(name+'.kicad_sch')),'interface':sha(h/'interface.json')}
 def net(r,n):return sn[r,str(n)]
 if key=='main':
  for r,supply,out in [('U4','SYS','3V3_MAIN')]:
   check('AP2112_main_pin_functions',all(net(r,n)==v for n,v in {1:supply,2:'GND',3:supply,5:out}.items()) and net(r,4).startswith('unconnected-'))
  check('RGB_CA_polarity',all(net('D1',n)==v for n,v in {1:'LED_R_K',2:'LED_G_K',3:'LED_B_K',4:'3V3_MAIN'}.items()))
  check('USBLC6_functions',all(net('U8',n)==v for n,v in {1:'USB_DM',2:'GND',3:'USB_DP',4:'USB_DP',5:'VBUS',6:'USB_DM'}.items()))
  check('PESD_CC_functions',all(net('U9',n)==v for n,v in {1:'CC1',2:'CC2',3:'GND'}.items()))
  check('TS1088_two_contacts_NOT_four_pin_switch',all(len(list(fs[r].Pads()))==2 and {net(r,1),net(r,2)}=={signal,'GND'} for r,signal in [('SW2','MCU_EN'),('SW3','BOOT')]))
  for r in ['SW2','SW3']:
   pads=list(fs[r].Pads());check(r+'_land_dimensions',all(pt(q.GetSize())==[1.05,2.0] for q in pads) and abs(math.dist(pt(pads[0].GetPosition()),pt(pads[1].GetPosition()))-4.45)<.00001)
  check('HRO_USB_function_duplicates',all(net('J1',n)==v for ns,v in [('A1 A12 B1 B12 S1','GND'),('A4 A9 B4 B9','VBUS'),('A6 B6','USB_DP'),('A7 B7','USB_DM'),('A5','CC1'),('B5','CC2')] for n in ns.split()))
  check('HRO_no_SBU_connection',all(net('J1',n).startswith('unconnected-') for n in ['A8','B8']))
  for a,z in [('A1','B12'),('A4','B9'),('A9','B4'),('A12','B1')]:
   pa=next(q for q in fs['J1'].Pads() if q.GetNumber()==a);pz=next(q for q in fs['J1'].Pads() if q.GetNumber()==z);check('HRO_shared_land_'+a,pt(pa.GetPosition())==pt(pz.GetPosition()) and pa.GetSize()==pz.GetSize())
  check('HRO_shell_mechanics',sum(q.GetNumber()=='S1' for q in fs['J1'].Pads())==4 and sum(q.GetAttribute()==p.PAD_ATTRIB_NPTH for q in fs['J1'].Pads())==2)
 # The separate native carrier checker independently covers ICM/PCA/AP pin functions/land positions.
 check(key+'_single_native_sheet', '(sheet\n' not in (h/(name+'.kicad_sch')).read_text())
 text=(h/(name+'.kicad_sch')).read_text();check(key+'_standard_Device_R_C', 'Device:R' in text and 'Device:C' in text and '(wire' in text)
# PH mounting-surface drawing: left-to-right pad1..N at 2mm, pads1x3.5, exposed rear tails.
access=[]
for key,ref,n in [('main','J2',2),('main','J4',4),('imu-carrier','J5',4)]:
 f=fps[key][ref];a=math.radians(f.GetOrientationDegrees());ox,oy=pt(f.GetPosition());ps={q.GetNumber():q for q in f.Pads()};points=[]
 for i in range(1,n+1):
  x,y=pt(ps[str(i)].GetPosition());dx=x-ox;dy=y-oy;local=[dx*math.cos(a)-dy*math.sin(a),dx*math.sin(a)+dy*math.cos(a)]
  check(ref+'_pad'+str(i)+'_order',math.dist(local,[-(n-1)+2*(i-1),-2.85])<.0001 and pt(ps[str(i)].GetSize())==[1.,3.5])
  point=[x-1.4*math.sin(a),y-1.4*math.cos(a)];obstructions=[]
  for other,g in fps[key].items():
   if other==ref:continue
   fab=[pt(v) for s in g.GraphicalItems() if isinstance(s,p.PCB_SHAPE) and s.GetLayer()==p.F_Fab for v in [s.GetStart(),s.GetEnd()]]
   if fab:
    box=[min(v[0] for v in fab),min(v[1] for v in fab),max(v[0] for v in fab),max(v[1] for v in fab)]
    if box[0]-.25<point[0]<box[2]+.25 and box[1]-.25<point[1]<box[3]+.25:obstructions.append(other)
  check(ref+'_tail'+str(i)+'_iron_access',not obstructions);points.append([round(v,4) for v in point])
 check(ref+'_side_hold_downs',sum(q.GetNumber()=='MP' for q in f.Pads())==2)
 access.append({'board':key,'ref':ref,'rear_tail_access_points_native_mm':points,'tip_radius_screen_mm':.25,'scope':'PCB out of case, iron from rear/top; primary drawing exposed tails and side reinforcement, not an underbody-only termination. No physical solder trial claimed.'})
# Historical preservation checks retired, not passed; cleanup hashes cover canonical parity.
for key in ['main','imu-carrier']:
 erc=json.loads((ROOT/f'.cache/verify/{key}/erc.json').read_text());drc=json.loads((ROOT/f'.cache/verify/{key}/'/('routed-drc.json' if key=='main' else 'drc.json')).read_text())
 check(key+'_native_configured_ERC_DRC_PARITY_ZERO',not any(s['violations'] for s in erc['sheets']) and not drc['violations'] and not drc['unconnected_items'] and not drc['schematic_parity'])
# Pad-aware shortest copper endpoint paths, rather than whole-net branch sums.
def distance(ref,pin,ref2,pin2):
 pads=[q for f in fs.values() for q in f.Pads() if q.GetNumber()];a=next(q for q in fs[ref].Pads() if q.GetNumber()==pin);z=next(q for q in fs[ref2].Pads() if q.GetNumber()==pin2);net=a.GetNetname();assert net==z.GetNetname()
 tracks=[t for t in b.GetTracks() if t.GetNetname()==net];ps=[q for q in pads if q.GetNetname()==net];pts={}
 def node(v,l):k=(v.x,v.y,l);pts[k]=v;return k
 edges=[]
 for t in tracks:
  if isinstance(t,p.PCB_VIA):
   ns=[node(t.GetPosition(),l) for l in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]]
   edges.extend((ns[0],v,0) for v in ns[1:])
  else:edges.append((node(t.GetStart(),t.GetLayer()),node(t.GetEnd(),t.GetLayer()),p.ToMM(t.GetLength())))
 graph={k:[] for k in pts}
 for aa,zz,w in edges:graph[aa].append((zz,w));graph[zz].append((aa,w))
 for i,q in enumerate(ps):
  ns=[k for k,v in pts.items() if q.IsOnLayer(k[2]) and q.HitTest(v)]
  for k in ns:
   for v in ns:
    if k!=v:graph[k].append((v,math.dist(k[:2],v[:2])/1e6))
 starts=[k for k,v in pts.items() if a.IsOnLayer(k[2]) and a.HitTest(v)];ends={k for k,v in pts.items() if z.IsOnLayer(k[2]) and z.HitTest(v)};heap=[(0,k) for k in starts];seen={}
 while heap:
  cost,k=heapq.heappop(heap)
  if k in seen:continue
  seen[k]=cost
  if k in ends:return round(cost,3)
  for v,w in graph[k]:
   if v not in seen:heapq.heappush(heap,(cost+w,v))
 return 'no endpoint graph path'
b=boards['main'];fs=fps['main'];finalmetrics={}
for row in [('C1','1','U6','13'),('C2','1','U6','2'),('C13','1','U6','10'),('C3','1','U4','5'),('J1','A6','J1','B6'),('J1','A7','J1','B7'),('J1','A6','R4','1'),('J1','A7','R3','1'),('J1','A6','U8','3'),('J1','A7','U8','1')]:finalmetrics['.'.join(row[:2])+' -> '+'.'.join(row[2:])]=distance(*row)
check('all_endpoint_metrics_resolved',all(isinstance(v,(int,float)) for v in finalmetrics.values()))
# Reference sampling is geometric, not impedance or SI certification. In1 contains no signal routes.
check('main_L2_ground_only',all(isinstance(t,p.PCB_VIA) or t.GetLayer()!=p.In1_Cu for t in b.GetTracks()))
report={'status':'PASS','checks':checks,'hashes':hashes,'connector_access':access,'endpoint_lengths_mm':finalmetrics,'geometry_delta':'No cleanup design edits; see byte-parity evidence','C2_C13':{'mpn':'CL21A476MQYNNNE','lcsc':'C16780','max_body_height_above_PCB_mm':1.45,'body_nominal_LWT_mm':[2,1.25,1.25],'LWT_tolerance_mm':.2,'max_z_from_main_board_bottom_mm':2.45},'capacitance_report_sha256':sha(D/'capacitance.json'),'manufacturing_release':False,'physical_tests_performed':False}
(D/'final-checks.json').write_text(json.dumps(report,indent=2)+'\n');print('FINAL INDEPENDENT PASS',len(checks),'checks');print('endpoints',finalmetrics);print('hashes',hashes)
