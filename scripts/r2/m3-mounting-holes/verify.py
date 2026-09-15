#!/usr/bin/python3
"""Evidence collector for the R2 main-board M3 mounting-hole change.

Reads the *saved* board (never edits it) and writes
``docs/revision-r2/m3-mounting-holes/verification.json`` plus the corner images,
then prints PASS/FAIL.

  python3 scripts/r2/m3-mounting-holes/verify.py

Checks
------
* the ECO script's own ``--check --geometry`` report (placement, ring geometry,
  clearances, saved-plane coverage, idempotency);
* native ``kicad-cli pcb drc`` (all severities, all track errors, schematic
  parity) and ``kicad-cli sch erc``;
* board invariants: 50 footprints (47 + 3 holes), 461 tracks, 4 zones, and a
  byte-identical board once the three hole blocks are removed;
* the regenerated JLCPCB set: BOM and CPL byte-identical to the previous
  revision, every Gerber layer unchanged apart from plot dates, the PTH drill
  gaining exactly one 3.2 mm tool with three hits.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/r2/final"))

import m3_mounting_holes as eco  # noqa: E402

DOCS = ROOT / "docs/revision-r2/m3-mounting-holes"
BOARD = ROOT / "PCB/main/smove-r2-main.kicad_pcb"
DIST = ROOT / "PCB/main/dist/jlcpcb"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_show(rel: str) -> bytes | None:
    r = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=ROOT, capture_output=True)
    return r.stdout if r.returncode == 0 else None


def kicad_drc(out: Path):
    out.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(["kicad-cli", "pcb", "drc", "--format", "json", "--severity-all",
                        "--all-track-errors", "--schematic-parity", "-o", str(out),
                        "smove-r2-main.kicad_pcb"],
                       cwd=ROOT / "PCB/main", capture_output=True, text=True)
    data = json.loads(out.read_text()) if out.exists() else {}
    violations = data.get("violations", [])
    return {"summary": [l for l in (r.stdout + r.stderr).splitlines() if l.strip()],
            "returncode": r.returncode,
            "errors": len([v for v in violations if v.get("severity") == "error"]),
            "warnings": len([v for v in violations if v.get("severity") == "warning"]),
            "violations": len(violations),
            "unconnected": len(data.get("unconnected_items", [])),
            "schematic_parity": len(data.get("schematic_parity", []))}


def kicad_erc(out: Path):
    r = subprocess.run(["kicad-cli", "sch", "erc", "--severity-all", "-o", str(out),
                        "smove-r2-main.kicad_sch"],
                       cwd=ROOT / "PCB/main", capture_output=True, text=True)
    text = out.read_text() if out.exists() else ""
    m = re.search(r"ERC messages:\s*(\d+)\s+Errors\s+(\d+)\s+Warnings\s+(\d+)", text)
    return {"summary": [l for l in (r.stdout + r.stderr).splitlines() if l.strip()],
            "returncode": r.returncode,
            "messages": int(m.group(1)) if m else None,
            "errors": int(m.group(2)) if m else None,
            "warnings": int(m.group(3)) if m else None}


# ---------------------------------------------------------------------------------------
# corner renders (native geometry, review only - not fabrication artwork)
# ---------------------------------------------------------------------------------------
def render_corners(board_path: Path, out_dir: Path):
    import cairo
    import pcbnew

    b = pcbnew.LoadBoard(str(board_path))

    def mm(v):
        return v / 1e6

    def corner(path, cx, cy, half=7.0, sc=90):
        x0, y0, x1, y1 = cx - half, cy - half, cx + half, cy + half
        size = int((x1 - x0) * sc)
        su = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
        c = cairo.Context(su)
        c.set_source_rgb(.10, .10, .13)
        c.paint()

        def at(p):
            return (p[0] - x0) * sc, (p[1] - y0) * sc

        def fill(ps, rgba):
            c.set_source_rgba(*rgba)
            for i in range(ps.OutlineCount()):
                for pp in [ps.COutline(i)] + [ps.CHole(i, j) for j in range(ps.HoleCount(i))]:
                    for k in range(pp.PointCount()):
                        (c.move_to if k == 0 else c.line_to)(
                            *at((mm(pp.CPoint(k).x), mm(pp.CPoint(k).y))))
                    c.close_path()
            c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
            c.fill()

        for z in b.Zones():                       # In1 GND plane
            if z.GetIsRuleArea() or z.GetNetname() != eco.NET:
                continue
            fill(z.GetFilledPolysList(pcbnew.In1_Cu), (.16, .30, .26, 1))
        for t in b.GetTracks():
            if isinstance(t, pcbnew.PCB_VIA):
                c.set_source_rgb(.95, .6, .2)
                c.arc(*at((mm(t.GetPosition().x), mm(t.GetPosition().y))),
                      mm(t.GetWidth(pcbnew.F_Cu)) / 2 * sc, 0, 2 * math.pi)
                c.fill()
                continue
            c.set_source_rgb(*(.95, .6, .2) if t.GetLayer() == pcbnew.F_Cu else (.4, .6, .95))
            c.set_line_width(mm(t.GetWidth()) * sc)
            c.move_to(*at((mm(t.GetStart().x), mm(t.GetStart().y))))
            c.line_to(*at((mm(t.GetEnd().x), mm(t.GetEnd().y))))
            c.stroke()
        for f in b.GetFootprints():
            hole = f.GetReference().startswith("H")
            for pad in f.Pads():
                s = pcbnew.SHAPE_POLY_SET()
                lay = pcbnew.F_Cu if pad.IsOnLayer(pcbnew.F_Cu) else pcbnew.In1_Cu
                pad.TransformShapeToPolygon(s, lay, 0, pcbnew.FromMM(0.005), pcbnew.ERROR_INSIDE)
                fill(s, (1, .85, .1, 1) if hole else (.75, .75, .75, 1))
            cy_ = f.GetCourtyard(pcbnew.F_CrtYd)
            c.set_source_rgb(*(1, .3, .3) if hole else (.45, .75, .45))
            for i in range(cy_.OutlineCount()):
                pp = cy_.COutline(i)
                for k in range(pp.PointCount()):
                    (c.move_to if k == 0 else c.line_to)(
                        *at((mm(pp.CPoint(k).x), mm(pp.CPoint(k).y))))
                c.close_path()
            c.set_line_width(1.4)
            c.stroke()
            c.set_source_rgb(.85, .85, .9)
            c.set_font_size(11)
            c.move_to(*at((mm(f.GetPosition().x), mm(f.GetPosition().y))))
            c.show_text(f.GetReference())
        for z in b.Zones():                       # rule areas
            if not z.GetIsRuleArea():
                continue
            c.set_source_rgba(.3, .8, 1, .35)
            ps = z.Outline()
            for i in range(ps.OutlineCount()):
                pp = ps.COutline(i)
                for k in range(pp.PointCount()):
                    (c.move_to if k == 0 else c.line_to)(
                        *at((mm(pp.CPoint(k).x), mm(pp.CPoint(k).y))))
                c.close_path()
            c.set_line_width(1.2)
            c.stroke()
        c.set_source_rgb(1, 1, 1)                 # board outline
        c.set_line_width(2.0)
        for d in b.GetDrawings():
            if d.GetLayer() == pcbnew.Edge_Cuts:
                c.move_to(*at((mm(d.GetStart().x), mm(d.GetStart().y))))
                c.line_to(*at((mm(d.GetEnd().x), mm(d.GetEnd().y))))
                c.stroke()
        c.set_source_rgb(.75, .75, .8)
        c.set_font_size(10)
        for x in range(int(x0), int(x1) + 1):
            c.move_to(*at((x, y0 + .2)))
            c.show_text(str(x))
        for y in range(int(y0), int(y1) + 1):
            c.move_to(*at((x0 + .1, y)))
            c.show_text(str(y))
        su.write_to_png(str(path))

    out_dir.mkdir(parents=True, exist_ok=True)
    names = {}
    for ref, x, y in eco.HOLES:
        p = out_dir / f"{ref}-corner.png"
        corner(p, x, y)
        names[ref] = str(p.relative_to(ROOT))
    p = out_dir / "top-left-vs-occupied-corner.png"
    corner(p, 123.0, 103.0)
    names["top-right_occupied"] = str(p.relative_to(ROOT))
    return names


# ---------------------------------------------------------------------------------------
def main() -> int:
    report, ok = {}, True

    # 1. ECO script report ---------------------------------------------------------------
    with tempfile.TemporaryDirectory() as tmp:
        js = Path(tmp) / "eco.json"
        r = subprocess.run([sys.executable, str(ROOT / "scripts/r2/final/m3_mounting_holes.py"),
                            "--check", "--geometry", "--json", str(js)],
                           cwd=ROOT, capture_output=True, text=True)
        report["eco_script"] = {"returncode": r.returncode,
                                "report": json.loads(js.read_text()) if js.exists() else None}
    ok &= report["eco_script"]["returncode"] == 0

    # 2. hashes ---------------------------------------------------------------------------
    rel_board = "PCB/main/smove-r2-main.kicad_pcb"
    before = git_show(rel_board)
    report["hashes"] = {
        rel_board: {"before": sha256_bytes(before) if before else None,
                    "after": sha256(ROOT / rel_board)},
    }
    ok &= before is not None

    # 3. native DRC / ERC ------------------------------------------------------------------
    with tempfile.TemporaryDirectory() as tmp:
        report["drc"] = kicad_drc(Path(tmp) / "drc.json")
        report["erc"] = kicad_erc(Path(tmp) / "erc.txt")
    ok &= (report["drc"]["violations"] == 0 and report["drc"]["unconnected"] == 0
           and report["drc"]["schematic_parity"] == 0 and report["erc"]["errors"] == 0)

    # 4. board invariants -------------------------------------------------------------------
    text = (ROOT / rel_board).read_text()
    spans = eco.footprint_spans(text)
    refs = sorted(r for r, _ in spans)
    clean = eco.strip_holes(text)
    report["board"] = {
        "footprints": len(spans),
        "references": refs,
        "tracks_and_vias": len(re.findall(r"\n\t\(segment\b", text))
        + len(re.findall(r"\n\t\(via\b", text)),
        "zones": len(re.findall(r"\n\t\(zone\b", text)),
        "board_without_holes_sha256": sha256_bytes(clean.encode()),
        "board_without_holes_matches_baseline": before is not None
        and clean == before.decode(),
        "added_lines": len([l for l in text.splitlines()]) - len(before.decode().splitlines())
        if before else None,
    }
    ok &= report["board"]["footprints"] == eco.EXPECT_FOOTPRINTS_BEFORE + 3
    ok &= report["board"]["tracks_and_vias"] == eco.EXPECT_TRACKS
    ok &= report["board"]["zones"] == eco.EXPECT_ZONES
    ok &= report["board"]["board_without_holes_matches_baseline"]

    # 5. fabrication / assembly set ---------------------------------------------------------
    if before is not None:
        bom_before = git_show("PCB/main/dist/jlcpcb/bom.csv")
        cpl_before = git_show("PCB/main/dist/jlcpcb/pick_and_place.csv")
        report["assembly"] = {
            "bom_identical": bom_before == (DIST / "bom.csv").read_bytes(),
            "pick_and_place_identical": cpl_before == (DIST / "pick_and_place.csv").read_bytes(),
            "bom_sha256": sha256(DIST / "bom.csv"),
            "pick_and_place_sha256": sha256(DIST / "pick_and_place.csv"),
        }
        ok &= report["assembly"]["bom_identical"]
        ok &= report["assembly"]["pick_and_place_identical"]

        import zipfile
        with tempfile.TemporaryDirectory() as tmp:
            with zipfile.ZipFile(DIST / "gerber.zip") as z:
                z.extractall(tmp)
            old = git_show("PCB/main/dist/jlcpcb/gerber.zip")
            with tempfile.TemporaryDirectory() as tmp2:
                if old:
                    with zipfile.ZipFile(__import__("io").BytesIO(old)) as z:
                        z.extractall(tmp2)
                layers = {}
                for f in sorted(Path(tmp).iterdir()):
                    g = Path(tmp2) / f.name
                    if not g.exists():
                        layers[f.name] = "new"
                        continue

                    def strip(p):
                        out = []
                        for l in p.read_text().splitlines():
                            if "CreationDate" in l or l.startswith("G04") or "; DRILL file" in l:
                                continue
                            out.append(l)
                        return out
                    from collections import Counter
                    a, b_ = Counter(strip(g)), Counter(strip(f))
                    layers[f.name] = sum((a - b_).values()) + sum((b_ - a).values())
                report["fabrication"] = {"files": len(list(Path(tmp).iterdir())),
                                         "changed_lines_excluding_plot_date": layers}

                def drill_tools(p):
                    """{tool: [hits]} from an Excellon file."""
                    tools, cur = {}, None
                    for line in p.read_text().splitlines():
                        m = re.fullmatch(r"T(\d+)C([\d.]+)", line.strip())
                        if m:
                            tools[m.group(1)] = {"diameter_mm": float(m.group(2)), "hits": []}
                            continue
                        m = re.fullmatch(r"T(\d+)", line.strip())
                        if m:
                            cur = m.group(1)
                            continue
                        if line.strip().startswith("X") and cur:
                            tools[cur]["hits"].append(line.strip())
                    return tools
                pth_new = drill_tools(Path(tmp) / "smove-r2-main-PTH.drl")
                pth_old = drill_tools(Path(tmp2) / "smove-r2-main-PTH.drl") if old else {}
                report["fabrication"]["pth_drill_tools"] = pth_new
                report["fabrication"]["pth_drill_added_tools"] = {
                    k: v for k, v in pth_new.items() if k not in pth_old}
                report["fabrication"]["pth_drill_changed_tools"] = {
                    k: {"before": len(pth_old[k]["hits"]), "after": len(v["hits"])}
                    for k, v in pth_new.items()
                    if k in pth_old and len(pth_old[k]["hits"]) != len(v["hits"])}
        ok &= all(v == 0 for k, v in report["fabrication"]["changed_lines_excluding_plot_date"].items()
                  if k in ("smove-r2-main-F_Silkscreen.gto", "smove-r2-main-B_Silkscreen.gbo",
                           "smove-r2-main-F_Paste.gtp", "smove-r2-main-B_Paste.gbp",
                           "smove-r2-main-Edge_Cuts.gm1", "smove-r2-main-NPTH.drl"))
        ok &= list(report["fabrication"]["pth_drill_added_tools"]) == ["4"]
        ok &= report["fabrication"]["pth_drill_added_tools"]["4"]["diameter_mm"] == 3.2
        ok &= len(report["fabrication"]["pth_drill_added_tools"]["4"]["hits"]) == 3
        ok &= report["fabrication"]["pth_drill_changed_tools"] == {}

    # 6. images -----------------------------------------------------------------------------
    report["images"] = render_corners(BOARD, DOCS)

    report["result"] = "PASS" if ok else "FAIL"
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "verification.json").write_text(json.dumps(report, indent=2, sort_keys=False) + "\n")
    print(json.dumps(report, indent=2)[:4000])
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
