#!/usr/bin/python3
"""Add three M3 screw mounting holes with grounded copper rings to the main PCB.

Scope: **mechanical**, additive only.

* Three plated (PTH) 3.2 mm M3 clearance holes, one in each free corner of the
  25 x 30 mm board: top-left, bottom-left, bottom-right. The top-right corner is
  occupied by J2 (battery wire pads) and R3/R4/U8; no 5.5 mm screw-head envelope
  fits there.
* Every hole carries a **5.0 mm copper ring on all four copper layers** (0.90 mm
  annular) assigned to **GND**, with a solder-mask opening so the screw head sees
  the ring. The In1.Cu GND plane already covers all three positions, so the rings
  join the ground node by overlap.
* Nothing else changes: no track, via, zone outline, zone fill, placement, net,
  board outline or design-rule edit. Zones are deliberately **not** refilled - see
  "Zone fill" below.

The footprint is a project-local variant of KiCad's
``MountingHole:MountingHole_3.2mm_M3_Pad``: that standard part carries a 6.4 mm
pad, which needs 3.45 mm of board-edge clearance and does not fit any corner of
this board. 5.0 mm is the largest ring that keeps >=0.25 mm copper-to-edge,
>=0.15 mm foreign-net clearance and a non-overlapping courtyard at all three
places; the 2.75 mm courtyard is the 5.5 mm M3 socket-head envelope.

The holes are ``board_only`` ("not in schematic") and excluded from BOM/position
files, exactly like the removed compact-revision H1: mounting hardware has no
schematic symbol, and this keeps schematic parity at 0.

Zone fill
---------
A fresh ``ZONE_FILLER`` pass on the *unmodified* board already moves the In1 GND
plane (686.25 mm2 -> 654.67 mm2, board-edge inset 0.25 mm -> 0.50 mm), so
refilling here would re-cut copper this revision does not ask for. The three new
rings sit inside the saved fill, that overlap is what makes them ground, and KiCad
reports 0 unconnected items, so the fill is left exactly as saved. ``--geometry``
prints the fill-coverage proof.

Usage:
  python3 scripts/r2/final/m3_mounting_holes.py --check      # verify only
  python3 scripts/r2/final/m3_mounting_holes.py              # apply
  python3 scripts/r2/final/m3_mounting_holes.py --geometry   # pcbnew clearance report
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "PCB/main/smove-r2-main.kicad_pcb"
LIB = ROOT / "PCB/main/assets/smove-r2-main.pretty"

FP_NAME = "MountingHole_3.2mm_M3_Pad_5mm"
LIB_NICK = "smove-r2-main"
PAD_DIA = 5.0
DRILL = 3.2
COURTYARD_R = 2.75
NET = "GND"

# reference -> board coordinates (mm, native frame)
HOLES = [
    ("H1", 103.20, 103.20),   # top-left
    ("H2", 103.20, 126.80),   # bottom-left
    ("H3", 121.80, 126.80),   # bottom-right
]

EXPECT_FOOTPRINTS_BEFORE = 47
EXPECT_TRACKS = 461
EXPECT_ZONES = 4

NS = uuid.uuid5(uuid.NAMESPACE_URL, "https://smove.local/main-pcb")

DESCR = (f"M3 mounting hole: {DRILL:g} mm plated drill with a grounded {PAD_DIA:.1f} mm "
         f"copper ring ({(PAD_DIA - DRILL) / 2:.2f} mm annular), {COURTYARD_R:g} mm courtyard "
         f"= 5.5 mm head envelope. Project-local compact variant of KiCad's "
         f"MountingHole:MountingHole_3.2mm_M3_Pad, whose 6.4 mm pad does not fit the "
         f"25 x 30 mm R2 main board corners.")
TAGS = "mountinghole M3 screw shield ground ring PTH"
PAD_DESC = "M3 screw mounting hole, 3.2 mm PTH, 5.0 mm grounded copper ring"


def uid(*parts: str) -> str:
    return str(uuid.uuid5(NS, "/".join(parts)))


def _body(ref: str, indent: str, net_code: int | None) -> str:
    """Everything after the footprint header: frame fields plus geometry."""
    t, t2, t3 = indent, indent + "\t", indent + "\t\t"
    attr = ("(attr through_hole exclude_from_pos_files exclude_from_bom)" if net_code is None
            else "(attr through_hole board_only exclude_from_pos_files exclude_from_bom)")
    net = "" if net_code is None else f'{t2}(net {net_code} "{NET}")\n'
    key = (lambda k: uid(FP_NAME, k)) if net_code is None else (lambda k: uid(FP_NAME, ref, k))
    return (
        f'{t}(property "Reference" "{ref}"\n'
        f'{t2}(at 0 -3.2 0)\n{t2}(layer "F.Fab")\n{t2}(hide yes)\n'
        f'{t2}(uuid "{key("refprop")}")\n'
        f'{t2}(effects\n{t3}(font\n{t3}\t(size 0.6 0.6)\n{t3}\t(thickness 0.1)\n{t3})\n{t2})\n{t})\n'
        f'{t}(property "Value" "{FP_NAME}"\n'
        f'{t2}(at 0 3.2 0)\n{t2}(layer "F.Fab")\n{t2}(hide yes)\n'
        f'{t2}(uuid "{key("valueprop")}")\n'
        f'{t2}(effects\n{t3}(font\n{t3}\t(size 0.6 0.6)\n{t3}\t(thickness 0.1)\n{t3})\n{t2})\n{t})\n'
        f'{t}(property "Datasheet" ""\n'
        f'{t2}(at 0 0 0)\n{t2}(layer "F.Fab")\n{t2}(hide yes)\n'
        f'{t2}(uuid "{key("datasheet")}")\n'
        f'{t2}(effects\n{t3}(font\n{t3}\t(size 1.27 1.27)\n{t3}\t(thickness 0.15)\n{t3})\n{t2})\n{t})\n'
        f'{t}(property "Description" "{PAD_DESC}"\n'
        f'{t2}(at 0 0 0)\n{t2}(layer "F.Fab")\n{t2}(hide yes)\n'
        f'{t2}(uuid "{key("description")}")\n'
        f'{t2}(effects\n{t3}(font\n{t3}\t(size 1.27 1.27)\n{t3}\t(thickness 0.15)\n{t3})\n{t2})\n{t})\n'
        f'{t}{attr}\n'
        f'{t}(fp_circle\n{t2}(center 0 0)\n{t2}(end {DRILL / 2:g} 0)\n'
        f'{t2}(stroke\n{t3}(width 0.15)\n{t3}(type solid)\n{t2})\n{t2}(fill no)\n'
        f'{t2}(layer "Cmts.User")\n{t2}(uuid "{key("cmts")}")\n{t})\n'
        f'{t}(fp_circle\n{t2}(center 0 0)\n{t2}(end {COURTYARD_R:g} 0)\n'
        f'{t2}(stroke\n{t3}(width 0.05)\n{t3}(type solid)\n{t2})\n{t2}(fill no)\n'
        f'{t2}(layer "F.CrtYd")\n{t2}(uuid "{key("crtyd")}")\n{t})\n'
        f'{t}(fp_circle\n{t2}(center 0 0)\n{t2}(end {PAD_DIA / 2:g} 0)\n'
        f'{t2}(stroke\n{t3}(width 0.05)\n{t3}(type solid)\n{t2})\n{t2}(fill no)\n'
        f'{t2}(layer "F.Fab")\n{t2}(uuid "{key("fab")}")\n{t})\n'
        f'{t}(fp_text user "${{REFERENCE}}"\n'
        f'{t2}(at 0 0 0)\n{t2}(layer "F.Fab")\n{t2}(uuid "{key("fptext")}")\n'
        f'{t2}(effects\n{t3}(font\n{t3}\t(size 0.6 0.6)\n{t3}\t(thickness 0.1)\n{t3})\n{t2})\n{t})\n'
        f'{t}(pad "1" thru_hole circle\n'
        f'{t2}(at 0 0)\n{t2}(size {PAD_DIA:g} {PAD_DIA:g})\n{t2}(drill {DRILL:g})\n'
        f'{t2}(layers "*.Cu" "*.Mask")\n{t2}(remove_unused_layers no)\n{net}'
        f'{t2}(zone_connect 2)\n{t2}(uuid "{key("pad1")}")\n{t})\n'
        f'{t}(embedded_fonts no)\n'
    )


def library_text() -> str:
    """The project-library copy (`assets/smove-r2-main.pretty/<FP_NAME>.kicad_mod`)."""
    return (f'(footprint "{FP_NAME}"\n'
            f'\t(version 20241229)\n\t(generator "pcbnew")\n\t(generator_version "9.0")\n'
            f'\t(layer "F.Cu")\n\t(descr "{DESCR}")\n\t(tags "{TAGS}")\n'
            + _body("REF**", "\t", None) + ')\n')


def board_block(ref: str, x: float, y: float, net_code: int) -> str:
    """One board-frame footprint block, indented with one tab like its neighbours."""
    return (f'\t(footprint "{LIB_NICK}:{FP_NAME}"\n'
            f'\t\t(layer "F.Cu")\n\t\t(uuid "{uid(FP_NAME, ref, "footprint")}")\n'
            f'\t\t(at {x:g} {y:g})\n\t\t(descr "{DESCR}")\n\t\t(tags "{TAGS}")\n'
            + _body(ref, "\t\t", net_code) + '\t)\n')


# ---------------------------------------------------------------------------------------
# S-expression helpers (same approach as scripts/r2/final/silk_outlines.py)
# ---------------------------------------------------------------------------------------
def blk_end(s: str, i: int) -> int:
    depth, j, n = 0, i, len(s)
    while j < n:
        c = s[j]
        if c == '"':
            j += 1
            while j < n and s[j] != '"':
                j += 2 if s[j] == "\\" else 1
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return j + 1
        j += 1
    raise ValueError("unbalanced parentheses")


def children(s: str, i: int, j: int):
    out, k = [], i + 1
    while k < j - 1:
        if s[k] == "(":
            e = blk_end(s, k)
            out.append((k, e))
            k = e
        elif s[k] == '"':
            k += 1
            while s[k] != '"':
                k += 2 if s[k] == "\\" else 1
            k += 1
        else:
            k += 1
    return out


def head(s: str, span) -> str:
    return re.match(r'\(\s*([^\s()"]+)', s[span[0]:span[1]]).group(1)


def footprint_spans(text: str):
    out = []
    for span in children(text, 0, len(text)):
        if head(text, span) != "footprint":
            continue
        body = text[span[0]:span[1]]
        found = re.search(r'\(property "Reference" "([^"]+)"', body)
        out.append((found.group(1) if found else None, span))
    return out


def net_code_of(text: str) -> int:
    for span in children(text, 0, len(text)):
        if head(text, span) == "net":
            m = re.match(r'\(net\s+(\d+)\s+"GND"', text[span[0]:span[1]])
            if m:
                return int(m.group(1))
    raise SystemExit("net GND not found in the board file")


def strip_holes(text: str) -> str:
    """Board text with every H* mounting hole removed (the 'nothing else changed' diff)."""
    refs = {ref for ref, _, _ in HOLES}
    for ref, span in sorted(footprint_spans(text), key=lambda r: r[1][0], reverse=True):
        if ref in refs:
            start = text.rfind("\n", 0, span[0])
            text = text[:start] + text[span[1]:]
    return text


# ---------------------------------------------------------------------------------------
# apply / check
# ---------------------------------------------------------------------------------------
def apply_edit(text: str, apply_changes: bool):
    net_code = net_code_of(text)
    spans = footprint_spans(text)
    present = {ref for ref, _ in spans}
    missing = [(ref, x, y) for ref, x, y in HOLES if ref not in present]
    if not missing:
        return text, "already present", net_code
    label = [ref for ref, _, _ in missing]
    if not apply_changes:
        return text, f"would add {label}", net_code
    insert_at = max(span[1] for _, span in spans)
    blocks = "\n".join(board_block(ref, x, y, net_code).rstrip("\n") for ref, x, y in missing)
    return text[:insert_at] + "\n" + blocks + text[insert_at:], f"added {label}", net_code


PAD_RE = re.compile(
    r'\(pad "1" thru_hole (?P<shape>[a-z]+)\n'
    r'\t\t\t\(at (?P<x>[-.\d]+) (?P<y>[-.\d]+)\)\n'
    r'\t\t\t\(size (?P<w>[-.\d]+) (?P<h>[-.\d]+)\)\n'
    r'\t\t\t\(drill (?P<drill>[-.\d]+)\)\n'
    r'\t\t\t\(layers (?P<layers>[^\n]+)\)\n'
    r'\t\t\t\(remove_unused_layers no\)\n'
    r'\t\t\t\(net (?P<net>\d+) "GND"\)\n'
    r'\t\t\t\(zone_connect (?P<zc>\d+)\)')


def verify_text(text: str, before: str, net_code: int):
    report, ok = {}, True
    spans = footprint_spans(text)
    by_ref = dict(spans)
    report["footprint_count"] = len(spans)
    report["track_count"] = len(re.findall(r"\n\t\(segment\b", text)) + \
        len(re.findall(r"\n\t\(via\b", text))
    report["zone_count"] = len(re.findall(r"\n\t\(zone\b", text))
    ok &= report["footprint_count"] == EXPECT_FOOTPRINTS_BEFORE + len(HOLES)
    ok &= report["track_count"] == EXPECT_TRACKS
    ok &= report["zone_count"] == EXPECT_ZONES

    holes = {}
    for ref, x, y in HOLES:
        if ref not in by_ref:
            holes[ref] = {"present": False, "ok": False}
            ok = False
            continue
        block = text[by_ref[ref][0]:by_ref[ref][1]]
        at = re.search(r"\(at ([-.\d]+) ([-.\d]+)\)", block).groups()
        pad = PAD_RE.search(block)
        entry = {"present": True, "at": [float(at[0]), float(at[1])], "expected_at": [x, y],
                 "board_only": "(attr through_hole board_only exclude_from_pos_files exclude_from_bom)"
                               in block}
        if pad:
            entry.update({
                "pad_shape": pad.group("shape"),
                "pad_size_mm": [float(pad.group("w")), float(pad.group("h"))],
                "drill_mm": float(pad.group("drill")),
                "pad_layers": pad.group("layers"),
                "net_code": int(pad.group("net")),
                "zone_connect": int(pad.group("zc")),
            })
        entry["ok"] = bool(
            pad and entry["at"] == [x, y] and pad.group("shape") == "circle"
            and float(pad.group("w")) == PAD_DIA and float(pad.group("h")) == PAD_DIA
            and float(pad.group("drill")) == DRILL
            and '*.Cu' in pad.group("layers") and '*.Mask' in pad.group("layers")
            and int(pad.group("net")) == net_code and int(pad.group("zc")) == 2
            and entry["board_only"])
        ok &= entry["ok"]
        holes[ref] = entry
    report["holes"] = holes

    clean = strip_holes(text)
    report["other_content_unchanged"] = clean == strip_holes(before)
    ok &= report["other_content_unchanged"]
    report["ok"] = bool(ok)
    return report, ok


def geometry_report():
    import math
    import pcbnew

    def mm(v):
        return v / 1e6

    def seg_dist(p, a, b):
        (ax, ay), (bx, by) = a, b
        dx, dy = bx - ax, by - ay
        l2 = dx * dx + dy * dy
        t = 0.0 if l2 == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / l2))
        return math.hypot(p[0] - (ax + t * dx), p[1] - (ay + t * dy))

    def rings(ps):
        out = []
        for i in range(ps.OutlineCount()):
            for pp in [ps.COutline(i)] + [ps.CHole(i, j) for j in range(ps.HoleCount(i))]:
                out.append([(mm(pp.CPoint(k).x), mm(pp.CPoint(k).y)) for k in range(pp.PointCount())])
        return out

    def in_ring(p, ring):
        inside = False
        n = len(ring)
        for i in range(n):
            x1, y1 = ring[i]
            x2, y2 = ring[(i + 1) % n]
            if (y1 > p[1]) != (y2 > p[1]) and p[0] < (x2 - x1) * (p[1] - y1) / (y2 - y1) + x1:
                inside = not inside
        return inside

    def dist_rings(p, rs):
        best = 1e9
        for ring in rs:
            if in_ring(p, ring):
                return 0.0
            for i in range(len(ring)):
                best = min(best, seg_dist(p, ring[i], ring[(i + 1) % len(ring)]))
        return best

    b = pcbnew.LoadBoard(str(BOARD))
    pads, tracks, courts, edges = [], [], [], []
    for f in b.GetFootprints():
        for pad in f.Pads():
            s = pcbnew.SHAPE_POLY_SET()
            pad.TransformShapeToPolygon(s, pcbnew.F_Cu, 0, pcbnew.FromMM(0.005), pcbnew.ERROR_INSIDE)
            pads.append((pad.GetNetname(), rings(s), f"{f.GetReference()}.{pad.GetNumber()}"))
    for t in b.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            tracks.append((t.GetNetname(), (mm(t.GetPosition().x), mm(t.GetPosition().y)), None,
                           t.GetWidth(pcbnew.F_Cu) / 2e6))
        else:
            tracks.append((t.GetNetname(), (mm(t.GetStart().x), mm(t.GetStart().y)),
                           (mm(t.GetEnd().x), mm(t.GetEnd().y)), t.GetWidth() / 2e6))
    for f in b.GetFootprints():
        for ring in rings(f.GetCourtyard(pcbnew.F_CrtYd)):
            courts.append((f.GetReference(), ring))
    for d in b.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts:
            edges.append(((mm(d.GetStart().x), mm(d.GetStart().y)),
                          (mm(d.GetEnd().x), mm(d.GetEnd().y))))
    areas = [(z.GetZoneName(), rings(z.Outline())) for z in b.Zones() if z.GetIsRuleArea()]
    plane = [z for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname() == NET]

    holes = {}
    for ref, x, y in HOLES:
        p = (x, y)
        edge = min(seg_dist(p, a, c) for a, c in edges)
        fc, fwho = 1e9, None
        for netname, rs, tag in pads:
            if netname == NET:
                continue
            d = dist_rings(p, rs)
            if d < fc:
                fc, fwho = d, f"pad {tag} [{netname}]"
        for netname, a, c, r in tracks:
            if netname == NET:
                continue
            d = (max(0.0, math.hypot(p[0] - a[0], p[1] - a[1]) - r) if c is None
                 else max(0.0, seg_dist(p, a, c) - r))
            if d < fc:
                fc, fwho = d, f"track/via [{netname}]"
        cy, cwho = 1e9, None
        for r, ring in courts:
            if r == ref:
                continue
            d = dist_rings(p, [ring])
            if d < cy:
                cy, cwho = d, r
        hit = [n for n, rs in areas if any(in_ring(p, r) for r in rs)]
        filled = any(z.GetFilledPolysList(pcbnew.In1_Cu).Contains(
            pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))) for z in plane)
        holes[ref] = {
            "at": [x, y],
            "ring_radius_mm": PAD_DIA / 2,
            "copper_to_board_edge_mm": round(edge - PAD_DIA / 2, 3),
            "drill_to_board_edge_mm": round(edge - DRILL / 2, 3),
            "foreign_net_copper_clearance_mm": round(fc - PAD_DIA / 2, 3),
            "nearest_foreign_copper": fwho,
            "courtyard_gap_mm": round(cy - COURTYARD_R, 3),
            "nearest_courtyard": cwho,
            "centre_in_rule_area": hit or None,
            "inside_saved_gnd_plane": bool(filled),
        }
    conn = b.GetConnectivity()
    conn.Build(b)
    return {
        "holes": holes,
        "gnd_net_code": b.FindNet(NET).GetNetCode(),
        "unconnected_items": conn.GetUnconnectedCount(False),
        "ok": all(h["copper_to_board_edge_mm"] >= 0.25
                  and h["foreign_net_copper_clearance_mm"] >= 0.15
                  and h["courtyard_gap_mm"] >= 0.0
                  and h["centre_in_rule_area"] is None
                  and h["inside_saved_gnd_plane"]
                  for h in holes.values()),
    }


def main() -> int:
    global BOARD, LIB
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="verify only, write nothing")
    ap.add_argument("--geometry", action="store_true", help="include the pcbnew clearance report")
    ap.add_argument("--json", type=Path, help="write the report to this path")
    ap.add_argument("--board", type=Path, default=None, help="board file (default: PCB/main)")
    ap.add_argument("--lib", type=Path, default=None, help="project-local footprint library")
    args = ap.parse_args()

    BOARD = args.board or BOARD
    LIB = args.lib or LIB
    lib_path = LIB / f"{FP_NAME}.kicad_mod"
    want_lib = library_text()

    # --- apply ------------------------------------------------------------------------
    before = BOARD.read_text()
    text, status, net_code = apply_edit(before, apply_changes=not args.check)
    if not args.check and status.startswith("added"):
        if lib_path.exists() and lib_path.read_text() != want_lib:
            print(f"refusing: {lib_path} exists with different content", file=sys.stderr)
            return 2
        lib_path.write_text(want_lib)
        BOARD.write_text(text)

    # --- verify whatever is on disk now -------------------------------------------------
    report, ok = verify_text(BOARD.read_text(), before, net_code)
    report["status"] = status
    report["gnd_net_code"] = net_code
    try:
        report["library_footprint"] = str(lib_path.resolve().relative_to(ROOT))
    except ValueError:
        report["library_footprint"] = str(lib_path)
    report["library_up_to_date"] = lib_path.exists() and lib_path.read_text() == want_lib
    ok &= report["library_up_to_date"]

    if all(h.get("present") for h in report["holes"].values()):
        on_disk = BOARD.read_text()
        spans = dict(footprint_spans(on_disk))
        for ref, x, y in HOLES:
            block = on_disk[spans[ref][0]:spans[ref][1]]
            for token in (f'(at {x:g} {y:g})', f'(uuid "{uid(FP_NAME, ref, "footprint")}")'):
                block = block.replace(token, "")
            want = board_block(ref, x, y, net_code)
            have = block[block.index("(property"):block.rindex("(embedded_fonts")]
            want = want[want.index("(property"):want.rindex("(embedded_fonts")]
            same = [l for l in have.splitlines() if l.strip()] == \
                [l for l in want.splitlines() if l.strip()]
            report["holes"][ref]["board_matches_library_geometry"] = same
            ok &= same

    if args.geometry and report["holes"]["H1"].get("present"):
        geo = geometry_report()
        report["geometry"] = geo
        ok &= geo["ok"]

    report["ok"] = bool(ok)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2) + "\n")

    print(json.dumps(report, indent=2))
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
