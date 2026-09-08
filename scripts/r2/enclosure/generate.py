"""R2 vertical-carrier, two printed pieces. Native editable CSG/sketch/Spreadsheet.
Pinned ABI entry: python3 scripts/freecad/run.py housing/entry.py generate
Geometry is frozen-contract geometry, NOT a measured component/plug/pack model.
"""
import json
from pathlib import Path
import FreeCAD as A
import Part
import Sketcher
import MeshPart
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'housing'; EX=OUT/'dist';EX.mkdir(parents=True,exist_ok=True)
(ROOT/'.cache/housing').mkdir(parents=True,exist_ok=True)
assert json.loads((OUT/'status.json').read_text()).get('allow_generate_or_export'), 'Connector hold'
DATA=json.loads((ROOT/'.cache/housing/input-geometry.json').read_text())
MAIN=json.loads((ROOT/'PCB/main/interface.json').read_text())
CARRIER=json.loads((ROOT/'PCB/imu-carrier/interface.json').read_text())
P={'XMin':-17.5,'XMax':34.2,'YMin':-16.8,'YMax':42.1,'Floor':1.2,'Wall':1.4,
   'BaseTop':11.5,'ShelfTop':12.9,'RoofBottom':20.4,'Height':21.8,'StepY':-2.0,
   'BayX':1.0,'BayY':-14.5,'BayWidth':23.0,'BayLength':34.0,'BayHeight':8.0,
   'Barrier':1.2,'CarrierX':-9.3,'CarrierZ':1.5,'MainBottom':12.4,
   'SeatRadius':1.6,'HolePilot':0.85,'MainClampTop':13.4,'LipGap':0.2}
D=A.newDocument('sMove_R2_Enclosure'); D.Label='sMove R2 / vertical carrier / engineering fit prototype'
S=D.addObject('Spreadsheet::Sheet','Parameters')
for i,(k,v) in enumerate(P.items(),1):
    S.set(f'A{i}',k); S.set(f'B{i}',f'={v} mm'); S.setAlias(f'B{i}',k)
S.setColumnWidth('A',180); S.setColumnWidth('B',110)

def expr(v): return v if isinstance(v,str) else f'{v:.9g} mm'
def box(name,x,y,z,dx,dy,dz):
    o=D.addObject('Part::Box',name)
    for prop,v in zip(('Length','Width','Height','Placement.Base.x','Placement.Base.y','Placement.Base.z'),(dx,dy,dz,x,y,z)): o.setExpression(prop,expr(v))
    return o

def cyl(name,x,y,z,r,h,direction=None):
    o=D.addObject('Part::Cylinder',name)
    for prop,v in zip(('Radius','Height','Placement.Base.x','Placement.Base.y','Placement.Base.z'),(r,h,x,y,z)):o.setExpression(prop,expr(v))
    if direction:o.Placement.Rotation=A.Rotation(A.Vector(0,0,1),A.Vector(*direction))
    return o

def fuse(name,obs):
    o=D.addObject('Part::MultiFuse',name);o.Shapes=obs;o.Refine=True;return o

def cut(name,b,t):
    o=D.addObject('Part::Cut',name);o.Base=b;o.Tool=t;o.Refine=True;return o

def polygon(name,points,z,h):
    s=D.addObject('Sketcher::SketchObject',name+'Profile');s.Placement.Base.z=z
    for p,q in zip(points,points[1:]+points[:1]):
        i=s.addGeometry(Part.LineSegment(A.Vector(*p,0),A.Vector(*q,0)),False)
        s.addConstraint(Sketcher.Constraint('Block',i))
    o=D.addObject('Part::Extrusion',name);o.Base=s;o.Dir=A.Vector(0,0,1);o.LengthFwd=h;o.Solid=True
    return o

def role(o,r,label=None):
    o.addProperty('App::PropertyString','Role');o.Role=r
    if label:o.Label=label
    return o

def rb(name,x,y,z,dx,dy,dz,r='clearance'):
    return role(box(name,x,y,z,dx,dy,dz),r,'CONSERVATIVE / '+name)

