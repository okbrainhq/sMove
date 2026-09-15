#!/usr/bin/python3
"""Add component outlines and pin-1 indicators to the main board's silkscreen.

Scope (main PCB only; no copper, placement, net or schematic change):

* U1 ESP32-C3-MINI-1  - the 13.2 x 16.6 mm module body outline and the antenna
  keepout boundary are copied from F.Fab to F.SilkS, so the module body is visible
  in the fabrication silkscreen (and therefore in JLCPCB's placement preview, which
  is generated from uploaded Gerbers - F.Fab is not part of that set).
* U6 BQ24074RGTR       - the QFN had no silkscreen at all and therefore no pin-1
  indicator.  Adds three corner brackets plus a filled pin-1 triangle at the
  CHG-TS (pad 1) corner.
* D1 LTST-C19HE1WT     - replaces the two short library silkscreen lines with a
  closed outline that stays outside the land pattern and leaves a gap over the
  pad-1 corner (the pin-1 cue used by the library footprint).

The same geometry is applied to the project-local library footprints so the board
does not diverge from its libraries (KiCad DRC library check).

Usage:
  python3 scripts/r2/final/silk_outlines.py --check   # verify only, no writes
  python3 scripts/r2/final/silk_outlines.py           # apply
"""
from __future__ import annotations

import math
import re
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "PCB/main/smove-r2-main.kicad_pcb"
LIB = ROOT / "PCB/main/assets/smove-r2-main.pretty"
SILK_WIDTH = 0.12
FILL_WIDTH = 0.1

# --- footprint silkscreen specifications (footprint-local mm) ------------------------------
# lines: (start_x, start_y, end_x, end_y) drawn on F.SilkS
# polys: list of point lists, filled on F.SilkS
# drop_silk_lines: existing F.SilkS segments (start,end) to remove first
SPECS = {
    # 3 x 3 mm QFN-16: three corner brackets in the free diagonal corners, and the
    # pin-1 (TS, pad 1) corner gets the same outside arrowhead the IMU U2 uses -
    # apex on the silk corner, base 0.33 mm further out, pointing straight at pad 1.
    "U6": dict(library="BQ24074_RGT",
               lines=[(-1.6, 1.15, -1.6, 1.6), (-1.6, 1.6, -1.15, 1.6),
                      (1.15, 1.6, 1.6, 1.6), (1.6, 1.6, 1.6, 1.15),
                      (1.6, -1.15, 1.6, -1.6), (1.6, -1.6, 1.15, -1.6)],
               polys=[[(-1.6, -1.6), (-1.84, -1.93), (-1.36, -1.93)]],
               drop_silk_lines=[],
               drop_polys=[[(-1.6, -1.6), (-1.6, -1.15), (-1.15, -1.6)]]),
    # ESP32-C3-MINI-1: body outline copied from F.Fab and clipped to the board (the
    # module overhangs the 100.0 mm board edge with its antenna end, so only the
    # board-side part of the outline is drawn).  The F.Fab antenna-boundary line sits
    # exactly on the board edge, and the F.Fab corner chamfer runs across the left
    # anchor pad (-5.95,-2.25); both are therefore not copied.
    "U1": dict(library="ESP32-C3-MINI-1",
               lines=[(-6.6, 8.3, -6.6, -2.7), (6.6, 8.3, 6.6, -2.7),
                      (-6.6, 8.3, 6.6, 8.3)],
               polys=[],
               drop_silk_lines=[]),
    # 1.6 x 1.6 mm 4-pad LED: closed outline outside the land pattern, open over the
    # pad-1 corner (the pin-1 cue the library footprint already used).
    "D1": dict(library="LED_LiteOn_LTST-C19HE1WT",
               lines=[(-0.95, -0.35, -0.95, 1.32), (0.95, -1.32, 0.95, 1.32),
                      (-0.95, 1.32, 0.95, 1.32), (0.95, -1.32, -0.45, -1.32)],
               polys=[],
               drop_silk_lines=[((-0.95, -0.35), (-0.95, 0.8)),
                                ((0.95, -0.8), (0.95, 0.8))]),
    # USB-C receptacle: the footprint ships its silkscreen on F.Fab only (the five
    # standard shell lines), so the connector is invisible in the fabrication silk and
    # in JLCPCB's placement preview.  This restores a shell outline on F.SilkS: both
    # long sides and the pad-side end, offset outwards past the shell mounting pads
    # (S1 reaches +/-4.82 mm) and the A1..B12 pad row (y = -4.77 mm), and clipped
    # 0.22 mm short of the 124.45 mm board-edge notch.  The mouth face is off-board.
    "J1": dict(library="USB_C_Receptacle_HRO_TYPE-C-31-M-12",
               lines=[(5.0, -3.65, 5.0, 3.13), (-5.0, -3.65, -5.0, 3.13),
                      (-5.0, -5.0, 5.0, -5.0)],
               polys=[],
               drop_silk_lines=[]),
}


