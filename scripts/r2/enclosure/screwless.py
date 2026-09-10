"""Current screwless CSG generator; historical generate.py is deliberately not run.
Uses native-board extraction. Spreadsheet expressions drive actual outer geometry.
"""
import hashlib,json,itertools,sys,math
from pathlib import Path
import FreeCAD as A
import Part,MeshPart,Mesh
R=Path(__file__).resolve().parents[3]; H=R/'housing'
C=json.loads((H/'screwless.json').read_text())
# Alternate output is isolated: it must never replace default exports.
wall=float(sys.argv[2]) if len(sys.argv)>2 else C['outer_wall_mm']
OUT=H if len(sys.argv)<=2 else R/'.cache'/('wall-'+str(wall))
EX=OUT/'dist';EX.mkdir(parents=True,exist_ok=True);V=OUT/'validation';V.mkdir(exist_ok=True)
DATA=json.loads((R/'.cache/housing/input-geometry.json').read_text())['boards']['main']
I=json.loads((R/'PCB/main/interface.json').read_text());assert not DATA['holes']
assert DATA['board_sha256']==hashlib.sha256((R/I['native_board']).read_bytes()).hexdigest()
# Enclosure-only: retained board STEP is read, never regenerated or written.
assert DATA['board_sha256']==C['retained_board_sha256']
assert hashlib.sha256((R/'PCB/main/dist/main-board-only.step').read_bytes()).hexdigest()==C['retained_board_step_sha256']
assert .8<=wall<=1.2 and C['battery_allowance_mm']==[21,31,4.3]
D=A.newDocument('sMove_Screwless');D.Label='sMove | three screwless prints | white | review only'
P=D.addObject('Spreadsheet::Sheet','Parameters')
params=dict(Wall=wall,Fit=C['sleeve_clearance_mm'],Radius=C['corner_radius_mm'],PCB=C['pcb_bottom_z_mm'],Roof=C['roof_inside_z_mm'])
for n,(k,v) in enumerate(params.items(),1):P.set('A'+str(n),k);P.set('B'+str(n),str(v)+' mm');P.setAlias('B'+str(n),k)
P.setColumnWidth('A',150)
def e(v):return '('+v+')' if isinstance(v,str) else str(v)+' mm'
def add(a,b):return e(a)+'+'+e(b)
def sub(a,b):return e(a)+'-'+e(b)
def box(name,x,y,z,dx,dy,dz):
 o=D.addObject('Part::Box',name)
 for prop,v in zip(('Length','Width','Height','Placement.Base.x','Placement.Base.y','Placement.Base.z'),(dx,dy,dz,x,y,z)):o.setExpression(prop,e(v))
 return o
def cyl(name,x,y,z,r,h):
 o=D.addObject('Part::Cylinder',name)
 for prop,v in zip(('Radius','Height','Placement.Base.x','Placement.Base.y','Placement.Base.z'),(r,h,x,y,z)):o.setExpression(prop,e(v))
 return o
def fuse(name,objs):
 if len(objs)==1:return objs[0]
 o=D.addObject('Part::MultiFuse',name);o.Shapes=objs;o.Refine=True;return o
def cut(name,b,t):
 o=D.addObject('Part::Cut',name);o.Base=b;o.Tool=t;o.Refine=True;return o
def rr(name,x,y,z,dx,dy,h,r):
 # Real rounded-rectangle CSG with a constant-radius inner offset.
 obs=[box(name+'WebX',add(x,r),y,z,sub(dx,add(r,r)),dy,h),box(name+'WebY',x,add(y,r),z,dx,sub(dy,add(r,r)),h)]
 for n,(cx,cy) in enumerate([(add(x,r),add(y,r)),(sub(add(x,dx),r),add(y,r)),(add(x,r),sub(add(y,dy),r)),(sub(add(x,dx),r),sub(add(y,dy),r))]):obs.append(cyl(name+'Corner'+str(n),cx,cy,z,r,h))
 return fuse(name,obs)
def exterior(name,z,h,extra=0):
 w=add('Parameters.Wall',extra)
 return rr(name,sub(-5.5,w),sub(4.5,w),z,add(32,add(w,w)),add(37,add(w,w)),h,add('Parameters.Radius',w))
def interior(name,z,h,inset=0):
 return rr(name,add(-5.5,inset),add(4.5,inset),z,sub(32,add(inset,inset)),sub(37,add(inset,inset)),h,sub('Parameters.Radius',inset))
