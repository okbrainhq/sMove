#!/usr/bin/python3
"""Focused independent current-source / manufacturing-export consistency checks."""
from pathlib import Path
import csv, hashlib, json, re, zipfile, math
import pcbnew as p
from sexp import parse,many,one,val
R=Path(__file__).resolve().parents[3];H=R/'PCB/main';O=R/'docs/revision-r2/solder-wire/validation';checks=[]
def check(n,ok,detail=None):checks.append(dict(check=n,passed=bool(ok),detail=detail))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
b=p.LoadBoard(str(H/'smove-r2-main.kicad_pcb'));fps={f.GetReference():f for f in b.GetFootprints()};parts=json.loads((H/'parts-main.json').read_text());interface=json.loads((H/'interface.json').read_text());origin=b.GetDesignSettings().GetAuxOrigin()
def xy(pos):return [round((pos.x-origin.x)/1e6,6),round((origin.y-pos.y)/1e6,6)]
with (H/'dist/BOM.csv').open() as f:bom=list(csv.DictReader(f))
refs=[r for row in bom for r in row['Designator'].split(',')];fitted={r for r,v in parts.items() if v['fitted']}
check('BOM_exact_46',len(refs)==46 and set(refs)==fitted and 'J2' not in refs)
with (H/'dist/pick-and-place.csv').open() as f:cpl=list(csv.DictReader(f))
check('CPL_exact_46',len(cpl)==46 and {x['Designator'] for x in cpl}==fitted)
for row in cpl:
 f=fps[row['Designator']];check('CPL_pose:'+f.GetReference(),math.dist([float(row['Mid X']),float(row['Mid Y'])],xy(f.GetPosition()))<1e-6 and abs(float(row['Rotation'])-f.GetOrientationDegrees()%360)<1e-6 and row['Layer']=='Top')
placements=json.loads((H/'dist/assembly-placements.json').read_text())
check('placement_export_population',{x['reference'] for x in placements['parts']}==fitted)
for row in placements['parts']:
 f=fps[row['reference']];check('assembly_pose:'+f.GetReference(),row['xy_mm']==xy(f.GetPosition()) and row['rotation_deg']==f.GetOrientationDegrees()%360)
 for pad in row['pads']:check('assembly_pad:'+f.GetReference()+'.'+pad['number'],any(a.GetNumber()==pad['number'] and xy(a.GetPosition())==pad['xy_mm'] and a.GetNetname()==pad['net'] for a in f.Pads()))
with zipfile.ZipFile(H/'dist/gerbers.zip') as z:
 check('ZIP_exact_members',set(z.namelist())=={f.name for f in (H/'dist/gerbers').iterdir() if f.is_file()})
 for name in z.namelist():check('ZIP_member:'+name,z.read(name)==(H/'dist/gerbers'/name).read_bytes())
# Parse PTH drill tools and coordinates independently of native pad APIs.
text=(H/'dist/gerbers/smove-r2-main-PTH.drl').read_text();tools={k:float(v) for k,v in re.findall(r'^T(\d+)C([\d.]+)',text,re.M)};hits=[];tool=None
for line in text.splitlines():
 if re.fullmatch(r'T\d+',line):tool=line[1:]
 m=re.fullmatch(r'X(-?[\d.]+)Y(-?[\d.]+)',line)
 if m:hits.append((tools[tool],[float(v) for v in m.groups()]))
for pad in fps['J2'].Pads():check('J2_PTH_drill:'+pad.GetNumber(),any(abs(d-1.)<1e-6 and math.dist(pos,xy(pad.GetPosition()))<1e-6 for d,pos in hits))
text=(H/'dist/gerbers/smove-r2-main-NPTH.drl').read_text()
for ref in ['H1','H2']:
 x,y=xy(fps[ref].GetPosition());check('M3_NPTH_drill:'+ref,any(math.dist([float(a),float(c)],[x,y])<1e-6 for a,c in re.findall(r'^X(-?[\d.]+)Y(-?[\d.]+)',text,re.M)))
# Gerber board edge vertex set includes only the actual compact outline (aux frame, Y up).
g=(H/'dist/gerbers/smove-r2-main-Edge_Cuts.gm1').read_text();digits=int(re.search(r'%FSLAX\d(\d)Y',g)[1]);scale=10**digits
observed={(int(x)/scale,int(y)/scale) for x,y in re.findall(r'X(-?\d+)Y(-?\d+)D0[12]',g)}
expected={tuple(xy(p.VECTOR2I(round(x*1e6),round(y*1e6)))) for x,y in interface['outline_native_xy_mm']}
check('Gerber_exact_outline',observed==expected,dict(observed=sorted(observed),expected=sorted(expected)))
# Sources/artifacts recorded during the actual export must still match.
exports=json.loads((O/'exports.json').read_text())
for path,digest in {**exports['sources'],**exports['artifacts']}.items():check('export_hash:'+path,sha(R/path)==digest)
check('no_battery_connector_in_BOM','S2B-PH' not in (H/'dist/BOM.csv').read_text() and 'C295747' not in (H/'dist/BOM.csv').read_text())
check('native_and_interface_hash',sha(H/'smove-r2-main.kicad_pcb')==interface['geometry_sha256'])
for kind in ['mechanical','gui-inspection']:
 report=json.loads((R/'housing/validation'/f'{kind}.json').read_text());digest=report.get('native_sha256') or report['sources']['housing/smove-r2-enclosure.FCStd'];check('final_FCStd_hash:'+kind,sha(R/'housing/smove-r2-enclosure.FCStd')==digest)
check('nominal_insertion_not_compression',json.loads((R/'housing/validation/battery-insertion.json').read_text())['status']=='PASS_NOMINAL_BODY_ONLY')
failed=[x for x in checks if not x['passed']];report=dict(status='PASS' if not failed else 'FAIL',check_count=len(checks),checks=checks,failures=failed,manufacturing_release=False)
(O/'coherence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(status=report['status'],checks=len(checks),failures=failed),indent=2));raise SystemExit(bool(failed))
