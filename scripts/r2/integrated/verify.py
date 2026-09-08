#!/usr/bin/python3
"""Scoped post-ECO assertions against two genuine baseline XML netlists/native source.
No relaxed severities/exclusions; measured net/part/package equivalence, not physical approval.
"""
from pathlib import Path
import json,subprocess as sp,xml.etree.ElementTree as ET,csv,collections,hashlib,math
import pcbnew as p
from migrate import ROOT,H,C,BASE,old
from sexp import *
O=ROOT/'docs/revision-r2/integrated/validation';O.mkdir(parents=True,exist_ok=True);checks=[]
def check(n,ok,detail=None):checks.append(dict(check=n,passed=bool(ok),detail=detail))
def run(args):sp.run([str(v) for v in args],check=True,stdout=sp.DEVNULL)
def pins(file):
 t=ET.parse(file);return {(n.attrib['ref'],n.attrib['pin']):v.attrib['name'] for v in t.findall('./nets/net') for n in v.findall('node') if not n.attrib['ref'].startswith('#')}
run(['kicad-cli','sch','export','netlist','--format','kicadxml','-o',O/'post-main.xml',H/'smove-r2-main.kicad_sch']);after=pins(O/'post-main.xml')
# Latest intentional removals, compared by actual endpoint groups (names may change scope).
before=pins(O/'centered/baseline.xml');removed={k for k in before if k[0]=='J3' or k[0].startswith('TP')};new_nc={('U1','30'),('U1','31'),('U2','12')}
check('exact_intentional_removal',set(before)-set(after)==removed,sorted(removed))
check('no_unrequested_new_electrical_parts',set(after)-set(before)==set())
migrations=[]
for k,n in before.items():
 if k in removed:continue
 if k in new_nc:check('restored_NC:'+'.'.join(k),after[k].startswith('unconnected-'));continue
 expected={p0 for p0,n0 in before.items() if n0==n and p0 not in removed|new_nc}
 actual={p0 for p0,n0 in after.items() if n0==after[k]}
 check('preserved_net_endpoints:'+'.'.join(k),expected==actual,dict(before=n,after=after[k]))
 migrations.append(dict(ref=k[0],pin=k[1],before=n,after=after[k]))
(O/'centered/net-migrations.json').write_text(json.dumps(dict(intentional_removals=sorted(removed),restored_nc=sorted(new_nc),retained=migrations),indent=2)+'\n')
b=p.LoadBoard(str(H/'smove-r2-main.kicad_pcb'));fps={f.GetReference():f for f in b.GetFootprints()};parts=json.loads((H/'parts-main.json').read_text());oldparts=json.loads(old('PCB/main/parts-main.json'))
check('single_integrated_population',set(fps)==set(parts)|{'H1','H2'} and len(fps)==49 and sum(v['fitted'] for v in parts.values())==47)
for r,v in parts.items():
 f=fps[r];check('source_pose:'+r,parts[r]['placement']==[*list(p.ToMM(f.GetPosition())),f.GetOrientationDegrees()]);check('top_side:'+r,not f.IsFlipped())
 for pad in f.Pads():
  if not pad.GetNumber():continue
  check('PCB_net:'+r+'.'+pad.GetNumber(),pad.GetNetname()==after.get((r,pad.GetNumber()),''),dict(pcb=pad.GetNetname(),schematic=after.get((r,pad.GetNumber()),'')))
 if r in oldparts:check('preserved_main_MPN:'+r,v['mpn']==oldparts[r]['mpn'] and v.get('jlc')==oldparts[r].get('jlc'))
 if r.startswith('TP'):
  pad=next(iter(f.Pads()));check('safe_testpad:'+r,tuple(p.ToMM(pad.GetSize()))==(1.,1.) and not pad.IsOnLayer(p.F_Paste) and f.IsExcludedFromBOM() and f.IsExcludedFromPosFiles())
# Preserve exact carrier package/pad geometry under actual component rotation/translation.
c=p.LoadBoard(str(C/'smove-imu-carrier.kicad_pcb'))
for cf in c.GetFootprints():
 r=cf.GetReference()
 if r not in parts:continue
 f=fps[r];a=math.radians(f.GetOrientationDegrees()-cf.GetOrientationDegrees());cx,cy=p.ToMM(cf.GetPosition());x,y=p.ToMM(f.GetPosition())
 for cp in cf.Pads():
  np=next(pad for pad in f.Pads() if pad.GetNumber()==cp.GetNumber());px,py=p.ToMM(cp.GetPosition());u,v=px-cx,py-cy;ex=(x+math.cos(a)*u+math.sin(a)*v,y-math.sin(a)*u+math.cos(a)*v)
  check('actual_carrier_pad_transfer:'+r+'.'+cp.GetNumber(),math.dist(p.ToMM(np.GetPosition()),ex)<1e-6 and tuple(p.ToMM(np.GetSize()))==tuple(p.ToMM(cp.GetSize())))
