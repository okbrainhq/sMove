#!/usr/bin/python3
"""Seal/recheck this combined review delivery; builtin Python only, never saves CAD/PCB.
Run without args AFTER staging new source/docs to write reports and manifests.
--check verifies the complete manifest without writing anything.
"""
import hashlib,json,subprocess as sp,sys
from pathlib import Path
import xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[3];V=R/'docs/revision-r2/two-part-case';M=V/'manifest.json'
BASE='554e4fe387748bcd6bc3a2d5a674fdfb1e0a80cb';REPAIR='e033031';RECOVERY='0610d60'
def git(*args):return sp.check_output(['git',*args],cwd=R)
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads((R/p).read_text())
def put(p,j):(R/p).write_text(json.dumps(j,indent=2)+'\n')
def paths():return sorted(set(p.decode() for p in git('ls-files','-z','--cached','--others','--exclude-standard').split(b'\0') if p and (R/p.decode()).is_file()))
def nets(path):
    root=ET.parse(R/path).getroot()
    return sorted((n.attrib['name'],sorted((v.attrib['ref'],v.attrib['pin']) for v in n.findall('node'))) for n in root.findall('nets/net'))
checks=[]
def ck(n,ok):checks.append({'check':n,'passed':bool(ok)})
ck('main_unchanged',git('rev-parse','main').decode().strip()==BASE)
ck('repair_parent_is_main_baseline',git('rev-parse',REPAIR+'^').decode().strip()==BASE)
ck('complete_cherry_pick_tree_equals_repair',git('rev-parse',REPAIR+'^{tree}')==git('rev-parse',RECOVERY+'^{tree}'))
ck('recovery_is_ancestor_of_review_head',sp.run(['git','merge-base','--is-ancestor',RECOVERY,'HEAD'],cwd=R).returncode==0)
pcbpaths=[p for p in git('ls-tree','-r','--name-only',REPAIR,'PCB/main').decode().splitlines()]
ck('entire_PCB_main_unchanged_after_recovery',all((R/p).read_bytes()==git('show',REPAIR+':'+p) for p in pcbpaths))
for p in ('inherited-drc.json','inherited-erc.json'):
    j=read('docs/revision-r2/two-part-case/validation/'+p)
    issues=j.get('violations',[])+j.get('unconnected_items',[])+j.get('schematic_parity',[])+[x for s in j.get('sheets',[]) for x in s.get('violations',[])]
    ck('fresh_zero_all_issues:'+p,not issues)
ck('fresh_schematic_net_equivalence',nets('docs/revision-r2/two-part-case/validation/inherited-netlist.xml')==nets('docs/revision-r2/pcb-repair/validation/final-netlist.xml'))
h=read('housing/validation/mechanical.json');g=read('housing/validation/gui-inspection.json')
ck('all_saved_CAD_checks_pass',h['status']=='PASS_GEOMETRIC_PROTOTYPE' and not h['failed'])
ck('real_GUI_macro_checks_pass',g['status']=='PASS_REAL_FREECAD_GUI_CONTROLS')
ck('verified_GUI_native_hash_matches',g['native_sha256']==sha((R/'housing/smove-r2-enclosure.FCStd').read_bytes()))
b=read('housing/validation/build.json')
ck('central_H1_only_no_lead_geometry',b['screw_xy_mm']==b['H1_xy_mm']==[11.8,13.35] and b['lead_geometry']=='NONE_USER_ROUTED_NOT_VERIFIED')
ck('simplified_case_dimensions',all(abs(x-y)<1e-6 for x,y in zip(h['metrics']['current_LWH_mm'],[42,28.8,19.6])))
ck('exactly_two_active_STLs',sorted(p.name for p in (R/'housing/dist').glob('*.stl'))==['base.stl','lid.stl'])
ck('release_holds_retained',not read('housing/status.json')['manufacturing_release'] and not read('housing/status.json')['charging_release'])
if '--check' in sys.argv:
    manifest=json.loads(M.read_text());files=manifest['final_repository_files']
    ck('manifest_exact_repository_file_set',set(files)==set(paths())-{str(M.relative_to(R))})
    ck('all_manifest_SHA256_match',all((R/p).is_file() and sha((R/p).read_bytes())==v['sha256'] for p,v in files.items()))
