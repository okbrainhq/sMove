"""Integrated main PCB compact stack, editable native base/lid + removable insulating divider.
Two diagonal M3 clamps; measure current export bounds and retain sample/battery qualification gates.
"""
import hashlib,json,math
from pathlib import Path
import FreeCAD as A
import Part,Sketcher,MeshPart
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'housing';EX=OUT/'dist';EX.mkdir(parents=True,exist_ok=True)
CACHE=ROOT/'.cache/housing';DATA=json.loads((CACHE/'input-geometry.json').read_text());MAIN=json.loads((ROOT/'PCB/main/interface.json').read_text())
assert set(DATA['boards'])=={'main'}
P=dict(XMin=-2.2,XMax=27.2,YMin=-3.2,YMax=46.6,Floor=1.6,Wall=1.8,MainBottom=10.8,
       RoofBottom=18.4,Roof=1.2,BarrierBottom=6.3,BarrierThickness=.8,ScrewUnderHead=15.4,ScrewLength=8.)
D=A.newDocument('sMove_Integrated');D.Label='sMove | integrated IMU | underside toward BODY'
S=D.addObject('Spreadsheet::Sheet','Parameters')
for i,(k,v) in enumerate(P.items(),1):S.set(f'A{i}',k);S.set(f'B{i}',f'={v} mm');S.setAlias(f'B{i}',k)
S.setColumnWidth('A',190);S.setColumnWidth('B',110)
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


outer=box('BaseBlank','Parameters.XMin','Parameters.YMin',0,'Parameters.XMax-Parameters.XMin','Parameters.YMax-Parameters.YMin','Parameters.RoofBottom')
inner=box('BaseCavity','Parameters.XMin+Parameters.Wall','Parameters.YMin+Parameters.Wall','Parameters.Floor','Parameters.XMax-Parameters.XMin-2*Parameters.Wall','Parameters.YMax-Parameters.YMin-2*Parameters.Wall',20)
baseparts=[cut('OpenTray',outer,inner)];lidparts=[box('LidBlank','Parameters.XMin','Parameters.YMin','Parameters.RoofBottom','Parameters.XMax-Parameters.XMin','Parameters.YMax-Parameters.YMin','Parameters.Roof')]
basecuts=[];lidcuts=[];fasteners=[[xy[0]-100,139-xy[1]] for xy in MAIN['mounting']['holes_native_xy_mm'].values()];lands=fasteners
# Raised nut shelves attach to the inner walls, above the rigid battery divider.
# Two corner M3 through-PCB clamps, no external ears and no load on the cell or U2.
for i,(x,y) in enumerate(fasteners,1):
 baseparts.append(cyl(f'BoltSafetyFloor{i}',x,y,6.4,2.05,1.))
 baseparts += [cyl(f'ClosureBoss{i}',x,y,7.4,4.1,2.8),cyl(f'LowerBearing{i}',x,y,10.2,3.4,.6)]
 basecuts += [hexagon(f'NutPocket{i}',x,y,7.6,5.8,2.4),box(f'NutEntry{i}',x if i==1 else x-6,y-3.3,7.6,6.,6.6,2.4),cyl(f'ClosureBore{i}',x,y,7.2,1.7,3.7)]
 lidparts.append(cyl(f'LidBearingBoss{i}',x,y,11.8,3.4,6.7))
 lidcuts += [cyl(f'LidBore{i}',x,y,11.7,1.7,8.),cyl(f'HeadRecess{i}',x,y,15.4,3.05,4.3)]
# Side registration reduces slip; mounting sleeves carry clamp load, not pouch.
for x in (-.4,25.15):
 for y in (10.,30.):baseparts.append(box('BoardRegister',x,y,7.4,.25,1.,4.0))
for x in (-.4,24.):
 for y in (10.,29.):baseparts.append(box('DividerSeat',x,y,1.6,1.4,1.,4.7))
