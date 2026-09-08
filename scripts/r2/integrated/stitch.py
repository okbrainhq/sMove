#!/usr/bin/python3
"""Ground stitching for current native layout; no geometry edits.
DRC is run separately; all generated copper is subject to original constraints.
"""
import pcbnew as p,math,json
from route import H,B,D,refill
from sexp import *
b=p.LoadBoard(str(B))
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
    for zz in list(b.Zones())+[z for f in b.GetFootprints() for z in f.Zones()]:
     if zz.GetIsRuleArea() and p.SHAPE.Collide(sh,zz.Outline()):bad=True;break
    if not bad:pts.append((x,y))
  if pts:
   x,y=pts[len(pts)//2];via=p.PCB_VIA(b);via.SetPosition(V(x,y));via.SetWidth(p.FromMM(.45));via.SetDrill(p.FromMM(.2));via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(b.FindNet('GND'));b.Add(via);added.append([x,y])
print('surface stitching',added,flush=True)
pro=(H/'smove-r2-main.kicad_pro').read_bytes();p.SaveBoard(str(B),b);(H/'smove-r2-main.kicad_pro').write_bytes(pro);refill()
