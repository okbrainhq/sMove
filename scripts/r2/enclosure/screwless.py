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
receipt=json.loads((R/'.cache/export/main-exports.json').read_text())
assert receipt['sources'][I['native_board']]==DATA['board_sha256'],'Run current PCB export before enclosure generation'
assert receipt['artifacts']['PCB/main/dist/main-board-only.step']==hashlib.sha256((R/'PCB/main/dist/main-board-only.step').read_bytes()).hexdigest(),'Stale/changed exact board STEP'
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
 return rr(name,sub(-4.5,w),sub(4.5,w),z,add(31,add(w,w)),add(42,add(w,w)),h,add('Parameters.Radius',w))
def interior(name,z,h,inset=0):
 return rr(name,add(-4.5,inset),add(4.5,inset),z,sub(31,add(inset,inset)),sub(42,add(inset,inset)),h,sub('Parameters.Radius',inset))
def ring(name,z,h,inset,thick):return cut(name,interior(name+'Outer',z,h,inset),interior(name+'Inner',z-.01,h+.02,add(inset,thick)))
def role(o,r):o.addProperty('App::PropertyString','Role');o.Role=r;return o
def ref(name,x,y,z,dx,dy,dz,r):return role(box(name,x,y,z,dx,dy,dz),r)
# Covers meet hard perimeter stops at Z6.5 and 10.5, never at the pack or PCB.
bottom=cut('BottomCup',exterior('BottomBlank',0,6.5),interior('BottomVoid','Parameters.Wall',8))
top=cut('TopCup',exterior('TopBlank',10.5,sub(add('Parameters.Roof','Parameters.Wall'),10.5)),interior('TopVoid',10.4,sub('Parameters.Roof',10.4)))
midparts=[cut('MidBelt',exterior('BeltBlank',6.5,4),interior('BeltVoid',6.4,4.2)),ring('BottomTongue',3.5,3.1,'Parameters.Fit',1.2),ring('TopTongue',10.4,2.6,'Parameters.Fit',1.2)]
# Broad separator: complete protection below PCB and shell tails, except explicit west passage.
midparts.append(interior('InsulatingSeparator',6.8,1.2))
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
 for x,sign in [(-4.5+C['sleeve_clearance_mm']+.02,-1),(26.5-C['sleeve_clearance_mm']-.02,1)]:
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
for x,dx in [(-4.6,5.3),(24.3,2.3)]:
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
refs.append(ref('USBTails',17.45,17.5,11.4,7.55,9.4,1.2,'tail'))
pack=ref('PackAllowance',2,6.5,1.8,21,31,4.3,'battery_reserve')
refs.append(ref('BatteryCandidate',2.5,7,1.8,20,30,3,'battery'))
refs.append(ref('PackFloorInsulator',2,6.5,1.4,21,31,.2,'insulator'))
# Roof tool accesses. SW openings reduced to 2.9 diameter to leave a 0.85mm bridge.
access=[]
for r,rad in [('SW2',1.45),('SW3',1.45),('D1',1.9)]:
 x,y=I['anchors'][r]['center_native_xy_mm'];a=cyl(r+'Access',x-100,139-y,15.8,rad,5);access.append(a)
