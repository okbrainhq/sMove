#!/usr/bin/python3
"""Prepare/import constrained routing. Never changes manufacturing rules to hide violations.
Clean removes only DRC-reported dangling/copper-conflicting routing, not component evidence.
"""
from pathlib import Path
import subprocess as sp,json,sys,hashlib
import pcbnew as p
from sexp import *
R=Path(__file__).resolve().parents[3];H=R/'PCB/main';B=H/'smove-r2-main.kicad_pcb';D=R/'.cache/integrated'
def refill():
 pro=(H/'smove-r2-main.kicad_pro').read_bytes();b=p.LoadBoard(str(B));b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(B),b);(H/'smove-r2-main.kicad_pro').write_bytes(pro)
def clean():
 removed=[]
 for i in range(100):
  sp.run(['kicad-cli','pcb','drc','--format','json','--severity-all','--all-track-errors','-o',str(D/'clean-drc.json'),str(B)],stdout=sp.DEVNULL,check=True)
  j=json.loads((D/'clean-drc.json').read_text());ids=set()
  a=parse(B.read_text());items={val(one(x,'uuid')[1]):x for x in a if isinstance(x,list) and x[0] in ['segment','via']}
  for v in j['violations']:
   if v['type'] in ['track_dangling','via_dangling','copper_edge_clearance','items_not_allowed','clearance','shorting_items']:
    for x in v['items']:
     if x['uuid'] in items:ids.add(x['uuid'])
  if not ids:break
  removed+=sorted(ids)
  a[:]=[x for x in a if not(isinstance(x,list) and x[0] in ['segment','via'] and val(one(x,'uuid')[1]) in ids)]
  B.write_text(dump(a)+'\n');refill()
 (D/'removed-routes.json').write_text(json.dumps(removed,indent=2)+'\n');print('cleaned',len(removed),'segments/vias in',i,'passes')
 if i==99:raise RuntimeError('cleanup did not converge')
def export():
 b=p.LoadBoard(str(B));assert p.ExportSpecctraDSN(b,str(D/'main.dsn'))
 a=parse((D/'main.dsn').read_text().replace('(string_quote ")','(string_quote QUOTE)'))
 # Copper reference plane is NOT a routing layer. Lock pre-existing USB/power/local IMU traces.
 struct=one(a,'structure')
 struct[:]=[x for x in struct if not(isinstance(x,list) and x[0]=='plane' and one(x,'polygon')[1]!='In1.Cu')]
 for rule in many(struct,'rule'):
  for c in many(rule,'clearance'):c[1]='155'
 for w in many(one(a,'wiring'),'wire'):
  if many(w,'type'):one(w,'type')[1]='fix'
  else:w.append(['type','fix'])
 # Netclass clearances must match >=.15mm design, not KiCad's unused .05mm default for SMD.
 for x in walk(one(a,'network')):
  if x[0]=='clearance':x[1]='155'
  if x[0]=='width' and float(x[1])<150:x[1]='150'
 network=one(a,'network');single={n[1] for n in many(network,'net') if len(one(n,'pins'))<3}
 network[:]=[x for x in network if not(isinstance(x,list) and x[0]=='net' and x[1] in single)]
 for cl in many(network,'class'):cl[:]=[x for i,x in enumerate(cl) if i<2 or isinstance(x,list) or x not in single]
 # Via copper .45/.2 baseline; preserve stack/netclasses, export no fabrication artifact here.
 (D/'main.dsn').write_text(dump(a).replace('(string_quote QUOTE)','(string_quote ")')+'\n')
 (D/'pre-route.kicad_pcb').write_bytes(B.read_bytes())
 print('DSN prepared')
def apply():
 pro=(H/'smove-r2-main.kicad_pro').read_bytes();b=p.LoadBoard(str(B));assert p.ImportSpecctraSES(b,str(D/'main.ses'));p.SaveBoard(str(B),b);(H/'smove-r2-main.kicad_pro').write_bytes(pro);refill()
def merge_fixed():
 a=parse(B.read_text());prev=parse((D/'pre-route.kicad_pcb').read_text());names={x[1]:val(x[2]) for x in many(prev,'net')};codes={val(x[2]):x[1] for x in many(a,'net')}
 def sig(x):return dump([n for n in x if not(isinstance(n,list) and n[0]=='uuid')])
 keys={sig(x) for x in a if isinstance(x,list) and x[0] in ['segment','via']};count=0
 for x in prev:
  if isinstance(x,list) and x[0] in ['segment','via']:
   one(x,'net')[1]=codes[names[one(x,'net')[1]]]
   if sig(x) not in keys:a.append(x);keys.add(sig(x));count+=1
 B.write_text(dump(a)+'\n');refill();print('Restored fixed routes omitted by SES:',count)
if __name__=='__main__':globals()[sys.argv[1]]()