def cb(name,lo,hi,r='clearance'):
    return rb(name,f'Parameters.CarrierX-({hi[2]} mm)',lo[1],f'Parameters.CarrierZ+({lo[0]} mm)',hi[2]-lo[2],hi[1]-lo[1],hi[0]-lo[0],r)

# Carrier local +X -> enclosure +Z; +Y -> +Y; +Z -> -X. Proper rotation.
CF=A.Placement(A.Vector(P['CarrierX'],0,P['CarrierZ']), A.Rotation(A.Vector(0,1,0),-90))
outer=box('BaseBlank','Parameters.XMin','Parameters.YMin',0,'Parameters.XMax-Parameters.XMin','Parameters.YMax-Parameters.YMin','Parameters.BaseTop')
inner=box('BaseCavity','Parameters.XMin+Parameters.Wall','Parameters.YMin+Parameters.Wall','Parameters.Floor','Parameters.XMax-Parameters.XMin-2*Parameters.Wall','Parameters.YMax-Parameters.YMin-2*Parameters.Wall','Parameters.BaseTop+1 mm')
shell=cut('BaseOpenShell',outer,inner)
shell=cut('FrontBatteryEntry',shell,box('BatteryFrontOpening',1,-18,1.2,23,4,11))
shell=cut('WestServiceOpening',shell,box('WestSideOpening',-18,-15.4,1.4,2.1,56.1,12))
baseparts=[shell]
barrier=box('IntegralBatteryBarrier',0,-14.5,'Parameters.Floor+Parameters.BayHeight',25,35.1,'Parameters.Barrier');baseparts.append(barrier)
baseparts += [box('BayWestWall',0,-15.4,1.2,1,36,8),box('BayEastWall',24,-15.4,1.2,1,36,8),box('BayNorthStop',0,19.5,1.2,25,1.1,8)]
leadexit=box('PackLeadSideExit',23.8,-10,4.2,1.5,4,4)
# Rigid peripheral supports; only annuli touch. Nylon M2 shanks locate round+slot.
baseparts.append(box('CarrierRigidSpine',-6.5,16,1.2,1.6,3,17.4))
for i,z in enumerate((4.0,17.0),1):baseparts.append(cyl('CarrierSeat'+str(i),-8.3,17.5,z,'Parameters.SeatRadius',3.4,(1,0,0)))
key=polygon('CarrierChamferKey',[[-.3,20.3],[-.3,18.45],[1.55,20.3]],-2.8,3.0);key.Placement=CF;baseparts.append(key)
# Two reserved main lands only: bearing capsules have rounded lateral edges, no clips over copper.
for side,x in [('West',-1.5),('East',25)]:baseparts.append(box('Main'+side+'Tower',x,29.25,1.2,1.5,1.3,11.2))
for side,x in [('West',.5),('East',24.5)]:
    bearing=fuse('Main'+side+'RoundedLedge',[cyl(side+'LedgeA',x,29.55,11.4,.35,1),cyl(side+'LedgeB',x,30.15,11.4,.35,1),box(side+'LedgeWeb',x-.35,29.55,11.4,.7,.6,1),box(side+'LedgeArm',-0.15 if side=='West' else 24.5,29.55,11.4,.65,.6,1)])
    baseparts.append(bearing)
