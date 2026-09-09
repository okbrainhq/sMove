#!/usr/bin/python3
"""R2-only offline exports. Never loads legacy CFIX/global parts tables or saves native CAD."""
from pathlib import Path
import csv, hashlib, json, re, subprocess as sp, zipfile
import pcbnew as p
ROOT=Path(__file__).resolve().parents[3]
D=ROOT/'.cache/export'; D.mkdir(parents=True,exist_ok=True)
def sha(f): return hashlib.sha256(f.read_bytes()).hexdigest()
def dump(f,d): f.write_text(json.dumps(d,indent=2)+'\n')
def csvout(f,h,rows):
 with f.open('w',newline='') as s:
  w=csv.writer(s,lineterminator='\n');w.writerow(h);w.writerows(rows)
def run(tag,args):
 r=sp.run([str(a) for a in args],stdout=sp.PIPE,stderr=sp.STDOUT,text=True)
 (D/(tag+'.log')).write_text(r.stdout)
 assert r.returncode==0,(tag,r.stdout[-1500:])
 return r.stdout
def ignored(d,path=''):
 result={}
 if isinstance(d,dict):
  for k,v in d.items():
   if v=='ignore':result[path+k]=v
   elif isinstance(v,(dict,list)):result.update(ignored(v,path+k+'.'))
 elif isinstance(d,list):
  for i,v in enumerate(d):result.update(ignored(v,path+str(i)+'.'))
 return result