# --- tiny S-expression helpers ------------------------------------------------------------
def blk_end(s, i):
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


def children(s, i, j):
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


def head(s, span):
    return re.match(r'\(\s*([^\s()"]+)', s[span[0]:span[1]]).group(1)


def footprints(text):
    """Return {reference: (start, end)} for every footprint in a board file."""
    out = {}
    for span in children(text, 0, len(text)):
        if head(text, span) != "footprint":
            continue
        block = text[span[0]:span[1]]
        found = re.search(r'\(property "Reference" "([^"]+)"', block)
        out[found.group(1)] = span
    return out


def fmt(value):
    return f"{value:g}"


def line_sexp(x0, y0, x1, y1, indent, width=SILK_WIDTH):
    pad = "\t" * indent
    inner = "\t" * (indent + 1)
    inner2 = "\t" * (indent + 2)
    return (f"{pad}(fp_line\n"
            f"{inner}(start {fmt(x0)} {fmt(y0)})\n"
            f"{inner}(end {fmt(x1)} {fmt(y1)})\n"
            f"{inner}(stroke\n{inner2}(width {fmt(width)})\n{inner2}(type solid))\n"
            f"{inner}(layer \"F.SilkS\")\n"
            f"{inner}(uuid \"{uuid.uuid4()}\"))\n")


def poly_sexp(points, indent, width=FILL_WIDTH):
    pad = "\t" * indent
    inner = "\t" * (indent + 1)
    inner2 = "\t" * (indent + 2)
    pts = " ".join(f"(xy {fmt(x)} {fmt(y)})" for x, y in points)
    return (f"{pad}(fp_poly\n"
            f"{inner}(pts\n{inner2}{pts})\n"
            f"{inner}(stroke\n{inner2}(width {fmt(width)})\n{inner2}(type solid))\n"
            f"{inner}(fill yes)\n"
            f"{inner}(layer \"F.SilkS\")\n"
            f"{inner}(uuid \"{uuid.uuid4()}\"))\n")


def silk_geometry(text, span):
    """F.SilkS (lines, polys) of one footprint block, in local mm."""
    block = text[span[0]:span[1]]
    lines, polys = [], []
    for child in children(block, 0, len(block)):
        kind = head(block, child)
        body = block[child[0]:child[1]]
        if '(layer "F.SilkS")' not in body:
            continue
        if kind == "fp_line":
            start = re.search(r"\(start ([-\d.]+) ([-\d.]+)\)", body)
            end = re.search(r"\(end ([-\d.]+) ([-\d.]+)\)", body)
            lines.append(((float(start.group(1)), float(start.group(2))),
                          (float(end.group(1)), float(end.group(2)))))
        elif kind == "fp_poly":
            polys.append([(float(x), float(y)) for x, y in
                          re.findall(r"\(xy ([-\d.]+) ([-\d.]+)\)", body)])
    return lines, polys


def seg_rect_distance(a, b, rect):
    """Shortest distance between segment a-b and axis-aligned rect (x0,y0,x1,y1)."""
    (ax, ay), (bx, by) = a, b
    x0, y0, x1, y1 = rect
    if max(ax, bx) < x0 or min(ax, bx) > x1 or max(ay, by) < y0 or min(ay, by) > y1:
        dx = max(x0 - max(ax, bx), 0, min(ax, bx) - x1)
        dy = max(y0 - max(ay, by), 0, min(ay, by) - y1)
        return math.hypot(dx, dy)
    return 0.0


