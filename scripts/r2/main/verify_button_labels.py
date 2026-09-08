#!/usr/bin/python3
"""Read-only button-label regression check; canonical source is the native board.
Run after verify.py (uses its fresh XML netlist). Optional --baseline is a PCB
copy from before the label edit, for exact non-label byte preservation testing.
"""
from pathlib import Path
import argparse
import json
import re
import xml.etree.ElementTree as ET
import pcbnew as p

ROOT = Path(__file__).resolve().parents[3]
CAD = ROOT / 'PCB/main/smove-r2-main.kicad_pcb'
OUT = ROOT / '.cache/verify/main'
args = argparse.ArgumentParser(description=__doc__)
args.add_argument('--baseline', type=Path)
args = args.parse_args()
b = p.LoadBoard(str(CAD))
fps = {f.GetReference(): f for f in b.GetFootprints()}
xml = ET.parse(OUT / 'netlist.xml')
nets = {n.get('name'): n for n in xml.findall('.//nets/net')}
checks = {}
labels = []
for label, ref, signal, pin, function, y in [
    ('RESET', 'SW2', '/Compute/MCU_EN', '8', 'EN', 123.7),
    ('BOOT', 'SW3', '/Compute/BOOT', '23', 'GPIO9_/_BOOT', 130.0),
]:
    pads = {a.GetNumber(): a.GetNetname() for a in fps[ref].Pads()}
    mcu = {a.GetNumber(): a.GetNetname() for a in fps['U1'].Pads()}
    nodes = {(n.get('ref'), n.get('pin')): n for n in nets[signal].findall('node')}
    gnd = {(n.get('ref'), n.get('pin')) for n in nets['GND'].findall('node')}
    checks[label + '_mapping'] = (
        pads == {'1': signal, '2': 'GND'} and mcu[pin] == signal
        and (ref, '1') in nodes and (ref, '2') in gnd
        and nodes[('U1', pin)].get('pinfunction') == function
    )
    texts = [t for t in b.GetDrawings() if isinstance(t, p.PCB_TEXT) and t.GetText() == label]
    assert len(texts) == 1, (label, 'must exist exactly once')
    t = texts[0]
    checks[label + '_visible_geometry'] = (
        t.GetLayer() == p.F_SilkS and not t.IsMirrored()
        and fps[ref].GetLayer() == p.F_Cu
        and abs(p.ToMM(t.GetPosition().x) - 110.2) < 1e-6
        and abs(p.ToMM(t.GetPosition().y) - y) < 1e-6
        and t.GetTextAngle().AsDegrees() == 90
        and tuple(p.ToMM(t.GetTextSize())) == (0.8, 0.8)
        and p.ToMM(t.GetTextThickness()) == 0.15
    )
    labels.append(dict(text=label, reference=ref, signal=signal, mcu_pin=pin,
                       mcu_function=function, xy_mm=[110.2, y], rotation_deg=90,
                       size_mm=0.8, stroke_mm=0.15, layer='F.SilkS'))
if args.baseline:
    # This exact pattern matches only the two added standalone text records.
    text = CAD.read_text()
    stripped, count = re.subn(
        r'\t\(gr_text "(?:RESET|BOOT)"\n.*?\n\t\)\n', '', text, flags=re.S)
    checks['only_two_text_records_changed'] = count == 2 and stripped == args.baseline.read_text()
report = dict(status='PASS' if all(checks.values()) else 'FAIL', checks=checks, labels=labels)
(OUT / 'button-labels.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
raise SystemExit(0 if all(checks.values()) else 1)
