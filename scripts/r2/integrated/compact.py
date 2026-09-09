#!/usr/bin/python3
"""Explicit placement study/ECO from f8c7ef6, never a release rebuild.
Three independently screened arrangements BEFORE routing. No pad, courtyard,
part, clearance or RF substitutions. Current routed native CAD is authoritative.
"""
from pathlib import Path
import json, math, sys, subprocess as sp, gc
# KiCad SWIG proxies on this host must outlive mutation; avoid cyclic-GC callbacks.
gc.disable(); sys.excepthook = sys.__excepthook__
import pcbnew as p
from sexp import parse, dump, many, one, val, prop
R=Path(__file__).resolve().parents[3]; H=R/'PCB/main'; D=R/'.cache/compact'; E=R/'docs/revision-r2/compact-placement'
V=lambda x,y:p.VECTOR2I(p.FromMM(x),p.FromMM(y))
BPOSE={
 'SW2':(111.,124.1,0), 'SW3':(111.,127.85,0),
 'J2':(121.3,126.5,0), 'D1':(115.1,126.3,0),
 'R1':(115.,121.5,90), 'R2':(116.8,123.3,90),
 'R11':(117.35,125.5,90),'R12':(117.35,127.7,90),'R13':(118.75,123.25,0),
 'C1':(106.5,125.5,0),'C2':(106.35,128.6,0),
 'R16':(115.1,128.65,0),'R17':(106.7,126.9,0),
 'R21':(101.5,124.,90),'R23':(103.25,124.4,0), 'R22':(103.,129.25,0), 'U9':(108.5,120.25,90), 'U6':(102.75,126.85,0),
}
CASES={
 'A_32_two_M3':dict(length=32.,holes={'H1':(103.6,103.6),'H2':(121.4,128.4)},pose={**BPOSE,'SW2':(121.1,124.2,0),'SW3':(110.6,124.4,0),'J2':(111.3,129.2,0),'D1':(115.7,126.9,0),'R11':(114.1,125.5,90),'R12':(115.1,129.5,0),'R13':(116.5,123.4,0),'R16':(107.0,124.,90)}),
 'B_30_single_M3_keyed':dict(length=30.,holes={'H1':(103.6,103.6)},pose=BPOSE),
 'C_29_single_M3_tight':dict(length=29.,holes={'H1':(103.6,103.6)},pose={**BPOSE,'SW3':(111.,126.85,0),'C2':(106.75,127.7,0),'R22':(103.,128.5,0),'R12':(117.35,127.0,90),'R16':(115.1,128.0,0)}),
}
SELECTED='B_30_single_M3_keyed'
def outline(length):return [(100,100),(125,100),(125,111.5),(124.45,111.5),(124.45,122.1),(125,122.1),(125,100+length),(100,100+length)]
def build(key,remove_routes=True):
 c=CASES[key];raw=parse((D/'baseline.kicad_pcb').read_text())
 raw[:]=[x for x in raw if not(isinstance(x,list) and (
   (remove_routes and x[0] in ('segment','via')) or x[0]=='gr_text' or
   (x[0].startswith('gr_') and many(x,'layer') and val(one(x,'layer')[1])=='Edge.Cuts') or
   (x[0]=='footprint' and prop(x,'Reference').startswith('H') and prop(x,'Reference') not in c['holes']) or
   (x[0]=='zone' and many(x,'name') and val(one(x,'name')[1])=='H2_M3_NO_COPPER' and 'H2' not in c['holes']))) ]
 temp=D/'scratch.kicad_pcb';temp.write_text(dump(raw)+'\n');b=p.LoadBoard(str(temp));fs={f.GetReference():f for f in b.GetFootprints()}
 for r,pos in c['pose'].items():fs[r].SetOrientationDegrees(pos[2]);fs[r].SetPosition(V(*pos[:2]))
 for r in ('H1','H2'):
  if r in c['holes']:
   delta=V(*c['holes'][r])-fs[r].GetPosition();fs[r].Move(delta)
   for z in b.Zones():
    if z.GetZoneName()==r+'_M3_NO_COPPER':z.Move(delta)
 pts=outline(c['length'])
 for a,d in zip(pts,pts[1:]+pts[:1]):
  s=p.PCB_SHAPE(b);s.SetShape(p.SHAPE_T_SEGMENT);s.SetStart(V(*a));s.SetEnd(V(*d));s.SetWidth(p.FromMM(.05));s.SetLayer(p.Edge_Cuts);b.Add(s)
 for text,x,y,angle in [('RESET',111.,124.1,0),('BOOT',111.,127.85,0),('BAT+',120.03,124.4,0),('BAT-',122.57,124.4,0),('U2 +Z',112.5,117.5,0)]:
  s=p.PCB_TEXT(b);s.SetText(text);s.SetPosition(V(x,y));s.SetTextSize(V(.6,.6));s.SetTextThickness(p.FromMM(.1));s.SetLayer(p.F_SilkS);s.SetTextAngle(p.EDA_ANGLE(angle,p.DEGREES_T));b.Add(s)
 return b

def bb(f):
 z=f.GetCourtyard(p.F_CrtYd).BBox();return [round(x/1e6,5) for x in (z.GetX(),z.GetY(),z.GetRight(),z.GetBottom())]
