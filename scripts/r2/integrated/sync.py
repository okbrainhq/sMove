#!/usr/bin/python3
"""Publish actual current placement using immutable original conservative local envelopes.
Native PCB (including final routes) is authoritative; no component or geometry substitutions.
"""
import json,hashlib,math
from pathlib import Path
import pcbnew as p
from solder_wire import H,R,HOLES,OUTLINE
from sexp import parse,many,one,val
source=H/'mechanical-envelope-source.json'
j=json.loads(source.read_text());oldparts=json.loads((H/'mechanical-pose-source.json').read_text())
b=p.LoadBoard(str(H/'smove-r2-main.kicad_pcb'));fps={f.GetReference():f for f in b.GetFootprints()};parts=json.loads((H/'parts-main.json').read_text())
def point(r,xy):
 x0,y0,a0=oldparts[r]['placement'];x,y=p.ToMM(fps[r].GetPosition());a=math.radians(fps[r].GetOrientationDegrees()-a0);u,v=xy[0]-x0,xy[1]-y0
 return [round(x+math.cos(a)*u+math.sin(a)*v,6),round(y-math.sin(a)*u+math.cos(a)*v,6)]
def bbox(bb):return [bb.GetX()/1e6,bb.GetY()/1e6,bb.GetRight()/1e6,bb.GetBottom()/1e6]
def transform_rect(r,rect):
 x0,y0,x1,y1=rect;pts=[point(r,[x,y]) for x,y in [(x0,y0),(x0,y1),(x1,y0),(x1,y1)]]
 return [min(v[0] for v in pts),min(v[1] for v in pts),max(v[0] for v in pts),max(v[1] for v in pts)]
j['components']={r:c for r,c in j['components'].items() if r in parts}
for r,c in j['components'].items():
 if r=='J2':continue
 f=fps[r];rect=c['body_aabb_native_xy_mm'];rect=rect if rect!=[0,0,0,0] else c['courtyard_native_xy_mm']
 c['body_aabb_native_xy_mm']=transform_rect(r,rect);c['courtyard_native_xy_mm']=bbox(f.GetCourtyard(p.F_CrtYd).BBox());c['anchor_native_xy_mm']=list(p.ToMM(f.GetPosition()));c['rotation_ccw_deg']=f.GetOrientationDegrees();parts[r]['placement']=[*c['anchor_native_xy_mm'],f.GetOrientationDegrees()]
f=fps['J2'];parts['J2']['placement']=[*p.ToMM(f.GetPosition()),f.GetOrientationDegrees()]
j['components']['J2']=dict(ref='J2',mpn='PCB PTH wire pads - not fitted hardware',fitted=False,body_aabb_native_xy_mm=bbox(f.GetCourtyard(p.F_CrtYd).BBox()),courtyard_native_xy_mm=bbox(f.GetCourtyard(p.F_CrtYd).BBox()),anchor_native_xy_mm=list(p.ToMM(f.GetPosition())),rotation_ccw_deg=0,z_mm_from_board_bottom=[0,1])
j['anchors']['J2']={'center_native_xy_mm':list(p.ToMM(f.GetPosition())),'pins':{a.GetNumber():{'native_xy_mm':list(p.ToMM(a.GetPosition())),'net':a.GetNetname()} for a in f.Pads()},'wire_exit':'Through board to protected lower wire bay; no connector or mating reserve'}
for r,a in list(j['anchors'].items()):
 if r=='J2':continue
 if r not in parts:del j['anchors'][r];continue
 for k in ['center_native_xy_mm','mating_face_center_native_xy_mm']:
  if k in a:a[k]=point(r,a[k])
 if 'cavity_polygon_native_xy_mm' in a:
  a['cavity_polygon_native_xy_mm']=[point(r,xy) for xy in a['cavity_polygon_native_xy_mm']];a['outward_unit_native_xy']=[round(v,6) for v in [math.sin(math.radians(fps[r].GetOrientationDegrees())),math.cos(math.radians(fps[r].GetOrientationDegrees()))]]
 if 'pins' in a:
  for pin,data in a['pins'].items():
   pad=next(pad for pad in fps[r].Pads() if pad.GetNumber()==pin);data['native_xy_mm']=list(p.ToMM(pad.GetPosition()));data['net']=pad.GetNetname()
for k in ['antenna_body_native_xy_mm','antenna_all_layer_keepout_native_xy_mm']:j[k]=[point('U1',xy) for xy in j[k]]
j['antenna_3d']['clear_air_volume_native_xy_mm']=j['antenna_all_layer_keepout_native_xy_mm'];j['retention']=[];j['mounting']=dict(holes_native_xy_mm=HOLES,drill_mm=3.2,copper_exclusion_radius_mm=3.45,scheme='Two diagonal NPTH holes; lid insulating sleeves / PCB / raised base nut shelves; no conductive collar on copper')
j.pop('debug',None);j['retention_policy']={'contacts':'Two through-PCB M3 sleeves, plus non-preloaded side registration. No pressure on U2; stiffness/torque/sample fit unqualified.'}
j['sensor_frame']['native_position_mm']=[*p.ToMM(fps['U2'].GetPosition()),1];j['sensor_frame']['board_bbox_centre_native_mm']=[112.5,117.75];j['sensor_frame']['centre_offset_native_mm']=[0,-0.25];j['sensor_frame']['position_from_board_NW_mm']=[12.5,17.5,1]
j.update(schema='smove.solder-wire.interface.v3',geometry_sha256=hashlib.sha256((H/'smove-r2-main.kicad_pcb').read_bytes()).hexdigest(),outline_native_xy_mm=OUTLINE,board_size_mm=[25,35.5],status='COMPACT PTH BATTERY WIRES / CENTERED IMU / TWO M3; PROTOTYPE ONLY')
j['connector_selection']={'status':'NO_FITTED_BATTERY_CONNECTOR','J2':'Two plated through-hole wire solder pads; excluded from BOM/CPL; no header allowed','pitch_mm':2.54,'manufacturing_release':False}
j['battery_wire']={'pitch_centre_mm':2.54,'pad_diameter_mm':2.0,'finished_hole_target_mm':1.0,'finished_hole_acceptance_mm':[0.9,1.1],'tinned_bundle_max_diameter_mm':0.7,'insulation_max_diameter_mm':1.2,'nominal_annular_ring_mm':0.5,'mask_expansion_mm':0.05,'copper_gap_mm':0.54,'mask_web_mm':0.44,'wire_gauge_supplied':None,'wire_selection':'Engineering envelope only; measure tinned strand bundle and insulated OD, qualify rated current/flex/temperature; no exact gauge supplied','strain_relief':'Two lacing bores and captive bridge in lower case, paired insulated leads; pull test mandatory; solder joint is not strain relief','polarity':{'1':'BAT+ protected PACK_P','2':'BAT- GND'}}
j['bottom_envelope'].pop('J3',None)
j['bottom_envelope']['J2']='PTH leads from underside; trim top protrusion <=0.6mm, insulate underside down to wire insulation, route above divider before lower wire bay'
(H/'parts-main.json').write_text(json.dumps(parts,indent=2)+'\n');(H/'interface.json').write_text(json.dumps(j,indent=2)+'\n')
raw=parse((H/'smove-r2-main.kicad_pcb').read_text());(H/'native-layout-contract.json').write_text(json.dumps(dict(outline=OUTLINE,mounting=j['mounting'],sensor_frame=j['sensor_frame'],placement={r:parts[r]['placement'] for r in parts}),indent=2)+'\n')