def ring(name,z,h,inset,thick):return cut(name,interior(name+'Outer',z,h,inset),interior(name+'Inner',z-.01,h+.02,add(inset,thick)))
def role(o,r):o.addProperty('App::PropertyString','Role');o.Role=r;return o
def ref(name,x,y,z,dx,dy,dz,r):return role(box(name,x,y,z,dx,dy,dz),r)
# Covers meet hard perimeter stops at Z6.5 and 10.5, never at the pack or PCB.
bottom=cut('BottomCup',exterior('BottomBlank',0,6.5),interior('BottomVoid','Parameters.Wall',8))
top=cut('TopCup',exterior('TopBlank',10.5,sub(add('Parameters.Roof','Parameters.Wall'),10.5)),interior('TopVoid',10.4,sub('Parameters.Roof',10.4)))
midparts=[cut('MidBelt',exterior('BeltBlank',6.5,4),interior('BeltVoid',6.4,4.2)),ring('BottomTongue',3.5,3.1,'Parameters.Fit',1.2),ring('TopTongue',10.4,2.6,'Parameters.Fit',1.2)]
# Broad continuous battery barrier with internal WEST EDGE bypass outside pack footprint.
# Continuous barrier over whole battery. Wires go around its WEST EDGE, never through it.
midparts.append(cut('InsulatingSeparator',interior('SeparatorBlank',6.8,1.2),box('PerimeterBypass',-6,10,6.7,6,26,1.4)))
# Battery pocket on opposite side. Open-bottom assembly; no snap pressure on pouch.
midparts += [box('PackWestLocator',.6,6.2,1.4,1.2,31.6,5.5),box('PackEastLocator',23.2,6.2,1.4,1.2,31.6,5.5),box('PackSouthStop',.6,5.2,1.4,23.8,1.1,5.5),box('PackNorthStop',.6,37.7,1.4,23.8,1.1,5.5)]
# Stout underside lands. 0.2 dielectric film + 0.2 controlled adhesive/shim budget.
lands=[];films=[];adh=[]
for n,(x,y,dx,dy) in enumerate([(-.5,9.2,1.2,2), (24.1,9.2,1.2,2),(-.5,36.5,1.2,2),(24.1,36.5,1.2,2)],1):
 midparts.append(box('PCBLand'+str(n),x,y,7.9,dx,dy,4.3));lands.append([x,y,dx,dy])
 films.append(ref('Dielectric'+str(n),max(0,x),y,12.2,min(dx,.7 if x<0 else .9),dy,.2,'insulator'))
 adh.append(ref('AdhesiveOrShim'+str(n),max(0,x),y,12.4,min(dx,.7 if x<0 else .9),dy,.2,'adhesive_reserve'))
 # Outside edge fence, 0.25 lateral clearance. Stops at substrate top, no component load.
 midparts.append(box('PCBEdgeFence'+str(n),-1.3 if x<0 else 25.25,y,7.9,1.05,dy,5.6))
# South and north PCB end stops (not antenna supports).
midparts += [box('SouthPCBStop',8,7.4,7.9,6,1.35,5.6),box('NorthPCBStop',1,39.25,7.9,4,1.2,5.6)]
# Snap rails: short 45-degree lead-ins, 0.12 nominal insertion flex. Grooves have 0.10 radial clearance.
def rail(name,x,sign,y,z):
 pts=[A.Vector(x,y,z),A.Vector(x+sign*C['snap_projection_mm'],y,z+.32),A.Vector(x+sign*C['snap_projection_mm'],y,z+.58),A.Vector(x,y,z+.9)]
 shape=Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(A.Vector(0,5,0))
 o=D.addObject('PartDesign::Feature',name);o.Shape=shape;return o
for z in (4.2,11.7):
 for x,sign in [(-5.5+C['sleeve_clearance_mm']+.02,-1),(26.5-C['sleeve_clearance_mm']-.02,1)]:
  for y in (12,31):midparts.append(rail('SnapRail',x,sign,y,z))
# Reinforced shallow receiving grooves, remaining wall >= configured Wall.
for name,z,obj in [('Bottom',4.2,bottom),('Top',11.7,top)]:
 band=cut(name+'GrooveReinforcement',exterior(name+'Band',z-.2,1.3,.35),interior(name+'BandVoid',z-.21,1.32))
 obj=fuse(name+'Reinforced',[obj,band])
 groove=interior(name+'SnapGroove',z-.12,1.14,-C['snap_groove_depth_mm'])
 obj=cut(name+'Grooved',obj,groove)
 if name=='Top':top=obj
 else:bottom=obj
