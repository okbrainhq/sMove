"""Read-only native baseline comparison plus export/drill checks; no router.
Baseline defaults to current branch HEAD (aligned predecessor). Override --baseline
if this revision is later committed. Reports are reproducible from recorded git ID.
"""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R/'scripts/r2/integrated'))
from sexp import parse,many,one,prop
parser=argparse.ArgumentParser();parser.add_argument('--baseline',default='HEAD');args=parser.parse_args()
base=subprocess.check_output(['git','rev-parse',args.baseline],cwd=R,text=True).strip()
path='PCB/main/smove-r2-main.kicad_pcb';old=parse(subprocess.check_output(['git','show',base+':'+path],cwd=R,text=True));new=parse((R/path).read_text())
checks={}
def canonical(items):return sorted(json.dumps(i,sort_keys=True) for i in items)
for key in ('segment','via','arc','gr_line','gr_arc','setup','layers','net'):
 checks[key+'_identical']=canonical(many(old,key))==canonical(many(new,key))
fo={prop(x,'Reference'):x for x in many(old,'footprint')};fn={prop(x,'Reference'):x for x in many(new,'footprint')}
checks['only_H1_removed']=set(fo)-set(fn)=={'H1'} and not set(fn)-set(fo)
checks['all_remaining_footprints_byte_token_equivalent']=all(fo[r]==fn[r] for r in fn)
def rulezones(ast):
 return {one(z,'name')[1]:z for z in many(ast,'zone') if many(z,'keepout')}
zo=rulezones(old);zn=rulezones(new)
checks['only_H1_rule_removed']=set(zo)-set(zn)=={'"H1_M3_NO_COPPER"'} and all(zo[n]==zn[n] for n in zn)
checks['antenna_rule_retained']='"ANTENNA_ALL_LAYERS"' in zn
# USB component locating pegs (two 0.65mm NPTH) remain, NOT enclosure mounting holes.
drill=(R/'PCB/main/dist/gerbers/smove-r2-main-NPTH.drl').read_text()
checks['only_USB_component_NPTH_remain']= [line for line in drill.splitlines() if line.startswith(('X','Y'))]==['X18.5Y21.09','X18.5Y15.31'] and 'C3.200' not in drill and 'T1C0.650' in drill
inv=json.loads((R/'docs/revision-r2/screwless/pcb-invariants.json').read_text())
checks['protected_sources_identical']=all(hashlib.sha256((R/f).read_bytes()).hexdigest()==h for f,h in inv['protected_hashes'].items())
for kind in ('drc','erc'):
 j=json.loads((R/f'docs/revision-r2/screwless/{kind}.json').read_text())
 checks[kind+'_clean']=(not j['violations'] and not j['unconnected_items'] and not j['schematic_parity']) if kind=='drc' else all(not sh['violations'] for sh in j['sheets'])
report={'result':'PASS' if all(checks.values()) else 'FAIL','baseline_commit':base,'board_sha256':hashlib.sha256((R/path).read_bytes()).hexdigest(),'checks':checks,'track_segments':len(many(new,'segment')),'vias':len(many(new,'via')),'retained_footprints':len(fn),'scope':'Complete track/via and remaining footprint token trees; zones refilled; frozen schematic/rules. Configured DRC/ERC is not blanket electrical release.'}
(R/'docs/revision-r2/screwless/native-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2));assert report['result']=='PASS'