check('sensor_at_upper_centre',parts['U2']['mpn']=='ICM-20948' and parts['U2']['placement']==[112.5,117.5,-90.])
for text in ['RESET','BOOT','U2 +Z']:check('native_silk:'+text,sum(isinstance(t,p.PCB_TEXT) and t.GetText()==text and t.GetLayer()==p.F_SilkS for t in b.GetDrawings())==1)
check('all_external_debug_removed',not any(r=='J3' or r.startswith('TP') for r in fps) and not any('UART' in t.GetNetname() for t in b.GetTracks()))
from centered import HOLES
for r,xy in HOLES.items():
 f=fps[r];pad=next(iter(f.Pads()));check('M3_NPTH:'+r,list(p.ToMM(f.GetPosition()))==list(xy) and tuple(p.ToMM(pad.GetDrillSize()))==(3.2,3.2) and pad.GetAttribute()==p.PAD_ATTRIB_NPTH)
 exclusion=p.SHAPE_CIRCLE(f.GetPosition(),p.FromMM(3.45))
 for ff in fps.values():
  if ff.GetReference() in HOLES:continue
  check('M3_component_clear:'+r+':'+ff.GetReference(),not p.SHAPE.Collide(exclusion,ff.GetCourtyard(p.F_CrtYd)))
  for pp in ff.Pads():check('M3_all_layer_pad_clear:'+r+':'+ff.GetReference()+'.'+pp.GetNumber(),not p.SHAPE.Collide(exclusion,pp.GetEffectiveShape(p.F_Cu)))
comp=parse((H/'compute.kicad_sch').read_text());check('RGB_single_placed_symbol',sum(prop(s,'Reference')=='D1' for s in many(comp,'symbol'))==1)
root=parse((H/'smove-r2-main.kicad_sch').read_text());check('dedicated_four_functional_pages',set(prop(s,'Sheetname') for s in many(root,'sheet'))=={'USB','Power','Compute','IMU'});check('visible_hierarchy_wires',len(many(root,'wire'))>=15)
pro=json.loads((H/'smove-r2-main.kicad_pro').read_text());basepro=json.loads(old('PCB/main/smove-r2-main.kicad_pro'));check('unchanged_manufacturing_rules',pro==basepro and (H/'smove-r2-main.kicad_dru').read_text()==old('PCB/main/smove-r2-main.kicad_dru'))
check('four_layer_reference_plane_no_signals',b.GetCopperLayerCount()==4 and not any(t.GetLayer()==p.In1_Cu and not isinstance(t,p.PCB_VIA) for t in b.GetTracks()))
for typ in ['erc','drc']:
 args=['kicad-cli','sch' if typ=='erc' else 'pcb',typ,'--format','json','--severity-all']
 if typ=='drc':args+=['--all-track-errors','--schematic-parity']
 out=O/f'post-main-{typ}.json';run(args+['-o',out,H/('smove-r2-main.kicad_sch' if typ=='erc' else 'smove-r2-main.kicad_pcb')]);j=json.loads(out.read_text());v=[x for s in j.get('sheets',[]) for x in s['violations']] if typ=='erc' else j['violations']+j['unconnected_items']+j['schematic_parity'];check('native_'+typ+'_zero',not v,len(v))
# Exact baseline RF keepout polygon unchanged; no foreign copper is allowed on any layer.
baseline=parse(old('PCB/main/smove-r2-main.kicad_pcb'));raw=parse((H/'smove-r2-main.kicad_pcb').read_text());z=next(z for z in many(raw,'zone') if many(z,'name') and val(one(z,'name')[1])=='ANTENNA_ALL_LAYERS');bz=next(z for z in many(baseline,'zone') if many(z,'name') and val(one(z,'name')[1])=='ANTENNA_ALL_LAYERS');expected_poly=__import__('copy').deepcopy(one(bz,'polygon'));
for pt in one(expected_poly,'pts')[1:]:pt[1]=str(float(pt[1])+1.7)
check('RF_keepout_preserved',all(abs(float(a)-float(c))<1e-6 for pp,qq in zip(one(one(z,'polygon'),'pts')[1:],one(expected_poly,'pts')[1:]) for a,c in zip(pp[1:],qq[1:])) and one(z,'keepout')==one(bz,'keepout') and one(z,'layers')==one(bz,'layers'))
with (H/'dist/BOM.csv').open() as f:rows=list(csv.DictReader(f))
bomrefs=[r for row in rows for r in row['Designator'].split(',')];check('BOM_47_exact',set(bomrefs)=={r for r,v in parts.items() if v['fitted']} and len(bomrefs)==47)
# Actual copper lengths, NOT latency/EMC/rise-time approval. No optional probes remain. USB impedance/eye and rail-load drops require manufacturer stack/bench qualification.
lengths=collections.defaultdict(float)
for t in b.GetTracks():
 if not isinstance(t,p.PCB_VIA):lengths[t.GetNetname()]+=p.ToMM(t.GetLength())
minimums=dict(track_width_mm=min(p.ToMM(t.GetWidth()) for t in b.GetTracks() if not isinstance(t,p.PCB_VIA)),via_drill_mm=min(p.ToMM(t.GetDrillValue()) for t in b.GetTracks() if isinstance(t,p.PCB_VIA)))
failed=[c for c in checks if not c['passed']];report=dict(status='PASS' if not failed else 'FAIL',baseline_commit=BASE,check_count=len(checks),checks=checks,failures=failed,net_copper_lengths_mm=dict(sorted(lengths.items())),manufacturing_minimums=minimums,notes='Configured severities only; unchanged ignored defaults/exclusions retained. No RF/thermal/ESD/battery/load/printed-fit approval.')
(O/'electrical.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(status=report['status'],checks=len(checks),failures=failed,minimums=minimums),indent=2));raise SystemExit(bool(failed))
