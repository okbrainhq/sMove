#!/usr/bin/env python3
"""KiCad -> JLCPCB fabrication (Gerber) and assembly (BOM/CPL) export.

For one KiCad project directory this writes, into ``<project>/dist/jlcpcb/``:

    gerber.zip          fabrication data: Gerbers + Excellon drills, flat at ZIP root
    bom.csv             JLCPCB assembly BOM (grouped, one row per purchased part)
    pick_and_place.csv  JLCPCB CPL / centroid file (one row per reference)
    export-report.json  validation report - for review, NOT for upload

Everything is generated in a private temporary directory and published only after
every check passes; the project itself is never modified.

JLCPCB part numbers are read from native KiCad fields.  The field name is matched
ignoring case, spaces and punctuation, so ``LCSC``, ``LCSC_Part_Number`` and
``LCSC Part Number`` are the same field.  Values are validated as ``C`` + digits;
a value that is not a catalog number is rejected instead of being uploaded.

Fields are read from both storage places KiCad offers:

* the **board footprints** (``Footprint Properties`` in the PCB editor), and
* the **root schematic** via ``kicad-cli sch export netlist`` (hierarchical sheets
  and multi-unit symbols included).

A part number stored only on the schematic is still exported.  A *conflicting*
part number between the two sources stops the export: the tool never guesses
which of two different parts was meant.

Optional per-part placement correction: a native field ``JLCPCB Rotation Offset``
holding signed degrees (e.g. ``90`` or ``-90``) is added to KiCad's exported
rotation and normalized to ``[0, 360)``.  Use it only after checking JLCPCB's
placement preview for that part.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

# --- native field names -------------------------------------------------------------------
PART_FIELDS = (
    "LCSC",
    "LCSC PN",
    "LCSC Part #",
    "LCSC Part Number",
    "LCSC Part",
    "JLCPCB",
    "JLCPCB PN",
    "JLCPCB Part #",
    "JLCPCB Part Number",
    "JLCPCB Part",
    "JLC",
    "JLC Part #",
)
MPN_FIELDS = ("MPN", "Manufacturer Part Number", "Manufacturer Part #", "Mfr Part #", "Part Number")
MANUFACTURER_FIELDS = ("Manufacturer", "Mfr")
ROTATION_FIELDS = ("JLCPCB Rotation Offset", "JLC Rotation Offset", "Rotation Offset")

LCSC_RE = re.compile(r"^C\d+$")
BOM_HEADER = ("Comment", "Designator", "Footprint", "LCSC Part #", "Quantity", "Manufacturer", "MPN")
CPL_HEADER = ("Designator", "Mid X", "Mid Y", "Layer", "Rotation")
SIDES = {"top": "F.Cu", "bottom": "B.Cu"}
POSITION_SIDES = {"top": "front", "bottom": "back", "both": "both"}
ARTIFACTS = ("gerber.zip", "bom.csv", "pick_and_place.csv", "export-report.json")
GERBER_SUFFIXES = {
    ".gtl", ".g1", ".g2", ".g3", ".g4", ".g5", ".g6", ".gbl",
    ".gts", ".gbs", ".gto", ".gbo", ".gm1", ".gtp", ".gbp", ".drl", ".gbrjob",
}
TOKEN = re.compile(r'"(?:\\.|[^"\\])*"|[()]|[^\s()"]+')
MISSING = ""


class ExportError(Exception):
    """A condition the exporter refuses to work around."""


# --- small helpers ------------------------------------------------------------------------
def normalized(name: str) -> str:
    """Field-name comparison key: case, spaces and punctuation are insignificant."""
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


def natural_key(text: str):
    """Sort R2 before R10 and C1 before C10."""
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", str(text))]


def clean(value) -> str:
    """Normalize a field value; KiCad's ``~`` placeholder means 'not set'."""
    text = "" if value is None else str(value).strip()
    return MISSING if text in ("~",) else text


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