else:
    focus=['README.md','PCB/main/parts-main.json','PCB/main/native-layout-contract.json','scripts/r2/integrated/sync.py','scripts/r2/integrated/pcb_review_policy.py',
      'scripts/r2/enclosure/generate.py','scripts/r2/enclosure/verify.py','scripts/r2/enclosure/inspection.py','scripts/r2/enclosure/present.py','scripts/r2/enclosure/seal_delivery.py',
      'housing/InspectAssembly.FCMacro','housing/PRINTING-ASSEMBLY.md','housing/BOM.csv','housing/status.json']
    (V/'critical-source.patch').write_bytes(git('diff','--no-ext-diff','--no-color','--unified=0',BASE,'--',*focus))
    (V/'case-revision.patch').write_bytes(git('diff','--no-ext-diff','--no-color','--unified=0','b49ade5','--',*focus))
    put('docs/revision-r2/two-part-case/validation/delivery-checks.json',{
      'status':'PASS' if all(c['passed'] for c in checks) else 'FAIL','checks':checks,'base_main':BASE,
      'original_repair':git('rev-parse',REPAIR).decode().strip(),'complete_recovery_commit':git('rev-parse',RECOVERY).decode().strip(),
      'recovered_tree':git('rev-parse',RECOVERY+'^{tree}').decode().strip(),'PCB_main_files_verified':len(pcbpaths),
      'CAD_checks':len(h['checks']),'dimensions_LWH_mm':[round(v,6) for v in h['metrics']['current_LWH_mm']],'manufacturing_release':False,'merged':False})
    housingfiles=[p for p in paths() if (p.startswith('housing/') or p.startswith('scripts/r2/enclosure/') or p in ('scripts/freecad/bootstrap.py','scripts/freecad/run.py')) and p!='housing/dist/manifest.json']
    put('housing/dist/manifest.json',{'schema':'smove.two-part-housing.manifest.v1','manufacturing_release':False,'printed_parts':['Base','Lid'],
      'pcb_source_sha256':h['pcb_hash'],'files':{p:{'sha256':sha((R/p).read_bytes()),'bytes':(R/p).stat().st_size} for p in housingfiles}})
    inherited=git('diff-tree','--no-commit-id','--name-only','-r',REPAIR).decode().splitlines()
    retired=git('diff','--name-only','--diff-filter=D',BASE).decode().splitlines()
    put(str(M.relative_to(R)),{'schema':'smove.complete-combined-delivery.v1','review_branch':git('branch','--show-current').decode().strip(),
      'main_baseline':BASE,'complete_inherited_repair':git('rev-parse',REPAIR).decode().strip(),'recovered_as':git('rev-parse',RECOVERY).decode().strip(),
      'integration_requirement':'Include complete recovery commit AND subsequent casing commit together. NO MERGE until user review.',
      'manufacturing_release':False,'scope':'Complete final repository file set, including archives; NOT a list of approved fabrication inputs. Active PCB: PCB/main; active case: housing. Failed routing attempts are evidence only.',
      'self_hash_policy':'Only this manifest file excludes its own hash; Git commit identifies it.',
      'inherited_repair_files':{p:{'original_sha256':sha(git('show',REPAIR+':'+p)),'still_present':(R/p).is_file()} for p in inherited},
      'retired_from_main':retired,
      'final_repository_files':{p:{'sha256':sha((R/p).read_bytes()),'bytes':(R/p).stat().st_size} for p in paths() if R/p!=M}})
failed=[c['check'] for c in checks if not c['passed']]
print(json.dumps({'status':'PASS' if not failed else 'FAIL','checks':len(checks),'failed':failed,'PCB_files':len(pcbpaths),'mode':'read-only check' if '--check' in sys.argv else 'sealed'},indent=2))
if failed:sys.exit(1)
