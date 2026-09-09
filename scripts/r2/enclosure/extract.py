#!/usr/bin/env python3
"""Read ONLY project-local frozen inputs; independently inspect poses, pads, holes and edges."""
import hashlib
import json
import math
from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'housing'
(ROOT/'.cache/housing').mkdir(parents=True,exist_ok=True)
EXPECTED = {'main': None}  # Integrated build only. Old carrier is frozen provenance, not assembled.

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def xy(p): return [round(p.x / 1e6, 6), round(p.y / 1e6, 6)]
def near(a, b): return all(abs(x-y) < 0.00001 for x, y in zip(a,b))
def angle(a,b): return abs((a-b+180)%360-180) < 0.00001

def extract():
    report = {'schema': 'smove.r2.case.inputs.v1', 'boards': {}, 'warnings': []}
    for name in EXPECTED:
        folder = ROOT/'PCB'/name
        ip = folder/'interface.json'; bp = next(folder.glob('*.kicad_pcb'))
        d = json.loads(ip.read_text()); b = pcbnew.LoadBoard(str(bp))
        origin_y = 139 if name == 'main' else 120
        def local(p):
            x,y=xy(p); return [round(x-100,6),round(origin_y-y,6)]
        contracts = d['components'] if name == 'main' else {c['ref']:c for c in d['components']}
        fps = {}
        for f in b.GetFootprints():
            ref = f.GetReference(); p = xy(f.GetPosition()); c = contracts.get(ref)
            rec = {'native_xy':p, 'local_xy':local(f.GetPosition()), 'angle_deg':f.GetOrientationDegrees(),
                   'side': 'bottom' if f.IsFlipped() else 'top', 'pads':[]}
            assert rec['side'] == 'top', ref
            if c:
                assert near(p if name=='main' else rec['local_xy'], c['anchor_native_xy_mm'] if name=='main' else c['center_mm']), (name,ref,'POSE')
                assert angle(rec['angle_deg'],c['rotation_ccw_deg']), (name,ref,'ANGLE')
            for p in f.Pads():
                bb=p.GetBoundingBox()
                rec['pads'].append({'number':p.GetNumber(), 'local_xy':local(p.GetPosition()), 'native_xy':xy(p.GetPosition()),
                                   'drill_mm':xy(p.GetDrillSize()), 'size_mm':xy(p.GetSize()),
                                   'angle_deg':p.GetOrientationDegrees(), 'attribute':int(p.GetAttribute()),
                                   'aabb_native':[bb.GetX()/1e6,bb.GetY()/1e6,bb.GetRight()/1e6,bb.GetBottom()/1e6]})
            if name=='imu-carrier' and c:
                for expected in c['pads']:
                    assert any(p['number']==expected['number'] and near(p['local_xy'],expected['center_mm']) and near(p['size_mm'],expected['size_mm']) and angle(p['angle_deg'],expected['rotation_deg']) for p in rec['pads']), (ref,'PAD')
            if name=='main' and c:
                env=c['body_aabb_native_xy_mm']
                if env == [0,0,0,0]:
                    env=c['courtyard_native_xy_mm']
                    report['warnings'].append(f'{name}/{ref}: zero body AABB in contract; full declared courtyard used conservatively, not zero-sized part.')
                rec['envelope_xy']=[env[0]-100,origin_y-env[3],env[2]-100,origin_y-env[1]]
                rec['z_mm']=c['z_mm_from_board_bottom'];rec['fitted']=c['fitted']
            elif c:
                rec['envelope_xy']=c['envelope_xy_mm'];rec['z_mm']=[0,c['height_above_pcb_mm']];rec['fitted']=True
            fps[ref]=rec
        assert set(contracts)<=set(fps)
        holes=[]
        if name=='imu-carrier':
            assert len(fps)==16 and len(contracts)==14
            for h in d['mounting_features']:
                p=fps[h['ref']]['pads'][0]
                assert near(p['local_xy'],h['center_mm']) and near(p['drill_mm'],h['drill_mm']) and p['attribute']==pcbnew.PAD_ATTRIB_NPTH
                holes.append({'ref':h['ref'],'xy':p['local_xy'],'drill_mm':p['drill_mm']})
        else:
            assert len(fps)==48 and sum(c['fitted'] for c in contracts.values())==46
            for ref,xy0 in d['mounting']['holes_native_xy_mm'].items():
                pad=fps[ref]['pads'][0];assert near(pad['native_xy'],xy0) and near(pad['drill_mm'],[3.2,3.2]) and pad['attribute']==pcbnew.PAD_ATTRIB_NPTH
                holes.append(dict(ref=ref,xy=pad['local_xy'],drill_mm=pad['drill_mm']))
            for ref,a in d['anchors'].items():
                if 'center_native_xy_mm' in a: assert near(fps[ref]['native_xy'],a['center_native_xy_mm'])
                for num,p in a.get('pins',{}).items():
                    assert any(q['number']==num and near(q['native_xy'],p['native_xy_mm']) for q in fps[ref]['pads']), (ref,num)
        edges=[]
        for e in b.GetDrawings():
            if e.GetLayer()==pcbnew.Edge_Cuts: edges.append([local(e.GetStart()),local(e.GetEnd())])
        expected_outline = [[round(x-100,6),round(139-y,6)] for x,y in d['outline_native_xy_mm']]
        observed={tuple(p) for e in edges for p in e}
        assert observed=={tuple(p) for p in expected_outline}, (name,'OUTLINE',observed)
        assert abs(b.GetDesignSettings().GetBoardThickness()/1e6-d['thickness_mm'])<1e-6
        assert b.GetCopperLayerCount()==4
        zones=[]
        for z in b.Zones():
            if z.GetIsRuleArea():
                poly=z.Outline().COutline(0)
                zones.append({'native_xy':[xy(poly.CPoint(i)) for i in range(poly.PointCount())],
                              'copper_layers':[int(l) for l in (pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.B_Cu) if z.GetLayerSet().Contains(l)],
                              'no_copper':z.GetDoNotAllowCopperPour(),'no_tracks':z.GetDoNotAllowTracks(),'no_vias':z.GetDoNotAllowVias()})
        if name=='main':
            for polygon in [d['antenna_all_layer_keepout_native_xy_mm']]+[r['xy'] for r in d['retention']]:
                assert any({tuple(p) for p in z['native_xy']}=={tuple(p) for p in polygon} and len(z['copper_layers'])==4 and z['no_copper'] and z['no_tracks'] and z['no_vias'] for z in zones), 'KEEP-OUT LOST'
        ih=sha(ip)
        if EXPECTED[name] and ih!=EXPECTED[name]:report['warnings'].append(f'{name}: requested interface hash differs from accessible snapshot; actual board independently matches this snapshot. Orchestrator reconciliation required; no earlier file available for diff.')
        report['boards'][name]={'interface_sha256':ih,'requested_interface_sha256':EXPECTED[name], 'board_sha256':sha(bp),
                               'board_path':str(bp.relative_to(ROOT)), 'interface_path':str(ip.relative_to(ROOT)),
                               'outline_xy':expected_outline, 'thickness_mm':d['thickness_mm'],'copper_layers':4,
                               'footprints':fps,'holes':holes,'rule_areas':zones,'native_y_origin':origin_y,
                               'tracks_count':len(list(b.GetTracks()))}
    (ROOT/'.cache/housing/input-geometry.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'result':'PASS independently matched poses/pads/holes/outline/layer rules', 'warnings':report['warnings'],
                      'hashes':{n:{k:v for k,v in b.items() if k.endswith('sha256')} for n,b in report['boards'].items()}},indent=2))
    return report
if __name__=='__main__':extract()
