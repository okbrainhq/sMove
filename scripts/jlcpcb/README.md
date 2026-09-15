# JLCPCB fabrication + assembly export

`export.py` turns one KiCad project directory into the three files JLCPCB asks for,
plus a validation report:

```text
PCB/main/dist/jlcpcb/
  gerber.zip          fabrication data — Gerbers + Excellon drills
  bom.csv             assembly BOM (grouped purchase rows)
  pick_and_place.csv  CPL / centroid file (one row per reference)
  export-report.json  validation report — for review, NOT for upload
```

Upload `gerber.zip` as the PCB fabrication file, `bom.csv` as the assembly BOM and
`pick_and_place.csv` as the CPL / pick-and-place file.

The project is never modified: KiCad is driven from a private temporary directory and
the four files are published only after every check passes.

## Requirements

* Python 3.8+ (standard library only — no pip packages, no `pcbnew` bindings).
* KiCad 9's `kicad-cli` on `PATH` (tested with 9.0.8); override with `--kicad-cli` or
  the `KICAD_CLI` environment variable.

## Usage

```sh
# From the repository root: defaults to PCB/main -> PCB/main/dist/jlcpcb/
python3 scripts/jlcpcb/export.py

# Explicit project, explicit destination
python3 scripts/jlcpcb/export.py PCB/main --output /tmp/jlc-order

# Replace a previous export (existing files are protected by default)
python3 scripts/jlcpcb/export.py PCB/main --overwrite

# Other project layouts / options
python3 scripts/jlcpcb/export.py PCB/main --board smove-r2-main.kicad_pcb
python3 scripts/jlcpcb/export.py PCB/main --schematic main.kicad_sch
python3 scripts/jlcpcb/export.py PCB/main --pcb-only            # ignore the schematic
python3 scripts/jlcpcb/export.py PCB/main --side bottom         # one assembly side only
python3 scripts/jlcpcb/export.py PCB/main --include-through-hole
python3 scripts/jlcpcb/export.py PCB/main --part-field "Supplier Code"
python3 scripts/jlcpcb/export.py PCB/main --require-part-numbers
```

Fabrication layers are always plotted for the whole board, whatever `--side` selects
for assembly. Exit status: `0` success (warnings allowed), `1` error, `2` argument error.

## How JLCPCB part numbers are stored in KiCad

The exporter reads **native KiCad fields**; no plugin, custom library or third-party
tool is involved. Add the field `LCSC` in the Schematic Editor (**E** on a symbol →
*Symbol Properties* → add field) and let **Tools → Update PCB from Schematic (F8)**
copy it onto the footprint. Fields added directly in the PCB Editor's *Footprint
Properties* work too. Leave the field's *Show* checkbox off if you do not want it
drawn on the schematic.

Field names are matched ignoring case, spaces and punctuation, so `LCSC`,
`LCSC_Part_Number` and `LCSC Part Number` are the same field.

| Output column | Recognized native fields |
| --- | --- |
| `LCSC Part #` | `LCSC`, `LCSC PN`, `LCSC Part #`, `LCSC Part Number`, `LCSC Part`, `JLCPCB`, `JLCPCB PN`, `JLCPCB Part #`, `JLCPCB Part Number`, `JLCPCB Part`, `JLC`, `JLC Part #` |
| `MPN` | `MPN`, `Manufacturer Part Number`, `Manufacturer Part #`, `Mfr Part #`, `Part Number` |
| `Manufacturer` | `Manufacturer`, `Mfr` |

Extra recognized LCSC fields can be added with `--part-field NAME` (repeatable).

Rules the exporter enforces:

* A part number must be `C` followed by digits (`c1525` is normalized to `C1525`).
  URLs, manufacturer part numbers and other text are **rejected** instead of being
  uploaded as a wrong catalogue code.
* The same part number may be stored on the schematic and on the board; a
  **conflicting** pair stops the export — the tool never guesses which part was meant.
* A part number stored only on the schematic is still exported (the schematic is read
  through `kicad-cli sch export netlist`, hierarchical sheets included).
* A missing part number leaves the BOM cell blank and prints a warning; add
  `--require-part-numbers` to make that an error instead.

In this repository all 46 assembled parts carry verified `LCSC` + `MPN` fields on both
the symbols and the footprints. J2 (the two plated battery wire holes) is deliberately
PCB-only and has no purchase code.

