"""Seal enclosure-only evidence; --check is read-only. Never modifies PCB files."""
import hashlib,json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def git(*args):return subprocess.check_output(['git',*args],cwd=R)
def sha(b):return hashlib.sha256(b).hexdigest()
def put(p,d): (R/p).write_text(json.dumps(d,indent=2)+'\n')
M='housing/dist/manifest.json';P='housing/validation/pcb-preservation.json'
if '--check' in sys.argv:
 m=json.loads((R/M).read_text())
 assert all(sha((R/p).read_bytes())==v['sha256'] for p,v in m['files'].items())
 proof=json.loads((R/P).read_text())
 assert all(sha((R/p).read_bytes())==v['baseline_sha256']==v['after_sha256'] for p,v in proof['files'].items())
 print('PASS manifest hashes and PCB preservation:',len(m['files']),'delivery files;',len(proof['files']),'PCB files')
else:
 base=git('rev-parse','HEAD').decode().strip()
 paths=git('ls-tree','-r','--name-only',base,'PCB').decode().splitlines()
 files={p:dict(baseline_sha256=sha(git('show',base+':'+p)),after_sha256=sha((R/p).read_bytes())) for p in paths}
 assert all(v['baseline_sha256']==v['after_sha256'] for v in files.values())
 assert not git('status','--porcelain','--','PCB').strip()
 put(P,dict(result='PASS',baseline_commit=base,scope='Every tracked PCB file including schematic, routing, copper exclusions and exports; no PCB regeneration',file_count=len(files),files=files))
 for name in ('mechanical','wall-1.2','native-parameter','prototype','renders'):
  assert json.loads((R/f'housing/validation/{name}.json').read_text())['result']=='PASS'
 paths=git('ls-files','--cached','--others','--exclude-standard').decode().splitlines()
 paths=sorted(set(p for p in paths if (p.startswith('housing/') or p.startswith('scripts/r2/enclosure/') or p=='README.md') and p!=M and (R/p).is_file()))
 put(M,dict(schema='smove.enclosure-only.rf-prototype.v1',status='RF TEST PROTOTYPE',manufacturing_release=False,charging_release=False,full_espressif_housing_clearance_compliance=False,printed_parts=['Midframe','Top cover','Bottom cover'],self_hash_policy='Manifest excludes itself',files={p:dict(sha256=sha((R/p).read_bytes()),bytes=(R/p).stat().st_size) for p in paths}))
 print('PASS sealed',len(paths),'files; unchanged PCB files',len(files))
