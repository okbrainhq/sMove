#!/usr/bin/env python3
"""Replay recovered checks without overwriting recovered sources or historic reports.

Host Python + pcbnew: python3 scripts/freecad/recovery_verify.py electrical
Pinned FreeCAD Python: python3 scripts/freecad/run.py scripts/freecad/recovery_verify.py mechanical
Only report/output paths are redirected in memory. No hardware generation or editing.
"""
from pathlib import Path
import hashlib
import json
import runpy
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / 'docs/recovery/checks'
REPORTS.mkdir(parents=True, exist_ok=True)


def replay(path, replacements):
    text = path.read_text()
    for old, new in replacements:
        assert text.count(old) == 1, (path, old)
        text = text.replace(old, new)
    return exec(compile(text, str(path), 'exec'), {'__file__': str(path), '__name__': '__main__'})


def protected_hashes():
    names = set()
    for name in ('PCB/main/dist/manifest.json', 'housing/dist/manifest.json',
                 'docs/revision-r2/integrated/validation/delivery-manifest.json'):
        names.add(name)
        names.update(json.loads((ROOT / name).read_text())['files'])
    names.update(str(p.relative_to(ROOT)) for p in (ROOT/'docs/revision-r2/integrated').rglob('*') if p.is_file())
    return {n: hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in sorted(names)}


before = protected_hashes()
mode = sys.argv[1]
try:
    if mode == 'electrical':
        sys.path.insert(0, str(ROOT/'scripts/r2/integrated'))
        dest = REPORTS/'electrical'
        (dest/'centered').mkdir(parents=True, exist_ok=True)
        src = ROOT/'docs/revision-r2/integrated/validation/centered/baseline.xml'
        shutil.copyfile(src, dest/'centered/baseline.xml')
        replay(ROOT/'scripts/r2/integrated/verify.py', [
            ("O=ROOT/'docs/revision-r2/integrated/validation'", "O=ROOT/'docs/recovery/checks/electrical'")
        ])
    elif mode == 'mechanical':
        cache = ROOT/'.cache/housing'
        cache.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT/'housing/validation/build.json', cache/'build.json')
        assert (cache/'input-geometry.json').is_file(), 'Run scripts/r2/enclosure/extract.py first (cache-only).'
        dest = REPORTS/'mechanical'
        dest.mkdir(parents=True, exist_ok=True)
        replay(ROOT/'scripts/r2/enclosure/verify.py', [
            ("(OUT/'validation').mkdir(exist_ok=True);(OUT/'validation/mechanical.json')", "(ROOT/'docs/recovery/checks/mechanical').mkdir(exist_ok=True);(ROOT/'docs/recovery/checks/mechanical/mechanical.json')"),
            ("(OUT/'validation/build.json')", "(ROOT/'docs/recovery/checks/mechanical/build.json')")
        ])
    elif mode == 'movement':
        import FreeCAD as A
        doc = A.openDocument(str(ROOT/'housing/smove-r2-enclosure.FCStd'))
        doc.recompute()
        names = ('ViewBase', 'ViewLid', 'ViewMain', 'ViewDivider', 'ViewBattery', 'ViewCables', 'ViewHardware')
        groups = [doc.getObject(n) for n in names]
        sources = {link.LinkedObject.Name: link.LinkedObject for g in groups for link in g.Group}
        def engineering():
            return {n: (str(o.Placement), o.Shape.Volume) for n,o in sources.items()}
        fixed = engineering()
        rows = []
        for group in groups:
            saved = A.Placement(group.Placement)
            others = {g.Name: str(g.Placement) for g in groups if g != group}
            group.Placement.Base = group.Placement.Base + A.Vector(3,5,7)
            doc.recompute()
            rows.append({'part': group.Name, 'kind': 'group', 'passed':
                group.TypeId == 'App::Part' and (group.Placement.Base-saved.Base).Length > 9
                and engineering() == fixed and others == {g.Name:str(g.Placement) for g in groups if g != group}})
            group.Placement = saved
            for link in group.Group:
                old = A.Placement(link.LinkPlacement)
                peer_poses = {p.Name:str(p.LinkPlacement) for g in groups for p in g.Group if p != link}
                link.LinkPlacement = A.Placement(old.Base+A.Vector(2,4,6), old.Rotation)
                doc.recompute()
                rows.append({'part': link.Name, 'kind': 'individual_link', 'passed':
                    (link.LinkPlacement.Base-old.Base).Length > 7 and engineering() == fixed
                    and peer_poses == {p.Name:str(p.LinkPlacement) for g in groups for p in g.Group if p != link}})
                link.LinkPlacement = old
            doc.recompute()
        result = {'status':'PASS' if all(r['passed'] for r in rows) else 'FAIL',
                  'group_count':len(groups), 'individual_part_count':sum(len(g.Group) for g in groups),
                  'checks':rows, 'engineering_sources_unchanged':engineering()==fixed,
                  'saved_document':False}
        (REPORTS/'movement.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))
        A.closeDocument(doc.Name)
        assert result['status']=='PASS'
    else:
        raise ValueError(mode)
finally:
    after = protected_hashes()
    changed = [n for n in before if before[n] != after.get(n)]
    report = {'mode': mode, 'protected_files': len(before), 'changed': changed,
              'status': 'PASS' if not changed else 'FAIL',
              'note': 'Recovered native/source/export/historical report bytes must remain unchanged.'}
    (REPORTS/(mode+'-source-integrity.json')).write_text(json.dumps(report, indent=2)+'\n')
    assert not changed, changed
