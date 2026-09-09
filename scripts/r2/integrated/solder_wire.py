#!/usr/bin/python3
"""One-shot solder-wire ECO from main 4cb3c32; explicit --apply only.
Canonical output is routed native CAD. Never replay placement after routing.
"""
from pathlib import Path
import json, sys, subprocess as sp
import pcbnew as p
from sexp import *
R=Path(__file__).resolve().parents[3];H=R/'PCB/main';D=R/'.cache/solder-wire'
OUTLINE=[(100,100),(125,100),(125,111.5),(124.45,111.5),(124.45,122.1),(125,122.1),(125,135.5),(100,135.5)]
HOLES={'H1':(103.6,103.6),'H2':(121.4,131.9)}
POSE={'J2':(112.5,132.6,0),'SW3':(110.,127.,90),'D1':(116.,126.8,0),'R11':(114.2,126.,90),'R12':(114.2,128.3,90),'R13':(116.,124.,0)}
FP='BatteryWire_2x_PTH_P2.54mm_D1.0mm'
V=lambda x,y:p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def save(path,a):path.write_text(dump(a)+'\n')
def prop_set(a,k,v):next(x for x in many(a,'property') if val(x[1])==k)[2]=q(v)
def schematic():
 for path in [H/'power.kicad_sch',H/'smove-r2-main.kicad_sym']:
  a=parse(path.read_text());lib=one(a,'lib_symbols') if path.suffix=='.kicad_sch' else a
  s=next(x for x in many(lib,'symbol') if val(x[1]) in ['J2','smove-r2-main:J2']);one(s,'in_bom')[1]='no'
  pins=next(x for x in many(s,'symbol') if val(x[1])=='J2_1_1')
  pins[:]=[x for x in pins if not(isinstance(x,list) and x[0]=='pin' and val(one(x,'number')[1])=='MP')]
  for pin in many(pins,'pin'):one(pin,'name')[1]=q('BAT+' if val(one(pin,'number')[1])=='1' else 'BAT-')
  if path.suffix=='.kicad_sch':
   s=next(x for x in many(a,'symbol') if prop(x,'Reference')=='J2');one(s,'in_bom')[1]='no'
   for k,v in {'Value':'Battery wire pads 2.54mm','Footprint':'smove-r2-main:'+FP,'MPN':'','LCSC':''}.items():prop_set(s,k,v)
   s[:]=[x for x in s if not(isinstance(x,list) and x[0]=='pin' and val(x[1])=='MP')]
   # Remove only the old mounting-tab GND branch at (50.8,91.44), not battery return.
   for x in list(many(a,'wire')):
    pts=one(x,'pts')[1:]
    if ['xy','50.8','91.44'] in pts:a.remove(x)
   for x in list(many(a,'symbol')):
    if prop(x,'Reference')=='#PWR10':a.remove(x)
   # The branch was a separately labelled stub; its endpoint label is no longer useful.
   for x in list(many(a,'label')):
    if one(x,'at')[1:3]==['50.8','96.52']:a.remove(x)
   for x in many(a,'text'):
    if 'PH2' in val(x[1]) or 'J2' in val(x[1]):x[1]=q('J2: direct PTH battery wire pads; 2.54mm (0.1in) centre pitch; 1.0mm holes.\n1 BAT+ = protected PACK_P; 2 BAT- = GND. No connector / no BOM item.\nQualify protected cell and charge current first; secure insulated wires to housing lacing bridge.')
  save(path,a)
 # Remove obsolete header footprint rather than leaving a selectable obsolete assembly part.
 (H/'smove-r2-main.pretty/JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal.kicad_mod').unlink()

