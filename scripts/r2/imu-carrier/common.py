"""Carrier-only paths/data. No writes outside the four owned directories."""
from pathlib import Path
import json, uuid, csv
ROOT = Path(__file__).resolve().parents[3]
H = ROOT/'PCB/imu-carrier'
D = ROOT/'.cache/verify/imu-carrier'
M = ROOT/'PCB/imu-carrier/dist'
NAME = 'smove-imu-carrier'
LIB = H/'carrier.pretty'
for p in (H,D,M,LIB): p.mkdir(parents=True,exist_ok=True)
def uid(s): return str(uuid.uuid5(uuid.NAMESPACE_URL,'smove:reusable-carrier:v1:'+str(s)))
def dump(p,o): p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
def q(s): return json.dumps(str(s),ensure_ascii=False)
NETS=json.loads((H/'electrical-contract.json').read_text())
PARTS=json.loads((H/'parts.json').read_text())
assert len(PARTS)==14 and PARTS.keys()==NETS.keys()
FP={r:('R_0402_1005Metric' if r[0]=='R' else 'C_0603_1608Metric' if r in ('C5','C6') else 'C_0402_1005Metric') for r in PARTS}
FP.update(U2='InvenSense_QFN-24_3x3mm_P0.4mm',U3='PCA9306_DCU0008A',U5='SOT-23-5',J5='JST_PH_S4B-PH-SM4-TB_1x04-1MP_P2.00mm_Horizontal')
# XY is the carrier right-handed frame: +X pin1->4, +Y away from mating face.
PLACE={
 'J5':(9,4.9,0),'U2':(9.5,16.2,0),'U3':(12.9,11.7,0),'U5':(3.8,11.7,0),
 'C5':(.95,11.9,90),'C6':(5.0,14.3,0),'C7':(12.6,15.0,0),
 'C8':(7.6,13.4,0),'C9':(9.7,13.05,0),
 'R16':(14.7,13.9,0),'R17':(14.7,15.2,0),
 'R18':(8.8,10.6,0),'R19':(8.15,11.8,0),'R20':(16.4,11.7,90)}
OUTLINE=[[0,0],[18,0],[18,20],[1.5,20],[0,18.5]]
HOLES=[{'ref':'H1','center_mm':[2.5,17.5],'drill_mm':[2.2,2.2],'support_radius_mm':1.65},
       {'ref':'H2','center_mm':[15.5,17.5],'drill_mm':[2.7,2.2],'support_radius_mm':1.65}]
# Board editor origin offsets; physical-frame z=0 is top PCB/component seating face.
ORIGIN=(100,120)
def pcbxy(x,y):
    import pcbnew as p
    return p.VECTOR2I(p.FromMM(100+x),p.FromMM(120-y))
def localxy(pos):
    import pcbnew as p
    x,y=p.ToMM(pos); return [round(x-100,6),round(120-y,6)]
