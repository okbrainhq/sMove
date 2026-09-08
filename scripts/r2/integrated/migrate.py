#!/usr/bin/python3
"""Explicit, reproducible R2-to-integrated ECO from c1050a0 native sources.
Overwrites main schematic/layout ONLY with --apply; routing is a separate checked step.
Carrier remains a frozen reference, NOT part of the integrated assembly/BOM.
"""
if __name__ == '__main__':
 raise SystemExit('Historical destructive ECO helper disabled for the finalized layout; see integrated/README.md native-CAD rebuild workflow.')
from pathlib import Path
import argparse, copy, json, subprocess as sp, shutil
from sexp import *
ROOT=Path(__file__).resolve().parents[3]; H=ROOT/'PCB/main'; C=ROOT/'PCB/imu-carrier'
BASE='c1050a07339897e7203f43137aec96de5bbc41cc'
TOP='8e261347-838a-5848-981d-f693675e8aa0'; COMP='eeb5ed75-de0b-5a0c-8356-c78aafd0bbd1'; IMU=uid('sheet-imu')
def old(path):return sp.check_output(['git','show',BASE+':'+path],cwd=ROOT,text=True)
def save(path,a):path.write_text(dump(a)+'\n')
def wire(a,b):return node(f'(wire (pts (xy {a[0]} {a[1]}) (xy {b[0]} {b[1]})) (stroke (width 0) (type default)) (uuid {uid((a,b))}))')
def label(name,xy,kind='label',shape='passive',angle=0):
 return node(f'({kind} {q(name)} '+(f'(shape {shape}) ' if kind=='hierarchical_label' else '')+f'(at {xy[0]} {xy[1]} {angle}) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid {uid((name,xy,kind))}))')
def text(s,xy,size=1.27):return node(f'(text {q(s)} (at {xy[0]} {xy[1]} 0) (effects (font (size {size} {size})) (justify left)) (uuid {uid((s,xy))}))')
def tp_symbol():return node('''(symbol "debug:TestPad" (pin_names (offset 0) (hide yes)) (in_bom no) (on_board yes)
(property "Reference" "TP" (at 0 4 0) (effects (font (size 1.27 1.27))))
(property "Value" "TestPad" (at 0 6 0) (effects (font (size 1.27 1.27))))
(symbol "TestPad_0_1" (circle (center 0 2) (radius 1) (stroke (width .2) (type default)) (fill (type none))))
(symbol "TestPad_1_1" (pin passive line (at 0 0 90) (length 1) (name "1" (effects (font (size 1 1)))) (number "1" (effects (font (size 1 1)))))))''')
# Existing service header J3 remains; duplicate convenient power/bus test pads are NO BOM/NO paste.
TP=[('TP1','GND','Power',101.5,136.5),('TP2','VBUS','Power',105,136.5),('TP3','PACK_P','Power',108.5,136.5),
 ('TP4','SYS','Power',112,136.5),('TP5','3V3_MAIN','Compute',115.5,136.5),('TP6','MCU_EN','Compute',119,136.5),
 ('TP7','BOOT','Compute',122.5,136.5),('TP8','UART_RX','Compute',123.5,110.8),('TP9','UART_TX','Compute',121,111.8),
 ('TP10','SCL_HOST','IMU',103,134),('TP11','SDA_HOST','IMU',105.5,134),
 ('TP12','1V8_IMU','IMU',101.5,131.5),('TP13','GND','IMU',107.8,131.7),('TP14','INT1_1V8','IMU',108.7,128)]

