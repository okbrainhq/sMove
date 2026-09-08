#!/usr/bin/python3
"""Validate standalone per-design deliverables; never create a whole-repository ZIP.
--seal refreshes per-design manifests after an intentional export (not cleanup proof).
"""
from pathlib import Path
import argparse, csv, hashlib, json, re, zipfile
import pcbnew as p
ROOT = Path(__file__).resolve().parents[3]

def sha(f): return hashlib.sha256(f.read_bytes()).hexdigest()
def dump(f, data): f.write_text(json.dumps(data, indent=2)+'\n')
def inventory(folder):
    return {str(f.relative_to(ROOT)): sha(f) for f in sorted(folder.rglob('*'))
            if f.is_file() and f.name != 'manifest.json' and '__pycache__' not in f.parts
            and not f.name.endswith(('.kicad_prl', '.pyc'))}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seal', action='store_true')
    args = parser.parse_args()
    checks = []; unavailable_standard_models = set()
    def check(name, value):
        if not value: raise AssertionError(name)
        checks.append(name)
    for old in ['hardware', 'manufacturing', 'mechanical', 'releases']:
        check('absent legacy directory '+old, not (ROOT/old).exists())
    for key, name, count, headers in [('main','smove-r2-main',35,{'J2','J4'}), ('imu-carrier','smove-imu-carrier',14,{'J5'})]:
        h=ROOT/'PCB'/key; d=h/'dist'
        board=p.LoadBoard(str(h/(name+'.kicad_pcb')))
        fps={f.GetReference():f for f in board.GetFootprints() if not f.IsExcludedFromBOM() and not f.IsDNP()}
        parts=json.loads((h/('parts-main.json' if key=='main' else 'parts.json')).read_text())
        with (d/'BOM.csv').open() as f: bom=list(csv.DictReader(f))
        with (d/'pick-and-place.csv').open() as f: cpl=list(csv.DictReader(f))
        br=[r for row in bom for r in row['Designator'].split(',')]; cr=[row['Designator'] for row in cpl]
        check(key+' unique fitted BOM/CPL/native refs', len(br)==len(set(br))==len(cr)==len(set(cr))==count and set(br)==set(cr)==set(fps))
        check(key+' all headers JLC fitted', headers<=set(br))
        for row in bom:
            refs=row['Designator'].split(',')
            check(key+' BOM quantity '+row['Designator'],len(refs)==int(row['Quantity']))
            for r in refs:
                fields={f.GetName():f.GetText() for f in fps[r].GetFields()}
                check(key+' native CID/MPN '+r, row['LCSC Part #']==fields['LCSC']==parts[r]['jlc'] and row['Manufacturer Part Number']==fields['MPN']==parts[r]['mpn'])
        origin=board.GetDesignSettings().GetAuxOrigin()
        for row in cpl:
            f=fps[row['Designator']]; xy=f.GetPosition()
            check(key+' native placement '+row['Designator'],row['Layer']=='Top' and not f.IsFlipped() and abs(float(row['Mid X'])-(xy.x-origin.x)/1e6)<1e-5 and abs(float(row['Mid Y'])-(origin.y-xy.y)/1e6)<1e-5 and abs((float(row['Rotation'])-f.GetOrientationDegrees()+180)%360-180)<.001)
        with zipfile.ZipFile(d/'gerbers.zip') as z:
            names=z.namelist()
            allowed={'.gtl','.g1','.g2','.gbl','.gts','.gbs','.gto','.gbo','.gm1','.gtp','.drl','.gbrjob'}
            check(key+' fabrication-only ZIP CRC',z.testzip() is None and bool(names) and len(names)==len(set(names)) and all('/' not in n and Path(n).suffix in allowed for n in names))
            check(key+' ZIP/raw Gerbers exact equality',set(names)=={f.name for f in (d/'gerbers').iterdir() if f.is_file()} and all(z.read(n)==(d/'gerbers'/n).read_bytes() for n in names))
        for table in ['sym-lib-table','fp-lib-table']:
            for uri in re.findall(r'\(uri "([^"]+)"\)',(h/table).read_text()):
                check(key+' local library '+uri,Path(uri.replace('${KIPRJMOD}',str(h))).exists())
        for f in [h/(name+'.kicad_pcb'), *h.rglob('*.kicad_mod')]:
            for model in re.findall(r'\(model\s+"([^"]+)"',f.read_text()):
                resolved=model.replace('${KIPRJMOD}',str(h)).replace('${KICAD9_3DMODEL_DIR}','/usr/share/kicad/3dmodels')
                if model.startswith(('${KICAD9_3DMODEL_DIR}', '${KICAD8_3RD_PARTY}')) and not Path(resolved).is_file():
                    unavailable_standard_models.add(model)
                else: check(key+' model '+model,Path(resolved).is_file())
    for folder in [ROOT/'PCB/main',ROOT/'PCB/imu-carrier',ROOT/'housing']:
        manifest=folder/'dist/manifest.json'; actual=inventory(folder)
        if args.seal: dump(manifest,{'manufacturing_release':False,'files':actual})
        check(str(folder.relative_to(ROOT))+' manifest',json.loads(manifest.read_text())['files']==actual)
    with zipfile.ZipFile(ROOT/'housing/smove-r2-enclosure.FCStd') as z:
        check('FreeCAD container CRC and native document',z.testzip() is None and 'Document.xml' in z.namelist())
    for folder in [ROOT/'docs', ROOT/'PCB', ROOT/'housing']:
        for f in folder.rglob('*.md'):
            for url in re.findall(r'\]\(([^)]+)\)',f.read_text()):
                if '://' in url or url.startswith('#'): continue
                check(str(f.relative_to(ROOT))+' link '+url,(f.parent/url.split('#')[0]).exists())
    for url in re.findall(r'\]\(([^)]+)\)',(ROOT/'README.md').read_text()):
        if '://' not in url and not url.startswith('#'):check('root link '+url,(ROOT/url.split('#')[0]).exists())
    out=ROOT/'.cache/verify';out.mkdir(parents=True,exist_ok=True)
    dump(out/'package.json',{'status':'PASS','checks_count':len(checks),'checks':checks,'manufacturing_release':False,'unavailable_standard_models':sorted(unavailable_standard_models),'geometry_reopen':'FCStd ZIP integrity only; not a FreeCAD reopen'})
    print('Standalone deliverables PASS',len(checks),'checks; no bundle created; unavailable optional standard models:',len(unavailable_standard_models))
if __name__=='__main__': main()