fasteners=[(-5,-11,12.9),(30,-11,12.9),(-5,31.5,21.8),(30,31.5,21.8)]
for i,(x,y,top) in enumerate(fasteners,1):baseparts.append(cyl(f'ClosureBoss{i}',x,y,1.2,2.5,top-6.5))
baseparts += [cyl('PackCleat1',28.7,-7,1.2,1.5,7.6),cyl('PackCleat2',27.5,-.8,1.2,1.5,7.6)]
base=fuse('BaseStructuralUnion',baseparts)
basecuts=[leadexit,box('EastRegisterPocket',31.8,23.8,9.3,1.4,10.4,3),box('NorthRegisterPocket',-1.2,39.8,9.3,25.4,1.3,3)]
for i,(x,y,top) in enumerate(fasteners,1):basecuts.append(cyl(f'ClosurePilot{i}',x,y,top-10,.85,5))
for i,z in enumerate((4.,17.),1):basecuts.append(cyl(f'CarrierBlindPilot{i}',-8.4,17.5,z,.85,3.2,(1,0,0)))
base=cut('Base',base,fuse('BaseDrillsAndLeadExit',basecuts));role(base,'print','BASE / barrier + rigid vertical carrier spine + main lands')
# Lid west wall comes away to expose horizontal carrier fasteners. Stepped east front exposes USB.
upperblank=box('UpperLidBlank','Parameters.XMin','Parameters.YMin','Parameters.BaseTop','Parameters.XMax-Parameters.XMin','Parameters.YMax-Parameters.YMin','Parameters.Height-Parameters.BaseTop')
uppervoid=box('UpperLidVoid',-16.1,-15.4,11.0,48.9,56.1,9.4)
upper=cut('UpperCap',upperblank,uppervoid)
upper=cut('USBFrontRecess',upper,box('FrontRoofNotch',-8,-18,12.9,44,16,11))
lidparts=[upper,box('LowFrontShelf',-8,-16.8,11.5,42.2,15.0,1.4),box('FrontRiser',-8,-2,12.9,42.2,1.4,8.9),
          box('RemovableWestSkirt',-17.5,-15.2,1.6,1.4,55.6,10.1),
          box('FrontClosureTongue',1.2,-16.8,1.4,22.6,1.4,10.1),box('BatteryFrontStop',1.2,-15.4,1.4,22.6,.9,7.5),
          box('EastLidRegister',32.0,24,9.5,1.0,4,2.2),box('NorthLidRegisterWest',-1,40.0,9.5,5,.9,2.2),box('NorthLidRegisterEast',21,40.0,9.5,3,.9,2.2)]
for side,x in [('West',.5),('East',24.5)]:
    lidparts.append(fuse('Main'+side+'UpperBearing',[cyl(side+'UpperA',x,29.55,'Parameters.MainClampTop',.35,7),cyl(side+'UpperB',x,30.15,'Parameters.MainClampTop',.35,7),box(side+'UpperWeb',x-.35,29.55,'Parameters.MainClampTop',.7,.6,7.1)]))
for i,(x,y,top) in enumerate(fasteners,1):lidparts.append(cyl(f'LidClosureSleeve{i}',x,y,top-5.3,2.5,5.3))
lidparts += [box('PackKeeper1',25.2,-5.4,8.2,7.3,.8,3.5),box('PackKeeper2',30.8,2.0,8.2,1.6,.8,12.3)]
lid=fuse('LidStructuralUnion',lidparts)
lidcuts=[box('USBOpening',14.58,-17,11.0,10.6,18,6.8)]
for ref,r in [('SW2',1.5),('SW3',1.5),('D1',1.3)]:
    x,y=MAIN['anchors'][ref]['center_native_xy_mm'];lidcuts.append(cyl(ref+'Access',x-100,135-y,15.7,r,8))
for i,(x,y,top) in enumerate(fasteners,1):lidcuts += [cyl(f'LidScrewClearance{i}',x,y,top-6,1.1,7),cyl(f'LidHeadRecess{i}',x,y,top-1.6,2.05,2.6)]
lid=cut('Lid',lid,fuse('LidOpenings',lidcuts));role(lid,'print','LID / removable west skirt + USB recess + bearing pairs')
refs=[];clearances=[];hardware=[]
for name,b in DATA['boards'].items():
    carrier=name=='imu-carrier';short='Carrier' if carrier else 'Main';z=-1 if carrier else P['MainBottom']
    pcb=polygon(short+'Substrate',b['outline_xy'],z,1)
    drills=[]
    for ref,f in b['footprints'].items():
        for j,p in enumerate(f['pads']):
            dx,dy=p['drill_mm'];x,y=p['local_xy']
            if dx>0 and dy>0:
                if abs(dx-dy)<1e-5:drills.append(cyl(f'{short}_{ref}_Hole{j}',x,y,z-.1,dx/2,1.2))
                elif ref=='H2':drills.append(fuse('CarrierSlotCutter',[cyl('SlotEnd1',x-.25,y,z-.1,1.1,1.2),cyl('SlotEnd2',x+.25,y,z-.1,1.1,1.2),box('SlotMiddle',x-.25,y-1.1,z-.1,.5,2.2,1.2)]))
                else:drills.append(box(f'{short}_{ref}_Slot{j}',x-dx/2,y-dy/2,z-.1,dx,dy,1.2))
    if drills:pcb=cut(short+'PCB',pcb,fuse(short+'PCBDrills',drills))
    if carrier:pcb.Placement=CF
    refs.append(role(pcb,short.lower()+'_pcb',short+' PCB / actual outline and drills / substrate'))
    for ref,f in b['footprints'].items():
        if not f.get('fitted'):continue
        x0,y0,x1,y1=f['envelope_xy'];z0,z1=f['z_mm']
        if carrier:o=cb(short+'_'+ref,[x0,y0,z0],[x1,y1,z1],short.lower()+'_component')
        else:o=rb(short+'_'+ref,x0,y0,f'Parameters.MainBottom+({z0} mm)',x1-x0,y1-y0,z1-z0,short.lower()+'_component')
        mpn=(MAIN['components'][ref]['mpn'] if not carrier else next(c['mpn'] for c in CARRIER['components'] if c['ref']==ref))
        o.Label=short+' '+ref+' '+mpn+' / conservative contract envelope';refs.append(o)
