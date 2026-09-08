"""Current native audit inputs only; no placement/build behavior."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[3]
H=ROOT/'PCB/main'; D=ROOT/'.cache/verify/main'
D.mkdir(parents=True,exist_ok=True)
PARTS=json.loads((H/'parts-main.json').read_text())
OUTLINE=[[100,100],[125,100],[125,135],[100,135]]
ANTENNA=[[105.9,94.6],[119.1,94.6],[119.1,100],[105.9,100]]
RF_KEEPOUT=[[90.9,79.6],[134.1,79.6],[134.1,100],[90.9,100]]
RETENTION=[{'name':'west','xy':[[100,104.2],[101.1,104.2],[101.1,106.0],[100,106.0]]}, {'name':'east','xy':[[123.9,104.2],[125,104.2],[125,106.0],[123.9,106.0]]}]
