"""Coplanar, outward-facing R2 assembly: simple open tray + flat lid.
Run extract.py first, then pinned run.py housing/entry.py generate.
The PCBs are canonical; component/pack/plug envelopes are conservative, not fit proof.
"""
import hashlib
import json
import math
from pathlib import Path
import FreeCAD as A
import Part
import Sketcher
import MeshPart
ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'housing'; EX = OUT/'dist'; EX.mkdir(parents=True, exist_ok=True)
CACHE = ROOT/'.cache/housing'; CACHE.mkdir(parents=True, exist_ok=True)
assert json.loads((OUT/'status.json').read_text())['allow_generate_or_export']
DATA = json.loads((CACHE/'input-geometry.json').read_text())
MAIN = json.loads((ROOT/'PCB/main/interface.json').read_text())
CARRIER = json.loads((ROOT/'PCB/imu-carrier/interface.json').read_text())
P = dict(XMin=-38., XMax=71., YMin=-5., YMax=43., Floor=1.6, Wall=2.,
         RoofBottom=12.5, Roof=2., MainBottom=4., CarrierX=-27.5, CarrierY=16., CarrierTop=5.,
         BayX=36., BayY=-1., BayWidth=23., BayLength=34., BayHeight=8.,
         SeatRadius=1.6, LocatorRadius=.9, NutTop=10.5, NutSlotBottom=7.7,
         BoreBottom=5.8, BossRadius=5., ScrewLength=8., ScrewHeadRadius=2.84, ScrewHeadHeight=3.)
D = A.newDocument('sMove_R2_Enclosure'); D.Label = 'sMove R2 | COPLANAR | base toward BODY'
S = D.addObject('Spreadsheet::Sheet','Parameters')
for i,(k,v) in enumerate(P.items(),1):
    S.set(f'A{i}',k); S.set(f'B{i}',f'={v} mm'); S.setAlias(f'B{i}',k)
S.setColumnWidth('A',180); S.setColumnWidth('B',110)

def expr(v): return v if isinstance(v,str) else f'{v:.9g} mm'
def box(name,x,y,z,dx,dy,dz):
    o=D.addObject('Part::Box',name)
    for prop,v in zip(('Length','Width','Height','Placement.Base.x','Placement.Base.y','Placement.Base.z'),(dx,dy,dz,x,y,z)):
        o.setExpression(prop,expr(v))
    return o

def cyl(name,x,y,z,r,h):
    o=D.addObject('Part::Cylinder',name)
    for prop,v in zip(('Radius','Height','Placement.Base.x','Placement.Base.y','Placement.Base.z'),(r,h,x,y,z)):
        o.setExpression(prop,expr(v))
    return o

def fuse(name,obs):
    o=D.addObject('Part::MultiFuse',name); o.Shapes=obs; o.Refine=True; return o

def cut(name,b,t):
    o=D.addObject('Part::Cut',name); o.Base=b; o.Tool=t; o.Refine=True; return o

def polygon(name,points,z,h):
    s=D.addObject('Sketcher::SketchObject',name+'Profile'); s.Placement.Base.z=z
    for p,q in zip(points,points[1:]+points[:1]):
        i=s.addGeometry(Part.LineSegment(A.Vector(*p,0),A.Vector(*q,0)),False)
        s.addConstraint(Sketcher.Constraint('Block',i))
    o=D.addObject('Part::Extrusion',name); o.Base=s; o.Dir=A.Vector(0,0,1); o.LengthFwd=h; o.Solid=True
    return o

def hexagon(name,x,y,z,af,h):
    r=af/math.sqrt(3)
    return polygon(name,[[x+r*math.cos(i*math.pi/3+math.pi/6),y+r*math.sin(i*math.pi/3+math.pi/6)] for i in range(6)],z,h)

def role(o,r,label=None):
    o.addProperty('App::PropertyString','Role'); o.Role=r
    if label:o.Label=label
    return o

def rb(name,x,y,z,dx,dy,dz,r='clearance'):
    return role(box(name,x,y,z,dx,dy,dz),r,'CONSERVATIVE / '+name)

def cb(name,lo,hi,r='clearance'):
    return rb(name,P['CarrierX']+lo[0],P['CarrierY']+lo[1],P['CarrierTop']+lo[2],
              hi[0]-lo[0],hi[1]-lo[1],hi[2]-lo[2],r)

