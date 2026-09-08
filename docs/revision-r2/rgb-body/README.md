> **Historical/superseded topology.** Current integrated main-PCB design and release gates: [integrated ECO](../integrated/README.md). Carrier/PH4/old enclosure/count/hash claims below are archival, not current build instructions.

# Unified RGB / coplanar body-outward assembly

**RGB and real mechanical redesign implemented. Body-contact blocker resolved by explicit owner clarification.**
Started from current local `main`, `fcbf69674c16e1a262ea21fec5447508a549ae40`, in isolated workspace 020. No other chats/advisors, no merge, no manufacturing or charge approval.

## D1: actual part, not three physical LEDs

Before this edit D1 was already **one placed KiCad unit, one UUID, one four-pad footprint, one BOM/CPL item**. Its three unboxed diode drawings made the package look separated. This ECO draws all three dies within **one continuous package body**, with R/G/B labels, one common-anode rail and one D1 reference. It does not combine three physical parts or change the circuit.

- Exact part: Lite-On **LTST-C19HE1WT**, C458749, common-anode four-pad RGB. Manufacturer pin assignments are red 1, green 2, blue 3. [source](https://optoelectronics.liteon.com/upload/download/ds22-2008-0044/ltst-c19he1wt.pdf) [source](https://jlcpcb.com/partdetail/LiteOn-LTSTC19HE1WT/C458749)
- Native footprint remains `smove-r2-main:LED_LiteOn_LTST-C19HE1WT`, at `(119.15,122.7)` mm, top, 0 degrees.
- Instance UUID remains `02ba7497-9a8d-56fa-99a3-83e5b10889a3`. Complete hierarchical PCB association stays unchanged.
- Pin 4's **drawn length only** is shortened to terminate at the body border and keep its number legible. All four electrical endpoints, pin numbers, pin functions/types and pin UUIDs stay unchanged. Hidden pin-name text is replaced visually by unobstructed R/G/B die labels; names remain in the netlist.

| D1 pad | Exact net | Existing drive |
|---|---|---|
| 1, red cathode | `/Compute/LED_R_K` | R11 1k to `/Compute/LED_R`, U1 pin 20 |
| 2, green cathode | `/Compute/LED_G_K` | R12 1k to `/Compute/LED_G`, U1 pin 21 |
| 3, blue cathode | `/Compute/LED_B_K` | R13 1k to `/Compute/LED_B`, U1 pin 16 |
| 4, common anode | `/3V3_MAIN` | Existing supply wiring unchanged |

The editable Compute sheet and local symbol library both contain the same generated body. **All sheet wires, labels, other instances, overview/USB/Power sheets, footprint/copper and BOOT/RESET silk are preserved.** No PCB save, refill, reassociation, footprint substitution or fabrication regeneration was needed.

Review: [native schematic close-up PNG](views/rgb-close-up.png), [SVG](views/rgb-close-up.svg), [four-page PDF](../../../PCB/main/dist/schematic.pdf), [full Compute page](../../../PCB/main/dist/schematic-compute.png).

## Actual mechanical redesign and resolved body frame

Owner clarification: **main PCB BOTTOM faces the body through the base**, both boards parallel to that face, accel/gyro +Z outward, LED TOP/outward and visible. Worn-up antenna/USB direction is explicitly not important. The old perpendicular/compactness rationale is superseded, not retained as an alternative accepted installation.

The new source/native assembly uses **coplanar substrate slabs Z=4…5 mm**, both component faces outward, main translation `(0,0,4)` and carrier component-frame translation `(-27.5,16,5)` mm, both identity rotations. The body datum is flat base underside **Z=0**, +Z away from body; +Y is conveniently toward the main antenna and +X is native main PCB +X. No anatomical up/right or skin-fit claim.

The real housing changes include a simple open base and flat lid, horizontal peripheral carrier seats/round-slot locators/chamfer key/lid bearings, relocated main bearings/stops, separate top-entry battery bay, full connector reserves, rerouted PH4/PH2 and accessible USB/BOOT/RESET/top RGB aperture. Four **M3×8 socket-cap screws + standard side-loaded M3 hex nuts**, not printed threads, close the housing. M3 does not enter either board.

The deliberate simplicity tradeoff is **109×48×14.5 mm**, 17.5 mm with assumed heads: wider but thinner than the old case, with no overhead pouch shelf or stepped lid. User screw head type/material and actual pack/lead dimensions still require inspection. The source geometry is an engineering proposal, not a measured assembly.

[Full hardware/printing/frame/assembly guide](../../../housing/PRINTING-ASSEMBLY.md), [native FCStd](../../../housing/smove-r2-enclosure.FCStd), [fresh mechanical receipt](../../../housing/validation/mechanical.json), [build parameters](../../../housing/validation/build.json).

Review: [assembled internals + outward axis](../../../housing/dist/assembled.png), [top / RGB](../../../housing/dist/top.png), [body-side](../../../housing/dist/body-side.png), [real section](../../../housing/dist/section.png).

### Native movable FreeCAD assembly

Separate Base/Lid/Main/Carrier/Battery/Cables/Hardware native `App::Part` groups contain named links to fixed engineering sources. Default placements are **assembled**. Run [InspectAssembly.FCMacro](../../../housing/InspectAssembly.FCMacro) explicitly for lift lid, explode slider, restore, transparency and per-group XYZ offsets. Moving these groups does not alter fixed validation/export geometry. No fused-only replacement or auto-save macro.

The real FreeCAD GUI opened and rendered the delivered native document. Actual Qt button/macro smoke tests exercised lift, explode, base movement and restore; source placements/volumes stayed unchanged. [GUI screenshot](../../../housing/dist/freecad-inspection.png), [receipt](../../../housing/validation/gui-inspection.json). Desktop-agent capture failed with an inhibited PipeWire session, so programmatic GUI verification is reported honestly, not mouse-driven review. Exploded views are inspection illustrations, never alignment evidence.

### Signed sensor evidence independently checked

Manufacturer **DS-000189 rev 1.3**, p19 Fig3 and p83 Figs12/13, was fetched from the SparkFun mirror and visually inspected. All 24 native U2 pad coordinates were checked against the top-view numbering; U2 is top-side, 0 degrees, native anchor `(109.5,103.8)` mm, pin 1 `(108.0,102.8)` mm. The direct TDK rev1.5 download returned HTTP 403, so this is **not** a latest-datasheet claim. [source](https://cdn.sparkfun.com/assets/7/f/e/c/d/DS-000189-ICM-20948-v1.3.pdf)

Evidence: [pin-order page](evidence/icm-pinout.png), [signed-axis page](evidence/icm-axes.png), [retrieval receipts](evidence/sources.json), [native-placement/pad audit](validation/mechanical-audit.json).

Carrier C axes: +X along J5 pad1 toward pad4; +Y from its connector edge into the board; +Z out of component face. Based on the package pin-1 view, not the conservative STEP envelope:

```text
v_C = R * v_sensor
R_accel_to_C = R_gyro_to_C = identity
R_mag_to_C = diag(1,-1,-1)

Implemented coplanar placement, body frame = enclosure E:
R_C_to_E = R_AG_to_body = identity
R_MAG_to_body = diag(1,-1,-1)
```

Thus the magnetometer's raw +X agrees with accel/gyro, while raw +Y and +Z are reversed. Accelerometer/gyro +Z is out of the package's component face; magnetometer +Z is into it. Gyro positive rotations follow Fig12's signed/right-hand convention. **Do not promise that both raw Z axes point outward or apply the same raw transform to all nine channels.** No firmware changes or physical calibration were performed.

## Verification and known inherited failures

- **Baseline and post, both boards:** configured ERC zero; DRC zero; zero opens; zero schematic-parity issues. Reports and XML netlists are in [validation](validation/). No severity changes or new exclusions.
- **146 scoped RGB/electrical/preservation checks pass.** Housing has its own independent checks.
- **Exact electrical equivalence:** full hierarchical net names, all connected ref/pin/function/type sets and all component metadata/UUIDs match baseline. Every numbered main PCB pad matches the fresh XML netlist. One D1 BOM/CPL item and original PCB association verified.
- **Preservation:** both native PCBs, electrical connectivity/association, board fabrication outputs, footprint libraries, BOM/CPL, carrier exports and stored silk are byte-identical. Housing geometry/STEP/STL are intentionally regenerated and independently checked. See [RGB regression receipt](validation/rgb-verification.json).
- **BOOT/RESET:** existing detailed silk/function checker passes. [Receipt](validation/button-labels.json).
- **Mechanical retention:** main retention lands pass baseline/post copper/track/via/fill screens; the installed carrier annular seats also pass fresh contact screens. [Baseline](validation/baseline-retention.json), [post](validation/post-retention.json). Fresh native BRep checks independently cover the relocated carrier and housing.
- **Inherited main verifier failure:** `scripts/r2/main/verify.py` fails three assertions already on baseline because it assumes pre-hierarchy net names (`lstrip('/')` does not remove `Compute/` or `Power/`). Native ERC/DRC/parity still pass. The dedicated ECO checker compares exact hierarchical names instead, without weakening that legacy script. [Original failure receipt](validation/baseline-main-invariants.json).
- **Inherited package failure:** full `package.py` already stops on missing `hierarchy-alignment/README.md` and other missing old review links. It is not claimed green. Source/output manifests are resealed and checked separately; missing historical evidence is not recreated or asserted proven. [Original package log](validation/baseline-package.log).
- The optional exporter was corrected to retain all four main schematic pages and hash all child schematics/local symbols. Only the schematic export path was run; unrelated Gerbers/PCB/3D exports were not regenerated.
- [Delivery review](validation/delivery-review.json): all new native views and GUI screenshots visually inspected. Fresh native mechanical screens pass (4,565 checks), covering screws/nuts, solids, clearances, insertion samples, axes and GUI-link preservation. Pre-edit geometry was separately recomputed: its 1,938 legacy mechanical screens pass, but its board planes were 90 degrees apart and did not satisfy the clarified requirement. [Baseline receipt](../../../housing/validation/baseline-mechanical.json).
- Physical fit, clamp/print strength, sensor repeatability/calibration, true harness slack and hardware magnetic influence remain unproven. M3×8 longest-envelope tips remain internal with 0.41-mm nominal blind-bottom reserve; full nut traversal and shortest-screw projection are checked. These are dimensions, not torque or fatigue ratings.

## Reproduce the scoped change and checks

Run from repository root with system Python/KiCad/Poppler/librsvg:

```sh
/usr/bin/python3 scripts/r2/main/unify_rgb.py
/usr/bin/python3 scripts/r2/main/unify_rgb.py --check
/usr/bin/python3 scripts/r2/main/render_rgb.py
/usr/bin/python3 scripts/r2/main/verify_rgb.py
/usr/bin/python3 scripts/r2/enclosure/audit_body_frame.py
/usr/bin/python3 scripts/r2/enclosure/contact_audit.py
```

`verify_rgb.py` uses the committed pre-edit receipts and baseline Git commit. It reruns current native checks; it does not overwrite the historical baseline. The RGB generator is idempotent; geometry uses its separate reproducible generator and native validator. [Complete reproduction including GUI rendering](../final-export/README.md). Source/output manifest reseal uses `scripts/r2/final/package.py --seal`; the existing missing-link failure remains after resealing.

## Remaining gates

No unresolved body-contact/worn-up blocker remains. The wider case, assumed socket-cap M3×8 hardware/nuts, real protected pack, actual PH plugs/crimps and wire bundle must be trial-fitted. Sensor-board registration, small main bearing strength, lid stiffness/preload, nut-slot printing, wire/tab strain relief, magnetic/current bias, RF/thermal/on-body suitability require physical tests. No waterproofing, skin, manufacturing or charge approval. Existing electrical bench gates and supervised off-body charging restrictions remain open.
