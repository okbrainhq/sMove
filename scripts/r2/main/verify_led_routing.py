#!/usr/bin/python3
"""Verify the LED-only route completion against the user's b155f03 layout.

Run from the repository root. Only reports are written (under --output).
The native PCB remains authoritative; this script never regenerates routing.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import pcbnew as p

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/r2/integrated'))
from sexp import parse, many, one, val, prop

BASE = 'b155f033f849d78e28f899b0d9df355177c8b5ed'
REL = 'PCB/main/smove-r2-main.kicad_pcb'
RESERVES = {'M3_NW_RESERVE': (103.15, 103.15, 3.0),
            'M3_SE_RESERVE': (121.65, 126.85, 3.0)}
BOOT = 'Net-(U1-GPIO9_{slash}_BOOT)'
LED_NETS = {'/Compute/LED_' + c for c in 'RGB'}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, default=ROOT / '.cache/led-route/verification')
    args = ap.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    raw = subprocess.check_output(['git', 'show', BASE + ':' + REL], cwd=ROOT)
    current = (ROOT / REL).read_bytes()
    old, new = parse(raw.decode()), parse(current.decode())
    checks = {}
    fps = lambda tree: {prop(x, 'Reference'): x for x in many(tree, 'footprint')}
    checks['all_47_footprints_unchanged'] = fps(old) == fps(new) and len(fps(new)) == 47
    ordinary = lambda tree: [x for x in tree if not (isinstance(x, list) and x[0] in {'segment', 'via', 'zone'})]
    checks['outline_stackup_setup_nets_graphics_unchanged'] = ordinary(old) == ordinary(new)
    routes = lambda tree: {val(one(x, 'uuid')[1]): x for k in ('segment', 'via') for x in many(tree, k)}
    before, after = routes(old), routes(new)
    added = after.keys() - before.keys()
    removed = before.keys() - after.keys()
    nets = {x[1]: val(x[2]) for x in many(new, 'net')}
    net = lambda x: nets[one(x, 'net')[1]]
    checks['every_retained_route_token_unchanged'] = all(before[k] == after[k] for k in before.keys() & after.keys())
    checks['only_obsolete_boot_stub_removed'] = (
        len(removed) == 18 and all(net(before[k]) == BOOT for k in removed)
        and Counter(before[k][0] for k in removed) == {'segment': 17, 'via': 1})
    checks['only_led_routes_and_one_ground_via_added'] = (
        all(net(after[k]) in LED_NETS | {'GND'} for k in added)
        and sum(net(after[k]) == 'GND' for k in added) == 1
        and all(after[k][0] == 'via' for k in added if net(after[k]) == 'GND'))
    checks['no_tracks_on_reference_plane'] = all(
        val(one(after[k], 'layer')[1]) != 'In1.Cu' for k in added if after[k][0] == 'segment')
    zones = lambda tree: {val(one(x, 'uuid')[1]): x for x in many(tree, 'zone')}
    oz, nz = zones(old), zones(new)
    config = lambda z: [x for x in z if not (isinstance(x, list) and x[0] == 'filled_polygon')]
    checks['existing_zone_rules_and_configuration_unchanged'] = all(k in nz and config(z) == config(nz[k]) for k, z in oz.items())
    unchanged_files = ['PCB/main/smove-r2-main.kicad_pro', 'PCB/main/smove-r2-main.kicad_dru']
    unchanged_files += [str(f.relative_to(ROOT)) for f in (ROOT / 'PCB/main').glob('*.kicad_sch')]
    checks['schematics_project_and_drc_rules_unchanged'] = all(
        (ROOT / f).read_bytes() == subprocess.check_output(['git', 'show', BASE + ':' + f], cwd=ROOT)
        for f in unchanged_files)

    b = p.LoadBoard(str(ROOT / REL))
    footprints = {f.GetReference(): f for f in b.GetFootprints()}
    padnet = lambda ref, number: next(pad.GetNetname() for pad in footprints[ref].Pads() if pad.GetNumber() == number)
    for color, ref, pin, cathode in [('R', 'R11', '20', '1'), ('G', 'R12', '21', '2'), ('B', 'R13', '16', '3')]:
        checks['LED_' + color + '_mapping'] = (
            padnet('U1', pin) == padnet(ref, '1') == '/Compute/LED_' + color
            and padnet(ref, '2') == padnet('D1', cathode) == '/Compute/LED_' + color + '_K')
    checks['LED_common_anode_3V3'] = padnet('D1', '4') == '/3V3_MAIN'
    layers = [p.F_Cu, p.In1_Cu, p.In2_Cu, p.B_Cu]
    reserve_results = []
    for name, (x, y, radius) in RESERVES.items():
        matches = [z for z in b.Zones() if z.GetZoneName() == name]
        checks[name + '_exists'] = len(matches) == 1
        if len(matches) != 1:
            continue
        z = matches[0]
        checks[name + '_all_copper_and_components_excluded'] = (
            z.GetIsRuleArea() and all(z.IsOnLayer(l) for l in layers)
            and z.GetDoNotAllowTracks() and z.GetDoNotAllowVias()
            and z.GetDoNotAllowCopperPour() and z.GetDoNotAllowPads()
            and z.GetDoNotAllowFootprints())
        circle = p.SHAPE_CIRCLE(p.VECTOR2I(p.FromMM(x), p.FromMM(y)), p.FromMM(radius))
        hits = []
        for t in b.GetTracks():
            if p.SHAPE.Collide(circle, t.GetEffectiveShape()):
                hits.append(t.m_Uuid.AsString())
        for f in b.GetFootprints():
            for pad in f.Pads():
                for layer in layers:
                    if pad.IsOnLayer(layer) and p.SHAPE.Collide(circle, pad.GetEffectiveShape(layer)):
                        hits.append(f.GetReference() + '.' + pad.GetNumber())
            f.BuildCourtyardCaches()
            for layer in [p.F_CrtYd, p.B_CrtYd]:
                courtyard = f.GetCourtyard(layer)
                if courtyard.OutlineCount() and p.SHAPE.Collide(circle, courtyard):
                    hits.append(f.GetReference() + ' courtyard')
        for copper in b.Zones():
            if copper.GetIsRuleArea():
                continue
            for layer in layers:
                if copper.IsOnLayer(layer) and p.SHAPE.Collide(circle, copper.GetFilledPolysList(layer)):
                    hits.append(copper.GetZoneName())
        checks[name + '_physical_copper_and_courtyard_clear'] = not hits
        reserve_results.append(dict(name=name, centre_mm=[x, y], diameter_mm=2*radius, collisions=hits))

    report_path = out / 'drc.json'
    subprocess.run(['kicad-cli', 'pcb', 'drc', '--format', 'json', '--severity-all',
                    '--all-track-errors', '--schematic-parity', '-o', str(report_path),
                    str(ROOT / REL)], cwd=ROOT, check=True)
    drc = json.loads(report_path.read_text())
    checks['zero_drc_errors'] = not any(v['severity'] == 'error' for v in drc['violations'])
    checks['zero_unconnected_items'] = not drc['unconnected_items']
    checks['zero_schematic_parity_issues'] = not drc['schematic_parity']
    expected_warnings = {
        ('lib_footprint_mismatch', '77d30cb7-256c-4e69-8d72-a4f5d795d1a6'),
        ('via_dangling', 'b711e05e-fc77-47c4-8784-87a180f26cb1'),
        ('track_dangling', 'b2aa4d17-9829-40e8-b5b8-05c6a4463628')}
    checks['only_three_known_baseline_warnings'] = {
        (v['type'], v['items'][0]['uuid']) for v in drc['violations']} == expected_warnings
    result = dict(status='PASS' if all(checks.values()) else 'FAIL', base_commit=BASE,
                  board_sha256=hashlib.sha256(current).hexdigest(), checks=checks,
                  added_routes=dict(Counter(after[k][0] for k in added)),
                  removed_routes=dict(Counter(before[k][0] for k in removed)),
                  preserved_route_items=len(before.keys() & after.keys()), reserves=reserve_results,
                  removed_uuids=sorted(removed), added_uuids=sorted(added))
    (out / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in {'removed_uuids', 'added_uuids'}}, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == '__main__':
    raise SystemExit(main())