divider_blank=box('DividerBlank',1.,1.,6.3,23.,35.,.8)
barrier=role(cut('BatteryDivider',divider_blank,fuse('DividerCornerReliefs',[cyl('DividerRelief',x,y,6.2,4.35,1.) for x,y in fasteners])),'divider','REMOVABLE rigid insulating battery divider | no preload')
# East USB shoulder near MCU. Connector shell/plug allowed through this aperture only.
basecuts.append(box('USBNotch',23.9,16.7,11.4,4.,11.,7.0))
for ref,r in [('SW2',1.7),('SW3',1.7),('D1',2.2)]:
 x,y=MAIN['anchors'][ref]['center_native_xy_mm'];lidcuts.append(cyl(ref+'Access',x-100,139-y,11.9,r,8.))
base=role(cut('Base',fuse('BaseStructure',baseparts),fuse('BaseOpenings',basecuts)),'print','BASE | flat underside BODY')
lid=role(cut('Lid',fuse('LidStructure',lidparts),fuse('LidOpenings',lidcuts)),'print','LID | TOP / OUTWARD | RGB RESET BOOT')
refs=[];clearances=[];hardware=[]
b=DATA['boards']['main'];pcb=polygon('MainSubstrate',b['outline_xy'],10.8,b['thickness_mm']);drills=[]
for ref,f in b['footprints'].items():
 for i,p in enumerate(f['pads']):
  dx,dy=p['drill_mm'];x,y=p['local_xy']
  if dx>0 and dy>0:
   if abs(dx-dy)<1e-5:drills.append(cyl(f'Main_{ref}_Hole{i}',x,y,10.7,dx/2,1.2))
   else:drills.append(box(f'Main_{ref}_Slot{i}',x-dx/2,y-dy/2,10.7,dx,dy,1.2))
pcb=cut('MainPCB',pcb,fuse('MainPCBDrills',drills));refs.append(role(pcb,'main_pcb','ONE integrated main PCB | 25 x 39 x 1mm | +Z outward'))
for ref,f in b['footprints'].items():
 if not f.get('fitted'):continue
 x0,y0,x1,y1=f['envelope_xy'];z0,z1=f['z_mm'];o=rb('Main_'+ref,x0,y0,10.8+z0,x1-x0,y1-y0,z1-z0,'main_component');o.Label=ref+' '+MAIN['components'][ref]['mpn']+' | conservative envelope';refs.append(o)
refs.append(rb('Main_USB_ShellTails',17.45,17.5,9.6,7.55,9.4,1.2,'tail'))
# Listed pouch body only. A separate generous acceptance envelope is the supplier/sample gate.
refs.append(rb('BatteryCandidate_UNQUALIFIED',2.5,4.,1.8,20.,30.,3.,'battery'))
clearances.append(rb('BatteryAcceptance_21x31x4_3',2.,3.5,1.8,21.,31.,4.3,'battery_reserve'))
clearances.append(rb('RF_NO_BATTERY_HARNESS_METAL',-7.4,39.,-4.2,43.2,20.4,33.4,'rf_keepout'))
for ref in ('J1','J2'):
 a=MAIN['anchors'][ref];pts=a['cavity_polygon_native_xy_mm'];xs=[x-100 for x,y in pts];ys=[139-y for x,y in pts];z0,z1=a['cavity_z_mm_from_board_bottom']
 clearances.append(rb('Main_'+ref+'_MatingInsertion',min(xs),min(ys),10.8+z0,max(xs)-min(xs),max(ys)-min(ys),z1-z0))
# No PH4 harness. Reserved PH2 lead descent stays outside the PCB/divider footprint.
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


# Reserved wire route: exits mate towards south, turns down in notch then enters the cell-end reserve.
packpoints=[[12.5,-.2,14.],[12.5,-.2,4.],[12.5,3.,4.]]
ph2,packlength=rounded_route('PH2_ProtectedPackLeads',packpoints,2.,.55);refs.append(ph2)
for i,(x,y) in enumerate(fasteners,1):
 screw=fuse(f'ClosureScrew{i}',[cyl(f'ScrewShank{i}',x,y,7.4,1.5,8.),cyl(f'ScrewHead{i}',x,y,15.4,2.84,3.)]);hardware.append(role(screw,'hardware','M3x8 socket cap | assumed max head 5.68 x 3mm'))
 nut=cut(f'ClosureNut{i}',hexagon(f'NutBlank{i}',x,y,7.6,5.5,2.4),cyl(f'NutHole{i}',x,y,7.5,1.5,2.6));hardware.append(role(nut,'hardware','M3 nut | AF5.5 x 2.4mm | side load'))