# --- KiCad s-expression reading -----------------------------------------------------------
def parse_sexpr(text: str):
    """Parse a KiCad s-expression file into nested lists of strings."""
    tokens = TOKEN.findall(text)
    stack: list = []
    root: list = []
    for token in tokens:
        if token == "(":
            node: list = []
            if stack:
                stack[-1].append(node)
            else:
                root.append(node)
            stack.append(node)
        elif token == ")":
            if not stack:
                raise ExportError("unbalanced ')' while reading a KiCad file")
            stack.pop()
        else:
            if token.startswith('"'):
                token = token[1:-1].replace('\\"', '"').replace("\\\\", "\\")
            if not stack:
                continue
            stack[-1].append(token)
    if stack:
        raise ExportError("unbalanced '(' while reading a KiCad file")
    if len(root) != 1:
        raise ExportError("expected exactly one top-level s-expression")
    return root[0]


def children(node, name):
    return [item for item in node if isinstance(item, list) and item and item[0] == name]


def child(node, name):
    found = children(node, name)
    return found[0] if found else None


def atom(node, index, default="") -> str:
    if isinstance(node, list) and len(node) > index and not isinstance(node[index], list):
        return str(node[index])
    return default


def pairs(node, name):
    """Read ``(name "key" "value")`` style entries into a dict."""
    result = {}
    for entry in children(node, name):
        if len(entry) > 2:
            result[str(entry[1])] = str(entry[2])
    return result


def flagged(node) -> set:
    return {str(item) for item in node[1:] if not isinstance(item, list)} if node else set()


def read_board(path: Path) -> dict:
    """Read a .kicad_pcb without pcbnew: layers, aux origin, footprints and fields."""
    root = parse_sexpr(path.read_text(encoding="utf-8", errors="replace"))
    if not root or root[0] != "kicad_pcb":
        raise ExportError(f"{path.name} is not a KiCad PCB file")

    layers = []
    for group in children(root, "layers"):
        for entry in group[1:]:
            if isinstance(entry, list) and len(entry) > 1:
                layers.append(str(entry[1]))
    copper = [name for name in layers if name.endswith(".Cu")]

    aux_origin = None
    setup = child(root, "setup")
    origin = child(setup, "aux_axis_origin") if setup else None
    if origin and len(origin) > 2:
        aux_origin = (float(origin[1]), float(origin[2]))

    footprints = []
    for node in children(root, "footprint"):
        lib_id = atom(node, 1)
        layer = atom(child(node, "layer"), 1, "F.Cu")
        at = child(node, "at")
        attrs = flagged(child(node, "attr"))
        fields = pairs(node, "property")
        pads = []
        for pad in children(node, "pad"):
            pad_type = atom(pad, 2)
            pad_layers = {str(item) for item in (child(pad, "layers") or [])[1:]}
            pads.append((pad_type, pad_layers))
        electrical = any(kind in ("smd", "thru_hole", "connect") for kind, _ in pads)
        footprints.append({
            "lib_id": lib_id,
            "footprint": lib_id.split(":")[-1],
            "side": "top" if layer == "F.Cu" else "bottom" if layer == "B.Cu" else layer,
            "layer": layer,
            "x": float(at[1]) if at and len(at) > 1 else 0.0,
            "y": float(at[2]) if at and len(at) > 2 else 0.0,
            "rotation": (float(at[3]) % 360.0) if at and len(at) > 3 else 0.0,
            "attrs": attrs,
            "fields": fields,
            "pads": pads,
            "electrical": electrical,
            "smd": "smd" in attrs or any(kind == "smd" for kind, _ in pads),
            "dnp": "dnp" in attrs,
            "excluded_from_bom": "exclude_from_bom" in attrs,
            "excluded_from_pos": "exclude_from_pos_files" in attrs,
            "ref": clean(fields.get("Reference", "")),
            "value": clean(fields.get("Value", "")),
        })
    return {
        "path": path,
        "layers": layers,
        "copper_layers": copper,
        "aux_origin": aux_origin,
        "footprints": footprints,
    }