# Both substrates occupy Z=4..5. All component faces and accel/gyro +Z face outward.
CF=A.Placement(A.Vector(P['CarrierX'],P['CarrierY'],P['CarrierTop']),A.Rotation())
outer=box('BaseBlank','Parameters.XMin','Parameters.YMin',0,'Parameters.XMax-Parameters.XMin',
          'Parameters.YMax-Parameters.YMin','Parameters.RoofBottom')
inner=box('BaseCavity','Parameters.XMin+Parameters.Wall','Parameters.YMin+Parameters.Wall','Parameters.Floor',
          'Parameters.XMax-Parameters.XMin-2*Parameters.Wall','Parameters.YMax-Parameters.YMin-2*Parameters.Wall',15)
baseparts=[cut('OpenTray',outer,inner)]
lidparts=[box('LidBlank','Parameters.XMin','Parameters.YMin','Parameters.RoofBottom',
              'Parameters.XMax-Parameters.XMin','Parameters.YMax-Parameters.YMin','Parameters.Roof')]
basecuts=[]; lidcuts=[]
# NO printed threads. Side-loaded standard M3 hex nuts, supported by 2mm boss roofs.
fasteners=[(-33.,1.),(-33.,30.),(66.,1.),(66.,30.)]
for i,(x,y) in enumerate(fasteners,1):
    baseparts.append(cyl(f'ClosureBoss{i}',x,y,'Parameters.Floor','Parameters.BossRadius','Parameters.RoofBottom-Parameters.Floor'))
    pocket=hexagon(f'NutPocket{i}',x,y,P['NutSlotBottom'],6.,P['NutTop']-P['NutSlotBottom'])
    slot=box(f'NutEntry{i}',x-3.,y if y<10 else y-5.5,P['NutSlotBottom'],6.,5.5,P['NutTop']-P['NutSlotBottom'])
    basecuts += [pocket,slot,cyl(f'ClosureBore{i}',x,y,'Parameters.BoreBottom',1.7,8.)]
    lidcuts.append(cyl(f'LidClearance{i}',x,y,12.4,1.7,2.2))
# Top-entry battery bay adjacent to electronics: no overhead bridge or pouch beneath solder.
baseparts += [box('BayWestWall',34.4,-2.6,1.6,1.6,37.2,8),box('BayEastWall',59,-2.6,1.6,1.6,37.2,8),
              box('BaySouthWall',36,-2.6,1.6,23,1.6,8),box('BayNorthWall',36,33,1.6,23,1.6,8)]
basecuts.append(box('PackLeadExit',34.3,4.2,6.5,1.8,3.6,3.2))
# Roof keepers stop at the acceptance bay ceiling, NEVER preload the accepted pouch.
for y in (0.,30.):lidparts.append(box('PackKeeper'+str(int(y)),38,y,9.6,19,2,3.0))
# Main supports only the pre-existing verified all-layer copper-free lands.
for side,x in [('West',.5),('East',24.5)]:
    baseparts.append(box('Main'+side+'Tower',-1.5 if side=='West' else 25.,29.3,1.6,1.5,1.2,2.4))
    for top,z,h in [(False,3.,1.),(True,5.,7.6)]:
        n='Main'+side+('UpperBearing' if top else 'LowerBearing')
        b=fuse(n,[cyl(n+'A',x,29.7,z,.35,h),cyl(n+'B',x,30.1,z,.35,h),box(n+'Web',x-.35,29.7,z,.7,.4,h)])
        (lidparts if top else baseparts).append(b)
    baseparts.append(box('Main'+side+'Arm',-.15 if side=='West' else 24.5,29.7,3.,.65,.4,1.))
    baseparts.append(box('Main'+side+'SideStop',-1.5 if side=='West' else 25.15,29.3,1.6,1.35,1.2,4.))
for y in (-.85,35.15):baseparts.append(box('MainEndStop'+str(y).replace('.','_').replace('-','M'),.1,y,1.6,1.,.7,4.))
# Carrier: annular seats + small plastic round/slot locators, held by lid annuli.
# No M3 through the existing 2.2mm holes; no stress support under U2.
for i,x0 in enumerate((2.5,15.5),1):
    x=P['CarrierX']+x0; y=P['CarrierY']+17.5
    baseparts += [cyl(f'CarrierSeat{i}',x,y,1.6,1.6,2.4),cyl(f'CarrierLocator{i}',x,y,4.,.9,1.6)]
    lidparts.append(cyl(f'CarrierUpperBearing{i}',x,y,5.,1.6,7.6))
    lidcuts.append(cyl(f'CarrierLocatorRelief{i}',x,y,4.9,1.2,1.1))