def study():
 from PIL import Image, ImageDraw, ImageFont
 font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
 reports=[]
 for key,c in CASES.items():
  b=build(key);fs={f.GetReference():f for f in b.GetFootprints()};boxes={r:bb(f) for r,f in fs.items() if not r.startswith('H')}
  collisions=[];outside=[]
  for r,a in boxes.items():
   for s,v in boxes.items():
    if s<=r:continue
    dx=min(a[2],v[2])-max(a[0],v[0]);dy=min(a[3],v[3])-max(a[1],v[1])
    if dx>0 and dy>0 and p.SHAPE.Collide(fs[r].GetCourtyard(p.F_CrtYd),fs[s].GetCourtyard(p.F_CrtYd)):collisions.append(dict(refs=[r,s],overlap_mm2=round(dx*dy,6)))
   if r not in ['U1','J1'] and (a[0]<100.2 or a[2]>124.8 or a[1]<100.2 or a[3]>100+c['length']-.2):outside.append(r)
   for h,(x,y) in c['holes'].items():
    distance=math.hypot(max(a[0]-x,0,x-a[2]),max(a[1]-y,0,y-a[3]))
    if distance<3.45:collisions.append(dict(refs=[r,h],bearing_clearance_mm=round(distance-3.45,4)))
  pads={r:[dict(number=a.GetNumber(),net=a.GetNetname(),xy_mm=list(p.ToMM(a.GetPosition()))) for a in fs[r].Pads()] for r in ['SW2','SW3','J2']}
  report=dict(candidate=key,board_mm=[25,c['length']],bounding_area_mm2=25*c['length'],area_reduction_pct=round(100*(35.5-c['length'])/35.5,3),placements=c['pose'],mounts=c['holes'],courtyard_aabbs_mm=boxes,courtyard_collisions=collisions,edge_assembly_violations=outside,pad_mapping=pads,lower_region_mm=[100,122,125,100+c['length']],lower_courtyard_area_mm2=round(sum(max(0,min(a[3],100+c['length'])-max(a[1],122))*max(0,min(a[2],125)-max(a[0],100)) for a in boxes.values()),3),screen_pass=not collisions and not outside,screen_scope='Conservative courtyard AABBs + unchanged 0.2mm assembly-to-board reserve + 3.45mm M3 bearing reserve, no routing assumed')
  reports.append(report)
  p.SaveBoard(str(D/(key+'.kicad_pcb')),b)
  image=Image.new('RGB',(820,1280),'white');draw=ImageDraw.Draw(image);scale=28
  def pt(x,y):return (55+(x-100)*scale,145+(y-100)*scale)
  draw.text((25,15),key,font=font,fill='black');draw.text((25,45),f"25 x {c['length']} mm | pre-route placement",font=font,fill='black')
  draw.polygon([pt(*a) for a in outline(c['length'])],fill='#dbece0',outline='black',width=2)
  for r,a in boxes.items():
   col='#e9ac6a' if r in c['pose'] else '#b7c7d9';draw.rectangle([pt(a[0],a[1]),pt(a[2],a[3])],fill=col,outline='#465060');draw.text(pt((a[0]+a[2])/2-.55,(a[1]+a[3])/2-.25),r,font=font,fill='black')
  for h,(x,y) in c['holes'].items():draw.ellipse([pt(x-3.45,y-3.45),pt(x+3.45,y+3.45)],outline='#bb0000',width=3);draw.ellipse([pt(x-1.6,y-1.6),pt(x+1.6,y+1.6)],fill='white',outline='black')
  draw.text((25,1170),f"Courtyard/bearing conflicts: {len(collisions)} | edge: {len(outside)}",font=font,fill='black');draw.text((25,1200),'Orange = relocated. Blue = retained. Not routing proof.',font=font,fill='black');image.save(E/'images'/(key+'.png'))
  print(key,'conflicts',collisions,'outside',outside)
 (E/'validation/placement-study.json').write_text(json.dumps(dict(baseline='f8c7ef6',selected=SELECTED,candidates=reports),indent=2)+'\n')
def apply():
 assert sp.check_output(['git','rev-parse','--short','HEAD'],text=True).strip()=='f8c7ef6'
 j=json.loads((E/'validation/placement-study.json').read_text());assert next(c for c in j['candidates'] if c['candidate']==SELECTED)['screen_pass']
 b=build(SELECTED,False);moved=set(CASES[SELECTED]['pose'])
 # Remove all routes touching moved non-GND nets, and all lower-region copper.
 # Retain high-speed USB pair and local IMU/regulator routing when unaffected.
 codes={a.GetNetCode() for f in b.GetFootprints() if f.GetReference() in moved for a in f.Pads() if a.GetNetname() not in ('','GND')}
 removed=[]
 for t in list(b.GetTracks()):
  ymax=max(t.GetStart().y,t.GetEnd().y)/1e6
  if t.GetNetCode() in codes or ymax>122.15:removed.append(t.m_Uuid.AsString())
 pro=(H/'smove-r2-main.kicad_pro').read_bytes();path=H/'smove-r2-main.kicad_pcb';p.SaveBoard(str(path),b)
 raw=parse(path.read_text());raw[:]=[x for x in raw if not(isinstance(x,list) and x[0] in ('segment','via') and val(one(x,'uuid')[1]) in removed)];path.write_text(dump(raw)+'\n')
 b=p.LoadBoard(str(path));b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(path),b);(H/'smove-r2-main.kicad_pro').write_bytes(pro)
 (E/'validation/placement-eco.json').write_text(json.dumps(dict(selected=SELECTED,removed_routes=removed,reroute_netcodes=sorted(codes),parts_unchanged=True,rules_unchanged=True),indent=2)+'\n')
if __name__=='__main__':
 if sys.argv[1:]==['study']:study()
 elif sys.argv[1:]==['--apply']:apply()
 else:raise SystemExit('study | --apply; never replay after routing')
