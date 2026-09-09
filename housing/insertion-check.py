"""Bounded rigid nominal-body insertion screen; never bend/squeeze a battery.
Includes XY translations during tilt, then densely resamples a connected path.
This is not a supplier-pack or continuous swept-volume certification.
"""
import FreeCAD as A,Part,json,math
from pathlib import Path
R=Path(__file__).resolve().parents[1];d=A.openDocument(str(R/'housing/smove-r2-enclosure.FCStd'));base=d.Base.Shape
c=Part.makeBox(20,30,3,A.Vector(-10,-15,-1.5));attempts=[];chosen=None;tested=0
for axis in [(-1,0,0),(1,0,0),(0,-1,0),(0,1,0)]:
 states={};parents={};levels=[]
 def shape(angle,x,y):
  s=c.copy();s.rotate(A.Vector(),A.Vector(*axis),angle);s.translate(A.Vector(x,y,1.8-s.BoundBox.ZMin));return s
 for angle in range(90,-1,-5):
  good={}
  for x2 in (20,25,30):
   for y2 in (35,40,45,50,55):
    s=shape(angle,x2/2,y2/2);bb=s.BoundBox
    if bb.XMin<-.39 or bb.XMax>25.39 or bb.YMin<1.61 or bb.YMax>44.79:continue
    prev=next((key for key in states if abs(key[0]-x2)<=5 and abs(key[1]-y2)<=5),None)
    if angle!=90 and prev is None:continue
    tested+=1
    if base.common(s).Volume>1e-6:continue
    good[x2,y2]=True;parents[angle,x2,y2]=prev
  states=good;levels.append([angle,len(good)])
  if not states:break
 attempts.append(dict(axis=axis,levels=levels))
 if not states or angle!=0:continue
 end=min(states,key=lambda k:abs(k[0]-25)+abs(k[1]-45));path=[]
 while True:
  path.append([angle,end[0]/2,end[1]/2]);prev=parents[(angle,*end)]
  if prev is None:break
  end=prev;angle+=5
 path=list(reversed(path));path.append([0,12.5,22.5]);collisions=[];samples=0
 # Entry starts fully above the roof; slide the vertical body down before tilting.
 first=shape(*path[0]);above=max(0,20-first.BoundBox.ZMin)
 for i in range(41):
  s=first.copy();s.translate(A.Vector(0,0,above*(1-i/40)));samples+=1
  if base.common(s).Volume>1e-6:collisions.append(['entry',i])
 for a,b in zip(path,path[1:]):
  for i in range(31):
   vals=[u+(v-u)*i/30 for u,v in zip(a,b)];samples+=1
   if base.common(shape(*vals)).Volume>1e-6:collisions.append(vals)
 if not collisions:chosen=dict(axis=axis,path=path,samples=samples,collisions=[]);break
 attempts[-1]['dense_collisions']=collisions
report=dict(status='PASS_NOMINAL_BODY_ONLY' if chosen else 'NO_PATH_FOUND',body_mm=[20,30,3],search_poses=tested,attempts=attempts,result=chosen,notes='Rigid body only, no compression. Includes vertical entry and sampled tilt/XY translation. Lid/PCB/divider/nuts and wires removed. Final body X2.5..22.5 Y7.5..37.5 Z1.8..4.8. Complete protected pack/PCM/tabs/leads and removal remain sample gates.')
(R/'housing/validation/battery-insertion.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='attempts'},indent=2));raise SystemExit(not bool(chosen))