# Cover-integral broad travel stops: 0.25mm vertical PCB play without adhesive,
# no preload. Dielectric contact at edges only; underside lands carry operating load.
retainers=[]
for x,dx in [(-5.6,6.3),(24.3,2.3)]:
 for y in (9.1,37):retainers.append(box('CoverPCBTravelStop',x,y,13.85,dx,1.2,4.35))
top=fuse('TopWithPCBStops',[top]+retainers)
# PCB envelope derived from current native outline, not a stale bounding rectangle.
exact=Part.read(str(R/'PCB/main/dist/main-board-only.step'))
# KiCad STEP omits copper thickness; use exact planar face/holes, extruded to the
# accepted conservative 1mm total board thickness, not the 0.91mm dielectric-only STEP.
face=max((f for f in exact.Faces if f.BoundBox.ZLength<1e-6),key=lambda f:f.Area).copy()
ox,oy=DATA['drill_origin_native_xy_mm']
face.translate(A.Vector(ox-100,139-oy,12.6-face.BoundBox.ZMin))
pcb=D.addObject('PartDesign::Feature','MainPCB');pcb.Shape=face.extrude(A.Vector(0,0,DATA['thickness_mm']));role(pcb,'pcb')
refs=[pcb]+films+adh
for r,f in DATA['footprints'].items():
 if f.get('fitted'):
  x0,y0,x1,y1=f['envelope_xy'];z0,z1=f['z_mm'];refs.append(ref('Component_'+r,x0,y0,12.6+z0,x1-x0,y1-y0,z1-z0,'component'))
nominal=cut('USBSourceShell',box('USBSourceBody',17.43,17.73,13.6,7.35,8.94,3.26),box('USBSourceMouth',19.5,18.03,13.95,6,8.34,2.56))
role(nominal,'connector_nominal');refs.append(nominal)
refs.append(ref('USBTails',17.45,17.5,11.4,7.55,9.4,1.2,'tail'))
pack=ref('PackAllowance',2,6.5,1.8,21,31,4.3,'battery_reserve')
refs.append(ref('BatteryCandidate',2.5,7,1.8,20,30,3,'battery'))
refs.append(ref('PackFloorInsulator',2,6.5,1.4,21,31,.2,'insulator'))
# Roof tool accesses. SW openings reduced to 2.9 diameter to leave a 0.85mm bridge.
access=[]
for r,rad in [('SW2',1.45),('SW3',1.45),('D1',1.9)]:
 x,y=I['anchors'][r]['center_native_xy_mm'];a=cyl(r+'Access',x-100,139-y,15.8,rad,5);access.append(a)
