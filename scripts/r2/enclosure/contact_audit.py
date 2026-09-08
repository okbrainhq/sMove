#!/usr/bin/env python3
"""Read-only canonical PCB contact audit: main lands and installed carrier annular seats."""
import json, math
from pathlib import Path
import pcbnew
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'housing'
(ROOT/'.cache/housing').mkdir(parents=True,exist_ok=True)
d=json.loads((ROOT/'PCB/main/interface.json').read_text());b=pcbnew.LoadBoard(str(ROOT/'PCB/main/smove-r2-main.kicad_pcb'))
rows=[];fail=[]
carrier=pcbnew.LoadBoard(str(ROOT/'PCB/imu-carrier/smove-imu-carrier.kicad_pcb'))
carrier_contract=json.loads((ROOT/'PCB/imu-carrier/interface.json').read_text())
regions=[(b,r) for r in d['retention']]
for mount in carrier_contract['mounting_features']:
    x,y=mount['center_mm'];x+=100;y=120-y
    # Circumscribed 64-gon covers the complete actual R1.6-mm seat/upper bearing.
    radius=1.6/math.cos(math.pi/64)
    points=[[x+radius*math.cos(i*2*math.pi/64),y+radius*math.sin(i*2*math.pi/64)] for i in range(64)]
    regions.append((carrier,dict(name='carrier_'+mount['ref'],xy=points)))
for b,r in regions:
    poly=pcbnew.SHAPE_POLY_SET();poly.NewOutline()
    for x,y in r['xy']:poly.Append(round(x*1e6),round(y*1e6))
    x0=min(p[0] for p in r['xy']);x1=max(p[0] for p in r['xy']);y0=min(p[1] for p in r['xy']);y1=max(p[1] for p in r['xy'])
    def hit(item):
        bb=item.GetBoundingBox();return min(x1,bb.GetRight()/1e6)-max(x0,bb.GetX()/1e6)>1e-7 and min(y1,bb.GetBottom()/1e6)-max(y0,bb.GetY()/1e6)>1e-7
    hits=[]
    for f in b.GetFootprints():
        for pad in f.Pads():
            if pad.GetAttribute()!=pcbnew.PAD_ATTRIB_NPTH and pad.IsOnCopperLayer() and hit(pad):hits.append('pad:'+f.GetReference()+':'+pad.GetNumber())
    for t in b.GetTracks():
        if hit(t) and poly.Collide(t.GetEffectiveShape()):hits.append('track_or_via:'+str(t.GetNetCode()))
    fill_layers=0
    for z in b.Zones():
        if z.GetIsRuleArea():continue
        for layer in (pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.B_Cu):
            if z.HasFilledPolysForLayer(layer):
                fill_layers+=1;overlap=pcbnew.SHAPE_POLY_SET(z.GetFilledPolysList(layer));overlap.BooleanIntersection(poly)
                if overlap.Area()>1:hits.append('filled_copper:'+b.GetLayerName(layer))
    row={'land':r['name'],'collisions':hits,'filled_zone_layers_inspected':fill_layers,'passed':not hits and fill_layers>0};rows.append(row)
    if not row['passed']:fail.append(row)
report={'status':'PASS' if not fail else 'FAIL','method':'Conservative pad AABBs; exact effective track/via shape collision (AABB broad phase), exact stored filled-copper polygon intersection in all four layers. Not electrical DRC or new refill.','lands':rows}
(ROOT/'.cache/housing/contact-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
assert not fail