## What is exported

### `gerber.zip`

* Every copper layer declared in the board (all inner layers included), plus front/back
  mask, silkscreen and paste where present, and `Edge.Cuts`.
* Separate plated (`PTH`) and non-plated (`NPTH`) Excellon drill files in millimetres.
* Only freshly plotted fabrication files, flat at the ZIP root — no BOM, no project
  metadata, no stale plots. Protel-style extensions (`.gtl`, `.g1`, `.gbl`, `.drl`, …)
  plus KiCad's `.gbrjob`.

KiCad writes its plot creation date into every Gerber (`%TF.CreationDate%` and a `G04`
comment), so the per-file hashes in `export-report.json` differ between runs even though the
plotted geometry is byte-identical. `bom.csv` and `pick_and_place.csv` are byte-stable for
unchanged inputs.

### `bom.csv`

```csv
Comment,Designator,Footprint,LCSC Part #,Quantity,Manufacturer,MPN
47uF / 6.3V,"C2, C13",C_0805_2012Metric,C16780,2,,CL21A476MQYNNNE
```

The illustrative row above is real for this board. `Comment` is the board value,
`Footprint` is the footprint name without its library prefix, and references are listed
explicitly (never compressed to ranges) with correct CSV quoting. Rows are grouped only
when **value, footprint, part number, manufacturer and MPN all match**, so two
different purchase codes are never merged. If one part number legitimately appears in
more than one row (same part, different schematic values), the report lists it under
`part_number_used_by_several_rows` for review.

### `pick_and_place.csv`

```csv
Designator,Mid X,Mid Y,Layer,Rotation
C13,7.3000,15.0500,Top,270.00
```

Coordinates are millimetres in KiCad's **drill/place file origin** frame (this board:
`aux_axis_origin 100 135`), `Layer` is `Top`/`Bottom`, and `Rotation` is KiCad's
counter-clockwise footprint angle normalized to `[0, 360)`. Both CSVs always contain the
same reference set.

If a part needs a vendor orientation correction, add the native field
`JLCPCB Rotation Offset` with signed degrees (`90`, `-90`). It is added to the exported
rotation and recorded in the report; check the result in JLCPCB's placement preview.
Position offsets are not supported — fix the footprint anchor in KiCad instead.

## Selection rules

A footprint is assembled when all of the following hold:

* it has electrical pads (pure graphics and non-plated mounting holes are ignored);
* it is an SMD footprint (add `--include-through-hole` to also assemble through-hole
  parts after checking JLCPCB's availability);
* it is not marked *Do Not Populate*, *Exclude from BOM* or *Exclude from position
  files* on the board, and not *Exclude from BOM* / *Exclude from board* in the
  schematic;
* it is on the side selected by `--side` (default: both).

Skipped references and their reasons are listed in `export-report.json`. These flags do
**not** remove copper from the Gerbers.

## Checks performed

* KiCad's position file must agree with the board file this tool parses (origin, X, Y and
  rotation), so a mismatched or stale input cannot be exported silently.
* Duplicate or unannotated references, unreadable/absent positions, malformed or
  conflicting part fields and KiCad CLI failures stop the export.
* Value or footprint differences between schematic and board are warnings; the physical
  board wins. References present in only one source are reported.
* The plotted layer set, drill split, unique filenames and ZIP contents are validated
  before publishing.
* `export-report.json` records the SHA-256 of every source file, every fabrication file
  and the three upload files, plus layers, counts, skipped parts and warnings.

## Limits — read before ordering

The report is explicitly **not** a manufacturing release. This tool exports the saved
design; it does **not** refill copper zones, run DRC/ERC, repair outlines, edit the
project, check part stock or validate that a purchase code is electrically suitable.
Before ordering: save both editors, update the PCB from the schematic, refill zones, run
DRC and check the ZIP in a Gerber viewer; then verify part matches, polarity, placement
anchors, rotations and both sides in JLCPCB's preview.

## Tests

```sh
# Unit tests + end-to-end test with a fake kicad-cli (KiCad not required)
python3 -B -m unittest scripts.jlcpcb.test_export -v

# Additionally run the real exporter against PCB/main
JLC_INTEGRATION=1 python3 -B -m unittest scripts.jlcpcb.test_export -v
```
