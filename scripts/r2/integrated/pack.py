#!/usr/bin/python3
"""Bounded courtyard-based placement refinement; retain fixed functional anchors.
No courtyard edits, no relaxation. Pad/route DRC independently verifies output.
"""
if __name__ == '__main__':
 raise SystemExit('Historical destructive ECO helper disabled for the finalized layout; see integrated/README.md native-CAD rebuild workflow.')
import pcbnew as p,json,math
def box(x0,y0,x1,y1):return (x0,y0,x1,y1)
def translate(b,x,y):return (b[0]+x,b[1]+y,b[2]+x,b[3]+y)
def rotate(b,angle,origin=None):
 if abs(angle)%180<.01:return b
 return (b[1],-b[2],b[3],-b[0])
def dist(a,b):return math.hypot(max(a[0]-b[2],b[0]-a[2],0),max(a[1]-b[3],b[1]-a[3],0))
def inside(s):
 return s[0]>=100.1 and s[2]<=124.9 and s[1]>=100.1 and s[3]<=138.9 and not(s[2]>124.35 and s[3]>111.4 and s[1]<122.2) and not(s[2]>107.6 and s[0]<117.4 and s[3]>132.9)
from centered import H,R,D,OUTLINE,HOLES,POSE
B=H/'smove-r2-main.kicad_pcb';b=p.LoadBoard(str(B));V=lambda x,y:p.VECTOR2I(p.FromMM(x),p.FromMM(y))
fps={f.GetReference():f for f in b.GetFootprints()};polys={}
for r,f in fps.items():
 if r in HOLES:continue
 s=f.GetCourtyard(p.F_CrtYd);sbb=s.BBox();bb=box(sbb.GetX()/1e6,sbb.GetY()/1e6,sbb.GetRight()/1e6,sbb.GetBottom()/1e6)
 x,y=p.ToMM(f.GetPosition());polys[r]=translate(bb,-x,-y)
fixed=['U1','U2','J1','J2','SW2','SW3'];occupied=[box(x-3.55,y-3.55,x+3.55,y+3.55) for x,y in HOLES.values()]
for r in fixed:occupied.append(translate(polys[r],*p.ToMM(fps[r].GetPosition())))
poses={r:POSE[r] for r in fixed}
# Larger packages first, followed by local decoupling before generic resistors.
order=['U8','U9','U4','U5','U6','U3','D1','C3','C13','C2','C1','C6','C5','C8','C9','C7','C4','C11','C10']
order += sorted(set(polys)-set(fixed)-set(order))
for r in order:
 dx,dy,ang=POSE[r];opts=[]
 for a in [ang,ang+90]:
  local=rotate(polys[r],-(a-ang),origin=(0,0))
  for ix in range(401,500):
   for iy in range(401,556):
    x,y=ix/4,iy/4;cost=(x-dx)**2+(y-dy)**2+(.3 if a!=ang else 0)
    if cost>100:continue
    s=translate(local,x,y)
    if not inside(s) or any(dist(s,o)<.075 for o in occupied):continue
    opts.append((cost,x,y,a,s))
 assert opts,('No safe pose within10mm',r)
 _,x,y,a,s=min(opts,key=lambda v:v[0]);occupied.append(s);f=fps[r];f.SetOrientationDegrees(a);f.SetPosition(V(x,y));poses[r]=[x,y,a];print(r,x,y,a,flush=True)
pro=(H/'smove-r2-main.kicad_pro').read_bytes();p.SaveBoard(str(B),b);(H/'smove-r2-main.kicad_pro').write_bytes(pro)
(D/'placement.json').write_text(json.dumps(poses,indent=2)+'\n')