def layout():
 path=H/'smove-r2-main.kicad_pcb';raw=parse(path.read_text());oldj=next(f for f in many(raw,'footprint') if prop(f,'Reference')=='J2');nets={val(a[1]):one(a,'net')[1:] for a in many(oldj,'pad')}
 # Reuse symbol linkage, but remove ALL connector pads, graphics and 3D/header geometry.
 raw=parse(path.read_text());j=next(f for f in many(raw,'footprint') if prop(f,'Reference')=='J2')
 j[1]=q('smove-r2-main:'+FP)
 j[:]=[x for x in j if not(isinstance(x,list) and x[0] in ['pad','fp_line','fp_rect','fp_circle','fp_arc','fp_poly','fp_text','model','zone','attr'])]
 j.append(['attr','through_hole','exclude_from_bom','exclude_from_pos_files'])
 one(j,'descr')[1]=q('Two PCB-only plated battery-wire solder pads; 2.54 mm centre pitch, 1.0 mm drill, 2.0 mm copper; no fitted connector; external strain relief required')
 one(j,'tags')[1]=q('battery wire solder pads PTH 2.54mm PCB-only')
 for k,v in {'Value':'Battery wire pads 2.54mm','MPN':'','LCSC':'','Manufacturer':''}.items():prop_set(j,k,v)
 # Pads have no paste: hand-solder stranded wire only, not an SMT procurement item.
 for num,x in [('1',-1.27),('2',1.27)]:
  j.append(node(f'(pad "{num}" thru_hole circle (at {x} 0) (size 2.0 2.0) (drill 1.0) (layers "*.Cu" "*.Mask") (solder_mask_margin 0.05) (zone_connect 2) (net {nets[num][0]} {nets[num][1]}))'))
 for a,c in [((-2.52,-2.2),(2.52,-2.2)),((2.52,-2.2),(2.52,2.2)),((2.52,2.2),(-2.52,2.2)),((-2.52,2.2),(-2.52,-2.2))]:
  j.append(node(f'(fp_line (start {a[0]} {a[1]}) (end {c[0]} {c[1]}) (stroke (width 0.05) (type solid)) (layer "F.CrtYd"))'))
 movedcodes={one(a,'net')[1] for f in many(raw,'footprint') if prop(f,'Reference') in POSE for a in many(f,'pad') if many(a,'net') and val(one(a,'net')[2]) not in ('','GND')}
 movednets={val(n[2]) for n in many(raw,'net') if n[1] in movedcodes};removed=[]
 for t in list(raw):
  if isinstance(t,list) and t[0] in ('segment','via'):
   coords=[one(t,'at')] if t[0]=='via' else [one(t,'start'),one(t,'end')]
   if one(t,'net')[1] in movedcodes or max(float(c[2]) for c in coords)>135.1:removed.append(val(one(t,'uuid')[1]));raw.remove(t)
 raw[:]=[x for x in raw if not(isinstance(x,list) and x[0]=='gr_line' and val(one(x,'layer')[1])=='Edge.Cuts')]
 save(path,raw);b=p.LoadBoard(str(path));fps={f.GetReference():f for f in b.GetFootprints()}
 for r,(x,y,ang) in POSE.items():fps[r].SetOrientationDegrees(ang);fps[r].SetPosition(V(x,y))
 delta=V(0,-3.5);fps['H2'].Move(delta)
 for z in b.Zones():
  if z.GetZoneName()=='H2_M3_NO_COPPER':z.Move(delta)
 for x in list(b.GetDrawings()):
  if x.GetLayer()==p.Edge_Cuts:b.Remove(x)
  elif isinstance(x,p.PCB_TEXT):
   if x.GetText()=='BOOT':x.SetPosition(V(107.8,127));x.SetTextAngle(p.EDA_ANGLE(90,p.DEGREES_T))
   if x.GetText()=='U2 +Z':x.SetPosition(V(103.7,132.5))
 for a,c in zip(OUTLINE,OUTLINE[1:]+OUTLINE[:1]):
  s=p.PCB_SHAPE(b);s.SetShape(p.SHAPE_T_SEGMENT);s.SetStart(V(*a));s.SetEnd(V(*c));s.SetLayer(p.Edge_Cuts);s.SetWidth(p.FromMM(.05));b.Add(s)
 for text,x,y in [('BAT+',111.23,130.25),('BAT-',113.77,130.25)]:
  t=p.PCB_TEXT(b);t.SetText(text);t.SetPosition(V(x,y));t.SetTextSize(V(.65,.65));t.SetTextThickness(p.FromMM(.1));t.SetLayer(p.F_SilkS);b.Add(t)
 pro=(H/'smove-r2-main.kicad_pro').read_bytes();b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(path),b);(H/'smove-r2-main.kicad_pro').write_bytes(pro)
 # Publish source library footprint from exactly the placed geometry, at its local origin.
 import copy
 f=copy.deepcopy(j);f[1]=q(FP);f[:]=[x for x in f if not(isinstance(x,list) and x[0] in ['at','path','sheetname','sheetfile','uuid'])]
 for pad in many(f,'pad'):pad[:]=[x for x in pad if not(isinstance(x,list) and x[0]=='net')]
 save(H/'smove-r2-main.pretty'/(FP+'.kicad_mod'),f)
 parts=json.loads((H/'parts-main.json').read_text());parts['J2'].update(mpn='',jlc='',manufacturer='',value='Battery wire pads 2.54mm',package='Two plated through-hole wire pads, no fitted component',purpose='Protected-pack direct wire attachment',notes='1 BAT+ PACK_P; 2 BAT- GND; 2mm pads / 1mm finished-hole target, 0.54mm copper / 0.44mm mask web; no paste; strain relief mandatory',fitted=False,fp=FP,pins={'1':'PACK_P','2':'GND'})
 for r,(x,y,ang) in POSE.items():parts[r]['placement']=[x,y,ang]
 (H/'parts-main.json').write_text(json.dumps(parts,indent=2)+'\n')
 (D/'eco-routing-intent.json').write_text(json.dumps(dict(changed_placements=POSE,changed_holes=HOLES,removed_route_uuids=removed,reroute_nets=sorted(movednets),unchanged_usb_and_sensor_placements=True),indent=2)+'\n')
if __name__=='__main__':
 if sys.argv[1:]!=['--apply']:raise SystemExit('Explicit --apply required; one-shot ECO, not a release rebuild.')
 assert sp.check_output(['git','rev-parse','HEAD'],text=True).strip()=='4cb3c32193bda18d624b7974b65162a7a44f69a0'
 schematic();layout()
