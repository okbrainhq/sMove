#!/usr/bin/python3
"""Render the current native board with the reusable review renderer."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from pcb_tools.render import render
import pcbnew as p

if __name__=='__main__':
    board=p.LoadBoard(str(ROOT/'PCB/main/smove-r2-main.kicad_pcb'))
    out=ROOT/'docs/revision-r2/main-routing';out.mkdir(parents=True,exist_ok=True)
    for layer in board.GetEnabledLayers().CuStack():render(board,out/(board.GetLayerName(layer)+'.png'),layer)
    render(board,out/'top-tracks.png',fill=False);render(board,out/'bottom-tracks.png',p.B_Cu,fill=False)
