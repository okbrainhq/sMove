#!/usr/bin/python3
"""Read native geometry, verify placement/authorized net ECO, render review diagrams.
Run from anywhere. Reports are placement evidence, not routing/manufacturing release.
"""
from pathlib import Path
import sys, json, subprocess, hashlib, math, csv, tempfile
from collections import Counter
import pcbnew as p
import cairo
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/r2/integrated'))
from sexp import parse, many, one, val, prop
BOARD = ROOT / 'PCB/main/smove-r2-main.kicad_pcb'
OUT = ROOT / 'docs/revision-r2/placement-routing'
BASE = '7128028'
RESERVES = {'M3_NW_RESERVE':(103.15,103.15,3), 'M3_SE_RESERVE':(121.65,126.85,3)}
UI = set('D1 R11 R12 R13 SW2 SW3 R7 R8 R9 R10 C10'.split())
POWER = set('U4 U6 C1 C2 C3 C4 C13 R5 R14 R15 C11 R21 R22 R23'.split())
IMU = set('U2 U3 U5 C5 C6 C7 C8 C9 R16 R17 R18 R19 R20'.split())
COLORS = {'UI':(0.98,.69,.23),'POWER':(.40,.80,.51),'IMU':(.37,.72,.98),'USB':(.74,.53,.96),'FIXED':(.73,.77,.82)}

def xy(pt): return (p.ToMM(pt.x), p.ToMM(pt.y))
def footprints(b): return {f.GetReference():f for f in b.GetFootprints()}
def group(ref):
    if ref in ('U1','J1','J2'):return 'FIXED'
    return 'UI' if ref in UI else 'POWER' if ref in POWER else 'IMU' if ref in IMU else 'USB'
def pose(f):return [*xy(f.GetPosition()),f.GetOrientationDegrees(),f.GetLayerName()]
def pad_geometry(a):
    return [a.GetNumber(), xy(a.GetPosition()), xy(a.GetSize()), xy(a.GetDrillSize()),a.GetOrientationDegrees(),int(a.GetShape()),int(a.GetAttribute()),a.GetLayerSet().FmtBin()]
def mst(b):
    nets={}
    for f in b.GetFootprints():
        for a in f.Pads():
            name=a.GetNetname()
            if not name or name=='GND' or name.startswith('unconnected-'):continue
            nets.setdefault(name,set()).add(xy(a.GetPosition()))
    result={}
    for net,points in nets.items():
        points=set(points); tree={points.pop()};total=0
        while points:
            d,a=min((math.dist(a,c),a) for a in points for c in tree)
            total+=d;tree.add(a);points.remove(a)
        result[net]=round(total,4)
    return result

