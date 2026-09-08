#!/usr/bin/python3
"""Read-only RGB ECO regression against pre-edit main; writes only review receipts.

Run after the pre-edit baseline ERC/DRC/XML reports have been captured. This audit
uses exact hierarchical net names, not leaf-name normalization that could hide
shorts. Existing main/verify.py's pre-hierarchy assumptions are NOT silently fixed.
"""
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess as sp
import xml.etree.ElementTree as ET
import pcbnew as p
from unify_rgb import TOKEN, block_span, replace_block, update

ROOT = Path(__file__).resolve().parents[3]
BASE = 'fcbf69674c16e1a262ea21fec5447508a549ae40'
OUT = ROOT/'docs/revision-r2/rgb-body/validation'


def git_bytes(path):
    return sp.check_output(['git', 'show', f'{BASE}:{path}'], cwd=ROOT)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def parse(text):
    stack = [[]]
    for token in TOKEN.findall(text):
        if token == '(':
            stack.append([])
        elif token == ')':
            stack[-2].append(stack.pop())
        else:
            if token.startswith('"'):
                token = json.loads(token)
            else:
                try:
                    token = float(token)
                except ValueError:
                    pass
            stack[-1].append(token)
    assert len(stack) == 1 and len(stack[0]) == 1
    return stack[0][0]


def children(tree, name):
    return [x for x in tree if isinstance(x, list) and x and x[0] == name]


def child(tree, name):
    values = children(tree, name)
    assert len(values) == 1, (name, len(values))
    return values[0]


def strip_presentation(text, lib_id):
    a, b = block_span(text, r'\(symbol\s+"'+re.escape(lib_id)+r'"(?=\s|\()')
    symbol = text[a:b]
    symbol = replace_block(symbol, r'\(symbol\s+"D1_0_1"', '(symbol "D1_0_1")')
    symbol = replace_block(symbol, r'\(pin_names\b', '(pin_names)')
    symbol = re.sub(r'(\(pin passive line\s*\(at 5\.08 20\.32 270\)\s*\(length )[^)]+',
                    r'\g<1>DRAWING_LENGTH', symbol)
    return text[:a]+symbol+text[b:]


def canonical_xml(node):
    return [node.tag, sorted(node.attrib.items()), (node.text or '').strip(),
            [canonical_xml(c) for c in node]]


