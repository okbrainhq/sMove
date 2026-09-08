"""Rigid pouch-envelope insertion screen; no bending/squeezing permitted."""
import FreeCAD as A,Part,json,math
from pathlib import Path
R=Path(__file__).resolve().parents[1];d=A.openDocument(str(R/'housing/smove-r2-enclosure.FCStd'));base=d.Base.Shape
# Test x-axis tilt, centre allowed to translate along Y; keep body bottom 1.8mm above floor datum.
c=Part.makeBox(20,30,3,A.Vector(-10,-15,-1.5));states={};parents={};levels=[]
for angle in range(90,-1,-5):
 good={}
 for y2 in range(15,72):
  y=y2/2;s=c.copy();s.rotate(A.Vector(),A.Vector(1,0,0),angle);s.translate(A.Vector(12.5,y,1.8-s.BoundBox.ZMin))
  if s.BoundBox.YMin < -1.39 or s.BoundBox.YMax>44.79:continue
  if base.common(s).Volume>1e-6:continue
  prev=next((k for k in states if abs(k-y2)<=3),None)
  if angle==90 or prev is not None:good[y2]=s;parents[(angle,y2)]=(angle+5,prev)
 states=good;levels.append([angle,len(good)])
 if not states:break
print('insertion levels',levels)
if states and angle==0:
 end=min(states,key=lambda k:abs(k-38));path=[]
 while True:
  path.append([angle,end/2]);p=parents[(angle,end)]
  if p[1] is None:break
  angle,end=p
 print('PATH',list(reversed(path)));(R/'.cache/centered/insertion-path.json').write_text(json.dumps(dict(status='NOMINAL_20x30x3_COARSE_RIGID_PATH_NOT_PACK_QUALIFICATION',path=list(reversed(path))),indent=2))
if states and path:
 path=list(reversed(path));path.append([0,19.]);collisions=[];minimum=1e9;count=0
 for (a0,y0),(a1,y1) in zip(path,path[1:]):
  for i in range(21):
   t=i/20;angle=a0+(a1-a0)*t;y=y0+(y1-y0)*t;s=c.copy();s.rotate(A.Vector(),A.Vector(1,0,0),angle);s.translate(A.Vector(12.5,y,1.8-s.BoundBox.ZMin));vol=base.common(s).Volume;count+=1
   if vol>1e-6:collisions.append([angle,y,vol])
 print('dense',count,'collisions',collisions)
 report=dict(status='PASS_NOMINAL_BODY_ONLY' if not collisions else 'FAIL',body_mm=[20,30,3],samples=count,path=path,collisions=collisions,notes='Rigid 20x30x3 body only, no bending or compression. Actual protected pack/seal/tabs/wires remain unqualified; larger installed acceptance envelope is NOT proven insertable. Lid/PCB/divider/nuts removed during insertion. Flat final slide to y19.')
 (R/'housing/validation/battery-insertion.json').write_text(json.dumps(report,indent=2)+'\n')
