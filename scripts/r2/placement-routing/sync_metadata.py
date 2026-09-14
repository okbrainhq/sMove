#!/usr/bin/python3
"""Refresh only placement/net handoff metadata; never regenerate PCB or enclosure."""
from pathlib import Path
import json, hashlib
import pcbnew as p
ROOT=Path(__file__).resolve().parents[3]
HOME=ROOT/'PCB/main'
board=HOME/'smove-r2-main.kicad_pcb'
b=p.LoadBoard(str(board))
poses={f.GetReference():[p.ToMM(f.GetPosition().x),p.ToMM(f.GetPosition().y),f.GetOrientationDegrees()] for f in b.GetFootprints()}
parts_path=HOME/'parts-main.json';parts=json.loads(parts_path.read_text())
assert set(parts)==set(poses)
for ref,pose in poses.items():parts[ref]['placement']=pose
parts['U1']['pins']['6']='LED_R';parts['U1']['pins']['20']=None
parts_path.write_text(json.dumps(parts,indent=2)+'\n')
path=HOME/'native-layout-contract.json';contract=json.loads(path.read_text())
contract['placement']=poses
sf=contract['sensor_frame'];sf['native_position_mm']=[112.5,126.5,1]
sf['centre_offset_native_mm']=[0.0,11.5];sf['position_from_board_NW_mm']=[12.5,26.5,1]
contract['mounting']['scheme']='Existing NW/SE M3 clear-disk reserves retained; no mounting holes present or added. Enclosure fastener integration is not qualified.'
contract['mounting']['reserved_disks_native_mm']={'NW':[103.15,103.15,3.0],'SE':[121.65,126.85,3.0]}
contract['mounting']['release_blocker']='Actual hole/head/washer/material selection, PCB support and enclosure openings require review; old screwless enclosure geometry was not regenerated.'
contract['revision_status']='placement-review-unrouted; not manufacturing or charging release'
contract['native_board_sha256']=hashlib.sha256(board.read_bytes()).hexdigest()
contract['led_gpio']={'red':3,'green':7,'blue':10}
path.write_text(json.dumps(contract,indent=2)+'\n')
print('Placement/net metadata refreshed; no housing or fabrication exports touched.')