key=polygon('CarrierChamferKey',[[-.3,20.3],[-.3,18.45],[1.55,20.3]],-3.4,3.6)
key.Placement=CF; baseparts.append(key)
# Easy vertical lid alignment, with 0.25mm nominal wall clearance.
for i,(x,y,dx,dy) in enumerate([(-35.75,12.,1.6,4.),(66.8,13.,1.6,4.),(4.,38.8,3.,1.95)]):
    lidparts.append(box('LidRegister'+str(i),x,y,10.5,dx,dy,2.1))
# Open-topped USB notch in the tray permits true top-down main-board insertion.
basecuts.append(box('USBNotch',14.38,-5.1,4.5,11.,6.2,8.1))
# Lid locally closes only the excess height above the USB insertion envelope.
lidparts.append(box('USBUpperClosure',14.63,-5.,9.1,10.5,1.8,3.5))
for ref,r in [('SW2',1.7),('SW3',1.7),('D1',3.)]:
    x,y=MAIN['anchors'][ref]['center_native_xy_mm']
    lidcuts.append(cyl(ref+'Access',x-100,135-y,7.,r,9.))
base=role(cut('Base',fuse('BaseStructure',baseparts),fuse('BaseOpenings',basecuts)),'print','BASE | flat underside = BODY CONTACT')
lid=role(cut('Lid',fuse('LidStructure',lidparts),fuse('LidOpenings',lidcuts)),'print','LID | TOP / OUTWARD | RGB + RESET + BOOT')
refs=[]; clearances=[]; hardware=[]
for name,b in DATA['boards'].items():
    carrier=name=='imu-carrier'; short='Carrier' if carrier else 'Main'; z=-1 if carrier else P['MainBottom']
    pcb=polygon(short+'Substrate',b['outline_xy'],z,b['thickness_mm']); drills=[]
    for ref,f in b['footprints'].items():
        for j,p in enumerate(f['pads']):
            dx,dy=p['drill_mm']; x,y=p['local_xy']
            if dx>0 and dy>0:
                if abs(dx-dy)<1e-5:drills.append(cyl(f'{short}_{ref}_Hole{j}',x,y,z-.1,dx/2,1.2))
                elif ref=='H2':drills.append(fuse('CarrierSlotCutter',[cyl('SlotEnd1',x-.25,y,z-.1,1.1,1.2),cyl('SlotEnd2',x+.25,y,z-.1,1.1,1.2),box('SlotMiddle',x-.25,y-1.1,z-.1,.5,2.2,1.2)]))
                else:drills.append(box(f'{short}_{ref}_Slot{j}',x-dx/2,y-dy/2,z-.1,dx,dy,1.2))
    pcb=cut(short+'PCB',pcb,fuse(short+'PCBDrills',drills))
    if carrier:pcb.Placement=CF
    refs.append(role(pcb,short.lower()+'_pcb',short+' PCB | actual outline/drills | TOP OUTWARD'))
    for ref,f in b['footprints'].items():
        if not f.get('fitted'):continue
        x0,y0,x1,y1=f['envelope_xy']; z0,z1=f['z_mm']
        if carrier:o=cb(short+'_'+ref,[x0,y0,z0],[x1,y1,z1],short.lower()+'_component')
        else:o=rb(short+'_'+ref,x0,y0,P['MainBottom']+z0,x1-x0,y1-y0,z1-z0,short.lower()+'_component')
        mpn=MAIN['components'][ref]['mpn'] if not carrier else next(c['mpn'] for c in CARRIER['components'] if c['ref']==ref)
        o.Label=short+' '+ref+' '+mpn+' | envelope'; refs.append(o)
refs.append(rb('Main_USB_ShellTails',15.18,-.9,2.8,9.4,7.55,1.2,'tail'))
refs.append(rb('ProtectedPack_ACCEPTANCE_ONLY',37.,0.,2.35,21.,32.,6.5,'battery'))
clearances.append(rb('BatteryBay_23x34x8',36.,-1.,1.6,23.,34.,8.))
ant=MAIN['antenna_3d']; pts=ant['clear_air_volume_native_xy_mm']; xs=[p[0]-100 for p in pts]; ys=[135-p[1] for p in pts]; zs=ant['clear_air_z_mm']
clearances.append(rb('RF_NO_BATTERY_HARNESS_CARRIER_METAL',min(xs),min(ys),P['MainBottom']+zs[0],max(xs)-min(xs),max(ys)-min(ys),zs[1]-zs[0],'rf_keepout'))
for ref in ('J1','J2','J4'):
    a=MAIN['anchors'][ref]; pts=a['cavity_polygon_native_xy_mm']; xs=[p[0]-100 for p in pts]; ys=[135-p[1] for p in pts]; z0,z1=a['cavity_z_mm_from_board_bottom']
    clearances.append(rb('Main_'+ref+'_MatingInsertion',min(xs),min(ys),P['MainBottom']+z0,max(xs)-min(xs),max(ys)-min(ys),z1-z0))
