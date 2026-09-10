"""Independent read-only CAD/mesh sweep; writes only its enclosure validation report.
Not physical, RF, sweat, sealing, thermal or snap-force qualification.
"""
import json
from pathlib import Path
import FreeCAD as A, Part, Mesh
R=Path(__file__).resolve().parents[1];H=R/'housing';checks=[];metrics={}
def ck(name,ok,**kw):checks.append(dict(name=name,passed=bool(ok),**kw))
for wall,folder in [(.8,H),(1.2,R/'.cache/wall-1.2')]:
 d=A.openDocument(str(folder/'smove-r2-enclosure.FCStd'))
 parts=[o for o in d.Objects if getattr(o,'Role','')=='print']
 leads=[o for o in d.Objects if getattr(o,'Role','')=='lead_envelope']
 for name in ('midframe','top-cover','bottom-cover'):
  m=Mesh.Mesh(str(folder/'dist'/f'{name}.stl'))
  ck(f'{wall} {name} manifold oriented single shell',m.isSolid() and not m.hasNonManifolds() and not m.hasNonUniformOrientedFacets() and m.countComponents()==1)
 for cover,direction in [(d.TopAccess,1),(d.BottomGrooved,-1)]:
  for z in (0,.25,.5,.75,1,1.5,2,3,4,6,10,20):
   sh=cover.Shape.copy();sh.translate(A.Vector(0,0,direction*z))
   for lead in leads:
    ck(f'{wall} {cover.Name} travel {z} vs {lead.Name}',sh.common(lead.Shape).Volume<1e-6)
 # Module end lies inside a capped volume, outside the main body. Six axis rays
 # are diagnostic enclosure coverage samples, NOT a water-tightness proof.
 shell=Part.makeCompound([o.Shape for o in parts])
 for point in [(8.2,43.5,14.8),(14.2,43.5,14.8),(20.2,43.5,14.8)]:
  for direction in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]:
   ray=Part.makeCylinder(.01,60,A.Vector(*point),A.Vector(*direction))
   ck(f'{wall} antenna cap coverage {point} {direction}',shell.common(ray).Volume>1e-7)
 # Opening at nominal metal mouth has no remaining plastic insertion tunnel.
 plug=Part.makeBox(15,10,4.3,A.Vector(24.78,17.2,13.1))
 ck(f'{wall} source mouth outward opening',all(o.Shape.common(plug).Volume<1e-6 for o in parts))
 metrics[str(wall)]={'minimum_lead_to_print_mm':min(a.Shape.distToShape(b.Shape)[0] for a in leads for b in parts),'minimum_wire_reserve_to_print_mm':min(d.WireRoutingReserve.Shape.distToShape(b.Shape)[0] for b in parts),'lead_to_lead_mm':leads[0].Shape.distToShape(leads[1].Shape)[0],'battery_to_RF_exclusion_mm':d.PackAllowance.Shape.distToShape(d.AntennaExclusion.Shape)[0],'wire_reserve_to_RF_exclusion_mm':d.WireRoutingReserve.Shape.distToShape(d.AntennaExclusion.Shape)[0]}
 A.closeDocument(d.Name)
r={'result':'PASS' if all(c['passed'] for c in checks) else 'FAIL','checks':checks,'metrics':metrics,'limits':'Nominal CAD only; sampled insertion/coverage does not prove physical assembly or liquid exclusion.'}
(H/'validation/prototype.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({'result':r['result'],'checks':len(checks),'metrics':metrics,'failed':[c for c in checks if not c['passed']]},indent=2));assert r['result']=='PASS'
