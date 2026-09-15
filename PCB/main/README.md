# Main PCB — 25 × 30 × 1 mm manual-layout reset

## Library and asset layout

All project-local KiCad libraries and models now live under `assets/` (moved from the project root; content byte-identical apart from the references below):

| Path | Contents |
|---|---|
| `assets/smove-r2-main.pretty/` | main footprint library (nickname `smove-r2-main`) |
| `assets/imu.pretty/` | integrated-IMU footprint library (nickname `imu`) |
| `assets/smove-r2-main.kicad_sym`, `assets/imu.kicad_sym`, `assets/Device.kicad_sym`, `assets/power.kicad_sym` | project-local symbol libraries |
| `assets/imu-models/` | local STEP models, referenced as `${KIPRJMOD}/assets/imu-models/...` |

`fp-lib-table`/`sym-lib-table` stay at the project root and point at `${KIPRJMOD}/assets/...`. Schematic sheets, project/design-rule files and `dist/` are untouched; only the U2 3D-model path (in the board and in `assets/imu.pretty/InvenSense_QFN-24_3x3mm_P0.4mm.kicad_mod`) changed text.

Verified with KiCad 9.0.8: the board reloads with the same 47 footprints, 461 tracks and 7 zones; DRC reports 0 violations / 0 unconnected / 0 schematic-parity (the DRC library check covers footprint-library resolution), ERC reports 0 violations, and all four symbol libraries parse and still contain every referenced symbol. Historical ECO scripts under `scripts/r2/` (for example `integrated/migrate.py`, `integrated/layout.py`) still name the pre-move project-root paths; they are documented as destructive historical helpers and must not be rerun on this board.

**Status note:** the headings below describe earlier working states. DRC on the currently saved `smove-r2-main.kicad_pcb` reports 0 violations, 0 unconnected items and 0 schematic-parity issues, and no footprint origin lies outside the board outline, so the "UNROUTED / components staged" wording below is stale and has not been rewritten here.

## JLCPCB fabrication and assembly export

`/usr/bin/python3 scripts/jlcpcb/export.py PCB/main` (add `--overwrite` to refresh an existing
set) writes `dist/jlcpcb/`: `gerber.zip` (all four copper layers, masks, silkscreen, paste, edge
cuts, separate PTH/NPTH millimetre drills), `bom.csv`, `pick_and_place.csv` and
`export-report.json`. See the [export tool documentation](../../scripts/jlcpcb/README.md).

- Generated from the currently saved board (47 footprints, 461 tracks, 70 vias, 7 zones, 4 copper
  layers, aux origin 100/135) at this revision. Native DRC/parity on that same file reports
  **0 violations, 0 unconnected items, 0 schematic-parity issues**; the export tool re-verifies
  KiCad's own position output against the board file before writing anything.
- All **46** assembled parts carry a JLCPCB/LCSC catalogue number in the native `LCSC` field,
  together with `MPN`, on both the schematic symbols and the board footprints. The verified
  numbers are recorded in [main-parts.csv](../../docs/revision-r2/main-parts.csv) and
  [stock.json](../../docs/revision-r2/stock.json). J2 (the two plated battery wire holes) is
  intentionally PCB-only and excluded from both BOM and CPL.
- Engineering export only: **not a fabrication, assembly or charging release**. The tool does not
  refill zones, run DRC/ERC, check supplier stock or qualify any purchase code, and `housing/`
  remains a separate historical snapshot.

## Current: schematic links repaired; components staged — UNROUTED

**All 47 schematic footprints are now present.** U1 (ESP32), J1 (USB-C), U2 (IMU), and J2 (battery +/− holes) retain their poses and geometry. The other **43 footprints are staged outside the board to the right** for manual placement. No tracks or vias were added.