for key,name,count,manual in [('main','smove-r2-main',46,set())]:
 h=ROOT/'PCB'/key;m=ROOT/'PCB'/key/'dist';m.mkdir(parents=True,exist_ok=True)
 cad=h/(name+'.kicad_pcb');sch=h/(name+'.kicad_sch');pro=h/(name+'.kicad_pro')
 hashes={str(f.relative_to(ROOT)):sha(f) for f in [cad,pro,h/'interface.json',*sorted(h.glob('*.kicad_sch')),*sorted(h.glob('*.kicad_sym'))]}
 b=p.LoadBoard(str(cad));parts=json.loads((h/('parts-main.json' if key=='main' else 'parts.json')).read_text());parts={r:v for r,v in parts.items() if v.get('fitted',True)}
 fps={f.GetReference():f for f in b.GetFootprints() if not f.IsExcludedFromBOM() and not f.IsDNP()}
 assert set(fps)==set(parts) and len(fps)==count,(key,len(fps),set(fps)^set(parts))
 assert b.GetCopperLayerCount()==4
 origin=b.GetDesignSettings().GetAuxOrigin()
 def xy(q):return [round((q.x-origin.x)/1e6,6),round((origin.y-q.y)/1e6,6)]
 placements=[]
 for r in sorted(fps,key=lambda r:(re.sub('[0-9]','',r),int(re.search('[0-9]+',r)[0]))):
  f=fps[r];fields={v.GetName():v.GetText() for v in f.GetFields()}
  assert fields['MPN']==parts[r]['mpn'] and fields['LCSC']==parts[r]['jlc'] and not f.IsFlipped(),r
  pads=[q for q in f.Pads() if q.GetNumber()=='1']
  if not pads:pads=[q for q in f.Pads() if q.GetNumber()=='A1']
  assert pads,r
  placements.append(dict(reference=r,mpn=fields['MPN'],jlc=fields['LCSC'],footprint=str(f.GetFPID().GetLibItemName()),value=f.GetValue(),xy_mm=xy(f.GetPosition()),rotation_deg=f.GetOrientationDegrees()%360,layer='Top',pad_reference=pads[0].GetNumber(),pad_reference_mm=xy(pads[0].GetPosition()),pads=[dict(number=q.GetNumber(),xy_mm=xy(q.GetPosition()),net=q.GetNetname()) for q in f.Pads()]))
 if key=='main':
  assert parts['C2']['jlc']==parts['C13']['jlc']=='C16780'
  nets={q.GetNumber():q.GetNetname() for q in fps['U6'].Pads()};assert 'GND' in nets['8'] and 'POWER' in nets['7'],nets
 for obsolete in ['BOM-hand-solder-headers.csv','CPL-hand-solder-headers.csv','ManualParts.csv']:(m/obsolete).unlink(missing_ok=True)
 bh=['Comment','Designator','Footprint','LCSC Part #','Quantity','Manufacturer Part Number'];ch=['Designator','Mid X','Mid Y','Layer','Rotation']
 for suffix,omit in [('',set())]:
  pp=[v for v in placements if v['reference'] not in omit];groups={}
  for v in pp:groups.setdefault((v['jlc'],v['mpn'],v['footprint']),[]).append(v)
  csvout(m/('BOM'+suffix+'.csv'),bh,[[vv[0]['value'],','.join(v['reference'] for v in vv),fp,cid,len(vv),mpn] for (cid,mpn,fp),vv in groups.items()])
  csvout(m/'pick-and-place.csv',ch,[[v['reference'],*['%.6f'%a for a in v['xy_mm']],'Top','%.3f'%v['rotation_deg']] for v in pp])
  assert len(pp)==count-len(omit)
 dump(m/'assembly-placements.json',{'frame':'mm, top view, native auxiliary origin; X right, Y up; native footprint anchor/centroid, CCW angle. No guessed vendor rotation offsets.','aux_origin_native_mm':list(p.ToMM(origin)),'parts':placements})
 guide=['# R2 '+key+' assembly pin-reference / rotation guide','','Engineering prototype; manufacturing_release=false. BOM/CPL fits '+str(count)+' electronic parts. J2 is two PCB-only plated wire holes on 2.54mm centre pitch, NOT a JST/header and excluded from BOM/CPL. No battery connector or mating cable is purchased. Hand-solder qualified battery leads only after verifying polarity and pack charge/discharge suitability; fit the housing lacing restraint before closing.','','J2 holes: 1.0mm finished target (accept 0.9–1.1mm), 2.0mm pads. Wire envelope assumption: tinned bundle <=0.7mm, insulated OD <=1.2mm; no exact gauge supplied. Insulation stays below PCB; solder TOP and trim top protrusion <=0.6mm. BAT+ = protected PACK_P, BAT- = GND. Never solder directly on a pouch; keep each battery lead individually insulated until its connection is made; isolate the pack for service whenever the pack permits. No USB connected during assembly.','','All positions mm, TOP/component face, X right/Y up at native auxiliary/drill origin; KiCad CCW angles, not vendor rotation offsets. Check assembly preview. No external UART or testpoints. Two M3 NPTH mounting holes excluded from BOM/CPL.','','|Ref|MPN|X|Y|CCW deg|Reference pad|Pad X|Pad Y|','|---|---|---:|---:|---:|---|---:|---:|']
 for v in placements:guide.append('|'+ '|'.join(map(str,[v['reference'],v['mpn'],*v['xy_mm'],v['rotation_deg'],v['pad_reference'],*v['pad_reference_mm']]))+'|')
 (m/'ASSEMBLY.md').write_text('\n'.join(guide)+'\n')
 ed=ROOT/'.cache/verify'/key;ed.mkdir(parents=True,exist_ok=True)
 run(key+'-erc',['kicad-cli','sch','erc','--format','json','--severity-all','--exit-code-violations','-o',ed/'erc.json',sch])
 run(key+'-drc',['kicad-cli','pcb','drc','--format','json','--severity-all','--all-track-errors','--schematic-parity','--exit-code-violations','-o',ed/('routed-drc.json' if key=='main' else 'drc.json'),cad])
 fab=m/'gerbers';fab.mkdir(exist_ok=True)
 for f in fab.iterdir():
  if f.is_file():f.unlink()
 run(key+'-gerbers',['kicad-cli','pcb','export','gerbers','--layers','F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts,F.Paste','--use-drill-file-origin','-o',str(fab)+'/',cad])
 run(key+'-drills',['kicad-cli','pcb','export','drill','--format','excellon','--drill-origin','plot','--excellon-units','mm','--excellon-separate-th','-o',str(fab)+'/',cad])
 exts={f.suffix.lower() for f in fab.iterdir()};assert {'.gtl','.g1','.g2','.gbl','.gts','.gbs','.gto','.gbo','.gm1','.drl'}<=exts
 drills=list(fab.glob('*NPTH.drl'));assert len(drills)==1 and list(fab.glob('*-PTH.drl'))
 if key=='imu-carrier':assert 'G85' in drills[0].read_text(),'slot drill missing'
 allowed={'.gtl','.g1','.g2','.gbl','.gts','.gbs','.gto','.gbo','.gm1','.gtp','.drl','.gbrjob'}
 with zipfile.ZipFile(m/'gerbers.zip','w',zipfile.ZIP_DEFLATED) as z:
  for f in sorted(fab.iterdir()):
   assert f.suffix.lower() in allowed,f
   z.write(f,f.name)
 run(key+'-pdf',['kicad-cli','sch','export','pdf','-o',m/'schematic.pdf',sch])
 sd=m/'schematic-svg';sd.mkdir(exist_ok=True)
 run(key+'-svg',['kicad-cli','sch','export','svg','-o',str(sd)+'/',sch])
 pages=['schematic','schematic-usb','schematic-power','schematic-compute','schematic-imu'] if key=='main' else ['schematic']
 assert re.search(rf'Pages:\s+{len(pages)}\b',run(key+'-pdfinfo',['pdfinfo',m/'schematic.pdf']))
 for page,png in enumerate(pages,1):
  run(key+'-'+png+'-png',['pdftoppm','-f',page,'-l',page,'-png','-scale-to','2600','-singlefile',m/'schematic.pdf',m/png])
 for side,layers in [('top','F.Cu,F.SilkS,F.Fab,Edge.Cuts'),('bottom','B.Cu,B.SilkS,Edge.Cuts')]:
  run(key+'-'+side,['kicad-cli','pcb','export','svg','--layers',layers,'--page-size-mode','2','-o',m/(side+'.svg'),cad])
  run(key+'-'+side+'-png',['kicad-cli','pcb','render','--width','1200','--height','1400','--side',side,'--zoom','.8','-o',m/(side+'-3d.png'),cad])
 run(key+'-assembly',['kicad-cli','pcb','export','pdf','--mode-single','--layers','F.Fab,F.SilkS,Edge.Cuts','--sketch-pads-on-fab-layers','-o',m/'assembly-top.pdf',cad])
 if key=='main':
  run(key+'-step-board',['kicad-cli','pcb','export','step','--force','--drill-origin','--board-only','-o',m/'main-board-only.step',cad])
  run(key+'-step',['kicad-cli','pcb','export','step','--force','--drill-origin','--subst-models','--no-dnp','-o',m/'main-installed-models.step',cad])
 for svg in list(m.rglob('*.svg'))+list(m.rglob('*.step')):svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
 assert all(sha(ROOT/f)==v for f,v in hashes.items()),'Native source modified'
 dump(D/(key+'-exports.json'),{'manufacturing_release':False,'configured_ERC_DRC':'0 violations, 0 opens, 0 schematic parity issues','severity_scope':'--severity-all includes configured severities only; ignored defaults are NOT checked','ignored_defaults':ignored(json.loads(pro.read_text())),'drc_exclusions':json.loads(pro.read_text()).get('board',{}).get('design_settings',{}).get('drc_exclusions',[]),'default_count':count,'assembly_policy':'46 electronic parts; PCB-only J2 wire soldering local','jlc_fitted_headers':sorted(manual),'sources':hashes,'artifacts':{str(f.relative_to(ROOT)):sha(f) for f in sorted(m.rglob('*')) if f.is_file() and f.name not in ('manifest.json','README.md','ON_HOLD.txt')}})
 print(key,'PASS full JLC export',count)