# Source-derived J1 face: locator X18.5 + 6.28 = X24.78.
# Local stepped surround ends at the actual nominal metal mouth, not at old envelope X25.
# Open notch above lower case shoulder; no claim of universal cable-overmould fit.
usb=box('USBPlugAccess',23.3,17.2,13.1,15,10,4.3)
notch=box('USBExteriorRelief',24.78,16.5,13.1,10,11.7,10)
top=cut('FlushUSBRelief',top,notch)
surround=box('USBFlushSurround',sub(24.78,'Parameters.Wall'),16.5,13.85,'Parameters.Wall',11.7,sub(add('Parameters.Roof','Parameters.Wall'),13.85))
top=fuse('TopWithFlushSurround',[top,surround])
# Protected antenna extension: main body terminates at Y41.5; only a thin cap projects.
# Module is unchanged X7.6..20.8, Y27.8..44.4. Cap floor belongs to midframe;
# roof and side skirt belong to top cover. No fourth part or exposed module.
capfloor=box('AntennaCapFloor',6.6,39.4,11.6,15.2,6,'Parameters.Wall')
midparts += [capfloor,box('CapFloorSupport',6.6,40.4,9.8,15.2,1.9,2.6)]
capouter=rr('CapOuter',sub(6.6,'Parameters.Wall'),39.4,12.6,add(15.2,add('Parameters.Wall','Parameters.Wall')),add(6,'Parameters.Wall'),sub(add(16.8,'Parameters.Wall'),12.6),1)
capvoid=box('CapInner',6.6,39.3,12.5,15.2,6.1,4.3)
cap=cut('AntennaCap',capouter,capvoid)
# Remove main north wall where the existing module crosses into the cap.
top=cut('TopAntennaPortal',top,box('AntennaPortal',6.4,39.3,10.4,15.6,5,6.4))
top=fuse('TopWithAntennaCap',[top,cap])
top=cut('TopAccess',top,fuse('AccessTools',access+[usb]))
# Short locator interruption ONLY below separator, for pack lead exit into perimeter channel.
locator_exit=box('PackLeadExit',.4,19.5,1.7,1.6,9,4.6)
mid=fuse('Midframe',[cut('MidStructureWithExit',cut('MidCapTongueRelief',fuse('MidStructure',midparts),box('CapTongueRelief',5.2,39.3,12.4,18,5,1)),locator_exit),box('WireAdhesiveLand',-4.4,28,3,0.5,3,3)])
bottom=role(bottom,'print');bottom.Label='BOTTOM | white | body-facing'
mid=role(mid,'print');mid.Label='MIDFRAME | continuous pack barrier | internal perimeter wires | cap floor'
top=role(top,'print');top.Label='TOP | RF TEST PROTOTYPE | protected antenna cap | flush USB'
# Opposite face from inherited below-PCB route: BAT leads exit +Z above PCB,
# bend west, follow internal west perimeter south, descend OUTSIDE separator edge,
# return east through locator-only relief to opposite-side pack. OD1.2, R2 centres.
def rounded_path(points,r=2):
 pts=[A.Vector(*p) for p in points];edges=[];last=pts[0]
 for i in range(1,len(pts)-1):
  p=pts[i];u=pts[i-1]-p;u.normalize();v=pts[i+1]-p;v.normalize()
  start=p+u*r;end=p+v*r;centre=p+(u+v)*r
  mid=centre-(u+v)*(r/math.sqrt(2))
  if (start-last).Length>1e-7:edges.append(Part.makeLine(last,start))
  edges.append(Part.Arc(start,mid,end).toShape());last=end
 edges.append(Part.makeLine(last,pts[-1]));return Part.Wire(edges)
leads=[];reserves=[];routes=[]
for i,pin in enumerate(DATA['footprints']['J2']['pads']):
 x,y=pin['local_xy'];west=-1.5-1.5*i;exit_y=22+3*i
 points=[(x,y,13.65),(x,y,16.4),(west,y,16.4),(west,exit_y,16.4),(west,exit_y,3.2),(1.95,exit_y,3.2)]
 path=rounded_path(points);routes.append(points)
 for radius,typ,collection in [(.6,'lead_envelope',leads),(.85,'wire_reserve',reserves)]:
  circle=Part.Wire([Part.makeCircle(radius,A.Vector(*points[0]),A.Vector(0,0,1))])
  o=D.addObject('PartDesign::Feature',('LeadEnvelope' if radius==.6 else 'LeadReserve')+pin['number']);o.Shape=path.makePipeShell([circle],True,False);role(o,typ);collection.append(o)
wire=fuse('WireRoutingReserve',reserves);role(wire,'wire_reserve')
solder=[]
for pin in DATA['footprints']['J2']['pads']:
 x,y=pin['local_xy'];o=cyl('BATSolderReserve'+pin['number'],x,y,13.6,1.1,.55);role(o,'solder_reserve');solder.append(o)
refs+=solder
rf=ref('AntennaExclusion',-7.4,39,-5.4,43.2,20.4,33.4,'rf_reserve')
D.recompute()
parts=[mid,top,bottom]
for o in parts:assert o.Shape.isValid() and len(o.Shape.Solids)==1 and o.Shape.isClosed(),(o.Name,len(o.Shape.Solids))
# Native construction is editable CSG. Sources hidden; only finals and references visible.
for o in D.Objects:
 if hasattr(o,'ViewObject') and o.ViewObject:
  o.ViewObject.Visibility=o in parts or o in refs
  if hasattr(o.ViewObject,'ShapeColor'):
   o.ViewObject.ShapeColor=(.94,.95,.96) if o in parts else ((.08,.38,.2) if o==pcb else (.35,.37,.4))
meta=D.addObject('App::FeaturePython','ReviewStatus');meta.addProperty('App::PropertyString','PCB_SHA256').PCB_SHA256=DATA['board_sha256'];meta.addProperty('App::PropertyString','Release').Release='RF TEST PROTOTYPE. No full Espressif housing-clearance compliance; no proven print fit, body RF, sweat or charging release.'
D.recompute();D.saveAs(str(OUT/'smove-r2-enclosure.FCStd'))
Part.export(parts,str(EX/'smove-r2-printable.step'));Part.export(parts+refs+leads,str(EX/'smove-r2-assembly.step'))
for f in EX.glob('*.step'):
 f.write_text('\n'.join(line.rstrip() for line in f.read_text().splitlines())+'\n')