def pad_rects(text, span):
    """Pad bounding rectangles in footprint-local mm (rect/roundrect pads only).

    A pad's rectangle is only swapped when the pad's angle is 90 degrees away from the
    footprint's angle: KiCad stores the pad angle in the board frame here, and the
    footprint's own rotation is applied on top of the file's (size w h).
    """
    block = text[span[0]:span[1]]
    fp_at = re.search(r"\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)", block)
    fp_angle = float(fp_at.group(3) or 0)
    rects = []
    for child in children(block, 0, len(block)):
        if head(block, child) != "pad":
            continue
        body = block[child[0]:child[1]]
        at = re.search(r"\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)", body)
        size = re.search(r"\(size ([-\d.]+) ([-\d.]+)\)", body)
        x, y = float(at.group(1)), float(at.group(2))
        w, h = float(size.group(1)), float(size.group(2))
        pad_angle = float(at.group(3) or 0)
        if (pad_angle - fp_angle) % 180 == 90:
            w, h = h, w
        rects.append((x - w / 2, y - h / 2, x + w / 2, y + h / 2))
    return rects


def expected_spec_geometry(spec):
    return ([tuple(map(float, line)) for line in spec["lines"]],
            [tuple((float(x), float(y)) for x, y in poly) for poly in spec["polys"]])


def drop_shapes(block, kind, wanted, apply_changes, ref):
    """Delete F.SilkS `kind` children whose geometry matches one of `wanted`."""
    wanted = {tuple((float(x), float(y)) for x, y in shape) for shape in wanted}
    spans = []
    for child in children(block, 0, len(block)):
        if head(block, child) != kind:
            continue
        body = block[child[0]:child[1]]
        if '(layer "F.SilkS")' not in body:
            continue
        if kind == "fp_poly":
            points = [(float(x), float(y))
                      for x, y in re.findall(r"\(xy ([-\d.]+) ([-\d.]+)\)", body)]
            if tuple(points) in wanted:
                spans.append(child)
    for start, end in sorted(spans, reverse=True):
        line_start = block.rfind("\n", 0, start) + 1
        line_end = block.find("\n", end) + 1
        block = block[:line_start] + block[line_end:]
    if len(spans) != len(wanted) and apply_changes:
        raise SystemExit(f"{ref}: expected to remove {len(wanted)} superseded {kind} "
                         f"item(s), removed {len(spans)}")
    return block, len(spans)


def has_geometry(lines, polys, expected_lines, expected_polys):
    for want in expected_lines:
        if tuple(want) not in [tuple(l[0]) + tuple(l[1]) for l in lines]:
            return False
    for want in expected_polys:
        if tuple(want) not in [tuple(p) for p in polys]:
            return False
    return True


# --- edits --------------------------------------------------------------------------------
def _drop_lines(block, wanted, indent, apply_changes, ref):
    """Remove the listed silk segments *if present* (a missing one is already the goal)."""
    tabs = "\t" * indent
    present = {tuple(l[0]) + tuple(l[1]) for l in silk_geometry(block, (0, len(block)))[0]}
    removed = 0
    for start, end in wanted:
        if tuple(start) + tuple(end) not in present:
            continue
        pattern = (tabs + r"\(fp_line\n"
                   + tabs + r"\t\(start " + re.escape(fmt(start[0])) + " " + re.escape(fmt(start[1])) + r"\)\n"
                   + tabs + r"\t\(end " + re.escape(fmt(end[0])) + " " + re.escape(fmt(end[1])) + r"\)\n"
                   + r"(?:.*?\n)*?" + tabs + r"\)\n")
        block, count = re.subn(pattern, "", block, count=1)
        if count != 1 and apply_changes:
            raise SystemExit(f"{ref}: could not remove the superseded silk line {start}-{end}")
        removed += count
    return block, removed