refs.append(rb('Main_USB_ShellTails',15.18,-.9,11.2,9.4,7.55,1.2,'tail'))
battery=rb('ProtectedPack_ACCEPTANCE_ONLY',2,-13.5,1.95,21,32,6.5,'battery');refs.append(battery)
clearances.append(rb('BatteryBay_23x34x8',1,-14.5,1.2,23,34,8))
ant=MAIN['antenna_3d'];pts=ant['clear_air_volume_native_xy_mm'];xs=[p[0]-100 for p in pts];ys=[135-p[1] for p in pts];zs=ant['clear_air_z_mm']
clearances.append(rb('RF_NO_BATTERY_HARNESS_CARRIER_METAL',min(xs),min(ys),P['MainBottom']+zs[0],max(xs)-min(xs),max(ys)-min(ys),zs[1]-zs[0],'rf_keepout'))
for ref in ('J1','J2','J4'):
    a=MAIN['anchors'][ref];pts=a['cavity_polygon_native_xy_mm'];xs=[p[0]-100 for p in pts];ys=[135-p[1] for p in pts];z0,z1=a['cavity_z_mm_from_board_bottom']
    clearances.append(rb('Main_'+ref+'_MatingInsertion',min(xs),min(ys),P['MainBottom']+z0,max(xs)-min(xs),max(ys)-min(ys),z1-z0))
for key in ('aabb_mm','wire_strain_relief_aabb_mm'):clearances.append(cb('Carrier_'+key,*CARRIER['plug_cavity'][key]))
clearances.append(cb('Carrier_NoSupport',*CARRIER['support']['no_support_aabb_mm'],'no_support'))
# Broad swept conservative corridors. Rounded routing lies inside each tubular elbow;
# corner sphere is not a claim of measured minimum wire bend radius.
def route(name,points,r):
    parts=[]
    for i,(p,q) in enumerate(zip(points,points[1:])):
        v=A.Vector(*q)-A.Vector(*p);parts.append(cyl(name+'Segment'+str(i),*p,r,v.Length,list(v)))
    for i,p in enumerate(points[1:-1]):
        o=D.addObject('Part::Sphere',name+'Corner'+str(i));o.Radius=r;o.Placement.Base=A.Vector(*p);parts.append(o)
    return role(fuse(name,parts),'harness',name+' / conservative corridor, not measured wire')
ph4points=[[.5,9,16.4],[-5.8,9,16.4],[-5.8,0,10.1],[-8,-7,10.1],[-12.3,-11.5,10.5],[-12.3,.5,10.5]]
refs.append(route('PH4_1to1_LE50mm',ph4points,.9))
packpoints=[[23,-8,6],[26,-8,6],[26,-4.5,6],[31,-4.5,6],[31,4,6],[29,7,9],[29,18.5,16.4],[24.5,18.5,16.4]]
refs.append(route('PH2_PairedProtectedPackLeads',packpoints,.9))
for i,(x,y,top) in enumerate(fasteners,1):
    o=fuse(f'NylonClosureScrew{i}',[cyl(f'ScrewShank{i}',x,y,top-9.5,1,8),cyl(f'ScrewHead{i}',x,y,top-1.5,1.9,1.5)])
    hardware.append(role(o,'nylon','NYLON ONLY M2x8 / envelope; threads intentionally engage pilot'))
