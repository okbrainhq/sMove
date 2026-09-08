#!/usr/bin/python3
"""Native carrier verification only; no fabrication/assembly/STEP exports."""
import gc;gc.disable()
from common import *
import pcbnew as p, subprocess as sp, csv, hashlib, zipfile, re, xml.etree.ElementTree as E
CAD=H/(NAME+'.kicad_pcb');SCH=H/(NAME+'.kicad_sch')
LOG=D/'export-logs';LOG.mkdir(exist_ok=True)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def run(tag,args):
    r=sp.run(args,stdout=sp.PIPE,stderr=sp.STDOUT,text=True)
    (LOG/(tag+'.log')).write_text(r.stdout)
    if r.returncode:raise RuntimeError((tag,r.returncode,r.stdout[-1200:]))
    return r.stdout
run('erc',['kicad-cli','sch','erc','--format','json','--severity-all','--exit-code-violations','-o',str(D/'erc.json'),str(SCH)])
run('netlist',['kicad-cli','sch','export','netlist','--format','kicadxml','-o',str(D/'netlist.xml'),str(SCH)])
run('drc',['kicad-cli','pcb','drc','--format','json','--severity-all','--all-track-errors','--schematic-parity','--exit-code-violations','-o',str(D/'drc.json'),str(CAD)])
b=p.LoadBoard(str(CAD));parts={f.GetReference():f for f in b.GetFootprints() if not f.IsExcludedFromBOM()}
assert set(parts)==set(PARTS) and len(parts)==14
assert b.GetCopperLayerCount()==4 and p.ToMM(b.GetDesignSettings().GetBoardThickness())==1
assert all(not f.IsFlipped() and not f.IsDNP() for f in parts.values())
assert len(list(b.GetTracks()))>0
sch=E.parse(D/'netlist.xml').getroot();sn={}
for n in sch.find('nets'):
    for node in n.findall('node'):sn[node.attrib['ref'],node.attrib['pin']]=n.attrib['name']
for r,f in parts.items():
    fields={v.GetName():v.GetText() for v in f.GetFields()}
    assert fields['MPN']==PARTS[r]['mpn'] and fields['LCSC']==PARTS[r]['jlc']
    assert str(f.GetFPID().GetLibItemName())==FP[r]
    for d in f.Pads():assert d.GetNetname()==sn[r,d.GetNumber()],(r,d.GetNumber(),d.GetNetname(),sn.get((r,d.GetNumber())))
    for n,net in NETS[r]['pins'].items():
        assert sn[r,n]==('/'+net if net else sn[r,n])
        if net is None:assert sn[r,n].startswith('unconnected-')
# Independent pin/land oracles taken from the archived manufacturer figures, not NETS.
pdmap={(r,d.GetNumber()):d for r,f in parts.items() for d in f.Pads()}
def net(r,n):return pdmap[r,str(n)].GetNetname().lstrip('/')
for n in (8,13,22):assert net('U2',n)=='1V8_IMU'
for n in (9,11,18,20):assert net('U2',n)=='GND'
assert net('U2',19).startswith('unconnected-') and net('U2',10)=='IMU_REGOUT'
assert net('U2',23)=='SCL_1V8' and net('U2',24)=='SDA_1V8'
assert {d.GetNumber() for d in parts['U2'].Pads()}=={str(i) for i in range(1,25)}
for n,expected in {1:'GND',2:'1V8_IMU',3:'SCL_1V8',4:'SDA_1V8',5:'SDA_3V3',6:'SCL_3V3',7:'I2C_BIAS',8:'I2C_BIAS'}.items():assert net('U3',n)==expected
for n,expected in {1:'3V3_IMU_IN',2:'GND',3:'3V3_IMU_IN',5:'1V8_IMU'}.items():assert net('U5',n)==expected
assert set((r,n) for (r,n),v in sn.items() if v=='/IMU_REGOUT')=={('U2','10'),('C9','1')}
assert set((r,n) for (r,n),v in sn.items() if v=='/I2C_BIAS')=={('U3','7'),('U3','8'),('R20','2')}
for n,xy in {1:[8,17.2],6:[8,15.2],8:[8.9,14.7],10:[9.7,14.7],13:[11,15.2],18:[11,17.2],19:[10.5,17.7],20:[10.1,17.7],23:[8.9,17.7],24:[8.5,17.7]}.items():assert localxy(pdmap['U2',str(n)].GetPosition())==xy
for d in parts['U3'].Pads():assert all(abs(a-v)<1e-6 for a,v in zip(p.ToMM(d.GetSize()),[.85,.3]))
assert localxy(pdmap['J5','1'].GetPosition())==[6,7.75] and localxy(pdmap['J5','4'].GetPosition())==[12,7.75]
contract=json.loads((H/'interface.json').read_text())
for row in contract['components']:
    f=parts[row['ref']];assert row['center_mm']==localxy(f.GetPosition()) and row['rotation_ccw_deg']==f.GetOrientationDegrees()
assert len([d for f in b.GetFootprints() for d in f.Pads() if d.GetAttribute()==p.PAD_ATTRIB_NPTH])==2
for h in HOLES:
    f=next(f for f in b.GetFootprints() if f.GetReference()==h['ref']);d=next(iter(f.Pads()))
    assert localxy(d.GetPosition())==h['center_mm'] and list(p.ToMM(d.GetDrillSize()))==h['drill_mm']

report={'status':'PASS','fitted':14,'erc_errors':0,'erc_warnings':0,'drc_violations':0,'opens':0,'native_parity_issues':0,'independent_pin_land_net_BOM_geometry_checks':'PASS','board_sha256':sha(CAD),'schematic_sha256':sha(SCH),'interface_sha256':sha(H/'interface.json'),'manufacturing_release':False}
dump(D/'verification.json',report)
print('Carrier PASS: ERC0/0, DRC0, opens0, native parity0, independent pins/BOM/geometry PASS')
