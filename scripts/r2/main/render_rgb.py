#!/usr/bin/python3
"""Export the native four-page main schematic and a readable D1 circuit crop.

Does not rebuild fabrication outputs or save/edit the native PCB/schematic.
The crop is from KiCad's own SVG, not a redrawn schematic.
"""
from pathlib import Path
import re
import subprocess
import gi

gi.require_version('Rsvg', '2.0')
from gi.repository import Rsvg

ROOT = Path(__file__).resolve().parents[3]


def export_schematic(schematic, out, main=False):
    out.mkdir(parents=True, exist_ok=True)
    subprocess.run(['kicad-cli', 'sch', 'export', 'pdf', '-o', str(out/'schematic.pdf'), str(schematic)], check=True)
    svg_dir = out/'schematic-svg'
    svg_dir.mkdir(exist_ok=True)
    subprocess.run(['kicad-cli', 'sch', 'export', 'svg', '-o', str(svg_dir)+'/', str(schematic)], check=True)
    for file in svg_dir.glob('*.svg'):
        file.write_text('\n'.join(line.rstrip() for line in file.read_text().splitlines()) + '\n')
    pages = ['schematic', 'schematic-usb', 'schematic-power', 'schematic-compute'] if main else ['schematic']
    info = subprocess.check_output(['pdfinfo', str(out/'schematic.pdf')], text=True)
    assert re.search(rf'Pages:\s+{len(pages)}\b', info), info
    for page, name in enumerate(pages, 1):
        subprocess.run(['pdftoppm', '-f', str(page), '-l', str(page), '-png', '-scale-to', '2600',
                        '-singlefile', str(out/'schematic.pdf'), str(out/name)], check=True)


def crop_rgb(out):
    svg = (out/'schematic-svg/smove-r2-main-Compute.svg').read_text()
    # Native schematic mm; includes R11/R12/R13 and real wiring to D1/pin4.
    x, y, width, height = 237, 77, 135, 78
    svg, count = re.subn(r'width="[^"]+" height="[^"]+" viewBox="[^"]+"',
                        f'width="2430" height="1404" viewBox="{x} {y} {width} {height}"', svg, count=1)
    assert count == 1
    start = svg.index('>', svg.index('<svg')) + 1
    svg = svg[:start] + f'<rect x="{x}" y="{y}" width="{width}" height="{height}" fill="white"/>' + svg[start:]
    target = ROOT/'docs/revision-r2/rgb-body/views'
    target.mkdir(parents=True, exist_ok=True)
    (target/'rgb-close-up.svg').write_text(svg)
    pix = Rsvg.Handle.new_from_data(svg.encode()).get_pixbuf()
    pix.savev(str(target/'rgb-close-up.png'), 'png', [], [])
    print(target/'rgb-close-up.png')


if __name__ == '__main__':
    out = ROOT/'PCB/main/dist'
    export_schematic(ROOT/'PCB/main/smove-r2-main.kicad_sch', out, main=True)
    crop_rgb(out)
