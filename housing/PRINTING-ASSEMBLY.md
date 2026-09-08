# R2 compact enclosure — engineering fit prototype

**51.7 × 58.9 × 21.8 mm, two printed pieces.** Vertical west-side carrier, battery below main behind an integral rigid barrier. This is a native geometric fit result, not a physical/manufacturing release.

## Files and reproduction

Native source is at `housing/smove-r2-enclosure.FCStd`; other deliverables are in `housing/dist/`:
- `smove-r2-enclosure.FCStd`: editable Part CSG, fixed-outline sketches and `Parameters` spreadsheet. Major case dimensions are expression driven; frozen board geometry, fit details and harness waypoints are deliberately constrained in the generator. Arbitrary spreadsheet edits are NOT automatically requalified.
- `base.stl`, `lid.stl`: printable orientations, one watertight connected outward-oriented mesh each.
- `smove-r2-printable.step`: two case solids at assembled locations.
- `smove-r2-assembly.step`: case, both actual-outline PCB substrates, conservative component/pack/harness envelopes and nylon hardware. Not an exact populated-component STEP. Keepout objects are separately named/hidden in FCStd, not physical assembly STEP parts.
- `assembled.png`, `exploded.png`, `section.png`: actual native FreeCAD views. Blue=plastic, green=PCBs, dark=component envelopes, gold=pack acceptance, red=harness corridors, pale=nylon. Assembled case is transparent for inspection. Exploded positions are illustrative; wires remain at assembled routes. Section is a real Boolean cut at enclosure Y=8 mm.

For current reproduction and runtime limits see [verification](../docs/revision-r2/final-export/README.md). GUI review remains unperformed; no GUI probing is part of cleanup.

## Printing and hardware limits

Starting settings to test, not proven print settings: unfilled nonconductive PETG or suitable unfilled nylon, 0.4-mm nozzle, 0.2-mm layers, at least three perimeters. No carbon/metal-filled filament near the IMU or antenna. Base floor down; lid roof down (STLs already oriented). The battery roof and stepped lid need tuned bridges or removable/soluble support. Clear all support through the open battery entrance before insertion; inspect the full roof and smooth the contact surfaces. Do not enlarge holes or sand the reserved PCB lands to force fit.

- Walls generally 1.4 mm; floor/rigid barrier 1.2 mm; battery side guides 1.0 mm. Fit offsets are nominal CAD clearances, not printer compensation.
- Four nylon M2×8 closure screws: modeled head diameter 3.8 mm, height 1.5 mm; case clearance diameter 2.2, head recess diameter 4.1, blind pilot diameter 1.7 mm. Verify actual head/thread dimensions; prepare threads with the PCBs/cell absent. Never force a screw through a blind floor.
- Two nylon M2×4 carrier screws: **head OD ≤3.2 mm, head height ≤1.3 mm** to keep contact inside the radius-1.65 reserved annuli. Actual availability/fit of reduced-head hardware remains a sourcing gate, not a verified product recommendation. M2 shanks locate the 2.2-mm round hole and 2.7×2.2-mm slot. No steel washers/fasteners.
- Carrier seats contact only peripheral radius-1.6 annuli; rigid spine stays outside the sensor no-support volume. Positive chamfer key prevents reversed seating. Seat snugly without bending the PCB; physical seating repeatability still needs testing.
- Main uses matched rounded-plan bearings only inside the two reserved edge lands, with a nominal 1.0-mm sandwich. Those lands passed canonical-board pad/track/via/filled-copper exclusion checks. Retention depends on the real board thickness, lid stiffness and friction; no preload/force or vibration retention claim. Reject a rocking/sliding main board, rather than tightening until it bends.

## Assembly and service

