#!/usr/bin/env python3
"""Seal/stage the complete compact-wire delivery; verify committed blobs and deletions.
No merge, reset, push or automatic commit. Verification is read-only.
"""
from pathlib import Path
import hashlib,json,subprocess as sp,sys
R=Path(__file__).resolve().parents[3]
BASE='4cb3c32193bda18d624b7974b65162a7a44f69a0'
DIR='docs/revision-r2/solder-wire';MAN=DIR+'/delivery-manifest.json';PATHS=DIR+'/commit-paths.txt'
def git(*args):return sp.check_output(['git',*args],cwd=R)
def sha(data):return hashlib.sha256(data).hexdigest()
def all_names():return set(git('ls-files','--cached','--others','--exclude-standard','-z').decode().strip('\0').split('\0'))
def changed():
 return sorted(set(git('diff','--name-only','--no-renames',BASE,'-z').decode().strip('\0').split('\0'))|set(git('ls-files','--others','--exclude-standard','-z').decode().strip('\0').split('\0'))-{''})
def write(path,data):(R/path).write_text(json.dumps(data,indent=2)+'\n')
def allowed(n):return n.startswith(('PCB/main/','housing/','scripts/r2/integrated/','scripts/r2/enclosure/','scripts/r2/final/','docs/revision-r2/solder-wire/')) or n in ('README.md','PCB/README.md','docs/revision-r2/integrated/README.md','docs/revision-r2/integrated/RADIO-BATTERY.md')
def seal():
 assert git('rev-parse','HEAD').decode().strip()==BASE,'Seal against original current-main base only'
 for folder in ('PCB/main','housing'):
  files={n:sha((R/n).read_bytes()) for n in sorted(all_names()) if n.startswith(folder+'/') and (R/n).is_file() and n!=folder+'/dist/manifest.json'}
  write(folder+'/dist/manifest.json',dict(manufacturing_release=False,scope='Current compact PTH-wire prototype; any historical backup/report files retained as provenance only',files=files))
 (R/MAN).write_text('{}\n');(R/PATHS).write_text('')
 paths=changed();assert all(allowed(n) for n in paths),[n for n in paths if not allowed(n)]
 (R/PATHS).write_text('\n'.join(paths)+'\n')
 names=all_names();files={n:sha((R/n).read_bytes()) for n in sorted(names) if allowed(n) and (R/n).is_file() and n!=MAN}
 changes=[]
 for n in paths:
  old=sp.run(['git','cat-file','-e',BASE+':'+n],cwd=R,stdout=sp.DEVNULL,stderr=sp.DEVNULL).returncode==0
  exists=(R/n).is_file();changes.append(dict(path=n,status='M' if old and exists else 'D' if old else 'A',before_sha256=sha(git('show',BASE+':'+n)) if old else None,after_sha256=files.get(n),self_hashed_by_git_tree=n==MAN))
 write(MAN,dict(schema='smove.complete-workspace-delivery.v1',baseline_commit=BASE,branch=git('branch','--show-current').decode().strip(),manufacturing_release=False,changed_path_count=len(paths),content_hash_file_count=len(files),changed_paths=changes,files=files,self_hash_note='Only this manifest excludes its own SHA256 to avoid recursion. Its staged/committed blob is byte-verified against the worktree; report its independent SHA256 alongside commit ID.',verification='Run seal_wire.py verify HEAD after committing, or verify --worktree after integrating the COMPLETE commit. No partial path import.'))
 # Explicitly stage every intended path, including deletions and all untracked deliverables.
 sp.run(['git','add','--',*paths],cwd=R,check=True)
 observed=sorted(git('diff','--cached','--name-only','--no-renames',BASE,'-z').decode().strip('\0').split('\0'))
 assert observed==paths,(set(observed)^set(paths))
 for n in paths:
  if (R/n).is_file():assert git('show',':'+n)==(R/n).read_bytes(),n
  else:assert sp.run(['git','cat-file','-e',':'+n],cwd=R,stdout=sp.DEVNULL,stderr=sp.DEVNULL).returncode!=0,n
 print(json.dumps(dict(status='PASS_COMPLETE_INDEX',changed_paths=len(paths),hashed_files=len(files),manifest_sha256=sha((R/MAN).read_bytes()),index_tree=git('write-tree').decode().strip()),indent=2))
def verify(ref):
 worktree=ref=='--worktree';raw=(R/MAN).read_bytes() if worktree else git('show',ref+':'+MAN);m=json.loads(raw);fail=[]
 for n,digest in m['files'].items():
  try:data=(R/n).read_bytes() if worktree else git('show',ref+':'+n)
  except Exception:fail.append(n+':missing');continue
  if sha(data)!=digest:fail.append(n+':hash')
 for row in m['changed_paths']:
  n=row['path']
  if row['status']=='D':
   absent=not (R/n).exists() if worktree else sp.run(['git','cat-file','-e',ref+':'+n],cwd=R,stdout=sp.DEVNULL,stderr=sp.DEVNULL).returncode!=0
   if not absent:fail.append(n+':deletion missing')
 if not worktree:
  actual=sorted(git('diff','--name-only','--no-renames',m['baseline_commit'],ref,'-z').decode().strip('\0').split('\0'));expected=sorted(x['path'] for x in m['changed_paths'])
  if actual!=expected:fail.append('commit path-set mismatch: '+str(set(actual)^set(expected)))
  if git('show',ref+':'+MAN)!=(R/MAN).read_bytes():fail.append('manifest committed blob differs from workspace')
 result=dict(status='PASS' if not fail else 'FAIL',commit=None if worktree else git('rev-parse',ref).decode().strip(),changed_paths=m['changed_path_count'],hashed_files=len(m['files']),verified_deletions=sum(x['status']=='D' for x in m['changed_paths']),manifest_sha256=sha(raw),failures=fail)
 print(json.dumps(result,indent=2));assert not fail
if __name__=='__main__':
 if sys.argv[1:]==['seal']:seal()
 elif len(sys.argv)==3 and sys.argv[1]=='verify':verify(sys.argv[2])
 else:raise SystemExit('Usage: seal_wire.py seal | verify HEAD | verify --worktree')
