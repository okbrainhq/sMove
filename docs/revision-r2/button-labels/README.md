# BOOT / RESET silkscreen — minimal edit

Engineering prototype only; manufacturing_release=false. No circuit, routing,
component placement, enclosure or RGB changes. No advisors, merge or commit.

## Verified mapping and exact edit

The current PCB and a fresh KiCad XML export of the hierarchical schematic agree:

|Label|Button|Button pad 1|ESP32 U1 connection|Button pad 2|Text anchor (native mm)|
|---|---|---|---|---|---|
|RESET|SW2|/Compute/MCU_EN|8: EN|GND|(110.2, 123.7)|
|BOOT|SW3|/Compute/BOOT|23: GPIO9 / BOOT|GND|(110.2, 130.0)|

Exactly two standalone `gr_text` records were appended to the canonical
[main PCB](../../../PCB/main/smove-r2-main.kicad_pcb). Both use **F.SilkS**, normal
unmirrored KiCad stroke text, **0.8 x 0.8 mm**, **0.15 mm stroke**, **90 degrees**.
They sit immediately left of their respective top-side switches, centered on
those switches, rather than ambiguously between them. The narrow channel between
J4 solder lands and switch bodies necessitates the vertical orientation. The
rendered strokes avoid solder-mask apertures, component body outlines and edges;
configured silk clearance passes without clipping or rule changes. Assembly
courtyards are not physical body outlines; this tight space is not an assertion
of generous assembly/tool access. Labels are for viewing the exposed PCB, not
through an installed enclosure lid.

## Source persistence and exports

The native PCB is the authoritative layout source in this repository. There is
**no retained main-board generator** to update. The final exporter reads this
board without saving/rebuilding it, so regenerated silk includes these labels.
Do not add function-specific labels to the generic TS1088 library footprint.
A dedicated [regression check](../../../scripts/r2/main/verify_button_labels.py)
asserts both exact label geometry and fresh schematic/physical pad mappings.

Only affected main-board outputs were refreshed: front silkscreen Gerber,
fabrication ZIP, top SVG, top 3D PNG and assembly-top PDF; the main manifest was
resealed. All other raw Gerbers/drills, BOM/CPL, schematics, STEP and housing
remain byte-identical. The broad historical exporter was not invoked: it has an
unrelated one-page schematic assertion despite the current four-page hierarchy.

## Validation

- [Baseline DRC](baseline-drc.json) and [post DRC](post-drc.json): **0 violations,
  0 unconnected items, 0 schematic-parity issues**, using `--severity-all
  --all-track-errors --schematic-parity --exit-code-violations` with the unchanged
  project rules/exclusions. Ignored project-default categories remain ignored;
  this is not a claim that all possible default rules were enabled.
- Native ERC: **0 violations** before and after.
- [Label and byte-preservation check](validation.json): all five checks PASS.
  Removing only the two new text blocks reproduces the pre-edit PCB exactly,
  including footprints, pads, tracks, vias, zones/fills, outline, nets and UUIDs.
- The broad main verifier has **three pre-existing invariant failures**:
  handoff net spelling, BQ pin-net spelling, and J4 host-net spelling. These
  checks compare old unscoped names against `/Compute/` and `/Power/` names.
  [Baseline](baseline-invariants.json) and [post](post-invariants.json) reports
  differ only in `pcb_sha256`; no new failures. They were not repaired or hidden.
- [Package validation](package-validation.json): native BOM/CPL, fabrication ZIP
  and manifest checks passed, but the full command is **blocked by a pre-existing
  missing `hierarchy-alignment/README.md` documentation target** referenced from
  `FINAL-ELECTRICAL.md`. Its absence was verified in HEAD. The main manifest was
  resealed before that failure; independent inventory and ZIP/raw equality
  assertions also pass. No full package PASS is claimed.
- [Close-up PNG](close-up.png) / [SVG](close-up.svg): native silk, mask apertures,
  and fabrication body outlines. **Cyan SW2/SW3 references and header are review
  annotations only, not added PCB silk.** Inspected at full resolution. The 3D
  preview lacks several part models (including switches); it is not populated
  physical-fit approval. The 2D outlines are the placement review evidence.

Recheck from repository root (system Python with pcbnew; render also needs
GObject Rsvg/GdkPixbuf):

```sh
/usr/bin/python3 scripts/r2/main/verify.py
/usr/bin/python3 scripts/r2/main/verify_button_labels.py
/usr/bin/python3 scripts/r2/main/render_button_labels.py
/usr/bin/python3 scripts/r2/final/package.py
```

`verify.py` reports the pre-existing FAIL status described above. For the exact
preservation check supply `--baseline /path/to/pre-edit.kicad_pcb` to the dedicated
label verifier; the session used `.cache/button-labels/baseline.kicad_pcb`.
Rendering/checking does not rewrite native CAD. To refresh only the silk Gerber,
use the final exporter's `pcb export gerbers --layers F.SilkS
--use-drill-file-origin` invocation into a temporary folder, replace only the
`.gto`, rebuild the fabrication-only ZIP from existing raw files, then reseal.

## RGB handoff — inspection only, no implementation

The current main board already specifies **one physical RGB LED D1**, not three
separate LEDs: `LTST-C19HE1WT / CA`, one 1.6 x 1.6 mm four-pad package. The three
schematic light-emitting channels belong to that single component. Confirmed
against native PCB pads, current parts data and fresh schematic XML:

|Channel|ESP32 drive|Series resistor|D1 cathode|
|---|---|---|---|
|Red|U1 pin 20, GPIO6; /Compute/LED_R|R11, 1k|pad 1; /Compute/LED_R_K|
|Green|U1 pin 21, GPIO7; /Compute/LED_G|R12, 1k|pad 2; /Compute/LED_G_K|
|Blue|U1 pin 16, GPIO10; /Compute/LED_B|R13, 1k|pad 3; /Compute/LED_B_K|

D1 pad 4 is the common anode on `/3V3_MAIN`. Existing intended function is RGB
status indication; parts notes call for low current and off while charging.
This inspection does not verify firmware behavior or redefine status semantics.

For Astra Max's follow-up, first establish whether the request is a schematic
presentation clarification rather than a hardware replacement. If replacing D1:
retain compatible **common-anode polarity and pin numbering**, or explicitly
redesign the drives for a different polarity; preserve three independent
current-limited GPIO/PWM channels, never tie the outputs together. Check actual
forward voltages, GPIO sink limits, per-channel resistors/brightness and startup
behavior against the selected part's primary data before selecting a substitute.

Verify exact land pattern, orientation, package height and optical center, not
just the generic RGB name. D1 is at native **(119.15, 122.7) mm**; housing source
already makes **one D1 opening, radius 1.3 mm**, alongside two separate switch
access holes. Review that aperture/light-pipe alignment and clearance with the
actual package; housing and part-model fit remain unqualified. No RGB component,
net, footprint, BOM, drive or housing changes were made here.
