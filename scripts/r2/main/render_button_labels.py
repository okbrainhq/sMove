#!/usr/bin/python3
"""Render native silk/mask/fab close-up. Cyan refs are evidence-only annotations."""
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET
import gi

gi.require_version('Rsvg', '2.0')
from gi.repository import Rsvg

ROOT = Path(__file__).resolve().parents[3]
CACHE = ROOT / '.cache/button-labels'
CACHE.mkdir(parents=True, exist_ok=True)
OUT = ROOT / 'docs/revision-r2/button-labels'
OUT.mkdir(parents=True, exist_ok=True)
raw = CACHE / 'labeled.svg'
subprocess.run(['kicad-cli', 'pcb', 'export', 'svg', '--mode-single', '--layers',
                'F.SilkS,F.Fab,F.Mask,Edge.Cuts', '--page-size-mode', '2', '-o',
                str(raw), str(ROOT / 'PCB/main/smove-r2-main.kicad_pcb')], check=True)
svg = raw.read_text()
# Determine KiCad's plot offset from the RESET text anchor, not raster guesses.
ns = {'s': 'http://www.w3.org/2000/svg'}
root = ET.fromstring(svg)
t = next(t for t in root.findall('.//s:text', ns) if t.text == 'RESET')
xoff = 110.2 - float(t.get('x'))
yoff = 123.7 - (float(t.get('y')) - 0.4)
x, y = 105 - xoff, 118 - yoff
svg = re.sub(r'width="[^"]+" height="[^"]+" viewBox="[^"]+"',
             f'width="1600" height="1700" viewBox="{x} {y} 16 17"', svg, count=1)
start = svg.index('>', svg.index('<svg')) + 1
svg = svg[:start] + f'<rect x="{x}" y="{y}" width="16" height="17" fill="#161c24"/>' + svg[start:]
annotations = f'<rect x="{x}" y="{y}" width="16" height="1.7" fill="#161c24"/><g fill="#70d6ff" stroke="none" font-family="sans-serif" font-size="0.48"><text x="{x+.3}" y="{y+.7}">TOP: silk + mask + component outlines</text><text x="{x+.3}" y="{y+1.35}">Cyan SW refs: review annotations, not silk</text>'
for ref, cy in [('SW2', 123.7), ('SW3', 130)]:
    annotations += f'<text text-anchor="middle" x="{112.3-xoff}" y="{cy-yoff+.2}" font-size="0.65">{ref}</text>'
annotations += '</g>'
svg = svg.replace('</svg>', annotations + '</svg>')
svg = '\n'.join(line.rstrip() for line in svg.splitlines()) + '\n'
(OUT / 'close-up.svg').write_text(svg)
pix = Rsvg.Handle.new_from_data(svg.encode()).get_pixbuf()
pix.savev(str(OUT / 'close-up.png'), 'png', [], [])
print(OUT / 'close-up.png')