The reported dialog was **Update Schematic from PCB**, the reverse direction. Use **Tools → Update PCB from Schematic (F8)** to bring schematic components into the board. The four old footprint paths also contained an extra root-sheet UUID; one reference-based re-link repaired them without replacing or moving the footprints. Re-link is now off for normal updates. A repeat forward-update preview reports **0 errors and 0 warnings**, without duplicate additions. KiCad also repaired duplicate pad UUIDs on save; all pad geometry/nets and footprint UUIDs remain unchanged.

[Update verification](../../docs/revision-r2/manual-layout-reset/schematic-update-verification.json): **0 schematic-parity issues**, 148 expected unconnected items, and one **pre-existing J2/U1 courtyard overlap**, left unchanged to preserve both fixed positions. Schematics and design rules on disk are unchanged. The latest saved zone state was preserved: five rule areas and one filled In1 GND plane; the earlier six-unfilled-zone reset below is historical. **Not for manufacture or charging; exports remain stale.**

## Historical: manual placement/routing reset — UNROUTED

Only **U1 (ESP32), J1 (USB-C), U2 (IMU), and J2 (battery +/− through-hole pads)** remain in the PCB layout, with their complete footprint definitions, positions, orientations and pad/net assignments unchanged. The other **43 footprints were deleted from the PCB only**; all schematic sheets and project/rule files remain unchanged.

Removed **500 track segments, 124 vias, and all 38 cached copper-fill polygons**. All six copper-zone definitions are retained **unfilled**, including In1 GND and the In2 GND / 3V3_MAIN / PACK_P regions. Board outline, stackup, drawings and all keepouts are unchanged. This is actual copper removal, not merely hidden pours.

[Verification](../../docs/revision-r2/manual-layout-reset/verification.json): exact-token preservation check and native board load pass; native DRC reports **0 geometric violations**, **45 intentionally unconnected items**, and **43 expected missing-footprint parity warnings**, plus the existing J2 library-footprint mismatch warning. Previous routed-board acceptance scripts/reports below are historical and are not acceptance criteria for this reset. **Not for fabrication/assembly/charging; existing exports and enclosure placement data are stale.**

For manual placement, open `smove-r2-main.kicad_pro` in KiCad and use **Update PCB from Schematic (F8)** when ready to re-add the missing footprints. Do not delete their schematic symbols. The standalone PCB Editor has this command disabled; launch the editors through the project. J2 was restored verbatim from the pre-reset board at the user’s request, retaining both battery +/− holes. The other 43 missing components have not been re-added or parked outside the board.

## Historical: routed review candidate

See the [routing completion and plane-selection evidence](../../docs/revision-r2/main-routing/README.md). The user's rotated-U8 USB routing is preserved, remaining nets are connected on **F.Cu/B.Cu**, In1 is continuous GND, and In2 has bounded **3V3_MAIN / PACK_P power regions** with GND elsewhere. C7 alone is rotated 180° to fix its isolated ground connection; other placements, pad nets and keepouts are unchanged.

**Fresh native checks: 0 DRC errors, 0 unconnected items, 0 schematic-parity issues, 0 ERC violations; one existing J2 footprint-library warning.** Reusable coordinate routing, via placement, rotation previews, explicit rip-up and cleanup tools are documented in [scripts/pcb_tools](../../scripts/pcb_tools/README.md). Run `/usr/bin/python3 scripts/r2/main-routing/verify.py` for current acceptance checks.

**Not released for fabrication or charging.** USB impedance, current/thermal margins and return paths still need engineering review. Some low-speed paths take long perimeter detours. `dist/` and the enclosure are stale; no manufacturing exports were regenerated.

## Historical: grouped placement review — UNROUTED

See the [placement revision and researched routing strategy](../../docs/revision-r2/placement-routing/README.md). U1, USB, battery pads, outline and both M3 reserved positions are unchanged. The LED/buttons are upper-left, charger/regulator parts are together beside USB, and U2 remains at X112.5 with its original orientation, now at Y126.5. RED is reassigned from GPIO6 to GPIO3; GREEN=GPIO7 and BLUE=GPIO10 remain unchanged. Firmware must adopt the RED pin change.

