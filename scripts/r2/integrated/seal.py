#!/usr/bin/env python3
"""Scoped prototype manifests; never asserts release or fabricates missing historical files."""
from pathlib import Path
import json,hashlib,subprocess as sp
R=Path(__file__).resolve().parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def selected(folder):
 return sorted(p for p in folder.rglob('*') if p.is_file() and not any(v in p.parts for v in ('__pycache__',)) and p.name!='manifest.json' and not p.name.startswith('~') and sp.run(['git','check-ignore','-q',str(p.relative_to(R))],cwd=R).returncode!=0 and not p.name.endswith(('.lck','.pyc','.FCBak','.kicad_prl','~')))
for base in ['PCB/main','housing']:
 files=selected(R/base)
 j=dict(manufacturing_release=False,scope='Integrated engineering prototype; fit/battery gates OPEN',files={str(p.relative_to(R)):sha(p) for p in files})
 (R/base/'dist/manifest.json').write_text(json.dumps(j,indent=2)+'\n')
# Carrier is historical; retain its export bytes but update README hash if manifest covered it.
p=R/'PCB/imu-carrier/dist/manifest.json';j=json.loads(p.read_text())
for name in j['files']:
 if name=='PCB/imu-carrier/README.md':j['files'][name]=sha(R/name)
p.write_text(json.dumps(j,indent=2)+'\n')
files=[p for folder in ['PCB/main','housing','scripts/r2/integrated','scripts/r2/enclosure'] for p in selected(R/folder)]+[R/'scripts/r2/final/export.py']
v=R/'docs/revision-r2/integrated/validation';(v/'delivery-manifest.json').write_text(json.dumps(dict(manufacturing_release=False,baseline_commit=sp.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),files={str(p.relative_to(R)):sha(p) for p in files}),indent=2)+'\n')
for f in [R/'PCB/main/dist/manifest.json',R/'housing/dist/manifest.json',v/'delivery-manifest.json']:
 for path,h in json.loads(f.read_text())['files'].items():assert sha(R/path)==h,path
print('Scoped manifests sealed and rechecked; release remains false')
