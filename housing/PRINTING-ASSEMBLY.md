# R2 coplanar enclosure — printing, hardware and assembly

**Engineering prototype, not a physical-fit/manufacturing/charging release.** The clarified body datum supersedes the old perpendicular-carrier build. The current CAD is a simple rectangular open base plus flat lid, **109 × 48 × 14.5 mm** excluding screw heads (**17.5 mm** overall with the assumed heads). It is intentionally **wider but thinner**: main, IMU and battery sit side-by-side to eliminate the old stepped lid, suspended battery roof, side-entry carrier screws and small printed threads. No size/comfort approval is implied.

## Body frame and physical installation

The user explicitly specified **main PCB BOTTOM toward the body through the base**, with both board planes parallel to that face, sensor +Z outward, and no preferred worn-up edge.

- Body contact reference is the uninterrupted **flat base underside, Z=0**. Body lies on the negative-Z side. This is a rigid design plane, not a claim that a human surface is flat.
- +Z points from body through the boards toward the lid. Both substrate slabs are **Z=4…5 mm**, hence **coplanar**, not merely visually parallel.
- +Y is chosen toward the main antenna, +X toward main native PCB +X. These are convenient device directions, **not anatomical up/right**.
- Main local coordinates: `(KiCad_x−100, 135−KiCad_y, z_from_board_bottom)`; translation to case `(0,0,4)` mm, rotation identity.
- Carrier local coordinates: `(KiCad_x−100, 120−KiCad_y, z_from_component_face)`; translation `(-27.5,16,5)` mm, rotation identity. Actual U2 footprint anchor becomes `(-18,32.2,5)` mm; not the die position or body centre.
- Manufacturer pin-1/top-view evidence and **all 24 actual U2 pad positions** support accel/gyro package-to-carrier identity. Magnetometer Y/Z differ; see [signed-axis evidence](../docs/revision-r2/rgb-body/README.md).

```text
Column vectors: v_body = R * v_raw
Accel/gyro R = [[1,0,0], [0,1,0], [0,0,1]]
Magnetometer R = [[1,0,0], [0,-1,0], [0,0,-1]]
```

Positive gyro rotations use the manufacturer's right-hand sense, not Euler-angle sign substitutions. Bench six-face acceleration, positive rotation and separate magnetic-axis tests remain required.

## Printed pieces and hardware

Only **base.stl + lid.stl** are printed; four M3×8 screws and four standard M3 nuts close the case. **M3 screws do not go through either PCB.** Existing carrier holes remain 2.2 mm round / 2.7×2.2 mm slot. No electronics was moved on its PCB, and BOOT/RESET silkscreen remains unchanged.

Assumed screw: **M3×0.5 × 8, fully threaded socket-head cap**, length measured **under the head**, nominal head diameter 5.5 mm (screened up to 5.68 for grooved heads), height ≤3 mm, 2.5-mm hex drive. The cited table gives length limits 7.71…8.29 mm. Measure the user's screws: this is not confirmation of their head type or material. No countersunk screw, washer or longer screw is silently substituted. [source](https://www.fasteners.eu/standards/iso/4762/)

