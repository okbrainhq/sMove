# Main PCB — 25 × 30 × 1 mm review candidate

## Current: LED routed on the revised layout

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