def read_netlist(cli: str, schematic: Path, workdir: Path) -> dict:
    """Read schematic symbol fields, including hierarchical sheets."""
    out = workdir / "schematic.net"
    run_cli(cli, ["sch", "export", "netlist", "--format", "kicadsexpr",
                  "-o", str(out), str(schematic)], workdir)
    root = parse_sexpr(out.read_text(encoding="utf-8", errors="replace"))
    symbols = {}
    for group in children(root, "components"):
        for comp in children(group, "comp"):
            ref = clean(atom(child(comp, "ref"), 1))
            fields = {}
            for fields_node in children(comp, "fields"):
                for entry in children(fields_node, "field"):
                    name = atom(child(entry, "name"), 1)
                    if name:
                        fields[name] = clean(atom(entry, 2))
            properties = {}
            for entry in children(comp, "property"):
                name = atom(child(entry, "name"), 1)
                value = atom(child(entry, "value"), 1)
                if name:
                    properties[name] = clean(value)
            symbols[ref] = {
                "value": clean(atom(child(comp, "value"), 1)),
                "footprint": clean(atom(child(comp, "footprint"), 1)).split(":")[-1],
                "fields": fields,
                "properties": properties,
                "excluded_from_bom": "exclude_from_bom" in properties,
                "excluded_from_board": "exclude_from_board" in properties,
            }
    if not symbols:
        raise ExportError("the schematic netlist contains no components")
    return symbols


def read_positions(cli: str, board: Path, workdir: Path, side: str) -> dict:
    """Run KiCad's own position export and index it by reference."""
    out = workdir / "positions.csv"
    run_cli(cli, [
        "pcb", "export", "pos",
        "--format", "csv", "--units", "mm", "--side", POSITION_SIDES[side],
        "--use-drill-file-origin", "-o", str(out), str(board),
    ], workdir)
    with out.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    positions = {}
    for row in rows:
        ref = clean(row.get("Ref"))
        if not ref:
            raise ExportError("KiCad's position file contains a row without a reference")
        if ref in positions:
            raise ExportError(f"KiCad's position file lists {ref} twice")
        positions[ref] = {key: clean(value) for key, value in row.items()}
    if not positions:
        raise ExportError("KiCad's position export produced no placements")
    return positions


def run_cli(cli: str, arguments: list, cwd: Path) -> str:
    """Run KiCad's CLI, always inside the private working directory."""
    command = [cli, *arguments]
    try:
        result = subprocess.run(command, cwd=str(cwd), stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True)
    except FileNotFoundError as error:
        raise ExportError(f"cannot run '{cli}': {error}") from error
    if result.returncode != 0:
        tail = "\n".join(result.stdout.strip().splitlines()[-12:])
        raise ExportError("KiCad CLI failed: " + " ".join(command) + ("\n" + tail if tail else ""))
    return result.stdout


def kicad_version(cli: str) -> str:
    try:
        result = subprocess.run([cli, "version"], stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True)
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except OSError:
        return "unknown"


# --- field resolution ---------------------------------------------------------------------
def field_value(records, aliases, label: str):
    """Return (value, source_label) for the first recognized field with a value."""
    matches = []
    for source, record, fields in records:
        for alias in aliases:
            for name, value in fields.items():
                if normalized(name) == normalized(alias) and clean(value):
                    matches.append((clean(value), f"{source}.{name}"))
    if not matches:
        return MISSING, MISSING
    distinct = {value for value, _ in matches}
    if len(distinct) > 1:
        described = ", ".join(f"{value} ({where})" for value, where in sorted(matches))
        raise ExportError(f"conflicting {label} values: {described}")
    return matches[0][0], matches[0][1]


def part_number(records, extra_fields=()) -> str:
    value, where = field_value(records, tuple(extra_fields) + PART_FIELDS, "JLCPCB/LCSC part number")
    if not value:
        return MISSING
    candidate = value.upper() if value[:1] in ("c", "C") else value
    if not LCSC_RE.match(candidate):
        raise ExportError(
            f"'{value}' ({where}) is not an LCSC/JLCPCB catalog number "
            "(expected 'C' followed by digits)")
    return candidate


def rotation_offset(records) -> float:
    value, where = field_value(records, ROTATION_FIELDS, "rotation offset")
    if not value:
        return 0.0
    try:
        return float(value)
    except ValueError as error:
        raise ExportError(f"'{value}' ({where}) is not a signed number of degrees") from error