Assumed nut: **standard M3 hex, AF≤5.5 mm, thickness 2.15…2.4 mm**; not a taller nyloc. Nut envelope includes a major-diameter thread bore, not helical threads. [source](https://www.fasteners.eu/standards/iso/4032/)

| Feature | Nominal CAD / screened limit |
|---|---|
| Case walls / base floor / flat lid | 2.0 / 1.6 / 2.0 mm |
| Closure centres | `(-33,1), (-33,30), (66,1), (66,30)` mm |
| Boss radius / screw clearance | 5.0 mm / Ø3.4 mm |
| Nut pocket / side-entry slot | AF6.0; Z=7.7…10.5 mm, 2.8 mm high |
| Nut roof | 2.0 mm, Z=10.5…12.5; lid adds 2.0 mm above it |
| Nut contact / screw under-head | Nut top Z=10.5; screw under-head Z=14.5 |
| Minimum full-nut engagement | Entire 2.4 mm nut traversed; shortest screw extends 1.31 mm past it |
| Longest screw tip | Z=6.21; **0.41 mm** above blind bore floor Z=5.8; never exits body floor |
| Nut pocket radial wall | ≥1.53 mm away from the intentional loading slot |

Nuts slide along +Y for the front pair, −Y for the rear pair, **before installing electronics/cell**. The side entry leaves a real boss roof for clamping; a top-open nut well that clamps only the lid was deliberately avoided. Snug gradually and evenly; no torque/strength claim. Do not use a steel-joint torque chart on printed plastic. Head loads are borne on the lid/bosses, not PCB holes.

**Magnetic material remains an acceptance risk.** Existing M3 screws may be steel. The case fasteners are not carrier supports and are outside the exact antenna environmental volume, but distance is not magnetic isolation. Prefer dimension-compatible low-magnetic hardware if available; stainless is not assumed nonmagnetic. Test the complete case under operating/charging currents and after hardware changes; substitute suitable nonmagnetic hardware if bias is unacceptable.

Starting print trial: unfilled nonconductive PETG, 0.4-mm nozzle, 0.2-mm layers, at least three perimeters. No carbon/metal-filled material. Base floor down; lid roof down (STLs already oriented). The tray/battery bay is open from above; only short nut-slot roofs require tuned bridging or removable support accessible through the slots. Clear strings/support, deburr and smooth body-facing edges. The 0.7-mm-wide main bearing pads are constrained by existing copper-free lands: inspect their strength and dimensions, do not enlarge them into copper or tighten until the board bends. No print tolerance or layer adhesion was measured.

## Board retention, cell and cable routing

- **Main**: rounded lower/upper bearing pairs contact only its two existing 1.1×1.8-mm all-layer copper-free edge lands. Nominal gap is 1.0 mm. Side/end stops limit sliding with nominal 0.15-mm edge clearance. This is not a measured preload or vibration-retention design; reject rocking/sliding or button-induced bending, rather than forcing the lid.
- **Carrier**: two Ø3.2-mm peripheral seats, Ø1.8-mm plastic round/slot locating pins, matching annular lid bearings and the positive chamfer key. Nominal gap is 1.0 mm. Lid reliefs receive the pin tips. No pressure pad or column is under U2's no-support volume. Inverted/180-degree seating is not acceptable; the CAD key rejects the 180-degree footprint. Pin clearance means repeatability still needs bench testing.
- **Battery**: separate east-side **23×34×8-mm** acceptance bay, with 1.6-mm side walls and lid keepers stopping at its Z=9.6 ceiling. Only accept a complete insulated **protected** pack ≤21×32×6.5 mm including protection/wrap. The rendered gold block is an acceptance envelope, not a purchased/qualified cell. The bay is beside, not beneath, solder/USB tails. Allow 0.75 mm nominal vertical clearance at each side of the rendered pack; do not compress, puncture or force a swollen pouch. Test restraint without stressing seals/tabs.
- **PH4**: unchanged main J4 ↔ carrier J5, PHR-4 each end, **1:1 3V3/GND/SDA/SCL**. The actual tangent-arc route is **34.64 mm** between modelled mating-face centres, with R=3-mm bends and Ø1.8-mm swept bundle reserve. It leaves about 15.36 mm of the existing ≤50-mm finished connection budget; a 10-mm allowance is explicitly checked. This does **not** prove plug/crimp length definition, suitable wire gauge, minimum bend radius or slack. Do not simply order a 34.64-mm cable.
- **PH2**: paired pack leads exit the open-topped bay notch and follow the east-side swept corridor to main J2 (PHR-2, pin1 PACK+, pin2 GND). Keep the pair together and relieve tab strain with appropriate insulated restraint after measuring the real leads. The model does not simulate flexible leads or a qualified strain-relief attachment.
- Full main J2/J4 mating cavities, carrier plug/bend reserves, sensor no-support region and exact RF environmental keepout are retained unshrunk. Only each harness's own connector/pack termination overlaps are intentional. The carrier's nearest PCB edge has 0.4 mm nominal separation from the RF exclusion boundary; this is not an RF performance margin.

## Assembly and usable access

1. Bench-inspect assembled boards and test electrical function with cell disconnected. Trial the **empty** base/lid and all M3 nuts/screws first; verify threads, head dimensions, nut capture, no breakthrough and unobstructed slots.
2. Load nuts from the interior along their slots. Lower the carrier vertically onto its two seats/pins with the chamfer matching; lower main onto its reserved bearings. Do not push on the IMU package or solder toes.
3. Mate the accepted PH4 harness with the lid removed, verify all four pin-to-pin connections and route along the reserved west corridor. Both boards remain component-side outward.
4. Lower the accepted protected pack into the separate bay. Route and restrain paired leads without pinching/pulling tabs, check PH2 polarity, then connect. Do not trap cables over bosses/bearing contacts.
5. Lower lid straight down, check locators/registers and tighten four M3×8 screws only enough to close without PCB/cell preload. Perform retention, sensor repeatability and current-dependent magnetic tests.
6. USB remains accessible through the front opening (11-mm-wide tray notch with removable lid closure). BOOT/RESET have Ø3.4-mm top holes for a small blunt insulating tool. **D1 stays on main TOP and is visible along outward +Z through the Ø6-mm RGB aperture**; no light pipe is assumed. Labels in CAD/images are display annotations, **not embossed/engraved print geometry**. Apply simple external labels after the print trial if wanted.
7. Remove external power before service. Lift lid, disconnect cell and cables; battery and both boards lift upward. J3 stays an unpopulated service interface; the 2-mm bottom probe reserve is retained, but probe/repair with main removed rather than inserting metal through the body side. No external PH ports are implied.

## Native GUI inspection

Open [smove-r2-enclosure.FCStd](smove-r2-enclosure.FCStd). It defaults to assembled placements with separate native linked objects, grouped under **MOVE THESE**: Base, Lid, Main, Carrier, Battery, Cables and Hardware. Expand groups for named individual parts. **ENGINEERING SOURCES** contains editable CSG/sketches and the parameter spreadsheet; leave its placements alone for inspection.

Run [InspectAssembly.FCMacro](InspectAssembly.FCMacro) explicitly via FreeCAD's Macro dialog (choose the housing directory, select the macro, Execute). The dock has **Lift lid only**, **Explode all parts** / slider, **Restore ASSEMBLED**, transparency, per-group XYZ offsets and view buttons. Alternatively select a MOVE THESE group and edit its normal Data → Placement. Restore resets group and individual link offsets. Controls never save/export automatically or alter the fixed engineering transforms. An exploded display is **not** an alternate valid assembly or fit check.

The actual FreeCAD GUI opened and rendered this native file; Qt button-driven lift/explode/base-move/restore tests passed, and fixed source placements/volumes stayed unchanged. [GUI screenshot](dist/freecad-inspection.png) / [receipt](validation/gui-inspection.json). Desktop-agent mouse review could not run because its PipeWire session capture was inhibited; do not confuse the programmatic GUI test with manual interaction or physical fit.

## Validation and residual gates

Measured CAD reserves include 9.5 mm between board edges, 0.3 mm between the full USB plug reserve and lid closure, 1.0 mm above PH4 plug reserves, 0.6 mm from the PH2 bundle to case, and 3.88 mm minimum hardware-to-electronics distance. Hardware is only about 10.89 mm from U2 at the closest envelope: magnetic qualification is essential. These nominal clearances include no printer compensation.

[Native mechanical receipt](validation/mechanical.json), [build/frame parameters](validation/build.json), [electrical/axis ECO review](../docs/revision-r2/rgb-body/README.md), [source/output manifest](dist/manifest.json).

Checks include fresh FCStd recompute, real BRep intersection volumes, actual two-board planes, outward optical/tool paths, screws/nuts/driver space, plug/cable/RF/no-support volumes, top insertion samples at 0.5-mm steps, lid lift, key rejection, fresh STEP volumes/solid count, and STL connectedness/winding/manifold/self-intersection/volume. The pre-edit perpendicular model passed its old 1,938 mechanical screens but did **not** meet the new body requirement; the new geometry has its own checks.

CAD does not establish continuous flexible-cable sweeps, print fit, rigidity/preload, nut-slot bridge strength, impact/vibration retention, on-body comfort/attachment, actual screw material, pack protection, calibrated sensor signs, magnetic offsets, thermal/RF performance, waterproofing or skin suitability. The wider flat case and exposed apertures have **no IP rating**. Supervised off-body charging/protected-pack and all electrical qualification restrictions remain in force.
