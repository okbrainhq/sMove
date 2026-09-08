#!/usr/bin/python3
"""Read-only compact delivery/native/export coherence checks. Writes recovery evidence only."""
from pathlib import Path
import collections
import csv
import hashlib
import json
import math
import re
import zipfile
import pcbnew as p

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'docs/recovery/checks'
OUT.mkdir(parents=True, exist_ok=True)
checks = []
def check(name, passed, detail=None):
    checks.append(dict(check=name, passed=bool(passed), detail=detail))
def near(a, b):
    return len(a) == len(b) and all(abs(x-y) < 1e-6 for x,y in zip(a,b))
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

board = p.LoadBoard(str(ROOT/'PCB/main/smove-r2-main.kicad_pcb'))
fps = {f.GetReference():f for f in board.GetFootprints()}
parts = json.loads((ROOT/'PCB/main/parts-main.json').read_text())
contract = json.loads((ROOT/'PCB/main/native-layout-contract.json').read_text())
origin = p.ToMM(board.GetDesignSettings().GetAuxOrigin())
outline = contract['outline']
vertices = [tuple(p.ToMM(v)) for edge in board.GetDrawings() if edge.GetLayer()==p.Edge_Cuts for v in (edge.GetStart(),edge.GetEnd())]
check('native_outline_equals_recovered_contract', set(vertices)==set(map(tuple,outline)))
check('PCB_outline_centreline_25x39_mm', near([max(x for x,y in vertices)-min(x for x,y in vertices),max(y for x,y in vertices)-min(y for x,y in vertices)], [25,39]))
check('47_fitted_plus_two_non_BOM_holes', len(parts)==47 and set(fps)==set(parts)|{'H1','H2'})
check('no_UART_header_or_testpoints', not any(n=='J3' or n.startswith('TP') for n in fps))
check('centred_IMU_pose', near([*p.ToMM(fps['U2'].GetPosition()),fps['U2'].GetOrientationDegrees()], [112.5,117.5,-90]))

rows = list(csv.DictReader((ROOT/'PCB/main/dist/pick-and-place.csv').open()))
check('CPL_reference_set', len(rows)==47 and {r['Designator'] for r in rows}==set(parts))
for row in rows:
    f = fps[row['Designator']];x,y=p.ToMM(f.GetPosition())
    check('CPL_native_pose:'+row['Designator'], near([float(row['Mid X']),float(row['Mid Y']),float(row['Rotation'])],[x-origin[0],origin[1]-y,f.GetOrientationDegrees()%360]) and row['Layer']=='Top')
placements = json.loads((ROOT/'PCB/main/dist/assembly-placements.json').read_text())
check('assembly_reference_set', len(placements['parts'])==47 and {r['reference'] for r in placements['parts']}==set(parts))
for row in placements['parts']:
    f=fps[row['reference']]; x,y=p.ToMM(f.GetPosition())
    check('assembly_native_pose:'+row['reference'], near(row['xy_mm'],[x-origin[0],origin[1]-y]) and abs((row['rotation_deg']-f.GetOrientationDegrees())%360)<1e-6)
    check('assembly_MPN:'+row['reference'], row['mpn']==parts[row['reference']]['mpn'])
    for pad in row['pads']:
        candidates=[q for q in f.Pads() if q.GetNumber()==pad['number']]
        check('assembly_pad:'+row['reference']+'.'+pad['number'],any(near(pad['xy_mm'],[p.ToMM(q.GetPosition())[0]-origin[0],origin[1]-p.ToMM(q.GetPosition())[1]]) and q.GetNetname()==pad['net'] for q in candidates))

text=(ROOT/'PCB/main/dist/gerbers/smove-r2-main-Edge_Cuts.gm1').read_text()
gerber_vertices={(int(x)/1e6,int(y)/1e6) for x,y in re.findall(r'X(-?\d+)Y(-?\d+)D0[12]\*',text)}
check('Gerber_outline_native_match',gerber_vertices=={(round(x-origin[0],6),round(origin[1]-y,6)) for x,y in vertices})
npth=(ROOT/'PCB/main/dist/gerbers/smove-r2-main-NPTH.drl').read_text()
hole_block=npth.split('\nT2\n',1)[1].split('M30')[0]
drills={(float(x),float(y)) for x,y in re.findall(r'X(-?[0-9.]+)Y(-?[0-9.]+)',hole_block)}
expected=set()
for name,xy in contract['mounting']['holes_native_xy_mm'].items():
    f=fps[name];pad=next(iter(f.Pads()))
    check('NPTH_native:'+name,near(p.ToMM(f.GetPosition()),xy) and near(p.ToMM(pad.GetDrillSize()),[3.2,3.2]) and pad.GetAttribute()==p.PAD_ATTRIB_NPTH)
    expected.add((round(xy[0]-origin[0],6),round(origin[1]-xy[1],6)))
check('Excellon_M3_diameter_and_positions','T2C3.200' in npth and drills==expected,sorted(drills))
with zipfile.ZipFile(ROOT/'PCB/main/dist/gerbers.zip') as z:
    files=[n for n in z.namelist() if not n.endswith('/')]
    actual={q.name for q in (ROOT/'PCB/main/dist/gerbers').iterdir() if q.is_file()}
    check('Gerber_zip_file_set',{Path(n).name for n in files}==actual)
    for n in files:
        check('Gerber_zip_exact:'+n,z.read(n)==(ROOT/'PCB/main/dist/gerbers'/Path(n).name).read_bytes())

for mf in ['PCB/main/dist/manifest.json','housing/dist/manifest.json','docs/revision-r2/integrated/validation/delivery-manifest.json']:
    j=json.loads((ROOT/mf).read_text())
    check('release_false:'+mf,j['manufacturing_release'] is False)
    for name,digest in j['files'].items():
        check('manifest:'+mf+':'+name,(ROOT/name).is_file() and sha(ROOT/name)==digest)
old = json.loads((ROOT/'housing/validation/input-geometry.json').read_text())
fresh = json.loads((ROOT/'.cache/housing/input-geometry.json').read_text())
notes = ['GetBoardEdgesBoundingBox includes stroke width (25.05 x 39.05); centreline outline and physical board bounds are 25 x 39 mm.',
         'Original manifests and historical reports are preserved byte-for-byte, not re-sealed.',
         'The unused Debug_5 library footprint is retained because deletion is forbidden; it is not placed in the board or schematic.']
if old != fresh:
    notes.append('Inherited housing/validation/input-geometry.json is not the fresh compact extraction; use docs/recovery/checks/current-input-geometry.json. It was already stale in the preserved delivery and is retained unchanged for provenance.')
(OUT/'current-input-geometry.json').write_text(json.dumps(fresh,indent=2)+'\n')
report={'status':'PASS' if all(r['passed'] for r in checks) else 'FAIL','checks':checks,'count':len(checks),'failures':[r for r in checks if not r['passed']],'notes':notes}
(OUT/'source-export-coherence.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2))
raise SystemExit(bool(report['failures']))
