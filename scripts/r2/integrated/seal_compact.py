#!/usr/bin/python3
"""Seal current compact delivery; no CAD mutations and no Git commit/merge.
Validate native/export report source hashes, placement/BOM/ZIP coherence, then
write artifact manifests. Full-repository delivery-manifest is made at staging.
"""
from pathlib import Path
import hashlib,json,csv,zipfile,subprocess as sp
import pcbnew as p
from PIL import Image,ImageDraw,ImageFont,ImageChops
R=Path(__file__).resolve().parents[3];H=R/'PCB/main';O=R/'housing';E=R/'docs/revision-r2/compact-placement';V=E/'validation'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def write(path,j):path.write_text(json.dumps(j,indent=2)+'\n')
checks=[]
def ck(n,v):checks.append(dict(check=n,passed=bool(v)));assert v,n
board=H/'smove-r2-main.kicad_pcb';native=O/'smove-r2-enclosure.FCStd';parts=json.loads((H/'parts-main.json').read_text());b=p.LoadBoard(str(board));fps={f.GetReference():f for f in b.GetFootprints()}
elec=json.loads((V/'electrical.json').read_text());ck('electrical_assertions',elec['status']=='PASS' and not elec['failures'])
for name in ('baseline-drc','post-drc'):
 j=json.loads((V/(name+'.json')).read_text());ck(name,not j['violations'] and not j['unconnected_items'] and not j['schematic_parity'])
for name in ('baseline-erc','post-erc'):
 j=json.loads((V/(name+'.json')).read_text());ck(name,not any(s.get('violations') for s in j['sheets']))
for name in ('mechanical','closure-insertion','gui-inspection','battery-insertion'):
 j=json.loads((O/'validation'/(name+'.json')).read_text());ck(name,j['status'].startswith('PASS'))
 if 'native_sha256' in j:ck(name+':native_hash',j['native_sha256']==sha(native))
 if 'sources' in j:
  for f,h in j['sources'].items():ck(name+':source:'+f,sha(R/f)==h)
 if 'source_sha256' in j:
  for f,h in j['source_sha256'].items():ck(name+':generator:'+f,sha(R/f)==h)
ex=json.loads((V/'exports.json').read_text())
for f,h in ex['sources'].items():ck('export-source:'+f,sha(R/f)==h)
for f,h in ex['artifacts'].items():ck('export-artifact:'+f,sha(R/f)==h)
ck('native_rules_unchanged',all((H/f).read_bytes()==sp.check_output(['git','show','f8c7ef6:PCB/main/'+f]) for f in ('smove-r2-main.kicad_pro','smove-r2-main.kicad_dru')))
placements=json.loads((H/'dist/assembly-placements.json').read_text());ck('46_electronic_CPL_no_J2',len(placements['parts'])==46 and not {'J2','H1','H2'}&{r['reference'] for r in placements['parts']})
origin=placements['aux_origin_native_mm']
for rec in placements['parts']:
 f=fps[rec['reference']];x,y=p.ToMM(f.GetPosition());ck('CPL:'+f.GetReference(),rec['xy_mm']==[round(x-origin[0],6),round(origin[1]-y,6)] and abs(rec['rotation_deg']-f.GetOrientationDegrees()%360)<1e-5 and rec['mpn']==parts[f.GetReference()]['mpn'])
with (H/'dist/BOM.csv').open() as f:ck('BOM_46',sum(int(r['Quantity']) for r in csv.DictReader(f))==46)
with zipfile.ZipFile(H/'dist/gerbers.zip') as z:
 ck('gerber_ZIP_all_members',set(z.namelist())=={f.name for f in (H/'dist/gerbers').iterdir()})
 for n in z.namelist():ck('ZIP:'+n,z.read(n)==(H/'dist/gerbers'/n).read_bytes())