1. Receive the fully JLC-assembled boards (including all SMT headers) and inspect both PCBs outside the case. Iron access to SMT lead toes is a soldering-stage issue, not additional in-case clearance. Complete electrical checks first with the cell disconnected.
2. Remove lid and all loose hardware. Present carrier from the open west side, component face west, align chamfer and round/slot locators, then install its two nylon screws. Never press beneath/on the sensor.
3. Lower main vertically onto its reserved lands. Mate the PH4 harness while the lid is off; retain the modeled insertion/bend pockets. Route around the front-left closure boss through the west/front channel.
4. Accept only a complete **protected** pack fitting 21×32×6.5 mm including its protection structure. Slide it through the front into the **23×34×8-mm** bay. The 1.2-mm uninterrupted roof isolates the cell from solder tails; the worst USB-tail reserve is 0.8 mm above this roof. Do not compress, puncture, glue the carrier onto, or force a swollen pouch. The unmeasured Duino 350 candidate is NOT established as protected or fitting.
5. Feed paired pack leads through the side exit below the roof, around the two broad cleats and below lid keepers; verify they cannot pull on the pouch tabs or be pinched. Mate PH2 with polarity checked, then lower the lid straight down. The front stop remains outside the battery roof, and the removable west skirt exposes both carrier screws when off. Snug four nylon screws without PCB/pouch preload.
6. USB is the only external connector. Use a small blunt insulating tool through RESET/BOOT holes; RGB is visible through the simple hole. Do not use button loads to stress the carrier.
7. Service with external power removed: lift lid, disconnect pack, slide cell out front; J3 bottom probe access has the modeled 2-mm reserve. Main removes upward; carrier removes westward after its screws and cable are removed. Reinstall against the same chamfer/round-hole datum and repeat axis calibration checks.

## Harness and spatial contract

- Main J2: `S2B-PH-SM4-TB(LF)(SN)`, mate **PHR-2**; pin1 PACK+, pin2 GND.
- Main J4 ↔ carrier J5: `S4B-PH-SM4-TB(LF)(SN)`, **PHR-4 to PHR-4**, pin1 3V3, pin2 GND, pin3 SDA, pin4 SCL. 1:1 continuity; no mirrored/crossover cable. **≤50 mm** per electrical contract. Modeled mating-face centerline route is 42.86 mm, not a measured cable or guaranteed slack allowance. Check the actual cable-length definition, plug depth, crimps, wire gauge, bend radius and polarity before ordering/using a harness. AliExpress listing names/colours are not dimensional or pinout evidence; no purchase made.
- Main socket body/lead envelopes and full J2/J4 8-mm outward cavities are retained; maximum mating reserve is 7.5 mm above main bottom. Carrier plug reserve is local `[2,-9,0]…[16,1,6.5]`; bend reserve `[3,-15,0]…[15,-9,6.5]`, transformed without shrinkage. These are conservative contract volumes, not exact PHR models.
- All-layer antenna reserve preserved exactly. Environmental no-battery/harness/carrier/metal volume is enclosure `X=-9.1…34.1, Y=35…55.4, Z=-2.6…30.8 mm` (extends outside the case). Only the module's own antenna is excepted. The recommended 15-mm RF setback is not replaced by plastic insulation.

## Frames and qualifications

Column vectors; enclosure +X east, +Y north/antenna, +Z upward. Main local-to-case: identity rotation, translation `(0,0,12.4)` mm. Carrier component-face origin: `(-9.3,0,1.5)` mm. Carrier PCB occupies `X=-9.3…-8.3`, `Y=0…20`, `Z=1.5…19.5`.

```text
R_carrier_to_case = [[0,0,-1], [0,1,0], [1,0,0]]
accel/gyro_to_case = R_carrier_to_case
mag_to_case = [[0,0,1], [0,-1,0], [1,0,0]]
```

The side carrier is rigidly referenced, **not at the enclosure's geometric center**. This is the compactness trade-off explicitly selected instead of a three-layer stack. Keep high-current paired leads on the east; finished-case magnetic, thermal, RF, six-face acceleration and positive-rotation checks remain necessary.

Verification receipts cover fresh FCStd and both STEP imports, closed single solids, mesh connectivity/winding/manifold/self-intersection/volume, native part and full keepout collisions, sampled lid/board/cell removal, driver/probe access and signed axes. They do not establish every continuous swept trajectory, print fit, harness/pack protection, thread strength, clamp forces or electronics correctness. No IP/waterproof, skin, RF-certification or manufacturing-readiness claims.
