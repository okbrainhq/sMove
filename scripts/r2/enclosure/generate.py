"""Two printed parts; frozen PCB; integral battery tunnel; central H1 M3 closure; NO modeled leads.
Run through housing/entry.py with the pinned FreeCAD runtime. Never writes PCB/.
All dimensions are nominal mm; see housing/PRINTING-ASSEMBLY.md for acceptance.
"""
import hashlib,json,math
from pathlib import Path
import FreeCAD as A
import Part,Sketcher,MeshPart
ROOT=Path(__file__).resolve().parents[3]; OUT=ROOT/'housing'; EX=OUT/'dist'; EX.mkdir(parents=True,exist_ok=True)
CACHE=ROOT/'.cache/housing'; DATA=json.loads((CACHE/'input-geometry.json').read_text()); MAIN=json.loads((ROOT/'PCB/main/interface.json').read_text())
assert DATA['boards']['main']['board_sha256']==hashlib.sha256((ROOT/MAIN['native_board']).read_bytes()).hexdigest()
P=dict(XMin=-1.9,XMax=26.9,YMin=4.6,YMax=46.6,Floor=1.6,Wall=1.4,
       MainBottom=12.6,RoofBottom=18.2,Roof=1.4,BarrierBottom=6.6,BarrierThickness=.8,
       ScrewX=11.8,ScrewY=13.35,ScrewUnderHead=16.4,ScrewLength=8.,GrooveCeiling=14.15)
D=A.newDocument('sMove_TwoPart'); D.Label='sMove | TWO PARTS | PCB underside BODY / IMU +Z OUTWARD'
S=D.addObject('Spreadsheet::Sheet','Parameters')
for i,(k,v) in enumerate(P.items(),1): S.set(f'A{i}',k); S.set(f'B{i}',f'={v} mm'); S.setAlias(f'B{i}',k)
S.setColumnWidth('A',190); S.setColumnWidth('B',110)
def expr(v): return v if isinstance(v,str) else f'{v:.9g} mm'
def box(name,x,y,z,dx,dy,dz):
    o=D.addObject('Part::Box',name)
    for prop,v in zip(('Length','Width','Height','Placement.Base.x','Placement.Base.y','Placement.Base.z'),(dx,dy,dz,x,y,z)):o.setExpression(prop,expr(v))
    return o
def cyl(name,x,y,z,r,h):
    o=D.addObject('Part::Cylinder',name)
    for prop,v in zip(('Radius','Height','Placement.Base.x','Placement.Base.y','Placement.Base.z'),(r,h,x,y,z)):o.setExpression(prop,expr(v))
    return o
def fuse(name,obs):
    if len(obs)==1:return obs[0]
    o=D.addObject('Part::MultiFuse',name);o.Shapes=obs;o.Refine=True;return o
def cut(name,b,t):
    o=D.addObject('Part::Cut',name);o.Base=b;o.Tool=t;o.Refine=True;return o
def polygon(name,points,z,h):
    s=D.addObject('Sketcher::SketchObject',name+'Profile');s.Placement.Base.z=z
    for p,q in zip(points,points[1:]+points[:1]):
        i=s.addGeometry(Part.LineSegment(A.Vector(*p,0),A.Vector(*q,0)),False);s.addConstraint(Sketcher.Constraint('Block',i))
    o=D.addObject('Part::Extrusion',name);o.Base=s;o.Dir=A.Vector(0,0,1);o.LengthFwd=h;o.Solid=True;return o
def hexagon(name,x,y,z,af,h):
    r=af/math.sqrt(3);return polygon(name,[[x+r*math.cos(i*math.pi/3+math.pi/6),y+r*math.sin(i*math.pi/3+math.pi/6)] for i in range(6)],z,h)
def role(o,r,label=None):
    o.addProperty('App::PropertyString','Role');o.Role=r
    if label:o.Label=label
    return o
