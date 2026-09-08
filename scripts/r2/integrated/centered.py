#!/usr/bin/python3
"""Explicit latest ECO from preserved workspace snapshot; --apply only. No firmware.
Deletes J3/TP1..14 and their branch copper; MCU UART and ICM INT return to NC.
Native PCB remains canonical after routing. Snapshot is task-local, not a new release.
"""
from pathlib import Path
import json,math,subprocess as sp,sys,shutil
import pcbnew as p
from sexp import *
R=Path(__file__).resolve().parents[3];H=R/'PCB/main';D=R/'.cache/centered';OLD=D/'baseline'
OUTLINE=[(100,100),(125,100),(125,111.5),(124.45,111.5),(124.45,122.1),(125,122.1),(125,139),(117.3,139),(117.3,133.0),(107.7,133.0),(107.7,139),(100,139)]
HOLES={'H1':(103.6,103.6),'H2':(121.4,135.4)}
POSE={'U8':(116,110,0),'U9':(114,121,0),'U1':(114.2,102.9,0),'U2':(112.5,117.5,-90),'U3':(105.8,121.5,-90),'U4':(103,111.2,0),'U5':(103,116.2,-90),'U6':(102.8,127,0),'J1':(121.1,116.8,90),'J2':(112.5,127.8,0),'SW2':(121.5,125.2,90),'SW3':(103.6,135.3,90),'D1':(119.9,130,0),
'C1':(102.8,130,0),'C2':(107,127,90),'C3':(102.8,108,90),'C4':(105,108.3,90),'C5':(102,119.3,0),'C6':(105.6,116.2,-90),'C7':(111.3,120.6,-90),'C8':(109.7,115.6,-90),'C9':(109.35,117.7,-90),'C10':(104,114,90),'C11':(106.3,112.8,0),'C13':(105,110.5,0),
'R1':(116,122.5,0),'R2':(118.2,122.5,0),'R3':(121.8,110.5,0),'R4':(123,109,90),'R5':(112.9,112.8,0),'R7':(102,114,90),'R8':(115.1,112.8,0),'R9':(123,106.5,90),'R10':(107.5,114.5,0),'R11':(118.8,128,90),'R12':(118.5,131,90),'R13':(117.8,124.9,90),'R14':(108.5,112.8,0),'R15':(110.7,112.8,0),'R16':(104.7,124.5,0),'R17':(107,124.5,0),'R18':(111,114.5,0),'R19':(113.2,114.5,0),'R20':(101.5,122.1,90),'R21':(105.8,126,90),'R22':(105.8,129,90),'R23':(101.2,124.5,0)}
def save(f,a):f.write_text(dump(a)+'\n')
def schematic():
 for file in ['compute','power','imu','smove-r2-main']:
  a=parse((OLD/(file+'.kicad_sch')).read_text());rem=[]
  for s in many(a,'symbol'):
   r=prop(s,'Reference')
   if r.startswith('TP') or r in ['J3','#PWR11']:rem.append(s)
  for x in list(a):
   if not isinstance(x,list):continue
   if x in rem:a.remove(x);continue
   if x[0]=='wire' and all(float(pt[2])>255 for pt in one(x,'pts')[1:]):a.remove(x)
   if x[0]=='label' and float(one(x,'at')[2])>255:a.remove(x)
  if file=='compute':
   remove_ids={'6b6fa877-7189-5e4e-8c19-ed61d1e35682','a7e85502-89fd-5b86-9dc8-0802d9f33c32','d1421e4a-49f7-56a6-9399-68face22ffe3','116b704c-29da-5532-991c-387f998185a4','c626ff33-c560-5780-bd58-c3dfd3620dc5','b5c4b5e5-d351-5bed-9776-e79d092f0baf','8039f423-5bfd-5c88-8d0a-d4b06488d092','e9816277-8600-57dd-830d-28668cb9e92f','64cd1b64-3a6d-5d2c-83c8-d80c616f17e8','a643cdcd-2bb5-53e7-9c27-1e12b2752395'}
   for w in many(a,'wire'):
    pts=[[float(v) for v in pt[1:]] for pt in one(w,'pts')[1:]]
    if val(one(w,'uuid')[1]) in remove_ids or pts in [[[241.3,152.4],[246.38,152.4]],[[241.3,165.1],[243.84,165.1]]]:a.remove(w)
   for l in many(a,'label'):
    if val(l[1]).startswith('UART') or one(l,'at')[1:3]==['279.4','236.22']:a.remove(l)
    elif val(l[1])=='MCU_EN':one(l,'at')[1:3]=['132.08','208.28']
   for y in [152.4,165.1]:a.append(node(f'(no_connect (at 241.3 {y}) (uuid {uid("uart-nc"+str(y))}))'))
  if file=='imu':
   for w in many(a,'wire'):
    if one(w,'pts')[1:]==[['xy','335.28','137.16'],['xy','353.06','137.16']]:a.remove(w)
   for l in many(a,'label'):
    if val(l[1])=='INT1_1V8':a.remove(l)
   a.append(node(f'(no_connect (at 335.28 137.16) (uuid {uid("int-restored-nc")}))'))
  for t in many(a,'text'):
   s=val(t[1])
   if any(k in s for k in ['TP14','test only','TEST ONLY','INT1:','J3','UART']):t[1]=q('No external UART or test pads. USB programming retained.\nICM INT1 NC; FIFO polling. BOOT / RESET retained.')
   if '100kHz' in s:t[1]=q('100kHz I2C, address 0x68; FIFO polling. INT1 NC; no testpoints.\nU2 F.Cu at native (112.50,117.50)mm: upper-centre; AG +Z OUTWARD, raw MAG +Z INWARD.\nTwo diagonal M3 mounts; nonmagnetic hardware and rigid fit require qualification.')
  # Remove no-longer-used local TP/J3 lib symbols.
  ls=one(a,'lib_symbols');ls[:]=[x for x in ls if not(isinstance(x,list) and x[0]=='symbol' and val(x[1]) in ['debug:TestPad','smove-r2-main:J3'])]
  save(H/(file+'.kicad_sch'),a)
 for file in ['sym-lib-table','fp-lib-table']:
  a=parse((H/file).read_text());a[:]=[x for x in a if not(isinstance(x,list) and x[0]=='lib' and val(one(x,'name')[1])=='debug')];save(H/file,a)
 for path in [H/'debug.pretty',H/'debug.kicad_sym']:
  if path.is_dir():shutil.rmtree(path)
  elif path.exists():path.unlink()
 sp.run(['kicad-cli','sch','export','netlist','--format','kicadxml','-o',str(D/'main.xml'),str(H/'smove-r2-main.kicad_sch')],check=True)
