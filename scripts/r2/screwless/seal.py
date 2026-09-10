"""Seal current screwless evidence and manifests, without merging or releasing.
Run after PCB exports, both CAD wall builds, rendering and check_native.py.
"""
import hashlib,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[3];H=R/'housing';O=R/'docs/revision-r2/screwless'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def read(f):return json.loads(f.read_text())
def write(f,j):f.write_text(json.dumps(j,indent=2)+'\n')
pcb=R/'PCB/main/smove-r2-main.kicad_pcb';native=H/'smove-r2-enclosure.FCStd'
a=read(H/'validation/mechanical.json');b=read(H/'validation/wall-1.2.json');n=read(H/'validation/native-parameter.json');v=read(O/'native-verification.json');g=read(H/'validation/renders.json')
assert all(x['result']=='PASS' for x in [a,b,n,v,g])
assert all(x['pcb_sha256']==sha(pcb) for x in [a,b]) and v['board_sha256']==sha(pcb)
assert n['native_sha256']==g['native_sha256']==sha(native)
assert a['wall_mm']==.8 and b['wall_mm']==1.2
assert not any((H/'dist'/name).exists() for name in ['base.stl','lid.stl','print-pair.png'])
assert sorted(p.name for p in (H/'dist').glob('*.stl'))==['bottom-cover.stl','midframe.stl','top-cover.stl']
limits=['Actual complete pack/lead exit/swelling/protection/charger suitability unknown or unqualified','Print support removal, snap insertion/extraction force, fit, creep, fatigue, impact and physical USB/button/LED access','Film/adhesive insulation and chemical compatibility; PCB deflection/IMU stability','Pack-to-west-entry wiring, wire bend rating, pull/flex restraint and pinch/polarity checks','On-body RF, magnetometer and thermal qualification; no full 15mm all-direction RF claim']
status=dict(schema='smove.screwless.status.v1',status='CAD_REVIEW_PHYSICAL_RELEASE_HELD',manufacturing_release=False,charging_release=False,physical_fit_proven=False,merge_authorized=False,merge_performed=False,advisor_used=False,printed_parts=['Midframe','Top cover','Bottom cover'],outer_wall_mm=.8,external_LWH_mm=[a['dimensions_XYZ_mm'][1],a['dimensions_XYZ_mm'][0],a['dimensions_XYZ_mm'][2]],pcb_sha256=sha(pcb),closure='Sleeve plus short ramped snap rails; no screws/nuts/inserts or PCB enclosure mounting holes',wire='Explicit west passage and conditional two OD1.2/R2 lead envelopes reaching BAT; vendor pack-to-entry connection unqualified',open_gates=limits)
write(H/'status.json',status)
write(O/'summary.json',dict(result='PASS_CAD_ONLY',mechanical_checks_per_wall=len(a['checks']),native_checks=len(n['checks']),pcb_checks=len(v['checks']),configured_drc=0,configured_erc=0,unconnected=0,parity=0,material_volume_cm3={'.8':sum(p['volume_mm3'] for p in a['parts'].values())/1000,'1.2':sum(p['volume_mm3'] for p in b['parts'].values())/1000},limits=limits))
# Preserve inherited rule severity scope in current evidence; no silent default suppression changes.
export=read(R/'.cache/export/main-exports.json')
write(O/'electrical-rule-scope.json',{k:export[k] for k in ['configured_ERC_DRC','severity_scope','ignored_defaults','drc_exclusions']})
for folder,source_paths in [(R/'PCB/main/dist',[pcb,R/'PCB/main/interface.json',R/'PCB/main/native-layout-contract.json',R/'scripts/r2/final/export.py']), (H/'dist',[native,H/'screwless.json',R/'scripts/r2/enclosure/screwless.py',H/'render.py',H/'entry.py'])]:
 write(folder/'manifest.json',dict(revision='screwless',manufacturing_release=False,charging_release=False,pcb_sha256=sha(pcb),sources={str(p.relative_to(R)):sha(p) for p in source_paths},artifacts={str(p.relative_to(R)):sha(p) for p in sorted(folder.rglob('*')) if p.is_file() and p.name!='manifest.json'}))
paths=set(subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=R,text=True).splitlines()+subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=R,text=True).splitlines())
paths.update(['docs/revision-r2/screwless/changed-paths.txt','docs/revision-r2/screwless/delivery-manifest.json'])
(O/'changed-paths.txt').write_text('\n'.join(sorted(paths))+'\n')
files=[p for folder in [H,O] for p in folder.rglob('*') if p.is_file() and not p.name.endswith(('.FCBak','.pyc')) and p.name!='delivery-manifest.json']
write(O/'delivery-manifest.json',dict(revision='screwless',baseline=v['baseline_commit'],status=status,artifacts={str(p.relative_to(R)):sha(p) for p in sorted(files)},pcb_manifest_sha256=sha(R/'PCB/main/dist/manifest.json')))
print('PASS: current manifests sealed; physical/charging/manufacturing release=false; no merge.')