def rb(name,x,y,z,dx,dy,dz,r='clearance'):return role(box(name,x,y,z,dx,dy,dz),r)
outer=box('BaseBlank','Parameters.XMin','Parameters.YMin',0,'Parameters.XMax-Parameters.XMin','Parameters.YMax-Parameters.YMin','Parameters.RoofBottom')
inner=box('BaseCavity',-.5,6.4,'Parameters.Floor',26.,38.4,22)
baseparts=[cut('OpenTray',outer,inner)];basecuts=[]
lidparts=[box('LidBlank','Parameters.XMin','Parameters.YMin','Parameters.RoofBottom','Parameters.XMax-Parameters.XMin','Parameters.YMax-Parameters.YMin','Parameters.Roof')];lidcuts=[]
# Monolithic battery tunnel. South entry stays open until the lid's integral skirt closes it.
baseparts += [box('PocketWestWall',.6,6.1,1.6,1.,31.9,5.),box('PocketEastWall',23.4,6.1,1.6,1.,31.9,5.),
              box('PocketNorthStop',.6,38.,1.6,23.8,1.,5.),
              box('IntegralBatteryCeiling',.6,6.1,'Parameters.BarrierBottom',23.8,32.9,'Parameters.BarrierThickness')]
basecuts += [box('BatteryInsertionMouth',1.6,4.5,1.6,21.8,2.,17.)]
lidparts.append(box('BatteryEntryClosingSkirt',1.85,4.6,1.85,21.3,1.2,16.35))
# ONLY central closure through existing unplated H1. Nut and screw are ABOVE
# the solid battery barrier, not in the cell. Side-entry below PCB is for nut only.
baseparts += [cyl('CentralNutBoss','Parameters.ScrewX','Parameters.ScrewY',7.4,4.6,4.5),
              box('CentralBossStructuralBeam',.6,10.7,7.4,23.8,5.3,1.)]
basecuts += [hexagon('CaptiveNutPocket',11.8,13.35,8.3,5.8,2.7),
             box('NutFrontEntry',8.3,8.65,8.3,7.,4.7,2.7),
             cyl('CentralBlindBore',11.8,13.35,7.4,1.8,5.1)]
# The closure reacts at case perimeter/hard stops, not on PCB or pouch.
# Wide bearing begins above nearby component envelopes. No metal washer on PCB.
lidparts += [cyl('CentralInsulatingBearing',11.8,13.35,15.1,4.3,3.1),
             box('IntegratedFrontNutStop',8.3,4.6,8.2,7.,3.95,10.)]
lidcuts += [cyl('CentralLidBore',11.8,13.35,15.,1.8,5.),
            cyl('CentralSocketRecess',11.8,13.35,'Parameters.ScrewUnderHead',3.5,4.)]
# Four stout, wall-rooted corners replace slender posts, webs and 0.3mm fences.
# Each corner is ONE stepped block; the PCB clearance cut creates its locating L.
seats=[];films=[]
for i,(x,y) in enumerate([(-1.9,6.4),(24.3,6.4),(-1.9,36.8),(24.3,36.8)],1):
    baseparts.append(box(f'SolidCorner{i}',x,y,1.6,2.6,4.6,12.4))
    fy=9.1 if y<20 else 37.0
    films.append(rb(f'SeatLiner{i}',-.25 if x<0 else 24.3,fy,12.4,.95,1.8 if y<20 else 2.,.2,'insulator'))
    # Roof-down printing: these broad integral pads grow from the lid, no hooks.
    lidparts.append(box(f'BroadLidPad{i}',-.3 if x<0 else 23.9,9.0 if y<20 else 37.0,'Parameters.GrooveCeiling',1.4,1.4 if y<20 else 2.,4.05))
    seats.append([-.4 if x<0 else 24.3,fy])