# --- assembly selection -------------------------------------------------------------------
def select_assembly(board: dict, symbols: dict, positions: dict, args) -> tuple:
    """Return (rows, skipped, warnings) for the reference set of both CSVs."""
    rows, skipped, warnings = [], [], []
    seen = {}

    for footprint in board["footprints"]:
        ref = footprint["ref"]
        if not ref:
            raise ExportError("a board footprint has no reference designator")
        if ref.endswith("?"):
            raise ExportError(f"{ref} is not annotated; annotate the schematic first")
        if ref in seen:
            raise ExportError(f"reference {ref} appears on more than one board footprint")
        seen[ref] = footprint

    board_refs = set(seen)
    schematic_refs = set(symbols)
    if not args.pcb_only:
        for ref in sorted(schematic_refs - board_refs, key=natural_key):
            warnings.append(f"{ref} is in the schematic but has no board footprint (not exported)")
        for ref in sorted(board_refs - schematic_refs, key=natural_key):
            warnings.append(f"{ref} has a board footprint but no schematic symbol (board data used)")

    for ref in sorted(board_refs, key=natural_key):
        footprint = seen[ref]
        symbol = symbols.get(ref)
        reasons = []
        if footprint["dnp"]:
            reasons.append("Do Not Populate")
        if footprint["excluded_from_bom"]:
            reasons.append("excluded from BOM")
        if footprint["excluded_from_pos"]:
            reasons.append("excluded from position files")
        if not footprint["electrical"]:
            reasons.append("no electrical pads")
        if footprint["smd"] is False and not args.include_through_hole:
            reasons.append("through-hole footprint")
        if args.side != "both" and footprint["side"] != args.side:
            reasons.append(f"{footprint['side']} side")
        if symbol and symbol["excluded_from_board"]:
            reasons.append("excluded from board in the schematic")
        if symbol and symbol["excluded_from_bom"]:
            reasons.append("excluded from BOM in the schematic")
        if reasons:
            skipped.append({"reference": ref, "reason": "; ".join(reasons)})
            continue

        if symbol:
            if symbol["value"] and footprint["value"] and symbol["value"] != footprint["value"]:
                warnings.append(
                    f"{ref}: schematic value '{symbol['value']}' differs from board value "
                    f"'{footprint['value']}' (board value exported)")
            if symbol["footprint"] and footprint["footprint"] and \
                    symbol["footprint"] != footprint["footprint"]:
                warnings.append(
                    f"{ref}: schematic footprint '{symbol['footprint']}' differs from board "
                    f"footprint '{footprint['footprint']}' (board footprint exported)")

        records = [("PCB", footprint, footprint["fields"])]
        if symbol:
            records.append(("schematic", symbol, symbol["fields"]))

        position = positions.get(ref)
        if position is None:
            raise ExportError(f"{ref} is selected for assembly but KiCad exported no position for it")

        board_x, board_y = footprint["x"], footprint["y"]
        origin = board["aux_origin"] or (0.0, 0.0)
        expected_x, expected_y = board_x - origin[0], origin[1] - board_y
        try:
            got_x, got_y, got_rotation = (float(position["PosX"]), float(position["PosY"]),
                                          float(position["Rot"]))
        except (KeyError, ValueError) as error:
            raise ExportError(f"unreadable position for {ref}: {position}") from error
        for axis, expected, got in (("X", expected_x, got_x), ("Y", expected_y, got_y)):
            if abs(expected - got) > 1e-4:
                raise ExportError(
                    f"{ref}: KiCad position {axis}={got:.6f} disagrees with the board file "
                    f"({expected:.6f}); the .kicad_pcb and its plotted position file are out of sync")
        # Self-test: KiCad's own position file must agree with the board file this tool parsed.
        # A bottom-side footprint may be reported with the mirrored angle, so accept either.
        expected_rotation = footprint["rotation"]
        deltas = [abs((got_rotation - expected_rotation + 180.0) % 360.0 - 180.0)]
        if footprint["side"] == "bottom":
            deltas.append(abs((got_rotation + expected_rotation + 180.0) % 360.0 - 180.0))
        if min(deltas) > 1e-3:
            raise ExportError(
                f"{ref}: KiCad rotation {got_rotation} disagrees with the board file "
                f"({expected_rotation}); the .kicad_pcb and its plotted position file are out of sync")

        offset = rotation_offset(records)
        rotation = (got_rotation + offset) % 360.0

        rows.append({
            "reference": ref,
            "value": footprint["value"],
            "footprint": footprint["footprint"],
            "lcsc": part_number(records, args.part_field),
            "mpn": field_value(records, MPN_FIELDS, "MPN")[0],
            "manufacturer": field_value(records, MANUFACTURER_FIELDS, "manufacturer")[0],
            "x": expected_x,
            "y": expected_y,
            "rotation": rotation,
            "side": footprint["side"],
            "rotation_offset": offset,
        })

    if not rows:
        raise ExportError("no component is selected for assembly; check the side/through-hole options")
    return rows, skipped, warnings


