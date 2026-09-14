#!/usr/bin/python3
"""Authorized RED LED reassignment only: GPIO6/U1.20 -> GPIO3/U1.6.

Preserves USB GPIO18/19, I2C GPIO4/5, BOOT GPIO9 and strap GPIO2/8.
Run after place.py. Updates the symbol library, schematic cache, wiring and PCB.
Firmware must change RED to GPIO3; GREEN=GPIO7, BLUE=GPIO10 remain unchanged.
"""
from pathlib import Path
import sys, copy, uuid
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/r2/integrated'))
from sexp import parse, dump, many, one, val, prop

def uid():
    return ['uuid', str(uuid.uuid4())]

def pins(symbol):
    for unit in many(symbol, 'symbol'):
        yield from many(unit, 'pin')

def fix_symbol(symbol):
    for pin in pins(symbol):
        number = val(one(pin, 'number')[1])
        if number in ('6', '20'):
            pin[1] = 'bidirectional'
            one(pin, 'name')[1] = '"GPIO3 / RED"' if number == '6' else '"GPIO6"'

def main():
    home = ROOT / 'PCB/main'
    libpath = home / 'smove-r2-main.kicad_sym'
    lib = parse(libpath.read_text())
    fix_symbol(next(s for s in many(lib, 'symbol') if val(s[1]) == 'U1'))
    libpath.write_text(dump(lib) + '\n')
    schpath = home / 'compute.kicad_sch'
    sch = parse(schpath.read_text())
    fix_symbol(next(s for s in many(one(sch, 'lib_symbols'), 'symbol') if val(s[1]) == 'smove-r2-main:U1'))
    changed = False
    for nc in many(sch, 'no_connect'):
        if list(map(float, one(nc, 'at')[1:])) == [165.1, 139.7]:
            one(nc, 'at')[1:] = ['241.3', '88.9']
            changed = True
    if changed:
        wire = next(w for w in many(sch, 'wire') if many(one(w, 'pts'), 'xy')[0][1:] == ['241.3', '88.9'])
        many(one(wire, 'pts'), 'xy')[0][1] = '246.38'
        label = next(n for n in many(sch, 'label') if val(n[1]) == 'LED_R')
        one(label, 'at')[1] = '246.38'
        label2 = copy.deepcopy(label)
        one(label2, 'at')[1:] = ['161.29', '139.7', '0']
        one(label2, 'uuid')[1] = str(uuid.uuid4())
        sch.append(label2)
        sch.append(['wire', ['pts', ['xy','161.29','139.7'], ['xy','165.1','139.7']],
                    ['stroke',['width','0'],['type','default']], uid()])
    schpath.write_text(dump(sch) + '\n')
    boardpath = home / 'smove-r2-main.kicad_pcb'
    board = parse(boardpath.read_text())
    red = next(n for n in many(board, 'net') if val(n[2]) == '/Compute/LED_R')
    unused = next(n for n in many(board, 'net') if val(n[2]) in ('unconnected-(U1-GPIO3-Pad6)', 'unconnected-(U1-GPIO6-Pad20)'))
    unused[2] = '"unconnected-(U1-GPIO6-Pad20)"'
    u1 = next(f for f in many(board, 'footprint') if prop(f,'Reference') == 'U1')
    for pad in many(u1, 'pad'):
        number = val(pad[1])
        if number in ('6', '20'):
            one(pad, 'net')[1:] = (red if number == '6' else unused)[1:]
            for key, value in [('pinfunction', '"GPIO3 / RED"' if number == '6' else '"GPIO6"'), ('pintype','"bidirectional"')]:
                if many(pad,key):one(pad,key)[1] = value
    boardpath.write_text(dump(board) + '\n')
    # Let KiCad restore its native formatting; never overwrite project rules.
    import pcbnew as p
    pro = boardpath.with_suffix('.kicad_pro')
    original_project = pro.read_bytes()
    try:
        b = p.LoadBoard(str(boardpath))
        p.SaveBoard(str(boardpath), b)
    finally:
        pro.write_bytes(original_project)
    print('RED GPIO6 -> GPIO3; GREEN GPIO7 and BLUE GPIO10 unchanged.')

if __name__ == '__main__':
    main()