**Placement only: 152 unconnected items; zero tracks/vias.** Obsolete routing was removed deliberately, not left connecting the wrong pads. Current zone definitions are retained but unfilled; the researched power-region strategy is not implemented yet. Placement geometry, ERC and schematic parity pass, with the existing J2 library-footprint warning. This is **not a finished reroute or manufacturing/charging release**. Existing `dist/` and enclosure openings are stale.

Run `/usr/bin/python3 scripts/r2/placement-routing/review.py` for this revision's checks. Do not use the historical LED-only verifier or layout generators as current acceptance tests.

## Historical: LED routed on the previous layout

The [LED routing update](../../docs/revision-r2/led-routing/README.md) builds on the user's `b155f03` routing setup. All RGB channels are connected, with D1 and every other footprint left in place. Top-left and bottom-right 6 mm clear disks are protected for future M3 hardware; no mounting holes were added. Fresh checks report **0 DRC errors, 0 unconnected items, 0 schematic-parity issues**, with three unchanged pre-existing warnings.

**The native PCB is authoritative. `dist/` and the enclosure are older snapshots, not regenerated for this routing update.** Do not use the older manufacturing bundle without regeneration and review. Run `scripts/r2/main/verify_led_routing.py` for current checks; do not run historical layout generators over this board.

## Historical screwless revision (before the user's reroute)

**Current: [screwless revision](../../docs/revision-r2/screwless/README.md). Not released for manufacture, assembly or charging.**

- Removed the H1 3.2 mm NPTH footprint and its H1-specific copper exclusion. Refilled copper zones into the reclaimed region; **did not reroute** or run legacy routing generators. Clean configured DRC/connectivity/parity did not require disturbing the accepted routing.
- Exact token comparisons retain all **1,726 segments, 97 vias, 47 non-H1 footprints and pad/net/placement data**, board outline, layer/setup data and antenna/corner rules. All five schematics, project rules and electrical parts are unchanged. Existing corner copper-free regions remain dielectric contact reserves, not fastener mounting features.
- Fresh configured ERC / DRC / unconnected / schematic-parity counts: **zero**. Existing ignored defaults remain unchanged; this is not electrical or charging release.
- Four layers, 1 mm nominal total board; In1 GND reference and existing circuit retained. Integrated top IMU +Z outward, underside toward body. Aligned RESET/BOOT at native X121.25; no new UART/testpoints/connectors.
- BAT+ native (104.5,105.57), BAT− (104.5,103.03); 2.54 mm pitch, 1 mm drill target, 2 mm pads unchanged. **USB's two 0.65 mm component locating NPTH holes and plated connector/BAT holes remain**: these belong to the preserved electrical connector footprint, not enclosure mounting hardware. No enclosure mounting holes remain.
- `dist/` is regenerated for this native PCB: Gerbers/drills, BOM/CPL, assembly PDF, board/installed-model STEP and renders. Conservative populated STEP uses exactly one instance per reference, no duplicate display copies. Missing vendor models remain limitations of installed-model renders.
- PCB-only STEP uses drill origin (100,135), unlike housing Y=139−nativeY. Its 0.91 mm dielectric thickness omits copper; the housing conservatively reserves the accepted total 1 mm. Do not mistake this export convention for a board-thickness ECO.

The native board is authoritative. Do not run legacy routing or historical sync tools over it. `scripts/r2/screwless/pcb.py` is the targeted, idempotent ECO/check entry; `scripts/r2/screwless/verify.py` compares against recorded aligned predecessor `b8f2836ac2fb26fc0bf774b803c6613a79e66f1b`. The enclosure uses insulated lands, optional adhesive and travel stops, not PCB or pouch clamping. Physical support/fit still needs qualification.

Historical [PCB repair](../../docs/revision-r2/pcb-repair/README.md) and [button alignment](../../docs/revision-r2/button-alignment/README.md) retain their original scope. Current exports are indexed by `dist/manifest.json`.