def bom_rows(rows: list) -> list:
    """Group references that share value, footprint, part number, manufacturer and MPN."""
    groups: dict = {}
    for row in rows:
        key = (row["value"], row["footprint"], row["lcsc"], row["manufacturer"], row["mpn"])
        groups.setdefault(key, []).append(row)
    output = []
    for key in sorted(groups, key=lambda item: natural_key(
            min((row["reference"] for row in groups[item]), key=natural_key))):
        members = groups[key]
        value, footprint, lcsc, manufacturer, mpn = key
        refs = sorted((row["reference"] for row in members), key=natural_key)
        output.append([value, ", ".join(refs), footprint, lcsc, len(refs), manufacturer, mpn])
    return output


def cpl_rows(rows: list) -> list:
    output = []
    for row in sorted(rows, key=lambda item: natural_key(item["reference"])):
        output.append([
            row["reference"],
            f"{row['x']:.4f}",
            f"{row['y']:.4f}",
            row["side"].capitalize(),
            f"{row['rotation']:.2f}",
        ])
    return output


# --- fabrication output -------------------------------------------------------------------
def gerber_layers(board: dict) -> tuple:
    """Fabrication layers to plot, from the board's own layer stack."""
    copper = list(board["copper_layers"])
    if not copper or copper[:1] != ["F.Cu"] or copper[-1:] != ["B.Cu"]:
        raise ExportError("unexpected copper layer stack; expected F.Cu ... B.Cu")
    fabrication = copper + ["F.Mask", "B.Mask", "F.SilkS", "B.SilkS", "Edge.Cuts", "F.Paste", "B.Paste"]
    available = set(board["layers"])
    return [name for name in fabrication if name in available], copper


def plot_gerbers(cli: str, board: Path, board_data: dict, workdir: Path) -> tuple:
    """Plot Gerbers and drills into workdir/fab and return (files, layers)."""
    layers, copper = gerber_layers(board_data)
    fab = workdir / "fab"
    fab.mkdir()
    run_cli(cli, [
        "pcb", "export", "gerbers",
        "--layers", ",".join(layers),
        "--use-drill-file-origin",
        "-o", str(fab) + os.sep, str(board),
    ], workdir)
    run_cli(cli, [
        "pcb", "export", "drill",
        "--format", "excellon", "--drill-origin", "plot",
        "--excellon-units", "mm", "--excellon-separate-th",
        "-o", str(fab) + os.sep, str(board),
    ], workdir)

    files = sorted(path for path in fab.iterdir() if path.is_file())
    if not files:
        raise ExportError("KiCad plotted no fabrication files")
    for path in files:
        if path.suffix.lower() not in GERBER_SUFFIXES:
            raise ExportError(f"unexpected fabrication file '{path.name}'")
    suffixes = {path.suffix.lower() for path in files}
    missing = {".gtl", ".gbl", ".gts", ".gbs", ".gto", ".gbo", ".gm1"} - suffixes
    if missing:
        raise ExportError("missing expected fabrication layers: " + ", ".join(sorted(missing)))
    drills = [path for path in files if path.suffix.lower() == ".drl"]
    if not drills:
        raise ExportError("KiCad plotted no Excellon drill file")
    if not all("PTH" in path.name.upper() for path in drills):
        raise ExportError("expected separate plated (PTH) and non-plated (NPTH) drill files, got: "
                          + ", ".join(path.name for path in drills))
    if len({path.name for path in files}) != len(files):
        raise ExportError("duplicate fabrication filenames")
    return files, copper


