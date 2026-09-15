# sMove — PCB + three-piece enclosure

> **Current PCB workspace revision: components staged, UNROUTED.** [Main PCB status](PCB/main/README.md): schematic links repaired; ESP32/U1, USB-C/J1, IMU/U2 and battery +/− holes/J2 remain fixed, with the other 43 footprints staged to the right for manual placement. No tracks/vias; latest zone state preserved. Forward schematic update reports 0 errors/warnings and DRC finds 0 schematic-parity issues. A pre-existing J2/U1 courtyard overlap and unrouted connections remain. **Not for fabrication or charging; exports/enclosure data are stale.**

> **Historical routed PCB revision:** [Routing completion, plane selection and verification](docs/revision-r2/main-routing/README.md): the user's rotated-U8 USB layout is retained, remaining nets use top/bottom routing, In1 is GND and In2 contains power regions. **0 DRC errors, 0 unconnected items, 0 parity issues; one existing J2 library warning.** [Reusable routing/rotation tools](scripts/pcb_tools/README.md) include exact manual coordinates and vias. **Not a fabrication/charging release; `dist/` and enclosure exports remain stale.** Earlier enclosure descriptions below are historical. The prior RED LED GPIO3 change remains required.

> **Previous PCB update:** The [LED is now fully routed on the user's revised layout](docs/revision-r2/led-routing/README.md), with top-left/bottom-right space reserved for future M3 hardware. The enclosure and `PCB/main/dist/` remain older snapshots; their alignment/manufacturing claims below do not apply to the revised PCB without regeneration and review.

**Current review: white rounded Midframe + Top cover + Bottom cover. No screws, nuts, inserts or PCB enclosure-mounting holes. Default outer wall 0.8 mm; configurable and checked at 1.2 mm. No merge, manufacturing release or charging release.**

- [Current enclosure and regeneration](housing/README.md): opposite-side battery/PCB pockets, insulated support, optional PCB adhesive, screwless sleeve/snap covers and an internal perimeter BAT route around the separator edge.
- [PCB](PCB/main/README.md): targeted H1/keepout removal and copper refill; all 1,726 tracks and 97 vias preserved. Circuit, pad geometry, aligned buttons, antenna rules and battery interface unchanged.
- [JLCPCB fabrication/assembly export](scripts/jlcpcb/README.md): regenerates `PCB/main/dist/jlcpcb/` (`gerber.zip`, `bom.csv`, `pick_and_place.csv`, `export-report.json`) from the native KiCad `LCSC`/`MPN` fields on the symbols and footprints.
- [Historical screwless revision evidence](docs/revision-r2/screwless/README.md): fresh configured DRC/ERC, full native comparisons, manifold solids, collision/access checks, actual wall variation, FreeCAD images and hash manifests.
- [Printing/assembly and physical gates](housing/PRINTING-ASSEMBLY.md): actual pack/lead exit, insulation/adhesive, print supports, snap fit/creep, PCB deflection and charging qualification still required. No proven physical fit.

Default envelope including snap reinforcement: **42.85 L × 34.3 W × 19.0 H mm**. Accepted 30×20×3 mm battery candidate / 31×21×4.3 mm complete-pack allowance retained, behind the north antenna exclusion. Main underside faces the body; IMU +Z remains outward. LED, RESET/BOOT and USB-C accesses align to the current native PCB.

Previous [button alignment](docs/revision-r2/button-alignment/README.md), [PCB repair](docs/revision-r2/pcb-repair/README.md), and [two-part case](docs/revision-r2/two-part-case/README.md) records are historical snapshots, not current assembly instructions. Unrelated electronics and history are preserved.

![Current three-piece exploded CAD](housing/dist/exploded.png)

### Enclosure-only RF test prototype

Current `housing/` preserves the validated 25×30 mm PCB unchanged. Three screwless prints integrate a protected original-module antenna cap, source-derived flush USB mouth and internal perimeter BAT route around (not through) the separator. Overall 42.85×34.3×19.0 mm at 0.8 mm walls. See [housing documentation](housing/README.md) for source evidence, nominal checks and physical/RF/sweat qualification holds. No PCB shrinking or external antenna substitution.
