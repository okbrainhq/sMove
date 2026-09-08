#!/usr/bin/python3
"""Locate readable native U2 +Z marking outside all populated component envelopes."""
import pcbnew as p,json
from route import B,H
b=p.LoadBoard(str(B));target=next(t for t in b.GetDrawings() if isinstance(t,p.PCB_TEXT) and t.GetText() in ['+Z','U2 +Z']);target.SetText('U2 +Z')
def box(bb,m=0):return [bb.GetX()/1e6-m,bb.GetY()/1e6-m,bb.GetRight()/1e6+m,bb.GetBottom()/1e6+m]
def overlaps(a,c):return a[0]<c[2] and c[0]<a[2] and a[1]<c[3] and c[1]<a[3]
obs=[]
from centered import HOLES
for x,y in HOLES.values():obs.append([x-3.45,y-3.45,x+3.45,y+3.45])
for f in b.GetFootprints():
 for pad in f.Pads():obs.append(box(pad.GetBoundingBox(),.16))
 for g in f.GraphicalItems():
  if g.GetLayer()==p.F_SilkS:obs.append(box(g.GetBoundingBox(),.11))
for c in json.loads((H/'interface.json').read_text())['components'].values():
 if c['fitted']:obs.append(c['body_aabb_native_xy_mm'] if c['body_aabb_native_xy_mm']!=[0,0,0,0] else c['courtyard_native_xy_mm'])
for t in b.GetDrawings():
 if isinstance(t,p.PCB_TEXT) and t!=target and t.GetLayer()==p.F_SilkS:obs.append(box(t.GetBoundingBox(),.11))
options=[]
for angle in [0,90]:
 target.SetTextAngle(p.EDA_ANGLE(angle,p.DEGREES_T))
 for ix in range(402,499):
  for iy in range(402,554):
   x,y=ix/4,iy/4;target.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)));bb=box(target.GetBoundingBox(),.12)
   if bb[0]<100.25 or bb[2]>124.75 or bb[1]<100.25 or bb[3]>138.75:continue
   if bb[2]>124.2 and bb[3]>111.2 and bb[1]<122.4:continue
   if bb[2]>107.45 and bb[0]<117.55 and bb[3]>132.75:continue
   if any(overlaps(bb,c) for c in obs):continue
   options.append(((x-112.5)**2+(y-117.5)**2,x,y,angle))
assert options,'No readable placement for U2 +Z'
_,x,y,angle=min(options);target.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)));target.SetTextAngle(p.EDA_ANGLE(angle,p.DEGREES_T));pro=(H/'smove-r2-main.kicad_pro').read_bytes();p.SaveBoard(str(B),b);(H/'smove-r2-main.kicad_pro').write_bytes(pro);print('Unobstructed U2 +Z',x,y,angle)