def draw(board, path, title):
    # Readable native-geometry diagram, not fabrication artwork.
    w,h=1140,1560; surf=cairo.ImageSurface(cairo.FORMAT_ARGB32,w,h);c=cairo.Context(surf)
    c.set_source_rgb(.055,.075,.10);c.paint();scale=35;ox=75;oy=115
    def loc(x,y):return ox+(x-99)*scale,oy+(y-94)*scale
    def text(t,x,y,size=15,color=(.93,.95,.97)):
        c.set_source_rgb(*color);c.select_font_face('DejaVu Sans',cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_NORMAL);c.set_font_size(size)
        ext=c.text_extents(t);c.move_to(x-ext.width/2-ext.x_bearing,y-ext.height/2-ext.y_bearing);c.show_text(t)
    text(title,570,42,24)
    text('Front view | native placement | copper routes/pours omitted',570,78,15)
    for d in board.GetDrawings():
        if d.GetLayer()==p.Edge_Cuts:
            c.set_source_rgb(.9,.93,.96);c.set_line_width(2.2);c.move_to(*loc(*xy(d.GetStart())));c.line_to(*loc(*xy(d.GetEnd())));c.stroke()
    c.set_dash([5,5]);c.set_source_rgba(.55,.73,.86,.45);c.set_line_width(1)
    c.move_to(*loc(112.5,111.5));c.line_to(*loc(112.5,130));c.stroke();c.set_dash([])
    for name,(x,y,r) in RESERVES.items():
        c.new_path();c.set_source_rgba(.12,.85,.76,.10);c.arc(*loc(x,y),r*scale,0,2*math.pi);c.fill_preserve()
        c.set_source_rgb(.2,.86,.78);c.set_line_width(2);c.stroke()
        text('M3 reserve',*loc(x,y-.35),13,(.3,.94,.83));text('NO HOLE',*loc(x,y+.3),11,(.3,.94,.83))
    for f in board.GetFootprints():
        ref=f.GetReference();color=COLORS[group(ref)];f.BuildCourtyardCaches();poly=f.GetCourtyard(p.F_CrtYd)
        for i in range(poly.OutlineCount()):
            pts=poly.COutline(i);c.new_path()
            for j in range(pts.PointCount()):
                q=loc(*xy(pts.CPoint(j)))
                (c.move_to if j==0 else c.line_to)(*q)
            c.close_path();c.set_source_rgba(*color,.14);c.fill_preserve();c.set_source_rgb(*color);c.set_line_width(1.1);c.stroke()
        for a in f.Pads():
            if not a.IsOnLayer(p.F_Cu):continue
            x,y=loc(*xy(a.GetPosition()));sx,sy=xy(a.GetSize());c.save();c.translate(x,y);c.rotate(-math.radians(a.GetOrientationDegrees()))
            c.set_source_rgba(*color,.8)
            if a.GetShape()==p.PAD_SHAPE_CIRCLE:c.arc(0,0,sx*scale/2,0,2*math.pi)
            else:c.rectangle(-sx*scale/2,-sy*scale/2,sx*scale,sy*scale)
            c.fill()
            drill=xy(a.GetDrillSize())
            if max(drill):c.set_source_rgb(.055,.075,.10);c.arc(0,0,max(drill)*scale/2,0,2*math.pi);c.fill()
            c.restore()
        x,y=loc(*xy(f.GetPosition()));size=12 if ref[0] in 'RC' else 16
        if ref=='U1':y-=100;size=22
        if ref=='J1':x+=45;size=22
        # A dark reference badge avoids confusing pad and reference colours.
        c.select_font_face('DejaVu Sans',cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_BOLD);c.set_font_size(size);e=c.text_extents(ref)
        c.set_source_rgba(.035,.045,.055,.86);c.rectangle(x-e.width/2-3,y-size/2-2,e.width+6,size+4);c.fill();text(ref,x,y,size)
    text('25 mm board width | ESP and connector poses fixed',570,1420,16)
    for i,(name,color) in enumerate(COLORS.items()):text(name,130+i*220,1460,16,color)
    text('PLACEMENT REVIEW ONLY - NOT ROUTED / NOT FOR MANUFACTURE',570,1510,18,(1,.53,.40))
    surf.write_to_png(str(path))

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    raw=subprocess.check_output(['git','show',f'{BASE}:PCB/main/smove-r2-main.kicad_pcb'],cwd=ROOT)
    with tempfile.NamedTemporaryFile(suffix='.kicad_pcb') as tmp:
        tmp.write(raw);tmp.flush();before=p.LoadBoard(tmp.name)
    after=p.LoadBoard(str(BOARD));old,new=footprints(before),footprints(after)
    a,z=parse(raw.decode()),parse(BOARD.read_text())
    checks={}
    checks['47_references_and_values_preserved']=set(old)==set(new) and len(new)==47 and all(old[r].GetValue()==new[r].GetValue() for r in old)
    checks['ESP_USB_BAT_poses_fixed']=all(pose(old[r])==pose(new[r]) for r in ('U1','J1','J2'))
    checks['ESP_USB_BAT_pad_geometry_fixed']=all([pad_geometry(pad) for pad in old[r].Pads()]==[pad_geometry(pad) for pad in new[r].Pads()] for r in ('U1','J1','J2'))
    checks['IMU_on_original_centerline_lowered_9mm_not_rotated']=pose(new['U2'])==[112.5,126.5,-90.0,'F.Cu'] and xy(old['U2'].GetPosition())==(112.5,117.5)
    checks['all_parts_still_front']=all(f.GetLayer()==p.F_Cu for f in new.values())
    checks['no_components_replaced']={prop(f,'Reference'):f[1] for f in many(a,'footprint')}=={prop(f,'Reference'):f[1] for f in many(z,'footprint')}
    def local_pads(fp):
        angle=float(one(fp,'at')[3]) if len(one(fp,'at'))>3 else 0
        records=[]
        for pad in many(fp,'pad'):
            at=one(pad,'at');pa=float(at[3]) if len(at)>3 else 0
            geom=[pad[:4],list(map(float,at[1:3])),round((pa-angle)%360,6)]
            geom += [many(pad,k) for k in ('size','drill','layers','roundrect_rratio','chamfer_ratio','chamfer','rect_delta','solder_mask_margin','solder_paste_margin','solder_paste_margin_ratio')]
            records.append(geom)
        return records
    checks['all_local_pad_shapes_sizes_drills_and_layers_preserved']={prop(f,'Reference'):local_pads(f) for f in many(a,'footprint')}=={prop(f,'Reference'):local_pads(f) for f in many(z,'footprint')}
    parts=json.loads((ROOT/'PCB/main/parts-main.json').read_text())
    contract=json.loads((ROOT/'PCB/main/native-layout-contract.json').read_text())
    checks['handoff_placement_metadata_matches_native']=set(parts)==set(new) and all(parts[r]['placement']==pose(new[r])[:3] and contract['placement'][r]==pose(new[r])[:3] for r in new)
    checks['handoff_LED_pin_metadata_matches_native']=parts['U1']['pins']['6']=='LED_R' and parts['U1']['pins']['20'] is None and contract['led_gpio']=={'red':3,'green':7,'blue':10}
    checks['handoff_contract_hash_matches_native']=contract['native_board_sha256']==hashlib.sha256(BOARD.read_bytes()).hexdigest()
    changes=[]
    for r in old:
        oldnets=[(p.GetNumber(),p.GetNetname()) for p in old[r].Pads()]
        newnets=[(p.GetNumber(),p.GetNetname()) for p in new[r].Pads()]
        for (pin,n0),(pin2,n1) in zip(oldnets,newnets):
            if n0!=n1:changes.append([r,pin,n0,n1])
    checks['only_authorized_RED_pin_nets_changed']=sorted(changes)==sorted([
        ['U1','6','unconnected-(U1-GPIO3-Pad6)','/Compute/LED_R'],
        ['U1','20','/Compute/LED_R','unconnected-(U1-GPIO6-Pad20)']])
    checks['outline_layer_count_thickness_retained']=all(many(a,k)==many(z,k) for k in ('gr_line','gr_arc','layers','general','setup'))
    oldrules={val(one(v,'name')[1]):v for v in many(a,'zone') if many(v,'keepout')}
    newrules={val(one(v,'name')[1]):v for v in many(z,'zone') if many(v,'keepout')}
    checks['all_existing_rule_areas_unchanged']=oldrules==newrules
    zone_configs=lambda tree:[[v for v in zone if not (isinstance(v,list) and v[0]=='filled_polygon')] for zone in many(tree,'zone')]
    checks['existing_zone_definitions_retained']=zone_configs(a)==zone_configs(z)
    checks['zone_fills_absent_for_placement_stage']=not any(many(zone,'filled_polygon') for zone in many(z,'zone'))
    checks['obsolete_routes_removed_not_left_on_wrong_pads']=len(list(after.GetTracks()))==0
    # Direct courtyard geometry tests, independent of configurable DRC severity.
    courtyards=[]
    for f in new.values():f.BuildCourtyardCaches();courtyards.append((f.GetReference(),f.GetCourtyard(p.F_CrtYd)))
    overlaps=[]
    for i,(r,c) in enumerate(courtyards):
        for r2,c2 in courtyards[i+1:]:
            if p.SHAPE.Collide(c,c2):overlaps.append([r,r2])
    checks['no_courtyard_overlaps']=not overlaps
    reserve_hits={}
    for name,(x,y,r) in RESERVES.items():
        circle=p.SHAPE_CIRCLE(p.VECTOR2I(p.FromMM(x),p.FromMM(y)),p.FromMM(r));hits=[]
        for ref,f in new.items():
            if p.SHAPE.Collide(circle,f.GetCourtyard(p.F_CrtYd)):hits.append(ref+' courtyard')
            for pad in f.Pads():
                if pad.IsOnLayer(p.F_Cu) and p.SHAPE.Collide(circle,pad.GetEffectiveShape(p.F_Cu)):hits.append(ref+'.'+pad.GetNumber())
        reserve_hits[name]=hits
    checks['both_original_M3_disks_clear']=not any(reserve_hits.values())
    for ext in ('kicad_pro','kicad_dru'):
        rel='PCB/main/smove-r2-main.'+ext
        checks[ext+'_unchanged']=(ROOT/rel).read_bytes()==subprocess.check_output(['git','show',f'{BASE}:{rel}'],cwd=ROOT)
    for name in ('smove-r2-main','usb','power','imu'):
        rel='PCB/main/'+name+'.kicad_sch'
        checks[name+'_schematic_unchanged']=(ROOT/rel).read_bytes()==subprocess.check_output(['git','show',f'{BASE}:{rel}'],cwd=ROOT)
    for kind,args in [('placement-drc',['pcb','drc','--all-track-errors','--schematic-parity']),('erc',['sch','erc'])]:
        source=BOARD if kind=='placement-drc' else BOARD.with_suffix('.kicad_sch')
        subprocess.run(['kicad-cli',*args,'--format','json','--severity-all','-o',str(OUT/(kind+'.json')),str(source)],check=True)
    drc=json.loads((OUT/'placement-drc.json').read_text());erc=json.loads((OUT/'erc.json').read_text())
    checks['no_geometric_DRC_errors']=not any(v['severity']=='error' for v in drc['violations'])
    checks['only_existing_J2_library_warning']=len(drc['violations'])==1 and drc['violations'][0]['type']=='lib_footprint_mismatch' and 'J2' in drc['violations'][0]['items'][0]['description']
    checks['schematic_parity_clean']=not drc['schematic_parity']
    checks['ERC_clean_all_severities']=not any(s.get('violations') for s in erc['sheets'])
    d=lambda fps,r,s:math.dist(xy(fps[r].GetPosition()),xy(fps[s].GetPosition()))
    distances={r+'-'+s:{'before_mm':round(d(old,r,s),3),'after_mm':round(d(new,r,s),3)} for r,s in [('U6','J1'),('U6','U1'),('U6','U4'),('U6','C13'),('U2','U3'),('U2','U5')]}
    m0,m1=mst(before),mst(after)
    metrics={'note':'Euclidean pad MST is a placement proxy, NOT routed length or proof of signal integrity.', 'before_total_mm':round(sum(m0.values()),3),'after_total_mm':round(sum(m1.values()),3),'per_net':{n:{'before_mm':m0.get(n,0),'after_mm':m1.get(n,0)} for n in sorted(m0.keys()|m1.keys())}}
    placement=[]
    for ref in sorted(new):placement.append({'reference':ref,'value':new[ref].GetValue(),'group':group(ref),'before':pose(old[ref]),'after':pose(new[ref])})
    report={'status':'PLACEMENT_PASS_UNROUTED' if all(checks.values()) else 'FAIL','base_commit':BASE,'checks':checks,'board_sha256':hashlib.sha256(BOARD.read_bytes()).hexdigest(),'unconnected_items':len(drc['unconnected_items']),'routed':False,'manufacturing_release':False,'pad_net_changes':changes,'reserve_collisions':reserve_hits,'courtyard_overlaps':overlaps,'distances':distances,'placement_proxy':metrics,'placements':placement}
    (OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    with (OUT/'placements.csv').open('w') as f:
        writer=csv.writer(f);writer.writerow(['reference','value','group','old_x_mm','old_y_mm','old_deg','old_layer','new_x_mm','new_y_mm','new_deg','new_layer'])
        for item in placement:writer.writerow([item['reference'],item['value'],item['group'],*item['before'],*item['after']])
    draw(before,OUT/'before.png','BEFORE - scattered functional groups')
    draw(after,OUT/'placement.png','AFTER - grouped placement candidate')
    print(json.dumps({k:report[k] for k in ('status','checks','unconnected_items','distances')},indent=2))
    return 0 if all(checks.values()) else 1
if __name__=='__main__':raise SystemExit(main())