basecuts.append(box('CornerPCBRelief',-.3,8.7,12.4,25.6,30.6,1.7))
# Annular R2.2 dielectric stop below H1 has 0.35mm initial gap. No clamp on PCB.
baseparts.append(cyl('H1InsulatingDeflectionStop',11.8,13.35,11.9,2.2,.35))
# Straight-down lid: no hooks, undercut hook pockets, slide or snap tabs.
# Corner pads register inside the wall; the central screw alone holds closure.
# Access envelopes, not connector-exact manufacturing models.
basecuts.append(box('USBOpening',24.0,16.7,12.9,4.,11.,5.7));lidcuts.append(box('USBRoofRelief',24.,16.7,12.9,4.,11.,5.7))
for ref,r in [('SW2',1.65),('SW3',1.65),('D1',1.9)]:
    x,y=MAIN['anchors'][ref]['center_native_xy_mm'];lidcuts.append(cyl(ref+'Access',x-100,139-y,13.8,r,7.))
base=role(cut('Base',fuse('BaseStructure',baseparts),fuse('BaseOpenings',basecuts)),'print','BASE | solid corners + battery slot + M3 socket | BODY underside')
lid=role(cut('Lid',fuse('LidStructure',lidparts),fuse('LidOpenings',lidcuts)),'print','LID | plain drop-on, broad integral pads | OUTWARD')
refs=[];clearances=[];hardware=[]
b=DATA['boards']['main'];pcb=polygon('MainSubstrate',b['outline_xy'],P['MainBottom'],b['thickness_mm']);drills=[]
for ref,f in b['footprints'].items():
    for i,p in enumerate(f['pads']):
        dx,dy=p['drill_mm'];x,y=p['local_xy']
        if dx>0 and dy>0:
            if abs(dx-dy)<1e-5:drills.append(cyl(f'Main_{ref}_Hole{i}',x,y,12.5,dx/2,1.2))
            else:drills.append(box(f'Main_{ref}_Slot{i}',x-dx/2,y-dy/2,12.5,dx,dy,1.2))
pcb=role(cut('MainPCB',pcb,fuse('MainPCBDrills',drills)),'main_pcb','FROZEN repaired PCB | 25 x 30 x 1 | central M3 through unchanged NPTH H1; groove retained');refs.append(pcb)
for ref,f in b['footprints'].items():
    if not f.get('fitted'):continue
    x0,y0,x1,y1=f['envelope_xy'];z0,z1=f['z_mm']
    o=rb('Main_'+ref,x0,y0,P['MainBottom']+z0,x1-x0,y1-y0,z1-z0,'main_component');o.Label=ref+' '+MAIN['components'][ref]['mpn']+' | conservative envelope';refs.append(o)
refs.append(rb('Main_USB_ShellTails',17.45,17.5,11.4,7.55,9.4,1.2,'tail'))
refs += films
refs.append(rb('PocketFloorLiner',1.7,6.1,1.6,21.6,31.8,.2,'insulator'))
refs.append(rb('BatteryCandidate_UNQUALIFIED',2.5,7.,1.8,20.,30.,3.,'battery'))
clearances.append(rb('BatteryAcceptance_21x31x4_3',2.,6.5,1.8,21.,31.,4.3,'battery_reserve'))
clearances.append(rb('RF_NO_BATTERY_METAL',-7.4,39.,-5.4,43.2,20.4,33.4,'rf_keepout'))
clearances.append(rb('USBPlugReserve',24.75,17.2,13.3,15.,10.,4.1))
# No wires, solder, lacing, channels, exits or reserved lead volume. User routes leads.
screwblank=fuse('ScrewBlank',[cyl('ScrewShank',11.8,13.35,8.4,1.5,8.),cyl('ScrewHead',11.8,13.35,16.4,2.84,3.)])
screw=role(cut('ClosureScrew',screwblank,hexagon('SocketHex',11.8,13.35,17.7,2.5,1.9)),'hardware','ONLY M3x8 | through H1 | insulating case bearing, no PCB clamp')
nut=role(cut('ClosureNut',hexagon('NutBlank',11.8,13.35,8.6,5.5,2.4),cyl('NutThreadEnvelope',11.8,13.35,8.5,1.5,2.6)),'hardware','M3 nut AF5.5 x 2.4 | above sealed battery ceiling; front insert')
hardware += [screw,nut]
D.recompute()
for o in (base,lid):assert o.Shape.isValid() and len(o.Shape.Solids)==1,(o.Name,len(o.Shape.Solids))
meta=D.addObject('App::DocumentObjectGroup','Provenance')
meta.addProperty('App::PropertyString','Frames').Frames='X=nativeX-100; Y=139-nativeY; board bottom Z12.6; board bounds Y9..39, NOT Y0..30. Main underside BODY; accel/gyro +Z OUTWARD.'
meta.addProperty('App::PropertyString','Status').Status='CAD prototype, NOT manufacturing/charging release. Complete repair e033031 inherited; no PCB edits. Leads entirely user routed and NOT verified. Physical fit/creep/battery qualification open.'
meta.addProperty('App::PropertyString','PCB_SHA256').PCB_SHA256=b['board_sha256']
source=D.addObject('App::DocumentObjectGroup','EngineeringSources');source.Group=[o for o in D.Objects if o not in (source,S,meta)]
assembly=D.addObject('App::DocumentObjectGroup','InspectionAssembly');assembly.Label='MOVE THESE | separate display groups (not installation paths)'
groups=[('ViewBase',[base],(0,0,0)),('ViewLid',[lid],(0,0,28)),('ViewMain',[o for o in refs if o.Name.startswith('Main')],(0,0,14)),
        ('ViewBattery',[o for o in refs if o.Role=='battery'],(0,-35,0)),
        ('ViewHardware',hardware,(0,0,42)),('ViewInsulation',[o for o in refs if o.Role=='insulator'],(0,-4,5))]
