"""Targeted ECO: remove only H1 and its copper rule area, then refill. No router.
Run once on aligned predecessor. Already-screwless input is checked without saving.
"""
import hashlib,json,subprocess
from pathlib import Path
import pcbnew as p
R=Path(__file__).resolve().parents[3]; H=R/'PCB/main'; O=R/'docs/revision-r2/screwless'; O.mkdir(exist_ok=True)
bp=H/'smove-r2-main.kicad_pcb'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def state(b):
 return {'tracks':sorted((t.m_Uuid.AsString(),t.GetNetname(),int(t.GetLayer()),tuple(p.ToMM(t.GetStart())),tuple(p.ToMM(t.GetEnd())),(t.GetWidth(t.GetLayer()) if isinstance(t,p.PCB_VIA) else t.GetWidth())) for t in b.GetTracks()),'pads':sorted((f.GetReference(),q.GetNumber(),q.GetNetname(),tuple(p.ToMM(q.GetPosition())),tuple(p.ToMM(q.GetSize())),tuple(p.ToMM(q.GetDrillSize()))) for f in b.GetFootprints() if f.GetReference()!='H1' for q in f.Pads()),'poses':sorted((f.GetReference(),tuple(p.ToMM(f.GetPosition())),f.GetOrientationDegrees()) for f in b.GetFootprints() if f.GetReference()!='H1')}
b=p.LoadBoard(str(bp)); before=state(b); oldhash=sha(bp)
protected={str(f.relative_to(R)):sha(f) for f in [*H.glob('*.kicad_sch'),H/'smove-r2-main.kicad_dru',H/'smove-r2-main.kicad_pro']}
holes=[f for f in b.GetFootprints() if f.GetReference().startswith('H')]
assert not holes or [f.GetReference() for f in holes]==['H1']
if holes:
 b.Remove(holes[0]);zones=[z for z in b.Zones() if z.GetZoneName()=='H1_M3_NO_COPPER'];assert len(zones)==1
 b.Remove(zones[0]);p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(bp),b)
assert state(p.LoadBoard(str(bp)))==before
assert all(sha(R/f)==h for f,h in protected.items())
j=json.loads((H/'interface.json').read_text());j['geometry_sha256']=sha(bp)
j['status']='SCREWLESS THREE-PIECE CAD REVIEW; NOT RELEASED'
j['mounting']={'holes_native_xy_mm':{},'scheme':'No mounting hardware or holes. Midframe edge locators and insulated underside lands; optional controlled adhesive. No PCB/pouch clamping.','release_blocker':'Physical support, button deflection, creep and adhesive qualification remain open.'}
j['retention_policy']={'status':'CAD_REVIEW_ONLY','contacts':'Insulated underside support lands and perimeter locating clearance. Copper-free southern corners retained as dielectric contact reserves, not hardware.'}
j['housing_compatibility']={'status':'SCREWLESS_CAD_REVIEW','reason':'See housing/validation and docs/revision-r2/screwless; physical fit not proven.'}
j['change_policy']='Native PCB canonical. Do not run legacy routing/sync generators. See scripts/r2/screwless/pcb.py and housing/README.md.'
j['battery_wire']['strain_relief']='West-side midframe passage and adhesive strain-relief land; measure pack lead exit and qualify pull/flex. Solder is not strain relief.'
(H/'interface.json').write_text(json.dumps(j,indent=2)+'\n')
c=json.loads((H/'native-layout-contract.json').read_text());c['mounting']=j['mounting'];(H/'native-layout-contract.json').write_text(json.dumps(c,indent=2)+'\n')
if holes:
 (O/'pcb-invariants.json').write_text(json.dumps({'before_sha256':oldhash,'after_sha256':sha(bp),'unchanged_tracks_vias':len(before['tracks']),'unchanged_pad_records':len(before['pads']),'unchanged_poses':len(before['poses']),'protected_hashes':protected,'removed':['H1 footprint including NPTH','H1_M3_NO_COPPER rule area'],'routing':'All existing tracks/vias preserved; copper zones refilled into reclaimed area. No routing generator run.','result':'PASS'},indent=2)+'\n')
for typ,src in [('pcb',bp),('sch',H/'smove-r2-main.kicad_sch')]:
 args=['kicad-cli',typ,'drc' if typ=='pcb' else 'erc','--format','json','--severity-all','--exit-code-violations','-o',str(O/('drc.json' if typ=='pcb' else 'erc.json'))]
 if typ=='pcb':args+=['--all-track-errors','--schematic-parity']
 subprocess.run(args+[str(src)],check=True)
print('PASS targeted ECO, routing/pads/poses/rules/schematic preserved; fresh DRC/ERC')