def schematic():
 root=parse(old('PCB/main/smove-r2-main.kicad_sch')); comp=parse(old('PCB/main/compute.kicad_sch'))
 imu=parse((C/'smove-imu-carrier.kicad_sch').read_text())
 for a in [root,comp]:
  for t in many(a,'text'):
   if 'separate' in val(t[1]) or 'PH4:' in val(t[1]) or 'No nested' in val(t[1]): t[1]=q('Integrated IMU on SAME main PCB.\nSee dedicated wired IMU page.\nNo J4/J5 or PH4 harness.')
   if 'three functional' in val(t[1]):t[1]=q('One main PCB, four functional pages. Green lines are actual hierarchical connections.')
   if 'Placement and routing unchanged' in val(t[1]):t[1]=q('Crossings without junction dots are NOT connected. Engineering prototype; release gated.')
 one(root,'paper')[1]=q('A3')
 one(one(root,'title_block'),'comment')[2]=q('MAIN PCB - USB / POWER / COMPUTE / INTEGRATED IMU')
 # Remove only former connector and its dead supply/ground ends; preserve shared D1 supply rail.
 comp[:]=[x for x in comp if not(isinstance(x,list) and x[0]=='symbol' and prop(x,'Reference') in ['J4','#PWR6','#PWR7'])]
 for w in many(comp,'wire'):
  pts=[[float(v) for v in p[1:]] for p in one(w,'pts')[1:]]
  if pts in [[[309.88,50.8],[317.5,50.8]],[[309.88,27.94],[309.88,50.8]],[[317.5,88.9],[317.5,101.6]],[[330.2,99.06],[330.2,101.6]]]:comp.remove(w)
 for n,y in [('SCL_HOST',63.5),('SDA_HOST',76.2)]:comp.append(label(n,(317.5,y),'hierarchical_label','bidirectional',0))
 # Add IMU to root, without hiding the inter-sheet wires behind net labels.
 cs=next(s for s in many(root,'sheet') if prop(s,'Sheetname')=='Compute')
 for n,y in [('SCL_HOST',63.5),('SDA_HOST',76.2)]:
  cs.append(node(f'(pin {q(n)} bidirectional (at 269.24 {y} 0) (effects (font (size 1.27 1.27)) (justify right)) (uuid {uid("compute-"+n)}))'))
 ims=node(f'''(sheet (at 312.42 45.72) (size 81.28 116.84) (stroke (width .254) (type default)) (fill (color 0 0 0 0)) (uuid {IMU})
 (property "Sheetname" "IMU" (at 312.42 44.45 0) (effects (font (size 1.52 1.52)) (justify left bottom)))
 (property "Sheetfile" "imu.kicad_sch" (at 312.42 163.83 0) (effects (font (size 1 1)) (justify left top)))
 (instances (project "smove-r2-main" (path "/{TOP}" (page "5")))))''')
 for n,y,kind in [('SCL_HOST',63.5,'bidirectional'),('SDA_HOST',76.2,'bidirectional'),('3V3_MAIN',129.54,'input'),('GND',157.48,'passive')]:
  ims.append(node(f'(pin {q(n)} {kind} (at 312.42 {y} 180) (effects (font (size 1.27 1.27)) (justify left)) (uuid {uid("imu-"+n)}))'))
  if n.endswith('HOST'):root.append(wire((269.24,y),(312.42,y)))
 root.append(ims);root.append(text('U5 local 1.8V\nU3 PCA9306 + BOTH pull-up pairs\nU2 ICM-20948\n1.8V INT1: test only; FIFO polling\nTop package +Z OUTWARD',(320,96),1.02))
 for x1,y1,x2,y2 in [(165.1,129.54,165.1,170.18),(165.1,170.18,299.72,170.18),(299.72,170.18,299.72,129.54),(299.72,129.54,312.42,129.54),(157.48,157.48,157.48,177.8),(157.48,177.8,294.64,177.8),(294.64,177.8,294.64,157.48),(294.64,157.48,312.42,157.48)]:root.append(wire((x1,y1),(x2,y2)))
 w=next(w for w in many(root,'wire') if one(w,'uuid')[1]=='c79cd7c1-c1d6-5348-9f01-77da356b27a3');root.remove(w);root.extend([wire((91.44,129.54),(165.1,129.54)),wire((165.1,129.54),(177.8,129.54))])
 root.append(node(f'(junction (at 165.1 129.54) (diameter 0) (color 0 0 0 0) (uuid {uid("3v3-branch")}))'))
 # Explicit root name prevents Compute/ scope drift, maps documented below.
 for n,y in [('SCL_HOST',63.5),('SDA_HOST',76.2)]:root.append(label(n,(284.48,y)))
 one(imu,'uuid')[1]=IMU
 one(one(imu,'title_block'),'title')[1]=q('sMove / integrated ICM-20948 / SAME main PCB')
 one(one(imu,'title_block'),'comment')[2]=q('Actual carrier circuitry transferred; no sensor substitution; +Z outward')
 imu[:]=[x for x in imu if not(isinstance(x,list) and ((x[0]=='symbol' and prop(x,'Reference') in ['J5','#FLG01','#FLG02']) or x[0]=='sheet_instances'))]
 # Former connector pin wires become hierarchy interfaces; shield branch is removed.
 for w in many(imu,'wire'):
  pts=[[float(v) for v in p[1:]] for p in one(w,'pts')[1:]]
  if pts==[[55.88,142.24],[60.96,142.24]]:imu.remove(w)
 for n,xy,kind in [('3V3_MAIN',(55.88,101.6),'input'),('GND',(55.88,111.76),'passive'),('SDA_HOST',(55.88,121.92),'bidirectional'),('SCL_HOST',(55.88,132.08),'bidirectional')]:imu.append(label(n,xy,'hierarchical_label',kind,180))
 for l in many(imu,'label'):
  l[1]=q({'3V3_IMU_IN':'3V3_MAIN','SDA_3V3':'SDA_HOST','SCL_3V3':'SCL_HOST'}.get(val(l[1]),val(l[1])))
 for t in many(imu,'text'):
  st=val(t[1])
  if 'REUSABLE' in st:t[1]=q('INTEGRATED ICM-20948 | SAME ESP32-C3 MAIN PCB | 3.3V HOST / LOCAL 1.8V')
  elif st.startswith('J5:'):t[1]=q('Internal PCB interconnect, NO harness.\nHost open-drain; no extra host pulls.\nTP14 INT1 is 1.8V TEST ONLY: no 3.3V injection.\nFIFO polling retained, no MCU IRQ/wake connection.')
  elif '100kHz' in st:
   one(t,'at')[2]='241.3';t[1]=q('100kHz I2C, address 0x68. FIFO polling retained. TP14 exposes INT1 (1.8V) for scope ONLY.\nU2 TOP, rotated -90 degrees in PCB: accel/gyro +Z OUTWARD, magnetometer raw +Z INWARD.\nRigid registered peripheral main-PCB seats; no support/clamping under U2. RF/magnetic/thermal/fit tests still required.')
 # Preserve all component UUIDs and references; deliberate project/path and library migration.
 for s in many(imu,'symbol'):
  for x in walk(s):
   if x[0]=='project':x[1]=q('smove-r2-main')
   if x[0]=='path':x[1]=q('/'+TOP+'/'+IMU)
   if x[0]=='lib_id' and val(x[1]).startswith('carrier:'):x[1]=q(val(x[1]).replace('carrier:','imu:'))
   if x[0]=='property' and val(x[1])=='Footprint':x[2]=q(val(x[2]).replace('carrier:','imu:'))
 for s in many(one(imu,'lib_symbols'),'symbol'):
  if val(s[1]).startswith('carrier:'):s[1]=q(val(s[1]).replace('carrier:','imu:'))
  for x in walk(s):
   if x[0]=='property' and val(x[1])=='Footprint':x[2]=q(val(x[2]).replace('carrier:','imu:'))
 # INT1 was intentionally NC; only a short passive debug pad is added, NOT 3.3V GPIO.
 for nc in many(imu,'no_connect'):
  if [float(v) for v in one(nc,'at')[1:]]==[335.28,137.16]:imu.remove(nc)
 imu.append(wire((335.28,137.16),(353.06,137.16)));imu.append(label('INT1_1V8',(353.06,137.16)))
 power=parse(old('PCB/main/power.kicad_sch')); sheets={'Power':power,'Compute':comp,'IMU':imu}
 for name,a in sheets.items():
  one(a,'lib_symbols').append(tp_symbol())
  rows=[t for t in TP if t[2]==name]
  for i,(ref,net,_,_,_) in enumerate(rows):
   x=40.64+i*35.56;y=257.81 if name=='IMU' else 261.62
   sid={'Power':'a926f61e-132d-5af0-876e-12788077b17d','Compute':COMP,'IMU':IMU}[name]
   inst=node(f'''(symbol (lib_id "debug:TestPad") (at {x} {y} 0) (unit 1) (in_bom no) (on_board yes) (dnp no) (uuid {uid(ref)})
 (property "Reference" "{ref}" (at {x} {y-5} 0) (effects (font (size 1.27 1.27))))
 (property "Value" "{net}" (at {x} {y-7.5} 0) (effects (font (size 1.0 1.0))))
 (property "Footprint" "debug:TestPad_1mm" (at {x} {y} 0) (effects (font (size 1 1)) (hide yes)))
 (pin "1" (uuid {uid(ref+'pin')})) (instances (project "smove-r2-main" (path "/{TOP}/{sid}" (reference "{ref}") (unit 1)))))''')
   a.extend([inst,wire((x,y),(x,y+5.08)),label(net,(x,y+5.08))])
 for f,a in [('smove-r2-main.kicad_sch',root),('compute.kicad_sch',comp),('power.kicad_sch',power),('imu.kicad_sch',imu)]:save(H/f,a)
 # Local caches and libraries: exact original sensor footprint/package, not a substitute.
 shutil.copytree(C/'carrier.pretty',H/'imu.pretty',dirs_exist_ok=True)
 shutil.copytree(C/'models',H/'imu-models',dirs_exist_ok=True)
 (H/'imu-models/J5_MAX_HEADER_ENVELOPE.step').unlink(missing_ok=True)
 ms=json.loads((H/'imu-models/model-status.json').read_text());ms.pop('J5',None);(H/'imu-models/model-status.json').write_text(json.dumps(ms,indent=2)+'\n')
 for model in (H/'imu-models').glob('*.step'):model.write_text('\n'.join(line.rstrip() for line in model.read_text().splitlines())+'\n')
 for f in (H/'imu.pretty').glob('*.kicad_mod'):f.write_text(f.read_text().replace('${KIPRJMOD}/models/','${KIPRJMOD}/imu-models/'))
 for f in ['JST_PH_S4B-PH-SM4-TB_1x04-1MP_P2.00mm_Horizontal.kicad_mod','H1_Locator.kicad_mod','H2_Locator.kicad_mod']:(H/'imu.pretty'/f).unlink()
 (H/'imu.kicad_sym').write_text((C/'carrier.kicad_sym').read_text().replace('carrier:','imu:'))
 for n in ['Device','power']:
  # Main uses its own embedded power GND symbols; table's imported power supplies PWR_FLAG only.
  lib=parse((C/(n+'.kicad_sym')).read_text()); names={val(x[1]) for x in many(lib,'symbol')}
  for sym in many(one(parse(old('PCB/main/compute.kicad_sch')),'lib_symbols'),'symbol'):
   if val(sym[1]).startswith(n+':') and val(sym[1]).split(':')[1] not in names:
    cp=copy.deepcopy(sym);cp[1]=q(val(sym[1]).split(':')[1]);lib.append(cp)
  save(H/(n+'.kicad_sym'),lib)
 save(H/'debug.kicad_sym',['kicad_symbol_lib',['version','20241209'],['generator',q('kicad_symbol_editor')],copy.deepcopy(tp_symbol())])
 a=parse((H/'debug.kicad_sym').read_text());many(a,'symbol')[0][1]=q('TestPad');save(H/'debug.kicad_sym',a)
 for filename,typ,libs in [('sym-lib-table','KiCad',{'imu':'imu.kicad_sym','debug':'debug.kicad_sym','Device':'Device.kicad_sym','power':'power.kicad_sym'}),('fp-lib-table','KiCad',{'imu':'imu.pretty','debug':'debug.pretty'})]:
  a=parse(old('PCB/main/'+filename));names={val(one(l,'name')[1]) for l in many(a,'lib')}
  for n,p in libs.items():
   if n not in names:a.append(node(f'(lib (name "{n}") (type "{typ}") (uri "${{KIPRJMOD}}/{p}") (options "") (descr "Project-local integrated circuit source"))'))
  save(H/filename,a)
 (H/'debug.pretty').mkdir(exist_ok=True)
 (H/'debug.pretty/TestPad_1mm.kicad_mod').write_text('''(footprint "TestPad_1mm" (version 20241229) (generator "pcbnew") (layer "F.Cu")
 (attr smd exclude_from_pos_files exclude_from_bom)
 (property "Reference" "TP**" (at 0 -1.2 0) (layer "F.SilkS") (effects (font (size .7 .7) (thickness .12))))
 (property "Value" "TestPad_1mm" (at 0 1.2 0) (layer "F.Fab") (effects (font (size .7 .7) (thickness .1))))
 (fp_circle (center 0 0) (end .65 0) (stroke (width .05) (type default)) (layer "F.CrtYd"))
 (pad "1" smd circle (at 0 0) (size 1 1) (layers "F.Cu" "F.Mask") (solder_mask_margin .05)))\n''')
 # Emit expected connection contract from two genuine sources with explicit mapping.
 parts=json.loads(old('PCB/main/parts-main.json'));del parts['J4']
 for r,v in parts.items():v['path']='/'+TOP+'/'+({'Compute':COMP,'Power':'a926f61e-132d-5af0-876e-12788077b17d','USB':'2bda09d7-02a6-5813-8901-250e661184c8'}[next(n for n,a in [('Compute',comp),('Power',power),('USB',parse(old('PCB/main/usb.kicad_sch')))] if any(prop(s,'Reference')==r for s in many(a,'symbol')))])+'/'+v['uuid']
 cp=json.loads((C/'parts.json').read_text());contract=json.loads((C/'electrical-contract.json').read_text())
 for r,v in cp.items():
  if r=='J5':continue
  s=next(s for s in many(imu,'symbol') if prop(s,'Reference')==r);v.update(board='main',ref=r,fitted=True,uuid=one(s,'uuid')[1],path='/'+TOP+'/'+IMU+'/'+one(s,'uuid')[1],fp=prop(s,'Footprint').split(':')[1],pins={k: {'3V3_IMU_IN':'3V3_MAIN','SDA_3V3':'SDA_HOST','SCL_3V3':'SCL_HOST'}.get(n,n) for k,n in contract[r]['pins'].items()})
  if r=='U2':v['pins']['12']='INT1_1V8'
  parts[r]=v
 for r,n,s,x,y in TP:parts[r]=dict(board='main',ref=r,value=n,fitted=False,fp='TestPad_1mm',mpn=None,jlc=None,pins={'1':n},uuid=uid(r),path='/'+TOP+'/'+{'Power':'a926f61e-132d-5af0-876e-12788077b17d','Compute':COMP,'IMU':IMU}[s]+'/'+uid(r),placement=[x,y,0])
 (H/'parts-main.json').write_text(json.dumps(parts,indent=2)+'\n')

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--apply',action='store_true',required=True);ap.parse_args();schematic();print('Schematic/source migration complete. Native PCB routing must be applied and validated separately.')