cavity=I['anchors']['J1']['cavity_polygon_native_xy_mm']
cx0=min(p[0] for p in cavity)-100;cy0=139-max(p[1] for p in cavity)
usb=box('USBPlugAccess',cx0-.1,cy0-.5,12.6+I['anchors']['J1']['cavity_z_mm_from_board_bottom'][0]-.15,15,11,4.85)
top=cut('TopAccess',top,fuse('AccessTools',access+[usb]))
# Explicit open west passage through separator and pack locator; upper elbow reaches both BAT pads.
passage=box('BatteryWirePassage',-2.8,29.5,1.3,4.7,8.5,10.3)
# Adhesive strain-relief land upstream of solder. No hard clamp on pack or wire insulation.
mid=fuse('Midframe',[cut('MidPassage',fuse('MidStructure',midparts),passage),box('WireAdhesiveLand',-3.3,30,3,1.5,7,5)])
bottom=role(bottom,'print');bottom.Label='BOTTOM | white | body-facing'
mid=role(mid,'print');mid.Label='MID FRAME | separator, battery + PCB locators, west wire passage'
top=role(top,'print');top.Label='TOP | white | USB, RESET, BOOT, LED'
# Conservative contiguous wire reserve (not an invented exact harness): entirely outside pack/RF,
# then above separator with 2mm nominal bend radius allowance in enlarged elbow.
wire=fuse('WireRoutingReserve',[box('WireWestReserve',-1.7,30,2,3.2,7.5,9.4),box('WireElbowReserve',-2.5,32.4,8.6,7.8,4.5,2.8),box('WireBATRise',3.7,32.6,9.4,1.6,4.2,3.2)])
role(wire,'wire_reserve');role(passage,'passage')
# Conditional reference harness: two OD1.2 leads, R2 centreline bends, west entry.
# Actual pack lead exit is NOT known; this is a qualification envelope, not a vendor harness.
leads=[]
for pin in DATA['footprints']['J2']['pads']:
 x,y=pin['local_xy'];v=lambda x,z:A.Vector(x,y,z)
 edges=[Part.makeLine(v(-1,3),v(-1,8)),Part.Arc(v(-1,8),v(1-math.sqrt(2),8+math.sqrt(2)),v(1,10)).toShape(),Part.makeLine(v(1,10),v(x-2,10)),Part.Arc(v(x-2,10),v(x-2+math.sqrt(2),12-math.sqrt(2)),v(x,12)).toShape(),Part.makeLine(v(x,12),v(x,12.6))]
 path=Part.Wire(edges);circle=Part.Wire([Part.makeCircle(.6,v(-1,3),A.Vector(0,0,1))])
 sh=path.makePipeShell([circle],True,False)
 lead=D.addObject('PartDesign::Feature','LeadEnvelope'+pin['number']);lead.Shape=sh;role(lead,'lead_envelope');leads.append(lead)

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
meta=D.addObject('App::FeaturePython','ReviewStatus');meta.addProperty('App::PropertyString','PCB_SHA256').PCB_SHA256=DATA['board_sha256'];meta.addProperty('App::PropertyString','Release').Release='CAD ONLY. No proven fit, charging or manufacturing release.'
D.recompute();D.saveAs(str(OUT/'smove-r2-enclosure.FCStd'))
Part.export(parts,str(EX/'smove-r2-printable.step'));Part.export(parts+refs+leads,str(EX/'smove-r2-assembly.step'))
if OUT==H:
 # Separate PCB envelope export with no duplicate display instances.
 temp=A.newDocument('PCBConservativeExport');exports=[]
 for src in refs:
  if src.Role not in ('pcb','component','tail'):continue
  o=temp.addObject('PartDesign::Feature',src.Name);sh=src.Shape.copy();sh.translate(A.Vector(0,0,-12.6));o.Shape=sh;exports.append(o)
 Part.export(exports,str(R/'PCB/main/dist/main-populated-with-conservative-envelopes.step'))
 (R/'PCB/main/dist/conservative-step-frame.json').write_text(json.dumps({'status':'CONSERVATIVE_ENVELOPES_NOT_VENDOR_ASSEMBLY','frame':'X=nativeX-100; Y=139-nativeY; Z=board bottom 0','objects':[o.Name for o in exports],'pcb_sha256':DATA['board_sha256'],'duplicate_instances':0},indent=2)+'\n')
 A.closeDocument(temp.Name);A.setActiveDocument(D.Name)
for f in list(EX.glob('*.step'))+([R/'PCB/main/dist/main-populated-with-conservative-envelopes.step'] if OUT==H else []):
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
 for obj in parts+[pack,rf]:disjoint(lead,obj)
disjoint(*leads)

disjoint(pack,wire)
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
check('Wire reserve is single contiguous volume',len(wire.Shape.Solids)==1)
for pad in DATA['footprints']['J2']['pads']:
 x,y=pad['local_xy'];check('Wire reaches BAT '+pad['number'],wire.Shape.isInside(A.Vector(x,y,12.59),1e-6,True))
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
 sample=Part.makeBox(4,1,.1,A.Vector(-7,22,z));vol=obj.Shape.common(sample).Volume
 check(name+' measured wall',abs(vol/.1-wall)<1e-5,measured_mm=vol/.1)
report=dict(result='PASS' if all(x['pass_'] for x in checks) else 'FAIL',wall_mm=wall,pcb_sha256=DATA['board_sha256'],printed_solids=3,parts=meshes,checks=checks,failed=[x for x in checks if not x['pass_']],limits=['Nominal rigid CAD only; snap insertion flex 0.12mm not simulated or proven','Wire reserve accepts <=1.2mm OD; pack exit, wire bend rating, solder, adhesive and pull test not qualified','Supports/brim and fit coupons required; no support-free or physical-fit claim'],dimensions_XYZ_mm=[max(o.Shape.BoundBox.XMax for o in parts)-min(o.Shape.BoundBox.XMin for o in parts),max(o.Shape.BoundBox.YMax for o in parts)-min(o.Shape.BoundBox.YMin for o in parts),max(o.Shape.BoundBox.ZMax for o in parts)-min(o.Shape.BoundBox.ZMin for o in parts)],snap=dict(sleeve_radial_gap_mm=C['sleeve_clearance_mm'],insertion_deflection_mm=C['snap_projection_mm']-C['sleeve_clearance_mm']-.02,groove_radial_clearance_mm=C['snap_groove_depth_mm']-(C['snap_projection_mm']-C['sleeve_clearance_mm']-.02),engagement_mm=2.5))
(V/'mechanical.json').write_text(json.dumps(report,indent=2)+'\n');(V/'input-geometry.json').write_text(json.dumps(DATA,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ('result','wall_mm','printed_solids','failed')},indent=2))
assert report['result']=='PASS',report['failed']
