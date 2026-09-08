#!/usr/bin/python3
"""ECO: relieve debug-edge PCB below retained USB insertion envelope; relocate 3 probes.
Do not alter USB signal routes or substitute a connector. Final DRC/net parity mandatory.
"""
if __name__ == '__main__':
 raise SystemExit('Historical destructive ECO helper disabled for the finalized layout; see integrated/README.md native-CAD rebuild workflow.')
import pcbnew as p,json,math
from route import B,H,D,refill
from sexp import *
a=parse(B.read_text());a[:]=[x for x in a if not(isinstance(x,list) and x[0]=='gr_line' and val(one(x,'layer')[1])=='Edge.Cuts')]
# Preserve original USB port's below-shell clearance. Three retained bearing lands give a triangle.
for z in list(many(a,'zone')):
 if many(z,'keepout') and any(float(v[1])>123 and float(v[2])>136 for v in one(one(z,'polygon'),'pts')[1:]):a.remove(z)
outline=[(100,100),(125,100),(125,135.35),(114.08,135.35),(114.08,139),(100,139)]
for i,(s,e) in enumerate(zip(outline,outline[1:]+outline[:1])):a.append(node(f'(gr_line (start {s[0]} {s[1]}) (end {e[0]} {e[1]}) (stroke (width .05) (type default)) (layer "Edge.Cuts") (uuid {uid("usb-edge-"+str(i))}))'))
B.write_text(dump(a)+'\n');b=p.LoadBoard(str(B));V=lambda x,y:p.VECTOR2I(p.FromMM(x),p.FromMM(y));fps=list(b.GetFootprints())
def bb(f):v=f.GetBoundingBox(False,False);return [v.GetX()/1e6,v.GetY()/1e6,v.GetRight()/1e6,v.GetBottom()/1e6]
receipt=[]
for ref,desired in [('TP5',(102,111)),('TP6',(102,113)),('TP7',(102,116))]:
 f=next(f for f in fps if f.GetReference()==ref);net=next(iter(f.Pads())).GetNetname();old=list(p.ToMM(f.GetPosition()));opts=[]
 for ix in range(404,495):
  for iy in range(428,538):
   x,y=ix/4,iy/4;v=V(x,y);shape=p.SHAPE_CIRCLE(v,p.FromMM(.81))
   if any(x0-.75<x<x1+.75 and y0-.75<y<y1+.75 for g in fps if g!=f for x0,y0,x1,y1 in [bb(g)]):continue
   if any((isinstance(t,p.PCB_VIA) or t.IsOnLayer(p.F_Cu)) and t.GetNetname()!=net and p.SHAPE.Collide(shape,t.GetEffectiveShape()) for t in b.GetTracks()):continue
   if any(z.GetIsRuleArea() and p.SHAPE.Collide(shape,z.Outline()) for z in b.Zones()):continue
   opts.append(((x-desired[0])**2+(y-desired[1])**2,x,y))
 assert opts,ref
 _,x,y=min(opts);f.SetPosition(V(x,y));receipt.append(dict(ref=ref,net=net,old_xy=old,new_xy=[x,y]));print(ref,x,y)
pro=(H/'smove-r2-main.kicad_pro').read_bytes();p.SaveBoard(str(B),b);(H/'smove-r2-main.kicad_pro').write_bytes(pro);refill();(D/'usb-access-eco.json').write_text(json.dumps(receipt,indent=2)+'\n')