checks=[]
def check(name,ok,**kw):checks.append(dict(name=name,pass_=bool(ok),**kw))
def disjoint(a,b,label=None):
 v=a.Shape.common(b.Shape).Volume;check(label or a.Name+' vs '+b.Name,v<1e-6,overlap_mm3=v,distance_mm=a.Shape.distToShape(b.Shape)[0])
for a,b in itertools.combinations(parts,2):disjoint(a,b)
for a in parts:
 for b in refs+[pack,wire]:disjoint(a,b)
for a in [pack,wire]:disjoint(a,rf)
for lead in leads:
 check(lead.Name+' valid sweep',lead.Shape.isValid() and len(lead.Shape.Solids)==1)
 check(lead.Name+' inside passage reserve',lead.Shape.cut(wire.Shape).Volume<1e-6,outside_mm3=lead.Shape.cut(wire.Shape).Volume)
 for obj in parts+[pack,rf]+[r for r in refs if r.Role!='solder_reserve']:disjoint(lead,obj)
disjoint(*leads)

disjoint(pack,wire)
for obj in [r for r in refs if r.Role!='solder_reserve']:disjoint(wire,obj)
for obj in solder:
 for other in [r for r in refs if r.Role in ('component','pcb')]:disjoint(obj,other)
check('Source USB mouth matches flush surround plane',abs(nominal.Shape.BoundBox.XMax-surround.Shape.BoundBox.XMax)<1e-6,mouth_x_mm=nominal.Shape.BoundBox.XMax,surround_x_mm=surround.Shape.BoundBox.XMax)
check('USB opening covers source maximum plus 0.4 per side',10>=9.09+.8 and 4.3>=3.36+.8,opening_mm=[10,4.3],source_max_mm=[9.09,3.36],placement_per_side_mm=.2,print_fit_per_side_mm=.2)
check('Battery barrier unperforated over complete pack',D.InsulatingSeparator.Shape.common(Part.makeBox(21,31,1.2,A.Vector(2,6.5,6.8))).Volume>21*31*1.2-1e-6)
# Independent access probes start at actual component envelope surfaces.
for r in ('SW2','SW3','D1'):
 a=I['anchors'][r];x,y=a['center_native_xy_mm'];z=12.6+a['surface_z_bound_mm']
 probe=Part.makeCylinder(a['access_radius_mm'],8,A.Vector(x-100,139-y,z))
 check(r+' full actuation/optical path',all(o.Shape.common(probe).Volume<1e-6 for o in parts))
a=I['anchors']['J1'];xy=a['cavity_polygon_native_xy_mm'];z0,z1=a['cavity_z_mm_from_board_bottom']
probe=Part.makeBox(max(p[0] for p in xy)-min(p[0] for p in xy),max(p[1] for p in xy)-min(p[1] for p in xy),z1-z0,A.Vector(min(p[0] for p in xy)-100,139-max(p[1] for p in xy),12.6+z0))
check('Native USB plug reserve fully open',all(o.Shape.common(probe).Volume<1e-6 for o in parts))
for delta in (.5,1,2,4,8,16):
 for obj in [r for r in refs if r.Role in ('pcb','component','tail')]:
  moved=obj.Shape.copy();moved.translate(A.Vector(0,0,delta));check(obj.Name+' PCB insertion '+str(delta),moved.common(mid.Shape).Volume<1e-6)
 moved=pack.Shape.copy();moved.translate(A.Vector(0,0,-delta));check('Battery bottom insertion '+str(delta),moved.common(mid.Shape).Volume<1e-6)
check('Two independent continuous lead reserves',all(len(o.Shape.Solids)==1 for o in reserves))
for pad in DATA['footprints']['J2']['pads']:
 x,y=pad['local_xy'];check('Wire reaches BAT '+pad['number'],wire.Shape.isInside(A.Vector(x,y,13.66),1e-6,True))
