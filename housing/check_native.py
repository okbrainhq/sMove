"""Independent reopened-native/STL and live spreadsheet checks; never saves edits."""
import json,hashlib
from pathlib import Path
import FreeCAD as A,Part,Mesh
R=Path(__file__).resolve().parents[1];H=R/'housing'
D=A.openDocument(str(H/'smove-r2-enclosure.FCStd'));alt=A.openDocument(str(R/'.cache/wall-1.2/smove-r2-enclosure.FCStd'))
parts=[o for o in D.Objects if getattr(o,'Role','')=='print'];checks={};details={}
checks['exactly_three_print_roles']=len(parts)==3
mapping={'Midframe':'midframe','TopAccess':'top-cover','BottomGrooved':'bottom-cover'}
for o in parts:
 name=mapping[o.Name];m=Mesh.Mesh(str(H/'dist'/(name+'.stl')))
 good=m.isSolid() and not m.hasNonManifolds() and not m.hasNonUniformOrientedFacets() and m.countComponents()==1
 checks[name+'_manifold_oriented_connected']=good
 details[name]={'nonmanifolds':m.hasNonManifolds(),'inconsistent_orientation':m.hasNonUniformOrientedFacets(),'components':m.countComponents(),'volume_error_fraction':abs(m.Volume-o.Shape.Volume)/o.Shape.Volume}
 checks[name+'_native_STL_volume']=details[name]['volume_error_fraction']<.005
old={o.Name:o.Shape.Volume for o in parts}
D.Parameters.set('B1','1.2 mm');D.recompute()
for o in parts:
 a=alt.getObject(o.Name)
 checks[o.Name+'_live_wall_matches_regenerated_1_2']=abs(o.Shape.Volume-a.Shape.Volume)<1e-5 and o.Shape.isValid() and len(o.Shape.Solids)==1
 checks[o.Name+'_wall_actually_changes_solid']=abs(old[o.Name]-o.Shape.Volume)>1
D.Parameters.set('B1','.8 mm');D.recompute()
checks['live_wall_roundtrip']=all(abs(o.Shape.Volume-old[o.Name])<1e-5 for o in parts)
# Verify the exported exact KiCad board frame and reconstructed CAD substrate compare.
k=Part.read(str(R/'PCB/main/dist/main-board-only.step'));bb=k.BoundBox
print('Exact KiCad STEP bounds',bb)
data=json.loads((H/'validation/input-geometry.json').read_text());ox,oy=data['drill_origin_native_xy_mm']
checks['exact_kicad_frame']=abs(bb.XMin+ox-100)<1e-5 and abs(bb.XMax+ox-125)<1e-5 and abs(bb.YMin+139-oy-9)<1e-5 and abs(bb.YMax+139-oy-39)<1e-5
face=max((f for f in k.Faces if f.BoundBox.ZLength<1e-6),key=lambda f:f.Area).copy();face.translate(A.Vector(ox-100,139-oy,12.6-face.BoundBox.ZMin));exact=face.extrude(A.Vector(0,0,1))
checks['native_substrate_exact_outline_and_holes']=D.MainPCB.Shape.cut(exact).Volume<1e-6 and exact.cut(D.MainPCB.Shape).Volume<1e-6
details['board_STEP']={'drill_origin_native_xy_mm':[ox,oy],'export_dielectric_thickness_mm':bb.ZLength,'conservative_total_board_mm':1,'note':'KiCad STEP dielectric thickness excludes copper; accepted 1mm total envelope retained.'}
report={'result':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'mesh_details':details,'native_sha256':hashlib.sha256((H/'smove-r2-enclosure.FCStd').read_bytes()).hexdigest(),'note':'Reopened FCStd Wall B1 changed to 1.2 and compared with independent regeneration, restored without saving.'}
(H/'validation/native-parameter.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2));assert report['result']=='PASS'
