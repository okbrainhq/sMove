"""Two printed parts; frozen PCB; integral battery tunnel; off-PCB M3 closure.
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
P=dict(XMin=-9.6,XMax=27.2,YMin=4.6,YMax=46.6,Floor=1.6,Wall=1.8,
       MainBottom=9.6,RoofBottom=15.2,Roof=1.4,BarrierBottom=6.6,BarrierThickness=.8,
       ScrewX=-5.,ScrewY=13.35,ScrewStop=12.,ScrewUnderHead=13.2,ScrewLength=8.,GrooveCeiling=11.15)
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
def rounded_route(name,points,bend,r,kind='harness'):
    vs=[A.Vector(*p) for p in points];edges=[];current=vs[0];setbacks=[]
    for a,b,c in zip(vs,vs[1:],vs[2:]):
        u=b-a;u.normalize();v=c-b;v.normalize();theta=math.acos(max(-1,min(1,u.dot(v))))
        setback=bend*math.tan(theta/2);setbacks.append(setback)
        start=b-u*setback;end=b+v*setback
        assert (start-current).dot(u)>-1e-6, 'Overlapping bend setbacks'
        if (start-current).Length>1e-7:edges.append(Part.makeLine(current,start))
        bisector=v-u;bisector.normalize();center=b+bisector*(bend/math.cos(theta/2))
        mid=(start-center)+(end-center);mid.normalize();mid=center+mid*bend
        edges.append(Part.Arc(start,mid,end).toShape());current=end
    if (vs[-1]-current).Length>1e-7:edges.append(Part.makeLine(current,vs[-1]))
    path=Part.Wire(edges);circle=Part.Wire([Part.makeCircle(r,vs[0],vs[1]-vs[0])])
    o=D.addObject('Part::Feature',name);o.Shape=path.makePipeShell([circle],True,False)
    o.addProperty('App::PropertyVectorList','RoutePoints');o.RoutePoints=vs
    o.addProperty('App::PropertyLength','BendRadius');o.BendRadius=bend
    o.addProperty('App::PropertyLength','EnvelopeRadius');o.EnvelopeRadius=r
    return role(o,kind),path.Length

outer=box('BaseBlank','Parameters.XMin','Parameters.YMin',0,'Parameters.XMax-Parameters.XMin','Parameters.YMax-Parameters.YMin','Parameters.RoofBottom')
inner=box('BaseCavity',-7.8,6.4,'Parameters.Floor',33.2,38.4,20)
baseparts=[cut('OpenTray',outer,inner)];basecuts=[]
lidparts=[box('LidBlank','Parameters.XMin','Parameters.YMin','Parameters.RoofBottom','Parameters.XMax-Parameters.XMin','Parameters.YMax-Parameters.YMin','Parameters.Roof')];lidcuts=[]
# Monolithic battery tunnel. South entry stays open until the lid's integral skirt closes it.
baseparts += [box('PocketWestWall',.6,6.1,1.6,1.,31.9,5.),box('PocketEastWall',23.4,6.1,1.6,1.,31.9,5.),
              box('PocketNorthStop',.6,38.,1.6,23.8,1.,5.),
              box('IntegralBatteryCeiling',.6,6.1,'Parameters.BarrierBottom',23.8,32.9,'Parameters.BarrierThickness')]
basecuts += [box('BatteryInsertionMouth',1.6,4.5,1.6,21.8,2.,14.),box('PackLeadSideExit',.5,32.,2.2,1.2,5.7,3.0)]
lidparts.append(box('BatteryEntryClosingSkirt',1.85,4.6,1.85,21.3,1.2,13.35))
# Off-board closure: the screw NEVER enters H1 or the pack projection.
baseparts.append(cyl('ClosureBoss','Parameters.ScrewX','Parameters.ScrewY',1.6,4.3,10.4))
baseparts.append(box('ClosureBossWeb',-8.,10.35,1.6,3.,6.,10.4))
basecuts += [hexagon('CaptiveNutPocket',-5.,13.35,5.3,5.8,2.7),box('NutSideEntry',-9.7,9.85,5.3,4.7,7.,2.7),
             cyl('BaseScrewBore',-5.,13.35,4.2,1.8,7.9),box('NutDoorSlidingRelief',-9.7,7.7,4.6,1.65,9.9,10.7)]
lidparts += [cyl('LidClosureBearing',-5.,13.35,'Parameters.ScrewStop',4.5,3.2),box('CaptiveNutDoor',-9.6,9.45,4.85,1.25,7.8,10.35)]
lidcuts += [cyl('LidScrewBore',-5.,13.35,11.9,1.8,5.),cyl('SocketHeadRecess',-5.,13.35,'Parameters.ScrewUnderHead',3.5,4.)]
basecuts.append(box('ClosureBearingSlidingRelief',-9.7,7.1,12.,2.4,11.,3.3))
# PCB drops into split grooves. Four insulating lower seats + lid lips; no screw preload.
seats=[];films=[]
for i,(x,y) in enumerate([(-.4,9.),(24.3,9.),(-.4,37.),(24.3,37.)],1):
    baseparts.append(box(f'GrooveSeat{i}',x,y,7.4,1.1,1.,2.0))
    # Structural webs attach seats to the integral tunnel, not to the pouch.
    baseparts.append(box(f'SeatWeb{i}',x,y,6.6,1.7 if x<0 else 1.1,1.,1.0))
    films.append(rb(f'SeatLiner{i}',-.25 if x<0 else 24.3,y,9.4,.95,1.,.2,'insulator'))
    lidparts.append(box(f'GrooveUpperLip{i}',0. if x<0 else 24.4,38.5 if y>30 else y+.1,'Parameters.GrooveCeiling',.6,.6 if y>30 else .8,4.05))
    seats.append([x,y])
# Separated edge fences bound translation AND rotation independently of closure friction.
for x in (-.6,25.3):
    for y in (9.,37.):baseparts.append(box('PCB_X_Stop',x,y,7.4,.3,2.,3.6))
for y in (8.4,39.3):
    for x in (-.4,24.3):baseparts.append(box('PCB_Y_Stop',x,y,7.4,1.1,.3,3.6))
for x in (-.4,24.3):baseparts.append(box('NorthStopWeb',x,37.,6.6,1.7 if x<0 else 1.1,2.6,1.0))
# H1 is now only a non-contact plastic deflection stop, not a metal screw bearing.
baseparts.append(cyl('H1InsulatingDeflectionStop',11.8,13.35,7.4,2.2,1.85))
# Two rigid north hooks; lower lid 1.5mm south, then slide north. Screw locks translation.
for i,x in enumerate((-5.,21.8),1):
    lidparts += [box(f'HookStem{i}',x,43.,12.6,3.,1.3,2.6),box(f'HookTongue{i}',x,43.,12.6,3.,2.8,1.2)]
    basecuts.append(box(f'HookPocket{i}',x-.2,44.6,12.35,3.4,1.5,1.7))
# Access envelopes, not connector-exact manufacturing models.
basecuts.append(box('USBOpening',24.0,16.7,9.9,4.,11.,5.7));lidcuts.append(box('USBRoofRelief',24.,16.7,9.9,4.,11.,5.7))
for ref,r in [('SW2',1.65),('SW3',1.65),('D1',1.9)]:
    x,y=MAIN['anchors'][ref]['center_native_xy_mm'];lidcuts.append(cyl(ref+'Access',x-100,139-y,10.8,r,7.))
# Open eyelets for separate insulated-wire lacing (not a clamp on the cell).
baseparts.append(box('LacingBridge',-7.9,31.5,8.0,5.1,6.5,1.2))
for y in (33.43,35.97):basecuts.append(cyl('LacingEyelet',-4.4,y,7.9,.7,1.4))
base=role(cut('Base',fuse('BaseStructure',baseparts),fuse('BaseOpenings',basecuts)),'print','BASE | integral insulated battery pocket | BODY underside')
lid=role(cut('Lid',fuse('LidStructure',lidparts),fuse('LidOpenings',lidcuts)),'print','LID | one M3 + two captured hooks | OUTWARD')
refs=[];clearances=[];hardware=[]
b=DATA['boards']['main'];pcb=polygon('MainSubstrate',b['outline_xy'],P['MainBottom'],b['thickness_mm']);drills=[]
for ref,f in b['footprints'].items():
    for i,p in enumerate(f['pads']):
        dx,dy=p['drill_mm'];x,y=p['local_xy']
        if dx>0 and dy>0:
            if abs(dx-dy)<1e-5:drills.append(cyl(f'Main_{ref}_Hole{i}',x,y,9.5,dx/2,1.2))
            else:drills.append(box(f'Main_{ref}_Slot{i}',x-dx/2,y-dy/2,9.5,dx,dy,1.2))
pcb=role(cut('MainPCB',pcb,fuse('MainPCBDrills',drills)),'main_pcb','FROZEN repaired PCB | 25 x 30 x 1 | H1 NOT a screw path');refs.append(pcb)
for ref,f in b['footprints'].items():
    if not f.get('fitted'):continue
    x0,y0,x1,y1=f['envelope_xy'];z0,z1=f['z_mm']
    o=rb('Main_'+ref,x0,y0,P['MainBottom']+z0,x1-x0,y1-y0,z1-z0,'main_component');o.Label=ref+' '+MAIN['components'][ref]['mpn']+' | conservative envelope';refs.append(o)
refs.append(rb('Main_USB_ShellTails',17.45,17.5,8.4,7.55,9.4,1.2,'tail'))
refs += films
refs.append(rb('PocketFloorLiner',1.7,6.1,1.6,21.6,31.8,.2,'insulator'))
refs.append(rb('BatteryCandidate_UNQUALIFIED',2.5,7.,1.8,20.,30.,3.,'battery'))
clearances.append(rb('BatteryAcceptance_21x31x4_3',2.,6.5,1.8,21.,31.,4.3,'battery_reserve'))
clearances.append(rb('RF_NO_BATTERY_HARNESS_METAL',-7.4,39.,-5.4,43.2,20.4,33.4,'rf_keepout'))
clearances.append(rb('USBPlugReserve',24.75,17.2,10.3,15.,10.,4.1))
packpoints=[];packlength=0.
# Top-exit wires turn WEST beside the shielded module, clear of all components.
# R2 centreline bend and 1.2mm OD are design reserves, subject to actual wire approval.
for i,y in enumerate((33.43,35.97),1):
    points=[[4.5,y,11.2],[4.5,y,13.2],[-1.5,y,13.2],[-1.5,y,3.5],[2.,y,3.5]]
    wire,length=rounded_route('BatteryWire'+str(i),points,2.,.6);refs.append(wire);packpoints.append(points);packlength+=length
    refs.append(role(cyl('BareWire'+str(i),4.5,y,9.1,.35,2.1),'harness','Tinned bundle <=0.7mm; trim below PCB <=0.5mm'))
    refs.append(role(cyl('SolderFillet'+str(i),4.5,y,10.6,.9,.6),'solder'))
    # Closed 0.4mm nylon lacing loop around bridge and vertical wire; not load-qualified.
    pts=[[-4.4,y,8.5],[-4.4,y,9.6],[-.6,y,9.6],[-.6,y,7.7],[-4.4,y,7.7],[-4.4,y,8.5]]
    lace,_=rounded_route('WireLacing'+str(i),pts,.3,.2,'lacing');refs.append(lace)
    clearances.append(rb('LacingKnotReserve'+str(i),-3.4,y-.5,9.7,1.,1.,1.,'lacing_reserve'))
screwblank=fuse('ScrewBlank',[cyl('ScrewShank',-5.,13.35,5.2,1.5,8.),cyl('ScrewHead',-5.,13.35,13.2,2.84,3.)])
screw=role(cut('ClosureScrew',screwblank,hexagon('SocketHex',-5.,13.35,14.5,2.5,1.9)),'hardware','M3x8 socket cap | max-envelope head 5.68 x 3 | off-PCB')
nut=role(cut('ClosureNut',hexagon('NutBlank',-5.,13.35,5.6,5.5,2.4),cyl('NutThreadEnvelope',-5.,13.35,5.5,1.5,2.6)),'hardware','M3 nut AF5.5 x 2.4 | side insert, lid captures entry');hardware += [screw,nut]
D.recompute()
for o in (base,lid):assert o.Shape.isValid() and len(o.Shape.Solids)==1,(o.Name,len(o.Shape.Solids))
meta=D.addObject('App::DocumentObjectGroup','Provenance')
meta.addProperty('App::PropertyString','Frames').Frames='X=nativeX-100; Y=139-nativeY; board bottom Z9.6; board bounds Y9..39, NOT Y0..30. Main underside BODY; accel/gyro +Z OUTWARD.'
meta.addProperty('App::PropertyString','Status').Status='CAD prototype, NOT manufacturing/charging release. Complete repair e033031 inherited; no PCB edits. Physical fit/creep/wire/battery/RF/magnetics open.'
meta.addProperty('App::PropertyString','PCB_SHA256').PCB_SHA256=b['board_sha256']
source=D.addObject('App::DocumentObjectGroup','EngineeringSources');source.Group=[o for o in D.Objects if o not in (source,S,meta)]
assembly=D.addObject('App::DocumentObjectGroup','InspectionAssembly');assembly.Label='MOVE THESE | separate display groups (not installation paths)'
groups=[('ViewBase',[base],(0,0,0)),('ViewLid',[lid],(0,0,28)),('ViewMain',[o for o in refs if o.Name.startswith('Main')],(0,0,14)),
        ('ViewBattery',[o for o in refs if o.Role=='battery'],(0,-35,0)),('ViewCables',[o for o in refs if o.Role in ('harness','solder','lacing')],(-12,0,14)),
        ('ViewHardware',hardware,(-6,0,34)),('ViewInsulation',[o for o in refs if o.Role=='insulator'],(0,-4,5))]
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
            pcb_bottom_z_mm=P['MainBottom'],screw_xy_mm=[-5,13.35],H1_xy_mm=[11.8,13.35],seat_xy_mm=seats,
            pack_route_points_mm=packpoints,pack_route_length_mm=packlength,input_hash=b['board_sha256'],printed_parts=2)
(OUT/'validation').mkdir(exist_ok=True);(OUT/'validation/build.json').write_text(json.dumps(report,indent=2)+'\n')
print('Generated TWO parts; unchanged PCB hash '+b['board_sha256'])