D.recompute()
for o in (base,lid,barrier):assert o.Shape.isValid() and len(o.Shape.Solids)==1,(o.Name,len(o.Shape.Solids))
meta=D.addObject('App::DocumentObjectGroup','Provenance');meta.addProperty('App::PropertyString','Frames').Frames='Main bottom Z10.8, top11.8. Base underside BODY. ICM AG +Z outward; raw mag +Z inward. AG Rz(-90), MAG Rz(-90)*diag(1,-1,-1).'
meta.addProperty('App::PropertyString','Status').Status='ENGINEERING PROTOTYPE ONLY; battery/physical fit/rigidity/RF/thermal/magnetic gates open.'
source=D.addObject('App::DocumentObjectGroup','EngineeringSources');source.Group=[o for o in D.Objects if o not in (source,S,meta)]
assembly=D.addObject('App::DocumentObjectGroup','InspectionAssembly');assembly.Label='MOVE THESE | separate inspection groups'
groups=[('ViewBase',[base],(0,0,0)),('ViewLid',[lid],(0,0,25)),('ViewMain',[o for o in refs if o.Name.startswith('Main')],(0,0,15)),('ViewDivider',[barrier],(0,0,7)),('ViewBattery',[o for o in refs if o.Role=='battery'],(-12,0,5)),('ViewCables',[o for o in refs if o.Role=='harness'],(12,0,10)),('ViewHardware',hardware,(0,0,35))]
for name,objects,offset in groups:
 g=D.addObject('App::Part',name);assembly.addObject(g);g.Label=name[4:]+' | movable inspection group';g.addProperty('App::PropertyVector','ExplodedOffset','Inspection');g.ExplodedOffset=A.Vector(*offset)
 for obj in objects:
  link=D.addObject('App::Link','Inspect_'+obj.Name);link.setLink(obj);link.LinkPlacement=obj.Placement;g.addObject(link);link.Label=obj.Label
D.recompute();Part.export([base,lid,barrier]+refs+hardware,str(EX/'smove-r2-assembly.step'));Part.export([base,lid,barrier],str(EX/'smove-r2-printable.step'))
mesh_reports={}
for name,obj in [('base',base),('lid',lid),('divider',barrier)]:
 sh=obj.Shape.copy()
 if name=='lid':sh.rotate(A.Vector(),A.Vector(1,0,0),180)
 bb=sh.BoundBox;sh.translate(A.Vector(-bb.XMin,-bb.YMin,-bb.ZMin));mesh=MeshPart.meshFromShape(Shape=sh,LinearDeflection=.04,AngularDeflection=.12,Relative=False);mesh.write(str(EX/f'{name}.stl'));mesh_reports[name]=dict(volume_mm3=obj.Shape.Volume,triangles=mesh.CountFacets)
import sys
sys.path.insert(0,str(OUT));from export_main import export as export_main_board
export_main_board(D)
for step in EX.glob('*.step'):step.write_text('\n'.join(line.rstrip() for line in step.read_text().splitlines())+'\n')
D.saveAs(str(OUT/'smove-r2-enclosure.FCStd'))
report=dict(status='GENERATED_REQUIRE_INDEPENDENT_VERIFY',parameters_mm=P,reference_objects=[o.Name for o in refs],hardware_objects=[o.Name for o in hardware],clearance_objects=[o.Name for o in clearances],inspection_groups=[g[0] for g in groups],fastener_xy_mm=fasteners,retention_xy_mm=lands,parts=mesh_reports,main_transform=[[1,0,0,0],[0,1,0,0],[0,0,1,10.8],[0,0,0,1]],pack_route_points_mm=packpoints,pack_route_length_mm=packlength,input_hash=DATA['boards']['main']['board_sha256'])
(CACHE/'build.json').write_text(json.dumps(report,indent=2)+'\n');print('Generated integrated stack; measure/check before claiming fit')
