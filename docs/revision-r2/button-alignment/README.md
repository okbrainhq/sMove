# RESET / BOOT physical alignment

Current review update; supersedes the previous byte-identical-PCB claim in the two-part-case delivery. Manufacturing and charging remain on hold.

| Switch | Previous native XY (mm) | Updated native XY (mm) |
|---|---|---|
| SW2 RESET | 121.50, 124.05 | 121.25, 124.25 |
| SW3 BOOT | 121.05, 128.00 | 121.25, 128.00 |

Both switches now share X=121.25 mm, with 3.75 mm center spacing. RESET moved slightly down to retain copper clearance; BOOT remains outside the southeast retention keepout. No tracks/vias were rerouted, no pad sizes/net assignments changed, and no design rules or schematic files changed. Copper zones were refilled. Both PCB labels are horizontal and centered on the same X axis; label placement is secondary to physical clearance.

The enclosure generator uses the updated native-board interface anchors. Both 3.3 mm lid openings are concentric with the switch axes: case XY (21.25,14.75) and (21.25,11.00) mm. Nominal material between openings is 0.45 mm; physical printing and actuation still require a trial. Base geometry, outer dimensions, battery allowance and H1 fastener location are unchanged.

## Evidence and deliverables

- `native-checks.json`: unchanged routing, pad nets/sizes, rules and schematics; only SW2/SW3 placements changed.
- `drc.json`: zero configured violations, unconnected items and schematic parity issues.
- `erc.json`: zero configured schematic violations.
- `housing/validation/mechanical.json`: 382 passing checks, including 8 new switch/hole alignment, diameter, separation and clear-actuation-path checks, plus STEP/STL checks.
- Updated native KiCad PCB, interface and placement contract; regenerated PCB Gerbers/drills, CPL, assembly PDF, STEP and renders.
- Updated native FreeCAD enclosure, printable/assembly STEP and lid STL. `base.stl` is unchanged.

Previous recovery and two-part-case reports/manifests describe historical snapshots, not this alignment revision. Use the alignment manifests for the updated PCB/enclosure deliverables. No automatic merge or manufacturing release.

## Visual review

The delivered presentation macro ran in the pinned FreeCAD GUI, regenerated assembly/exploded/print-pair/section images, and saved the assembled native document. Its GUI report hash matches the saved FCStd. A separate native desktop top-view inspection confirmed the two button openings form a straight vertical pair. PCB top render was also inspected; switch models are unavailable in that render, so native footprint positions and enclosure component envelopes remain the geometric evidence.
