#!/usr/bin/python3
"""Final native silk placement, ground stitching and debug-row edge reserve.
DRC is run separately; all generated copper is subject to original constraints.
"""
if __name__ == '__main__':
 raise SystemExit('Historical destructive ECO helper disabled for the finalized layout; see integrated/README.md native-CAD rebuild workflow.')
import pcbnew as p,math,json
from route import H,B,D,refill
from sexp import *
a=parse(B.read_text())
for e in many(a,'gr_line'):
 if val(one(e,'layer')[1])=='Edge.Cuts':
  for k in ['start','end']:
   if float(one(e,k)[2])==138:one(e,k)[2]='139'
for z in many(a,'zone'):
 for pl in many(z,'polygon'):
  for v in one(pl,'pts')[1:]:
   if float(v[2])==138:v[2]='139'
B.write_text(dump(a)+'\n');refill();b=p.LoadBoard(str(B))
V=lambda x,y:p.VECTOR2I(p.FromMM(x),p.FromMM(y))
# Connect isolated surface copper to the intact inner GND plane (never blind/microvias).
added=[]
for z in b.Zones():
 if z.GetIsRuleArea() or z.GetLayer()!=p.F_Cu:continue
 polys=z.GetFilledPolysList(p.F_Cu)
 for i in range(polys.OutlineCount()):
  poly=p.SHAPE_POLY_SET();poly.AddOutline(polys.COutline(i));bb=poly.BBox()
  vias=[t for t in b.GetTracks() if isinstance(t,p.PCB_VIA) and t.GetNetname()=='GND']
  if any(poly.Contains(v.GetPosition()) for v in vias):continue
  pts=[]
  for ix in range(math.ceil(bb.GetX()/250000),math.floor(bb.GetRight()/250000)+1):
   for iy in range(math.ceil(bb.GetY()/250000),math.floor(bb.GetBottom()/250000)+1):
    x,y=ix/4,iy/4;v=V(x,y)
    if not poly.Contains(v) or not polys.Contains(v):continue
    if not (100.7<x<124.3 and 100.7<y<138.3):continue
    sh=p.SHAPE_CIRCLE(v,p.FromMM(.385));bad=False
    for f in b.GetFootprints():
     for pad in f.Pads():
      if p.SHAPE.Collide(sh,pad.GetEffectiveShape(p.F_Cu)):bad=True;break
     if bad:break
    if bad:continue
    for t in b.GetTracks():
     if t.GetNetname()!='GND' and p.SHAPE.Collide(sh,t.GetEffectiveShape()):bad=True;break
     if isinstance(t,p.PCB_VIA) and (t.GetPosition()-v).EuclideanNorm()<p.FromMM(.65):bad=True;break
    if bad:continue
    for zz in b.Zones():
     if zz.GetIsRuleArea() and p.SHAPE.Collide(sh,zz.Outline()):bad=True;break
    if not bad:pts.append((x,y))
  if pts:
   x,y=pts[len(pts)//2];via=p.PCB_VIA(b);via.SetPosition(V(x,y));via.SetWidth(p.FromMM(.45));via.SetDrill(p.FromMM(.2));via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(b.FindNet('GND'));b.Add(via);added.append([x,y])
print('surface stitching',added,flush=True)
# Fit actual native text bounds clear of exposed copper and other silk, not export overlays.
tps={f.GetReference():f for f in b.GetFootprints() if f.GetReference().startswith('TP')}
labels={'GND':'GND','VBUS':'VBUS','BAT':'PACK_P','SYS':'SYS','3V3':'3V3_MAIN','RST':'MCU_EN','BOOT':'BOOT','RX':'UART_RX','TX':'UART_TX','SCL':'SCL_HOST','SDA':'SDA_HOST','1V8':'1V8_IMU','INT':'INT1_1V8'}
texts=[t for t in b.GetDrawings() if isinstance(t,p.PCB_TEXT) and t.GetLayer()==p.F_SilkS and t.GetText() not in ['RESET','BOOT']]
# BOOT silk of new testpoint is distinct from original BOOT at SW3.
texts += [t for t in b.GetDrawings() if isinstance(t,p.PCB_TEXT) and t.GetText()=='BOOT' and p.ToMM(t.GetPosition().y)>135]
def box(bb,margin=0):return [bb.GetX()/1e6-margin,bb.GetY()/1e6-margin,bb.GetRight()/1e6+margin,bb.GetBottom()/1e6+margin]
def overlap(a,c):return a[0]<c[2] and c[0]<a[2] and a[1]<c[3] and c[1]<a[3]
obs=[]
for f in b.GetFootprints():
 for pad in f.Pads():obs.append(box(pad.GetBoundingBox(),.16))
 for g in f.GraphicalItems():
  if g.GetLayer()==p.F_SilkS:obs.append(box(g.GetBoundingBox(),.11))
for t in b.GetDrawings():
 if isinstance(t,p.PCB_TEXT) and t.GetLayer()==p.F_SilkS and t not in texts:obs.append(box(t.GetBoundingBox(),.11))
receipt=[]
for t in texts:
 name=t.GetText();ox,oy=p.ToMM(t.GetPosition());tp=None
 if name in labels:
  choices=[f for f in tps.values() if f.GetValue()==labels[name]]
  if choices:tp=min(choices,key=lambda f:(f.GetPosition()-t.GetPosition()).EuclideanNorm())
 if tp:x,y=p.ToMM(tp.GetPosition());rad=4
 else:x,y=ox,oy;rad=7
 if name=='IMU +Z OUT':t.SetText('+Z');x,y=107.2,126.5;rad=5
 options=[]
 for an in [0,90]:
  t.SetTextAngle(p.EDA_ANGLE(an,p.DEGREES_T))
  for dx in range(-rad*4,rad*4+1):
   for dy in range(-rad*4,rad*4+1):
    xx,yy=x+dx/4,y+dy/4;t.SetPosition(V(xx,yy));bb=box(t.GetBoundingBox(),.1)
    if bb[2]>113.83 and bb[3]>135.10:continue
    if bb[0]<100.25 or bb[2]>124.75 or bb[1]<100.25 or bb[3]>138.75 or any(overlap(bb,c) for c in obs):continue
    options.append(((xx-x)**2+(yy-y)**2+(0 if an==0 else .3),xx,yy,an))
 if not options:raise RuntimeError(('No readable silk space',name))
 _,xx,yy,an=min(options);t.SetPosition(V(xx,yy));t.SetTextAngle(p.EDA_ANGLE(an,p.DEGREES_T));obs.append(box(t.GetBoundingBox(),.11));receipt.append(dict(text=t.GetText(),position=[xx,yy],angle=an,reference=tp.GetReference() if tp else 'U2'))
pro=(H/'smove-r2-main.kicad_pro').read_bytes();p.SaveBoard(str(B),b);(H/'smove-r2-main.kicad_pro').write_bytes(pro);refill();(D/'native-silk.json').write_text(json.dumps(receipt,indent=2)+'\n')