ck('all_rigid_contact_lands',json.loads((V/'retention.json').read_text())['status']=='PASS')
# Current/before images are composites of actual exports, not recreated layouts.
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',25);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
canvas=Image.new('RGB',(1200,990),'white');draw=ImageDraw.Draw(canvas)
for i,(path,title,dim) in enumerate([(E/'images/before-pcb.png','BEFORE | f8c7ef6','25 x 35.5 mm'),(H/'dist/top-3d.png','AFTER | compact keyed','25 x 30 mm')]):
 im=Image.open(path).convert('RGB');box=im.convert('L').point(lambda x:255 if x>25 else 0).getbbox();im=im.crop(box);im=im.resize((500,round(im.height*500/im.width)));canvas.paste(im,(50+i*600,110));draw.text((50+i*600,20),title,font=font,fill='black');draw.text((50+i*600,58),dim,font=font,fill='black')
draw.text((25,900),'Actual KiCad exports, normalized to the same nominal PCB width.',font=small,fill='black');draw.text((25,930),'Installed-model renders omit unavailable bodies; pads/outline are native.',font=small,fill='black');canvas.save(E/'images/pcb-comparison.png')
canvas=Image.new('RGB',(1800,710),'white');draw=ImageDraw.Draw(canvas)
for i,(path,title) in enumerate([(E/'images/before-housing.png','BEFORE | 46.8 x 29.4 x 19.6 mm'),(O/'dist/exploded.png','AFTER | 44.8 x 29.4 x 19.6 mm')]):
 im=Image.open(path).convert('RGB');im.thumbnail((890,590));canvas.paste(im,(i*900,70));draw.text((20+i*900,20),title,font=font,fill='black')
draw.text((25,665),'Native FreeCAD exploded views (not common scale). Dimensions include recessed M3x8 hardware.',font=small,fill='black');canvas.save(E/'images/housing-comparison.png')
with (E/'review/placements.csv').open('w',newline='') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(['Reference','Before X','Before Y','Before deg','After X','After Y','After deg']);w.writerows([[r['ref'],*r['before'],*r['after']] for r in elec['changed_placements']])
for folder in (H/'dist',O/'dist'):
 write(folder/'manifest.json',dict(schema='smove.compact-placement.artifacts.v1',manufacturing_release=False,native_sources={str(f.relative_to(R)):sha(f) for f in (board,native,H/'interface.json',H/'parts-main.json')},artifacts={str(f.relative_to(R)):sha(f) for f in sorted(folder.rglob('*')) if f.is_file() and f.name!='manifest.json'}))
write(O/'status.json',dict(status='PASS_NOMINAL_CAD_SCREENS',manufacturing_release=False,charging_release=False,dimensions_LWH_including_M3x8_mm=[44.8,29.4,19.6],mechanical='one M3, positive corner keys and two captured lid hooks',physical_qualification='NOT PERFORMED; see PRINTING-ASSEMBLY.md'))
write(V/'toolchain.json',dict(kicad=sp.check_output(['kicad-cli','version'],text=True).strip(),freecad_lock_sha256=sha(O/'toolchain.lock.json'),freerouting_source='https://github.com/freerouting/freerouting/releases/tag/v1.9.0',freerouting_archive_sha256=sha(R/'.tools/freerouting/release.zip'),methods=['KiCad native Python/CLI','Freerouting GUI/CLI DSN/SES with analytics disabled','clearance-aware Python completion, no In1 signal tracks','actual FreeCAD GUI and Qt controls','Ubuntu desktop observation'],no_native_KiCad_GUI_routing_claim=True))
write(V/'delivery.json',dict(status='PASS',checks=checks,check_count=len(checks),manufacturing_release=False,native_board_sha256=sha(board),native_FreeCAD_sha256=sha(native),rule_waivers_added=0,scoped_remaining_gates='Physical print/rigidity/torque/creep, complete protected pack and charging, strain-relief pull/flex, USB SI/reliability, RF/magnetic/thermal qualification.'))
print('PASS delivery coherence',len(checks),'checks')