def write_zip(files: list, destination: Path):
    """Write a ZIP whose bytes depend only on the file contents, not on the clock."""
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            info = zipfile.ZipInfo(path.name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())


def write_csv(path: Path, header, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(list(header))
        writer.writerows(rows)


# --- project selection and publishing -----------------------------------------------------
def select_inputs(args):
    project = Path(args.project_dir).expanduser()
    if not project.is_dir():
        raise ExportError(f"project directory not found: {project}")
    boards = sorted(project.glob("*.kicad_pcb"))
    if args.board:
        wanted = Path(args.board).name
        candidates = [path for path in boards if path.name == wanted or path.stem == Path(wanted).stem]
        if not candidates:
            raise ExportError(f"no board named '{args.board}' in {project}")
        boards = candidates
    if len(boards) != 1:
        names = ", ".join(path.name for path in boards) or "none"
        raise ExportError(f"expected exactly one .kicad_pcb in {project}; found: {names} "
                          "(use --board to choose)")
    board = boards[0]

    schematic = None
    if not args.pcb_only:
        if args.schematic:
            schematic = project / args.schematic
            if not schematic.is_file():
                schematic = Path(args.schematic)
        else:
            schematic = board.with_suffix(".kicad_sch")
        if not schematic.is_file():
            candidates = sorted(project.glob("*.kicad_sch"))
            if len(candidates) == 1:
                schematic = candidates[0]
            else:
                names = ", ".join(path.name for path in candidates) or "none"
                raise ExportError(f"cannot choose a root schematic in {project}; found: {names} "
                                  "(use --schematic, or --pcb-only)")
    return project.resolve(), board.resolve(), schematic.resolve() if schematic else None


def protect(destination: Path, names, overwrite: bool):
    if overwrite:
        return
    existing = [name for name in names if (destination / name).exists()]
    if existing:
        raise ExportError("refusing to replace existing output: " + ", ".join(existing) +
                          " (re-run with --overwrite)")


def publish(staged: Path, destination: Path):
    destination.mkdir(parents=True, exist_ok=True)
    published = []
    for name in ARTIFACTS:
        source = staged / name
        temp = destination / (name + ".tmp")
        shutil.copyfile(source, temp)
        os.replace(temp, destination / name)
        published.append(name)
    return published


def export_project(args) -> int:
    project, board, schematic = select_inputs(args)
    destination = Path(args.output).expanduser() if args.output else project / "dist" / "jlcpcb"
    protect(destination, ARTIFACTS, args.overwrite)

    board_data = read_board(board)
    if args.side != "both" and SIDES[args.side] not in board_data["copper_layers"]:
        raise ExportError(f"board has no {SIDES[args.side]} copper layer")

    workdir = Path(tempfile.mkdtemp(prefix="jlcpcb-export-"))
    try:
        positions = read_positions(args.kicad_cli, board, workdir, args.side)
        symbols = {} if args.pcb_only else read_netlist(args.kicad_cli, schematic, workdir)
        rows, skipped, warnings = select_assembly(board_data, symbols, positions, args)
        files, copper = plot_gerbers(args.kicad_cli, board, board_data, workdir)

        missing_numbers = [row["reference"] for row in rows if not row["lcsc"]]
        if missing_numbers and args.require_part_numbers:
            raise ExportError("no JLCPCB/LCSC part number for: " + ", ".join(missing_numbers) +
                              " (add a native 'LCSC' field, or drop --require-part-numbers)")
        for ref in missing_numbers:
            warnings.append(f"{ref}: no JLCPCB/LCSC part number; the BOM row is left blank")

        staged = workdir / "out"
        staged.mkdir()
        write_zip(files, staged / "gerber.zip")
        write_csv(staged / "bom.csv", BOM_HEADER, bom_rows(rows))
        write_csv(staged / "pick_and_place.csv", CPL_HEADER, cpl_rows(rows))

        sources = [board] + ([schematic] if schematic else [])
        sources += sorted(project.glob("*.kicad_sch")) if schematic else []
        source_hashes = {relative(path, project): sha256(path) for path in dict.fromkeys(sources)}

        # A part number may legitimately appear in more than one BOM row (same purchased part,
        # different schematic value).  JLCPCB matches row by row, but flag it for review.
        rows_by_number = {}
        for row in rows:
            if row["lcsc"]:
                rows_by_number.setdefault(row["lcsc"], set()).add(row["value"])
        repeated = {number: sorted(values) for number, values in sorted(rows_by_number.items())
                    if len(values) > 1}

        report = {
            "tool": "scripts/jlcpcb/export.py",
            "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "manufacturing_release": False,
            "note": "Engineering export for review; not a fabrication, assembly or charging release.",
            "kicad_cli": {"executable": args.kicad_cli, "version": kicad_version(args.kicad_cli)},
            "project": {"directory": str(project.resolve()), "board": board.name,
                        "schematic": schematic.name if schematic else None},
            "sources": source_hashes,
            "board": {"copper_layers": copper, "aux_origin_mm": list(board_data["aux_origin"])
                      if board_data["aux_origin"] else None,
                      "footprints": len(board_data["footprints"]),
                      "position_origin": "drill/place file origin"},
            "assembly": {
                "selected": len(rows),
                "bom_rows": len(bom_rows(rows)),
                "layer": args.side,
                "include_through_hole": bool(args.include_through_hole),
                "skipped": skipped,
                "missing_part_numbers": missing_numbers,
                "rotation_offsets_applied": {
                    row["reference"]: row["rotation_offset"] for row in rows if row["rotation_offset"]},
                "part_number_used_by_several_rows": repeated,
                "part_number_source": (
                    "board footprints only (--pcb-only)" if args.pcb_only
                    else "schematic netlist + board footprints"),
            },
            "fabrication": {
                "layers": [name for name in gerber_layers(board_data)[0]],
                "files": {path.name: sha256(path) for path in files},
                "note": "KiCad writes its plot creation date into each Gerber, so these hashes "
                        "change between runs; the plotted geometry does not.",
            },
            "artifacts": {name: sha256(staged / name) for name in ARTIFACTS[:-1]},
            "warnings": warnings,
        }
        (staged / "export-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        published = publish(staged, destination)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    print(f"{board.name}: {len(rows)} assembly parts, {report['assembly']['bom_rows']} BOM rows, "
          f"{len(files)} fabrication files")
    for name in published:
        print(f"  {destination / name}")
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    return 0


# --- command line -------------------------------------------------------------------------
def argument_parser():
    parser = argparse.ArgumentParser(
        prog="export.py", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Part numbers come from native KiCad fields such as 'LCSC' (a JLCPCB catalogue\n"
               "number like C12345).  Add the field to the symbols in the Schematic Editor and\n"
               "to the footprints in the PCB Editor; 'Tools > Update PCB from Schematic' copies\n"
               "the schematic fields onto the footprints.")
    parser.add_argument("project_dir", nargs="?", default="PCB/main",
                        help="directory containing the KiCad project (default: PCB/main)")
    parser.add_argument("--board", help="PCB filename or stem, when the directory holds several")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--schematic", help="root schematic filename (default: same stem as the board)")
    group.add_argument("--pcb-only", action="store_true",
                       help="read part numbers from the board only, ignoring the schematic")
    parser.add_argument("-o", "--output", help="output directory (default: PROJECT_DIR/dist/jlcpcb)")
    parser.add_argument("--overwrite", action="store_true",
                        help="replace only the four named output files after a successful export")
    parser.add_argument("--side", choices=("top", "bottom", "both"), default="both",
                        help="assembly side (default: both); fabrication layers are never filtered")
    parser.add_argument("--include-through-hole", action="store_true",
                        help="also assemble footprints with non-SMD pads (check JLC availability)")
    parser.add_argument("--part-field", action="append", default=[], metavar="NAME",
                        help="extra native field holding an LCSC number (repeatable)")
    parser.add_argument("--require-part-numbers", action="store_true",
                        help="fail instead of warning when a selected part has no LCSC number")
    parser.add_argument("--kicad-cli", default=os.environ.get("KICAD_CLI", "kicad-cli"),
                        help="KiCad CLI executable (default: $KICAD_CLI or kicad-cli)")
    return parser


def main(argv=None) -> int:
    args = argument_parser().parse_args(argv)
    try:
        return export_project(args)
    except ExportError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    except OSError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