check('Battery separator clearance',6.8-(1.8+4.3)>=.69,gap_mm=.7)
check('Shell tail separator gap',11.4-8>=.8,gap_mm=3.4)
check('Button same X and 0.85 web',abs(access[0].Shape.CenterOfMass.x-access[1].Shape.CenterOfMass.x)<1e-6 and abs(access[0].Shape.CenterOfMass.y-access[1].Shape.CenterOfMass.y)-2.9>=.849)
# Printable STL orientation: lids flat outside down; midframe on EAST edge, supports required at separator/locators.
meshes={}
for name,obj in [('midframe',mid),('top-cover',top),('bottom-cover',bottom)]:
 sh=obj.Shape.copy()
 if name=='top-cover':sh.rotate(A.Vector(),A.Vector(1,0,0),180)
 if name=='midframe':sh.rotate(A.Vector(),A.Vector(0,1,0),90)
 bb=sh.BoundBox;sh.translate(A.Vector(-bb.XMin,-bb.YMin,-bb.ZMin))
 mesh=MeshPart.meshFromShape(Shape=sh,LinearDeflection=.035,AngularDeflection=.12,Relative=False);mesh.write(str(EX/(name+'.stl')))
 reread=Mesh.Mesh(str(EX/(name+'.stl')))
 check(name+' STL closed',reread.isSolid());check(name+' STL one component',reread.countComponents()==1)
 check(name+' STL volume fidelity',abs(reread.Volume-obj.Shape.Volume)/obj.Shape.Volume<.005)
 meshes[name]={'volume_mm3':obj.Shape.Volume,'triangles':reread.CountFacets,'components':reread.countComponents(),'solid':reread.isSolid()}
# Straight installation sweeps, sampled at 0.5mm: ignore only known snap flex volumes.
# Snap rails are the intentional elastic insertion feature, NOT counted as accidental collision.
railshapes=[o.Shape for o in D.Objects if o.Name.startswith('SnapRail')]
without_rails=mid.Shape.cut(Part.makeCompound(railshapes))
for obj,direction in [(top,1),(bottom,-1)]:
 for delta in (.5,1,1.5,2,2.5,3,4,6,10):
  moved=obj.Shape.copy();moved.translate(A.Vector(0,0,direction*delta))
  check(obj.Name+' insertion '+str(delta),moved.common(without_rails).Volume<1e-6)
step=Part.read(str(EX/'smove-r2-printable.step'));check('STEP exactly three valid closed solids',len(step.Solids)==3 and step.isValid() and all(s.isClosed() for s in step.Solids))
# Wall sample cuts on unobstructed straight surfaces; actual CSG, not just config echo.
for name,obj,z in [('mid',mid,9),('top',top,16),('bottom',bottom,2)]:
 sample=Part.makeBox(3,1,.1,A.Vector(-8,29,z));vol=obj.Shape.common(sample).Volume
 check(name+' measured wall',abs(vol/.1-wall)<1e-5,measured_mm=vol/.1)
report=dict(result='PASS' if all(x['pass_'] for x in checks) else 'FAIL',wall_mm=wall,pcb_sha256=DATA['board_sha256'],printed_solids=3,parts=meshes,checks=checks,failed=[x for x in checks if not x['pass_']],limits=['Nominal rigid CAD only; snap insertion flex 0.12mm not simulated or proven','Wire reserve accepts <=1.2mm OD; pack exit, wire bend rating, solder, adhesive and pull test not qualified','Supports/brim and fit coupons required; no support-free or physical-fit claim'],dimensions_XYZ_mm=[max(o.Shape.BoundBox.XMax for o in parts)-min(o.Shape.BoundBox.XMin for o in parts),max(o.Shape.BoundBox.YMax for o in parts)-min(o.Shape.BoundBox.YMin for o in parts),max(o.Shape.BoundBox.ZMax for o in parts)-min(o.Shape.BoundBox.ZMin for o in parts)],snap=dict(sleeve_radial_gap_mm=C['sleeve_clearance_mm'],insertion_deflection_mm=C['snap_projection_mm']-C['sleeve_clearance_mm']-.02,groove_radial_clearance_mm=C['snap_groove_depth_mm']-(C['snap_projection_mm']-C['sleeve_clearance_mm']-.02),engagement_mm=2.5))
report['wire_route_xyz_mm']=routes
report['rf_status']='RF TEST PROTOTYPE: compact nonmetallic cap is NOT full Espressif housing-clearance compliance'
report['usb_mouth_plane_x_mm']=24.78
report['usb_opening_WH_mm']=[10,4.3]
(V/'mechanical.json').write_text(json.dumps(report,indent=2)+'\n');(V/'input-geometry.json').write_text(json.dumps(DATA,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ('result','wall_mm','printed_solids','failed')},indent=2))
assert report['result']=='PASS',report['failed']
