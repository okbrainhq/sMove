#!/usr/bin/python3
"""Generate D1's unified RGB body in local library AND Compute's embedded cache.

Only symbol graphics, pin-name visibility and pin 4's drawn length change. Keep
the complete instance, UUIDs, pin endpoints/functions, wires and board association.
Run --check to test that the native sources match this deterministic generator.
"""
import argparse
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
TOKEN = re.compile(r'"(?:\\.|[^"\\])*"|\(|\)|[^\s()]+')


def block_span(text, pattern):
    """Find exactly one balanced s-expression; ignore parentheses inside strings."""
    matches = list(re.finditer(pattern, text))
    assert len(matches) == 1, (pattern, len(matches))
    start = matches[0].start()
    depth = 0
    for token in TOKEN.finditer(text, start):
        if token.group() == '(':
            depth += 1
        elif token.group() == ')':
            depth -= 1
            if depth == 0:
                return start, token.end()
    raise ValueError('Unbalanced s-expression')


def replace_block(text, pattern, replacement):
    a, b = block_span(text, pattern)
    return text[:a] + replacement + text[b:]


def graphics():
    def poly(points, width=0.2):
        pts = ' '.join(f'(xy {x:g} {y:g})' for x, y in points)
        return f'(polyline (pts {pts}) (stroke (width {width:g}) (type default)) (fill (type none)))'

    elements = [
        '(rectangle (start -12.7 17.78) (end 8.89 -17.78) '
        '(stroke (width 0.254) (type default)) (fill (type background)))',
        # One shared anode rail, not three separate device bodies.
        poly([(5.08, 17.78), (5.08, -12.7)], 0.15),
    ]
    for name, y in [('R', 12.7), ('G', 0), ('B', -12.7)]:
        elements += [
            poly([(-7.62, y), (-2.54, y+2.54), (-2.54, y-2.54), (-7.62, y)]),
            poly([(-7.62, y-2.54), (-7.62, y+2.54)]),
            poly([(-12.7, y), (-7.62, y)], 0.15),
            poly([(-2.54, y), (5.08, y)], 0.15),
            f'(text "{name}" (at -5.08 {y-3.81:g} 0) (effects (font (size 1.27 1.27))))',
        ]
        # Two complete outward light arrows per die, both inside the package box.
        for x in (-5.08, -2.54):
            tip = (x+1.6, y+4.06)
            elements += [poly([(x, y+2.46), tip], 0.12),
                         poly([(tip[0]-0.9, tip[1]), tip, (tip[0], tip[1]-0.9)], 0.12)]
        if y != -12.7:
            elements.append(f'(circle (center 5.08 {y:g}) (radius 0.35) '
                            '(stroke (width 0) (type default)) (fill (type outline)))')
    return '(symbol "D1_0_1"\n        ' + '\n        '.join(elements) + ')'


def update(text, lib_id):
    pattern = r'\(symbol\s+"' + re.escape(lib_id) + r'"(?=\s|\()'
    a, b = block_span(text, pattern)
    symbol = text[a:b]
    symbol = replace_block(symbol, r'\(symbol\s+"D1_0_1"', graphics())
    # Names stay in the pin/netlist data; unobstructed die letters show each color.
    symbol = replace_block(symbol, r'\(pin_names\b', '(pin_names (offset .508) (hide yes))')
    # Terminate pin 4 at the package border so its number does not overlap it.
    # The electrical connection point remains (5.08,20.32), unchanged.
    symbol, count = re.subn(r'(\(pin passive line\s*\(at 5\.08 20\.32 270\)\s*\(length )[^)]+',
                            r'\g<1>2.54', symbol)
    assert count == 1
    return text[:a] + symbol + text[b:]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    for path, lib_id in [('PCB/main/smove-r2-main.kicad_sym', 'D1'),
                         ('PCB/main/compute.kicad_sch', 'smove-r2-main:D1')]:
        file = ROOT / path
        old = file.read_text()
        new = update(old, lib_id)
        if args.check:
            assert old == new, f'{path}: run unify_rgb.py to regenerate'
        elif old != new:
            file.write_text(new)
        print(('CHECKED ' if args.check else 'GENERATED ') + path)


if __name__ == '__main__':
    main()
