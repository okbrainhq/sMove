#!/usr/bin/python3
"""Placement-only ECO from a specified native board. Never run historical generators.

Usage: place.py INPUT OUTPUT
Old routes are intentionally removed from OUTPUT, not stretched between moved pads.
INPUT remains untouched. Complete and verify routing before fabrication.
"""
from pathlib import Path
import sys
import pcbnew as p
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'integrated'))
from sexp import parse, dump

V = lambda x, y: p.VECTOR2I(p.FromMM(x), p.FromMM(y))
# Front-view native coordinates, mm / degrees. U1, J1 and J2 are fixed.
PLACEMENT = {
    # Human interface: the narrow strip below the NW M3 reserve.
    'SW2': (102.4, 109.35, 90), 'SW3': (102.4, 115.45, 90),
    'D1': (105.7, 113.2, 90),
    'R11': (105.2, 115.2, 0), 'R12': (105.2, 116.3, 0),
    'R13': (105.2, 117.4, 0), 'R8': (105.2, 118.55, 0),
    'R7': (106.2, 109.05, 0), 'C10': (106.2, 110.25, 0),
    'R9': (106.8, 105.4, 90), 'C4': (106.8, 103.1, 90),
    'R14': (106.2, 106.85, 0), 'R15': (106.2, 107.95, 180),
    'C11': (106.2, 111.35, 0),
    # Power path: immediately below the ESP and beside the fixed USB connector.
    'U4': (109.25, 113.4, 180), 'C3': (108.25, 116.6, 0),
    'C13': (111.9, 116.6, 0), 'U6': (111.9, 119.5, 180),
    'C2': (114.75, 119.6, 90), 'C1': (111.75, 122.15, 0),
    'R21': (114.05, 122.4, 90), 'R22': (108.0, 119.45, 0),
    'R23': (112.55, 123.8, 0), 'R5': (108.0, 118.3, 0),
    # USB protection and termination. U8 stays at the connector's inner edge.
    'U8': (113.5, 113.5, 0), 'U9': (116.6, 123.95, 0),
    'R3': (122.25, 110.5, 0), 'R4': (123.0, 108.75, 90),
    'R1': (116.35, 126.5, 0), 'R2': (116.35, 127.65, 0),
    'R10': (105.2, 119.65, 0),
    # Quiet lower-centre IMU island. Preserve U2 rotation and X centreline.
    'U2': (112.5, 126.5, -90), 'U5': (104.5, 124.6, -90),
    'C5': (104.5, 121.55, 0), 'C6': (105.5, 128.0, 0),
    'C7': (111.15, 129.25, 0), 'C8': (109.25, 126.9, -90),
    'C9': (109.25, 128.45, 180), 'U3': (108.25, 123.5, 90),
    'R16': (115.55, 129.15, 0), 'R17': (113.25, 129.15, 0),
    'R18': (107.8, 120.55, 0), 'R19': (110.5, 123.8, 0),
    'R20': (107.8, 126.9, 90),
}

def main():
    src, dst = map(Path, sys.argv[1:3])
    if src.resolve() == dst.resolve():
        raise SystemExit('Input and output must differ; preserve the baseline.')
    tree = parse(src.read_text())
    tree[:] = [n for n in tree if not (isinstance(n, list) and n[0] in ('segment', 'via'))]
    for n in tree:
        if isinstance(n, list) and n[0] == 'zone':
            n[:] = [v for v in n if not (isinstance(v, list) and v[0] == 'filled_polygon')]
    with tempfile.NamedTemporaryFile(suffix='.kicad_pcb', mode='w') as tmp:
        tmp.write(dump(tree)); tmp.flush()
        b = p.LoadBoard(tmp.name)
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    assert set(PLACEMENT) | {'U1', 'J1', 'J2'} == set(fps)
    for ref, (x, y, angle) in PLACEMENT.items():
        f = fps[ref]
        f.SetOrientationDegrees(angle)
        f.SetPosition(V(x, y))
    for d in b.GetDrawings():
        if not hasattr(d, 'GetText'):
            continue
        if d.GetText() == '+Z':
            d.SetPosition(V(112.5, 126.5))
        elif d.GetText() in ('BOOT', 'RESET'):
            y = 115.45 if d.GetText() == 'BOOT' else 109.35
            d.SetPosition(V(102.4, y))
            if d.GetText() == 'RESET':
                d.SetText('RST')
            d.SetTextAngle(p.EDA_ANGLE(90, p.DEGREES_T))
            d.SetTextSize(V(.8, .8))
            d.SetTextThickness(p.FromMM(.08))
    b.BuildConnectivity()
    dst.parent.mkdir(parents=True, exist_ok=True)
    project = dst.with_suffix('.kicad_pro')
    project_bytes = project.read_bytes() if project.exists() else None
    try:
        p.SaveBoard(str(dst), b)
    finally:
        if project_bytes is not None:
            project.write_bytes(project_bytes)
    print(f'Placed {len(PLACEMENT)} references; U1/J1/J2 and every rule area retained.')

if __name__ == '__main__':
    main()