for key in ('aabb_mm','wire_strain_relief_aabb_mm'):clearances.append(cb('Carrier_'+key,*CARRIER['plug_cavity'][key]))
clearances.append(cb('Carrier_NoSupport',*CARRIER['support']['no_support_aabb_mm'],'no_support'))

def rounded_route(name,points,bend,r):
    """True tangent line/arc centerline, not sharp elbows or a claimed cable bend spec."""
    vs=[A.Vector(*p) for p in points]; edges=[]; current=vs[0]
    for a,b,c in zip(vs,vs[1:],vs[2:]):
        u=b-a; u.normalize(); v=c-b; v.normalize(); theta=math.acos(max(-1,min(1,u.dot(v))))
        setback=bend*math.tan(theta/2); assert (b-a).Length>=setback and (c-b).Length>=setback
        start=b-u*setback; end=b+v*setback
        if (start-current).Length>1e-7:edges.append(Part.makeLine(current,start))
        bisector=v-u; bisector.normalize(); center=b+bisector*(bend/math.cos(theta/2))
        mid=(start-center)+(end-center); mid.normalize(); mid=center+mid*bend
        edges.append(Part.Arc(start,mid,end).toShape()); current=end
    edges.append(Part.makeLine(current,vs[-1])); path=Part.Wire(edges)
    circle=Part.Wire([Part.makeCircle(r,vs[0],vs[1]-vs[0])])
    o=D.addObject('Part::Feature',name); o.Shape=path.makePipeShell([circle],True,False)
    o.addProperty('App::PropertyVectorList','RoutePoints');o.RoutePoints=vs
    o.addProperty('App::PropertyLength','BendRadius');o.BendRadius=bend
    o.addProperty('App::PropertyLength','EnvelopeRadius');o.EnvelopeRadius=r
    return role(o,'harness',name+' | swept reserve, measure real harness'),path.Length

ph4points=[[.5,9.,8.],[-10.,9.,8.],[-10.,3.,8.],[-18.5,3.,8.],[-18.5,16.5,8.]]
# Nonoverlapping tangent arcs on the 6mm segment meet exactly at R=3.
ph4,length=rounded_route('PH4_1to1_LE50mm',ph4points,3.,.9); refs.append(ph4)
packpoints=[[37.,6.,8.],[29.,6.,8.],[29.,18.5,8.],[24.5,18.5,8.]]
ph2,packlength=rounded_route('PH2_PairedProtectedPackLeads',packpoints,3.,.9); refs.append(ph2)
for i,(x,y) in enumerate(fasteners,1):
    screw=fuse(f'ClosureScrew{i}',[cyl(f'ScrewShank{i}',x,y,6.5,1.5,8.),cyl(f'ScrewHead{i}',x,y,14.5,2.84,3.)])
    hardware.append(role(screw,'hardware','M3x8 socket cap | assumed head <=5.68 x 3mm'))
    nut=cut(f'ClosureNut{i}',hexagon(f'NutBlank{i}',x,y,8.1,5.5,2.4),cyl(f'NutHole{i}',x,y,8.,1.5,2.6))
    hardware.append(role(nut,'hardware','M3 hex nut | AF5.5 x 2.4 | side loaded'))