for i,z in enumerate((4.,17.),1):
    o=fuse(f'NylonCarrierScrew{i}',[cyl(f'CarrierShank{i}',-9.3,17.5,z,1,4,(1,0,0)),cyl(f'CarrierHead{i}',-10.6,17.5,z,1.6,1.3,(1,0,0))])
    hardware.append(role(o,'nylon','NYLON ONLY M2x4 / head OD <=3.2 / round+slot locator'))
D.recompute()
for o in (base,lid):assert not o.Shape.isNull() and o.Shape.isValid() and len(o.Shape.Solids)==1,(o.Name,'invalid/disconnected',len(o.Shape.Solids))
meta=D.addObject('App::DocumentObjectGroup','Provenance')
meta.addProperty('App::PropertyString','InputHashes').InputHashes=json.dumps({n:{k:v for k,v in b.items() if k.endswith('sha256')} for n,b in DATA['boards'].items()},sort_keys=True)
meta.addProperty('App::PropertyString','Status').Status='ENGINEERING FIT PROTOTYPE; no physical fit, pack/harness, RF or magnetic test claim. Source HOLD text superseded by explicit user resume.'
meta.addProperty('App::PropertyString','Frames').Frames='Column vectors. Main: I,t=(0,0,12.4). Carrier: R=[[0,0,-1],[0,1,0],[1,0,0]],t=(-9.3,0,1.5). Accel/gyro use R; mag R*diag(1,-1,-1).'
EX.mkdir(parents=True,exist_ok=True)
D.recompute();D.saveAs(str(OUT/'smove-r2-enclosure.FCStd'))
Part.export([base,lid]+refs+hardware,str(EX/'smove-r2-assembly.step'))
Part.export([base,lid],str(EX/'smove-r2-printable.step'))
for stepname in ['smove-r2-assembly.step','smove-r2-printable.step']:
    sf=EX/stepname;st=sf.read_text();sf.write_text(st.replace('DATA;', '/* R2 FINAL INPUT HASHES '+meta.InputHashes+' */\nDATA;',1))
mesh_reports={}
for name,obj in [('base',base),('lid',lid)]:
    sh=obj.Shape.copy()
    if name=='lid':sh.rotate(A.Vector(),A.Vector(1,0,0),180)
    bb=sh.BoundBox;sh.translate(A.Vector(-bb.XMin,-bb.YMin,-bb.ZMin))
    mesh=MeshPart.meshFromShape(Shape=sh,LinearDeflection=.04,AngularDeflection=.12,Relative=False);mesh.write(str(EX/f'{name}.stl'))
    mesh_reports[name]={'object':obj.Name,'volume_mm3':obj.Shape.Volume,'triangles':mesh.CountFacets,'print_orientation':'floor down' if name=='base' else 'roof down, rotated180X'}
report={'status':'GENERATED_REQUIRE_INDEPENDENT_VERIFY','parameters_mm':P,'size_mm':[51.7,58.9,21.8],
        'outside_bounds_mm':[[-17.5,-16.8,0],[34.2,42.1,21.8]],'parts':mesh_reports,
        'reference_objects':[o.Name for o in refs],'hardware_objects':[o.Name for o in hardware],'clearance_objects':[o.Name for o in clearances],
        'main_transform':[[1,0,0,0],[0,1,0,0],[0,0,1,12.4],[0,0,0,1]],
        'carrier_transform':[[0,0,-1,-9.3],[0,1,0,0],[1,0,0,1.5],[0,0,0,1]],'sensor_axes':CARRIER['axes'],
        'ph4_centerline_mm':sum((A.Vector(*q)-A.Vector(*p)).Length for p,q in zip(ph4points,ph4points[1:])),
        'ph4_route_points_mm':ph4points,'pack_route_points_mm':packpoints,'input_warnings':DATA['warnings']}
(ROOT/'.cache/housing/build.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'result':'NATIVE ARTIFACTS CREATED','size_mm':report['size_mm'],'ph4_centerline_mm':report['ph4_centerline_mm'],'parts':mesh_reports},indent=2))
