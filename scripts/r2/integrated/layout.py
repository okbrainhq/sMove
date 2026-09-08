#!/usr/bin/python3
"""Transfer real sensor footprints and safe native probe pads; retain unaffected main routing.
Explicit --apply writes layout from baseline, not a generic board editor. Post-route DRC required.
"""
if __name__ == '__main__':
 raise SystemExit('Historical destructive ECO helper disabled for the finalized layout; see integrated/README.md native-CAD rebuild workflow.')
from migrate import ROOT,H,C,BASE,TOP,IMU,COMP,TP,old,uid
import pcbnew as p, json, argparse, xml.etree.ElementTree as ET
from sexp import parse, dump, many, one, val, prop
CACHE=ROOT/'.cache/integrated';CACHE.mkdir(exist_ok=True,parents=True)
def vec(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def netmap(xml):
 x=ET.parse(xml);return {(n.attrib['ref'],n.attrib['pin']):net.attrib['name'] for net in x.findall('./nets/net') for n in net.findall('node')}
def apply():
 bp=CACHE/'original.kicad_pcb'; raw=parse(old('PCB/main/smove-r2-main.kicad_pcb'))
 # Filter immutable S-expressions before load: this host's SWIG Board.Remove invalidates proxies.
 names={n[1]:val(n[2]) for n in many(raw,'net')}
 for o in list(raw):
  if not isinstance(o,list):continue
  remove=o[0]=='footprint' and prop(o,'Reference')=='J4'
  if o[0] in ['segment','via']:
   xy=[one(o,k)[1:3] for k in (['start','end'] if o[0]=='segment' else ['at'])]
   remove=names[one(o,'net')[1]] in ['/Compute/SCL_HOST','/Compute/SDA_HOST'] or any(float(x)<110 and 117.2<float(y)<135 for x,y in xy)
  if o[0]=='gr_text':remove=any(t in val(o[1]) for t in ['PH4','J4','SDA SCL','1:3V3'])
  if o[0]=='zone' and not many(o,'keepout'):
   for pl in many(o,'polygon'):
    for v in one(pl,'pts')[1:]:
     if float(v[2])>134:v[2]=str(float(v[2])+3)
  if remove:raw.remove(o)
 bp.write_text(dump(raw)+'\n')
 bp.with_suffix('.kicad_pro').write_text(old('PCB/main/smove-r2-main.kicad_pro'))
 bp.with_suffix('.kicad_dru').write_text(old('PCB/main/smove-r2-main.kicad_dru'))
 b=p.LoadBoard(str(bp));parts=json.loads((H/'parts-main.json').read_text())
 pins=netmap(CACHE/'main.xml'); nets={n.GetNetname():n for n in b.GetNetsByNetcode().values()}
 for n in sorted(set(pins.values())):
  if n not in nets: nn=p.NETINFO_ITEM(b,n);b.Add(nn);nets[n]=nn
 def setpins(f):
  r=f.GetReference()
  for pad in f.Pads():
   key=(r,pad.GetNumber())
   if key in pins:pad.SetNet(nets[pins[key]])
   else:pad.SetNetCode(0)
 # Preserve original named nets, except promoted host bus scope, and NC net names from fresh schematic.
 mapping={'/Compute/SCL_HOST':'/SCL_HOST','/Compute/SDA_HOST':'/SDA_HOST'}
 for t in b.GetTracks():
  if t.GetNetname() in mapping:t.SetNet(nets[mapping[t.GetNetname()]])
 for f in b.GetFootprints():setpins(f)
 c=p.LoadBoard(str(C/'smove-imu-carrier.kicad_pcb'))
 carrier_fps=list(c.GetFootprints()); carrier_tracks=list(c.GetTracks())
 for f in carrier_fps:
  r=f.GetReference()
  if r not in parts:continue
  nf=f.Duplicate()
  nf.Rotate(vec(100,100),p.EDA_ANGLE(-90,p.DEGREES_T));nf.Move(vec(11,17));b.Add(nf)
  nf.SetFPID(p.LIB_ID('imu',str(f.GetFPID().GetLibItemName())))
  nf.SetPath(p.KIID_PATH('/'+TOP+'/'+IMU+'/'+parts[r]['uuid']))
  for m in nf.Models():m.m_Filename=m.m_Filename.replace('${KIPRJMOD}/models/','${KIPRJMOD}/imu-models/')
  setpins(nf)
  if r=='C5':nf.Move(vec(-.6,0))
  nf.Reference().SetVisible(False);nf.Value().SetVisible(False)
 # Copy short local carrier circuitry routes. Translation/decoupling layout is not guessed.
 for t in carrier_tracks:
  xy=[p.ToMM(t.GetStart()),p.ToMM(t.GetEnd())]
  if not all(100.25<=x<=117.75 and 101.8<=y<=110.8 for x,y in xy):continue
  n=t.GetNetname()
  n={'GND':'GND','/3V3_IMU_IN':'/3V3_MAIN','/SDA_3V3':'/SDA_HOST','/SCL_3V3':'/SCL_HOST'}.get(n,'/IMU/'+n.lstrip('/'))
  if n not in nets:continue
  nt=t.Duplicate();nt.Rotate(vec(100,100),p.EDA_ANGLE(-90,p.DEGREES_T));nt.Move(vec(11,17));b.Add(nt);nt.SetNet(nets[n])
 # Extension for separated rail/control pads: 25 x 38 mm substrate (antenna overhang unchanged).
 for d in b.GetDrawings():
  if d.GetLayer()==p.Edge_Cuts:
   for getter,setter in [(d.GetStart,d.SetStart),(d.GetEnd,d.SetEnd)]:
    x,y=p.ToMM(getter())
    if abs(y-135)<.001:setter(vec(x,138))
 # Add two sensor-end bearing zones on bare PCB corners; no support under sensor/package.
 for x1,x2 in [(100,101.1),(123.9,125)]:
  z=p.ZONE(b);z.SetIsRuleArea(True);ls=p.LSET()
  for l in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]:ls.AddLayer(l)
  z.SetLayerSet(ls);z.SetDoNotAllowTracks(True);z.SetDoNotAllowVias(True);z.SetDoNotAllowCopperPour(True);z.SetDoNotAllowPads(True)
  z.Outline().NewOutline()
  for x,y in [(x1,129 if x1==100 else 136.8),(x2,129 if x1==100 else 136.8),(x2,130.8 if x1==100 else 138),(x1,130.8 if x1==100 else 138)]:z.Outline().Append(int(p.FromMM(x)),int(p.FromMM(y)))
  b.Add(z)
 def segdist(x,y,a,b):
  dx=b[0]-a[0];dy=b[1]-a[1];u=max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy))) if dx or dy else 0
  return ((x-a[0]-u*dx)**2+(y-a[1]-u*dy)**2)**.5
 rectangles=[]
 for f in b.GetFootprints():
  pts=[p.ToMM(v) for g in f.GraphicalItems() if g.GetLayer()==p.F_CrtYd for v in (g.GetStart(),g.GetEnd())]
  if pts:rectangles.append((min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts),max(y for x,y in pts)))
 occupied=[]
 for r,n,_,x,y in TP:
  target=pins[(r,'1')]
  candidates=[]
  for ix in range(405,496):
   for iy in range(440,549):
    xx,yy=ix/4,iy/4
    if any(x0-.72<xx<x1+.72 and y0-.72<yy<y1+.72 for x0,y0,x1,y1 in rectangles):continue
    if any(((xx-a)**2+(yy-bb)**2)**.5<2.2 for a,bb in occupied):continue
    if any(segdist(xx,yy,p.ToMM(t.GetStart()),p.ToMM(t.GetEnd()))<(.67+p.ToMM(t.GetWidth())/2) for t in b.GetTracks() if (isinstance(t,p.PCB_VIA) or t.GetLayer()==p.F_Cu) and t.GetNetname()!=target):continue
    if (xx<101.9 or xx>123.1) and 128.2<yy<131.6:continue
    candidates.append(((xx-x)**2+(yy-y)**2,xx,yy))
  assert candidates,r
  _,x,y=min(candidates);occupied.append((x,y));print(r,n,x,y,flush=True)
  f=p.FootprintLoad(str(H/'debug.pretty'),'TestPad_1mm');b.Add(f);f.SetReference(r);f.SetValue(n);f.SetFPID(p.LIB_ID('debug','TestPad_1mm'));f.SetPosition(vec(x,y));f.SetPath(p.KIID_PATH(parts[r]['path']));setpins(f)
  f.SetAttributes(p.FP_SMD|p.FP_EXCLUDE_FROM_BOM|p.FP_EXCLUDE_FROM_POS_FILES);f.Reference().SetVisible(False);f.Value().SetVisible(False)
  lab={'3V3_MAIN':'3V3','MCU_EN':'RST','PACK_P':'BAT','UART_RX':'RX','UART_TX':'TX','SCL_HOST':'SCL','SDA_HOST':'SDA','1V8_IMU':'1V8','INT1_1V8':'INT'}.get(n,n)
  t=p.PCB_TEXT(b);t.SetText(lab);t.SetPosition(vec(x,y+1.05 if y==136.5 else y-.95));t.SetTextSize(vec(.8,.8));t.SetTextThickness(p.FromMM(.1));t.SetLayer(p.F_SilkS);b.Add(t)
 for s,x,y,angle in [('IMU +Z OUT',105.5,124.0,90),('BODY SIDE -Z',112.5,127,0)]:
  t=p.PCB_TEXT(b);t.SetText(s);t.SetPosition(vec(x,y));t.SetTextSize(vec(.8,.8));t.SetTextThickness(p.FromMM(.1));t.SetLayer(p.B_SilkS if 'BODY' in s else p.F_SilkS);t.SetTextAngle(p.EDA_ANGLE(angle,p.DEGREES_T));
  if 'BODY' in s:t.SetMirrored(True)
  b.Add(t)
 for f in b.GetFootprints():
  if f.GetReference() in parts:parts[f.GetReference()]['placement']=[*p.ToMM(f.GetPosition()),f.GetOrientationDegrees()]
 (H/'parts-main.json').write_text(json.dumps(parts,indent=2)+'\n')
 b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(H/'smove-r2-main.kicad_pcb'),b)
 (H/'smove-r2-main.kicad_pro').write_text(old('PCB/main/smove-r2-main.kicad_pro'))
 print('Transferred sensor cluster and testpads; routing must be checked.')
if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--apply',action='store_true',required=True);ap.parse_args();apply()