def net_map(tree):
    return {net.get('name'): sorted(tuple(sorted(n.attrib.items())) for n in net.findall('node'))
            for net in tree.findall('.//nets/net')}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    checks = {}
    def check(name, value):
        checks[name] = bool(value)
        if not value:
            print('FAIL', name)

    for key, stem in [('main', 'smove-r2-main'), ('carrier', 'smove-imu-carrier')]:
        folder = ROOT/'PCB'/('main' if key == 'main' else 'imu-carrier')
        commands = [
            ['sch', 'erc', '--format', 'json', '--severity-all', '--exit-code-violations',
             '-o', OUT/f'post-{key}-erc.json', folder/f'{stem}.kicad_sch'],
            ['pcb', 'drc', '--format', 'json', '--severity-all', '--all-track-errors',
             '--schematic-parity', '--exit-code-violations', '-o', OUT/f'post-{key}-drc.json', folder/f'{stem}.kicad_pcb'],
            ['sch', 'export', 'netlist', '--format', 'kicadxml', '-o', OUT/f'post-{key}-netlist.xml', folder/f'{stem}.kicad_sch'],
        ]
        for command in commands:
            sp.run(['kicad-cli', *map(str, command)], check=True, cwd=ROOT)
        for phase in ('baseline', 'post'):
            erc = json.loads((OUT/f'{phase}-{key}-erc.json').read_text())
            drc = json.loads((OUT/f'{phase}-{key}-drc.json').read_text())
            check(f'{phase}_{key}_configured_ERC_zero', not any(s['violations'] for s in erc['sheets']))
            check(f'{phase}_{key}_DRC_opens_parity_zero', not any(drc[k] for k in ['violations','unconnected_items','schematic_parity']))
        pre = ET.parse(OUT/f'baseline-{key}-netlist.xml')
        post = ET.parse(OUT/f'post-{key}-netlist.xml')
        check(key+'_all_named_nets_pin_functions_types_identical', net_map(pre) == net_map(post))
        check(key+'_all_component_metadata_and_UUIDs_identical',
              canonical_xml(pre.find('components')) == canonical_xml(post.find('components')))

    sym = None
    for path, lib_id in [('PCB/main/compute.kicad_sch','smove-r2-main:D1'),
                         ('PCB/main/smove-r2-main.kicad_sym','D1')]:
        old, new = git_bytes(path).decode(), (ROOT/path).read_text()
        check(path+'_only_RGB_presentation_changed', strip_presentation(old,lib_id) == strip_presentation(new,lib_id))
        check(path+'_generator_idempotent', update(new,lib_id) == new)
        a,b = block_span(new, r'\(symbol\s+"'+re.escape(lib_id)+r'"(?=\s|\()')
        definition = parse(new[a:b])
        units = children(definition,'symbol')
        check(path+'_one_body_and_one_pin_unit', [u[1] for u in units] == ['D1_0_1','D1_1_1'])
        pins = children(units[1],'pin')
        expected = {'1':([-17.78,12.7,0],'R_K'), '2':([-17.78,0,0],'G_K'),
                    '3':([-17.78,-12.7,0],'B_K'), '4':([5.08,20.32,270],'A')}
        actual = {child(pin,'number')[1]:(child(pin,'at')[1:], child(pin,'name')[1]) for pin in pins}
        check(path+'_four_original_pin_endpoints_numbers_functions', actual == expected and all(pin[1:3] == ['passive','line'] for pin in pins))
        rect = child(units[0],'rectangle')
        check(path+'_single_enclosing_package_body', child(rect,'start')[1:] == [-12.7,17.78] and child(rect,'end')[1:] == [8.89,-17.78])
        check(path+'_all_RGB_channels_in_same_body', [t[1] for t in children(units[0],'text')] == ['R','G','B'])
        xy = [xy[1:] for poly in children(units[0],'polyline') for xy in children(child(poly,'pts'),'xy')]
        check(path+'_internal_drawing_inside_body', all(-12.7 <= x <= 8.89 and -17.78 <= y <= 17.78 for x,y in xy))
        definition[1] = 'D1'
        if sym is not None:
            check('library_and_embedded_symbol_identical', definition == sym)
        sym = definition

    pcb = p.LoadBoard(str(ROOT/'PCB/main/smove-r2-main.kicad_pcb'))
    fps = {f.GetReference():f for f in pcb.GetFootprints()}
    f = fps['D1']
    pins = {pad.GetNumber():pad.GetNetname() for pad in f.Pads()}
    check('D1_physical_part_and_four_pad_map', f.GetFPIDAsString() == 'smove-r2-main:LED_LiteOn_LTST-C19HE1WT' and pins == {
        '1':'/Compute/LED_R_K','2':'/Compute/LED_G_K','3':'/Compute/LED_B_K','4':'/3V3_MAIN'})
    check('D1_original_PCB_schematic_association', f.GetPath().AsString() ==
          '/8e261347-838a-5848-981d-f693675e8aa0/eeb5ed75-de0b-5a0c-8356-c78aafd0bbd1/02ba7497-9a8d-56fa-99a3-83e5b10889a3')
    tree = ET.parse(OUT/'post-main-netlist.xml')
    actual = {(n.get('ref'),n.get('pin')):net.get('name') for net in tree.findall('.//nets/net') for n in net.findall('node')}
    check('all_numbered_PCB_pads_match_exact_hierarchical_XML_nets', all(actual.get((ref,pad.GetNumber())) == pad.GetNetname() for ref,fp in fps.items() for pad in fp.Pads() if pad.GetNumber()))
    for color, resistor, pin, mcu in [('R','R11','1','20'),('G','R12','2','21'),('B','R13','3','16')]:
        check('RGB_'+color+'_unchanged_series_drive',
              actual['D1',pin] == actual[resistor,'2'] == '/Compute/LED_'+color+'_K' and
              actual[resistor,'1'] == actual['U1',mcu] == '/Compute/LED_'+color and fps[resistor].GetValue() == '1k')
    for name in ['BOM.csv','pick-and-place.csv']:
        rows = list(csv.DictReader((ROOT/'PCB/main/dist'/name).open()))
        row = [r for r in rows if 'D1' in r['Designator'].split(',')]
        check('D1_one_item_in_'+name, len(row) == 1 and (name != 'BOM.csv' or (row[0]['Quantity'] == '1' and row[0]['Manufacturer Part Number'] == 'LTST-C19HE1WT')))
    for label in ('BOOT','RESET'):
        check(label+'_silk_preserved', len([t for t in pcb.GetDrawings() if isinstance(t,p.PCB_TEXT) and t.GetText()==label and t.GetLayer()==p.F_SilkS and not t.IsMirrored()]) == 1)

    # Exact bytes prove that electrical/physical/fab outputs were not edited to
    # make the schematic checks pass. Documentation/manifest edits excluded.
    paths = sp.check_output(['git','ls-tree','-r','--name-only',BASE,'PCB'],cwd=ROOT,text=True).splitlines()
    fixed = []
    for path in paths:
        file = ROOT/path
        schematic_export = path.startswith('PCB/main/dist/schematic')
        if path.endswith('.md') or path.endswith('/dist/manifest.json') or schematic_export or path in ('PCB/main/compute.kicad_sch','PCB/main/smove-r2-main.kicad_sym'):
            continue
        check('byte_preserved:'+path, file.read_bytes() == git_bytes(path))
        fixed.append({'path':path,'sha256':sha(file.read_bytes())})
    for directory in ('PCB/main','PCB/imu-carrier','housing'):
        folder = ROOT/directory
        inventory = {str(file.relative_to(ROOT)):sha(file.read_bytes()) for file in sorted(folder.rglob('*'))
                     if file.is_file() and file.name != 'manifest.json' and '__pycache__' not in file.parts
                     and not file.name.endswith(('.kicad_prl','.pyc'))}
        check(directory+'_manifest_matches_sources_and_outputs',
              json.loads((folder/'dist/manifest.json').read_text())['files'] == inventory)
    check('exactly_one_placed_D1_symbol', sum(file.read_text().count('(lib_id "smove-r2-main:D1")')
          for file in (ROOT/'PCB/main').glob('*.kicad_sch')) == 1)
    report = dict(status='PASS' if all(checks.values()) else 'FAIL',baseline_commit=BASE,
                  scope='RGB presentation and exact PCB/electrical/fabrication preservation. Revised housing has independent native mechanical and body-frame receipts.',
                  kicad_cli=sp.check_output(['kicad-cli','version'],text=True).strip(),
                  checks=checks,unchanged_files=fixed,
                  D1=dict(footprint=f.GetFPIDAsString(),path=f.GetPath().AsString(),pads=pins),
                  limitations=['Configured ERC/DRC severities only; existing ignores unchanged.',
                               'Legacy main/verify.py has three baseline hierarchy-name failures; see baseline-main-invariants.json.',
                               'Package link audit has a pre-existing missing hierarchy-alignment/README.md.',
                               'Mechanical geometry revised separately; CAD and electrical checks do not establish physical qualification.'])
    (OUT/'rgb-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report['status'],len(checks),'RGB / preservation checks')
    raise SystemExit(0 if all(checks.values()) else 1)


if __name__ == '__main__':
    main()