D.recompute()
for o in (base,lid):assert o.Shape.isValid() and len(o.Shape.Solids)==1,(o.Name,len(o.Shape.Solids))
meta=D.addObject('App::DocumentObjectGroup','Provenance')
meta.addProperty('App::PropertyString','InputHashes').InputHashes=json.dumps({n:{k:v for k,v in b.items() if k.endswith('sha256')} for n,b in DATA['boards'].items()},sort_keys=True)
meta.addProperty('App::PropertyString','Frames').Frames='Body=case: Z outward, Y main antenna, X right. Main bottom=(0,0,4), carrier top=(-27.5,16,5); both R=I. accel/gyro=I, magnetometer=diag(1,-1,-1).'
meta.addProperty('App::PropertyString','Status').Status='ENGINEERING PROTOTYPE ONLY; no physical fit, magnetic, RF, thermal, skin or charge approval.'
# Separate native movable display groups. Links reference fixed engineering CSG;
# inspection offsets cannot silently change the validated/exported source placements.
source=D.addObject('App::DocumentObjectGroup','EngineeringSources'); source.Label='ENGINEERING SOURCES | fixed assembled geometry'
existing=[o for o in D.Objects if o not in (source,S,meta)]
source.Group=existing
assembly=D.addObject('App::DocumentObjectGroup','InspectionAssembly'); assembly.Label='MOVE THESE | inspection assembly (default assembled)'
groups=[('ViewBase',[base],(0,0,0)),('ViewLid',[lid],(0,0,32)),
        ('ViewMain',[o for o in refs if o.Name.startswith('Main')],(0,0,12)),
        ('ViewCarrier',[o for o in refs if o.Name.startswith('Carrier')],(-12,0,12)),
        ('ViewBattery',[o for o in refs if o.Role=='battery'],(12,0,10)),
        ('ViewCables',[o for o in refs if o.Role=='harness'],(0,-16,8)),
        ('ViewHardware',hardware,(0,0,40))]
for name,objects,offset in groups:
    group=D.addObject('App::Part',name); assembly.addObject(group)
    group.Label=name[4:]+' | movable inspection group'
    group.addProperty('App::PropertyVector','ExplodedOffset','Inspection'); group.ExplodedOffset=A.Vector(*offset)
    for obj in objects:
        link=D.addObject('App::Link','Inspect_'+obj.Name); link.setLink(obj); link.LinkPlacement=obj.Placement; group.addObject(link); link.Label=obj.Label
D.recompute()
# Engineering outputs always use original objects, never moved inspection links.
Part.export([base,lid]+refs+hardware,str(EX/'smove-r2-assembly.step'))
Part.export([base,lid],str(EX/'smove-r2-printable.step'))
mesh_reports={}
for name,obj in [('base',base),('lid',lid)]:
    sh=obj.Shape.copy()
    if name=='lid':sh.rotate(A.Vector(),A.Vector(1,0,0),180)
    bb=sh.BoundBox; sh.translate(A.Vector(-bb.XMin,-bb.YMin,-bb.ZMin))
    mesh=MeshPart.meshFromShape(Shape=sh,LinearDeflection=.04,AngularDeflection=.12,Relative=False); mesh.write(str(EX/f'{name}.stl'))
    mesh_reports[name]=dict(object=obj.Name,volume_mm3=obj.Shape.Volume,triangles=mesh.CountFacets,print_orientation='floor down' if name=='base' else 'roof down')
D.saveAs(str(OUT/'smove-r2-enclosure.FCStd'))
report=dict(status='GENERATED_REQUIRE_INDEPENDENT_VERIFY',parameters_mm=P,size_mm=[109.,48.,14.5],height_with_screw_heads_mm=17.5,
            parts=mesh_reports,reference_objects=[o.Name for o in refs],hardware_objects=[o.Name for o in hardware],
            clearance_objects=[o.Name for o in clearances],inspection_groups=[g[0] for g in groups],fastener_xy_mm=fasteners,
            main_transform=[[1,0,0,0],[0,1,0,0],[0,0,1,4],[0,0,0,1]],
            carrier_transform=[[1,0,0,-27.5],[0,1,0,16],[0,0,1,5],[0,0,0,1]],
            body_frame=dict(contact_face='flat base underside Z=0; main BOTTOM toward body through floor',origin_mm=[0,0,0],
                            X='main local +X, native PCB +X',Y='toward main antenna, native PCB -Y; convenience, NOT anatomical up',Z='outward away from body'),
            ph4_centerline_mm=length,ph4_route_points_mm=ph4points,ph4_bend_radius_mm=3.,
            pack_route_points_mm=packpoints,input_warnings=DATA['warnings'],
            sources_sha256={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [Path(__file__),ROOT/'scripts/r2/enclosure/extract.py',ROOT/'PCB/main/interface.json',ROOT/'PCB/imu-carrier/interface.json']})
(CACHE/'build.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'result':'COPLANAR NATIVE ASSEMBLY CREATED','size_mm':report['size_mm'],'ph4_centerline_mm':length,'parts':mesh_reports},indent=2))