def layout():
 import xml.etree.ElementTree as ET
 pins={(n.attrib['ref'],n.attrib['pin']):net.attrib['name'] for net in ET.parse(D/'main.xml').findall('./nets/net') for n in net.findall('node')}
 a=parse((OLD/'smove-r2-main.kicad_pcb').read_text())
 a[:]=[x for x in a if not(isinstance(x,list) and (x[0] in ['segment','via','gr_text','gr_line'] or x[0]=='footprint' and (prop(x,'Reference').startswith('TP') or prop(x,'Reference')=='J3') or x[0]=='zone' and many(x,'keepout') and not(many(x,'name') and val(one(x,'name')[1])=='ANTENNA_ALL_LAYERS')))]
 for z in many(a,'zone'):
  if many(z,'keepout'):
   for pt in one(one(z,'polygon'),'pts')[1:]:pt[1]=str(float(pt[1])+1.7)
 save(D/'placed.kicad_pcb',a);b=p.LoadBoard(str(D/'placed.kicad_pcb'));vec=lambda x,y:p.VECTOR2I(p.FromMM(x),p.FromMM(y))
 nets={n.GetNetname():n for n in b.GetNetsByNetcode().values()}
 for name in sorted(set(pins.values())):
  if name not in nets:n=p.NETINFO_ITEM(b,name);b.Add(n);nets[name]=n
 parts=json.loads((OLD/'parts-main.json').read_text());parts={r:v for r,v in parts.items() if not r.startswith('TP') and r!='J3'}
 assert set(parts)==set(POSE)
 for f in b.GetFootprints():
  r=f.GetReference();x,y,ang=POSE[r];f.SetOrientationDegrees(ang);f.SetPosition(vec(x,y));parts[r]['placement']=[x,y,ang]
  for pad in f.Pads():pad.SetNet(nets[pins[(r,pad.GetNumber())]]) if (r,pad.GetNumber()) in pins else pad.SetNetCode(0)
  f.Reference().SetVisible(False);f.Value().SetVisible(False)
 for r,xy in HOLES.items():
  f=p.FOOTPRINT(b);f.SetReference(r);f.SetValue('M3 NPTH 3.2mm');f.SetFPID(p.LIB_ID('','MountingHole_3.2mm_M3'));f.SetAttributes(p.FP_EXCLUDE_FROM_BOM|p.FP_EXCLUDE_FROM_POS_FILES|p.FP_BOARD_ONLY);f.SetPosition(vec(*xy));b.Add(f)
  pad=p.PAD(f);pad.SetAttribute(p.PAD_ATTRIB_NPTH);pad.SetShape(p.PAD_SHAPE_CIRCLE);pad.SetSize(vec(3.2,3.2));pad.SetDrillSize(vec(3.2,3.2));pad.SetLayerSet(p.LSET.AllCuMask());pad.SetPosition(vec(*xy));f.Add(pad)
  f.Reference().SetVisible(False);f.Value().SetVisible(False)
  z=p.ZONE(b);z.SetIsRuleArea(True);z.SetZoneName(r+'_M3_NO_COPPER');z.SetLayerSet(p.LSET.AllCuMask());z.SetDoNotAllowPads(False);z.SetDoNotAllowFootprints(False);z.SetDoNotAllowTracks(True);z.SetDoNotAllowVias(True);z.SetDoNotAllowCopperPour(True);z.Outline().NewOutline()
  for i in range(48):z.Outline().Append(*tuple(vec(xy[0]+3.45*math.cos(i*math.pi/24),xy[1]+3.45*math.sin(i*math.pi/24))))
  b.Add(z)
 for i,(start,end) in enumerate(zip(OUTLINE,OUTLINE[1:]+OUTLINE[:1])):
  s=p.PCB_SHAPE(b);s.SetShape(p.SHAPE_T_SEGMENT);s.SetStart(vec(*start));s.SetEnd(vec(*end));s.SetLayer(p.Edge_Cuts);s.SetWidth(p.FromMM(.05));b.Add(s)
 for text,x,y,ang in [('RESET',124.1,125.2,90),('BOOT',100.9,135.3,90),('U2 +Z',113.6,121.3,0),('BODY',112.5,119,0)]:
  t=p.PCB_TEXT(b);t.SetText(text);t.SetPosition(vec(x,y));t.SetTextSize(vec(.8,.8));t.SetTextThickness(p.FromMM(.12));t.SetTextAngle(p.EDA_ANGLE(ang,p.DEGREES_T));t.SetLayer(p.B_SilkS if text=='BODY' else p.F_SilkS);t.SetMirrored(text=='BODY');b.Add(t)
 parts['U1']['pins']['30']=None;parts['U1']['pins']['31']=None;parts['U2']['pins']['12']=None
 (H/'parts-main.json').write_text(json.dumps(parts,indent=2)+'\n');pro=(H/'smove-r2-main.kicad_pro').read_bytes();p.SaveBoard(str(H/'smove-r2-main.kicad_pcb'),b);(H/'smove-r2-main.kicad_pro').write_bytes(pro)
if __name__=='__main__':
 raise SystemExit('One-off migration record only. Current routed native CAD + parts/interface JSON are canonical; do not replay over final layout.')