for name,objects,offset in groups:
    g=D.addObject('App::Part',name);assembly.addObject(g);g.Label=name[4:]+' | movable inspection group';g.addProperty('App::PropertyVector','ExplodedOffset','Inspection');g.ExplodedOffset=A.Vector(*offset)
    for obj in objects:
        link=D.addObject('App::Link','Inspect_'+obj.Name);link.setLink(obj);link.LinkPlacement=obj.Placement;g.addObject(link);link.Label=obj.Label
D.recompute()
Part.export([base,lid]+refs+hardware,str(EX/'smove-r2-assembly.step'));Part.export([base,lid],str(EX/'smove-r2-printable.step'))
mesh_reports={}
for name,obj in [('base',base),('lid',lid)]:
    sh=obj.Shape.copy()
    if name=='lid':sh.rotate(A.Vector(),A.Vector(1,0,0),180)
    bb=sh.BoundBox;sh.translate(A.Vector(-bb.XMin,-bb.YMin,-bb.ZMin));mesh=MeshPart.meshFromShape(Shape=sh,LinearDeflection=.04,AngularDeflection=.12,Relative=False);mesh.write(str(EX/f'{name}.stl'))
    mesh_reports[name]=dict(volume_mm3=obj.Shape.Volume,triangles=mesh.CountFacets)
for step in EX.glob('*.step'):step.write_text('\n'.join(line.rstrip() for line in step.read_text().splitlines())+'\n')
# Source objects remain fixed; movable App::Link copies are the only display assembly.
D.saveAs(str(OUT/'smove-r2-enclosure.FCStd'))
report=dict(status='GENERATED_REQUIRE_VERIFY',parameters_mm=P,reference_objects=[o.Name for o in refs],hardware_objects=[o.Name for o in hardware],
            clearance_objects=[o.Name for o in clearances],inspection_groups=[g[0] for g in groups],parts=mesh_reports,
            pcb_bottom_z_mm=P['MainBottom'],screw_xy_mm=[11.8,13.35],H1_xy_mm=[11.8,13.35],seat_xy_mm=seats,
            lead_geometry='NONE_USER_ROUTED_NOT_VERIFIED',previous_LWH_mm=[42,36.8,16.6],prior_central_draft_LWH_mm=[42,28.8,19.6],print_simplification='Four wall-rooted corner blocks, broad lid pads, integral front nut stop, straight-down lid; no hook features or slender fences',input_hash=b['board_sha256'],printed_parts=2)
(OUT/'validation').mkdir(exist_ok=True);(OUT/'validation/build.json').write_text(json.dumps(report,indent=2)+'\n')
print('Generated TWO parts; unchanged PCB hash '+b['board_sha256'])
