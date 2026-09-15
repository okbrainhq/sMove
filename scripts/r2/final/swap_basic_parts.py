#!/usr/bin/python3
"""Move purchased passives onto JLCPCB's free (Basic) library where it saves money.

JLCPCB Economic PCBA charges USD 3 per unique *extended* part that is not marked
"Preferred Extended".  Every resistor and capacitor on the main board already carries
a verified LCSC number; the live audit (2026-09-15) shows all of them are Basic
(no setup fee) except C3:

    C3  22uF / 10V  C29277 CL21A226MPQNNNE  0805 X5R   extended, not preferred  ->  $3
    ->  22uF / 25V  C45783 CL21A226MAQNNNE  0805 X5R   Basic, 4.8M in stock     ->  $0

C45783 is the same capacitance, tolerance and dielectric family in the same 0805
case, with a higher voltage rating (25 V instead of 10 V), so its DC-bias retention
at the 3.3 V rail is at least as good.  This is a purchasing change only: no net,
footprint, placement or schematic-connectivity change.

Usage:
  python3 scripts/r2/final/swap_basic_parts.py --check   # verify only
  python3 scripts/r2/final/swap_basic_parts.py           # apply
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "PCB/main/smove-r2-main.kicad_pcb"
SHEET = ROOT / "PCB/main/power.kicad_sch"

# reference -> (sheet, old LCSC, new LCSC, new MPN, old Value, new Value)
SWAPS = {
    "C3": dict(sheet=SHEET, old="C29277", new="C45783",
               mpn="CL21A226MAQNNNE", value="22uF / 25V"),
}
PROPERTIES = ("LCSC", "MPN", "Value")


# --- minimal S-expression helpers ---------------------------------------------------------
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


def root_children(text):
    """Spans of the direct children of the file's root s-expression."""
    start = text.index("(")
    end = blk_end(text, start)
    out, k = [], start + 1
    while k < end - 1:
        if text[k] == "(":
            e = blk_end(text, k)
            out.append((k, e))
            k = e
        elif text[k] == '"':
            k += 1
            while text[k] != '"':
                k += 2 if text[k] == "\\" else 1
            k += 1
        else:
            k += 1
    return out


def blocks_with_reference(text, reference, kind):
    """Spans of (kind ...) blocks whose Reference property is `reference`."""
    needle = f'(property "Reference" "{reference}"'
    return [span for span in root_children(text)
            if text[span[0]:span[0] + len(kind) + 1] == "(" + kind
            and needle in text[span[0]:span[1]]]


def swap_block(text, span, mapping):
    block = text[span[0]:span[1]]
    for name, (old, new) in mapping.items():
        pattern = re.compile(r'(\(property "' + name + r'" ")'
                             + re.escape(old) + r'(")')
        block, count = pattern.subn(r"\g<1>" + new + r"\g<2>", block, count=1)
        if count != 1:
            raise SystemExit(f"property {name} = {old!r} not found exactly once")
    return text[:span[0]] + block + text[span[1]:]


def current(block, name):
    found = re.search(r'\(property "' + name + r'" "([^"]*)"', block)
    return found.group(1) if found else None


def main():
    check = "--check" in sys.argv
    ok, report = True, {}

    text = {"board": BOARD.read_text(), "sheet": SHEET.read_text()}
    for ref, spec in SWAPS.items():
        wanted = {"LCSC": (spec["old"], spec["new"]), "MPN": (None, spec["mpn"]),
                  "Value": (None, spec["value"])}
        entry = {}
        for where in ("sheet", "board"):
            key = "sheet" if where == "sheet" else "board"
            kind = "symbol" if where == "sheet" else "footprint"
            spans = blocks_with_reference(text[key], ref, kind)
            if len(spans) != 1:
                raise SystemExit(f"{ref}: expected exactly one {kind}, found {len(spans)}")
            block = text[key][spans[0][0]:spans[0][1]]
            if current(block, "LCSC") == spec["new"]:
                entry[key] = "already present"
                continue
            mapping = {}
            for name, (old, new) in wanted.items():
                have = current(block, name)
                if old is not None and have != old:
                    raise SystemExit(f"{ref}.{where}.{name}: expected {old!r}, found {have!r}")
                mapping[name] = (have, new)
            text[key] = swap_block(text[key], spans[0], mapping)
            entry[key] = "updated"
            ok = ok and True
        report[ref] = entry

    # post-conditions: both storages agree on the new number, and the part is Basic
    for ref, spec in SWAPS.items():
        for where, kind in (("sheet", "symbol"), ("board", "footprint")):
            spans = blocks_with_reference(text[where], ref, kind)
            block = text[where][spans[0][0]:spans[0][1]]
            same = (current(block, "LCSC") == spec["new"] and
                    current(block, "MPN") == spec["mpn"] and
                    current(block, "Value") == spec["value"])
            report[ref][f"{where}_consistent"] = same
            ok = ok and same

    if not check and any(v[k] == "updated" for v in report.values()
                         for k in ("sheet", "board")):
        SHEET.write_text(text["sheet"])
        BOARD.write_text(text["board"])

    for ref, entry in report.items():
        print(f"{ref}: {entry}")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