def apply_spec(block, spec, indent, apply_changes, ref):
    """Add the spec's missing F.SilkS items and drop its superseded ones.

    Per item, not all-or-nothing, so the same spec also repairs a partially applied
    state (for example a pin-1 marker that has since been redrawn).
    """
    lines, polys = silk_geometry(block, (0, len(block)))
    have_lines = {tuple(l[0]) + tuple(l[1]) for l in lines}
    have_polys = {tuple(p) for p in polys}
    add_lines = [line for line in spec["lines"] if tuple(map(float, line)) not in have_lines]
    add_polys = [poly for poly in spec["polys"]
                 if tuple((float(x), float(y)) for x, y in poly) not in have_polys]

    block, removed_lines = _drop_lines(block, spec.get("drop_silk_lines", []), indent,
                                       apply_changes, ref)
    block, removed_polys = drop_shapes(block, "fp_poly", spec.get("drop_polys", []),
                                       apply_changes, ref)

    if not any((add_lines, add_polys, removed_lines, removed_polys)):
        return block, "already present"

    additions = "".join(line_sexp(*line, indent=indent) for line in add_lines)
    additions += "".join(poly_sexp(points, indent=indent) for points in add_polys)
    if additions:
        last = children(block, 0, len(block))[-1][1]
        block = block[:last] + "\n" + additions.rstrip("\n") + block[last:]
    return block, "updated"


def board_edit(text, ref, spec, apply_changes):
    span = footprints(text)[ref]
    block, status = apply_spec(text[span[0]:span[1]], spec, 2, apply_changes, ref)
    if status == "already present":
        return text, status
    return text[:span[0]] + block + text[span[1]:], status


def library_edit(path, spec, apply_changes):
    text = path.read_text()
    inner = text[text.index("("):]
    root_end = blk_end(inner, 0)
    block, status = apply_spec(inner[:root_end], spec, 1, apply_changes, path.name)
    if status == "already present":
        return text, status
    return text[:text.index("(")] + block + inner[root_end:], status


def verify(text, report):
    spans = footprints(text)
    ok = True
    for ref, spec in SPECS.items():
        span = spans[ref]
        lines, polys = silk_geometry(text, span)
        expected_lines, expected_polys = expected_spec_geometry(spec)
        present = has_geometry(lines, polys, expected_lines, expected_polys)
        rects = pad_rects(text, span)
        clearances = [seg_rect_distance(l[0], l[1], rect)
                      for l in lines for rect in rects]
        clearance = min(clearances) if clearances else float("nan")
        poly_clearances = [min(math.dist(p, (max(r[0], min(p[0], r[2])),
                                             max(r[1], min(p[1], r[3])))) for r in rects)
                           for poly in polys for p in poly]
        poly_clearance = min(poly_clearances) if poly_clearances else float("nan")
        report[ref] = {"silk_present": present, "silk_lines": len(lines),
                       "silk_polys": len(polys),
                       "min_line_to_pad_mm": round(clearance, 3),
                       "min_poly_point_to_pad_mm": round(poly_clearance, 3)}
        ok = ok and present and clearance > 0.099
    return ok


def main():
    check = "--check" in sys.argv
    report, status = {}, {}

    board_text = BOARD.read_text()
    for ref, spec in SPECS.items():
        board_text, board_status = board_edit(board_text, ref, spec, apply_changes=not check)
        status.setdefault(ref, {})["board"] = board_status

    for ref, spec in SPECS.items():
        path = LIB / f"{spec['library']}.kicad_mod"
        new_text, lib_status = library_edit(path, spec, apply_changes=not check)
        status[ref]["library"] = lib_status
        if not check and lib_status == "updated":
            path.write_text(new_text)

    ok = verify(board_text, report)

    # cross-check: board footprint silk geometry must equal the library footprint's
    for ref, spec in SPECS.items():
        path = LIB / f"{spec['library']}.kicad_mod"
        lib_text = path.read_text()
        inner = lib_text[lib_text.index("("):]
        lib_block = inner[:blk_end(inner, 0)]
        lib_lines, lib_polys = silk_geometry(lib_block, (0, len(lib_block)))
        board_lines, board_polys = silk_geometry(board_text, footprints(board_text)[ref])
        same = (sorted(map(str, board_lines)) == sorted(map(str, lib_lines)) and
                sorted(map(str, board_polys)) == sorted(map(str, lib_polys)))
        report[ref]["board_matches_library"] = same
        ok = ok and same

    report = {ref: dict(status[ref], **report[ref]) for ref in SPECS}

    if not check and any(v[k] == "updated" for v in status.values() for k in v):
        BOARD.write_text(board_text)

    for ref in SPECS:
        print(f"{ref}: {report[ref]}")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
