# Two-part case: assembly, tolerances and release hold

## What is actually delivered

Exactly two printed parts, **Base + Lid**, with one M3×8 socket-cap screw, one captured M3 nut, insulating film and two nylon wire ties/lacings. The battery ceiling is integral to the base; the battery-entry closure is integral to the lid. Neither is a third panel.

Measured complete bounds: **42.0 L × 36.8 W × 16.6 H mm**. No 120 mm interpretation was adopted, and the design was not squeezed to an unanswered 12 mm target. The extra west width provides a genuinely off-PCB screw path and a separate lead bay; height is reduced from the inherited 19.6 mm case.

Mechanical frame: `X=nativeX−100`, `Y=139−nativeY`, PCB bottom `Z=9.6`. The PCB spans `X0..25, Y9..39`, **not Y0..30**. Board underside faces the body; accel/gyro +Z points outward. No sensor transform or firmware was changed.

## Mounting safety — deliberate replacement of the unsafe interface

**Do not put a screw through H1 with this case.** H1 at local `(11.8,13.35)` is left as the inherited 3.2 mm hole, below U2. The old radius-3.4 bearing and its 0.042612 mm copper margin are retired.

- New M3 axis: local **(−5,13.35)**, wholly west of the board and pouch. Screw and nut never contact PCB copper or rely on solder mask. Nominal nearest screw-to-PCB solid distance is **3.380 mm**; hardware-to-pack admission-envelope distance is **4.25 mm**.
- Closure load path: screw head → insulating lid bearing → base hard stop; nut reacts against the base's captive-pocket roof. This path bypasses PCB, IMU and battery. The lid's integral west door captures the nut side-entry slot.
- H1 has a **radius-2.2 mm solid plastic deflection stop**, 0.35 mm below the nominal PCB underside. No top clamp, metal sleeve or screw is at H1. The stop is rooted in the integral base ceiling and only limits abnormal PCB displacement.
- H1 nominal stop-edge to filled copper: **1.242612 mm**. Subtract 0.30 board play, 0.15 stop placement, 0.15 stop-radius error and 0.10 fabrication registration: **0.542612 mm remaining**. This is a conservative dimensional budget, not insulation certification. Worst accepted stop-height/seat-height mismatch leaves **0.05 mm** initial gap; reject a print that preloads the board.
- Four insulated lower seats support the PCB; four lid lips complete split grooves. X/Y stops separated across the PCB provide positive antirotation without screw friction. Nominal lateral play is 0.30 mm each side. With ±0.15 mm print error and 0.10 mm PCB edge allowance, minimum assembly clearance is 0.05 mm.
- Groove free height is **1.55 mm** around the 1 mm PCB; the stated thickness/print/liner stack leaves **0.20 mm minimum no-clamp play**. Nominal vertical float is 0.55 mm. This is intentionally not a rigid IMU clamp: vibration/fretting and button-load PCB motion require physical testing. Never remove clearance by tightening the case harder or adding pressure on U2.

M3 hardware screen: nominal 0.5 mm pitch, maximum 5.68 mm grooved head diameter, 3 mm head height, 2.5 mm hex drive; 8 mm length tolerance is screened as ±0.29 mm. These dimensions were checked against the ISO 4762 table. [source](https://www.fasteners.eu/standards/iso/4762/)

The CAD thread is a cylindrical envelope, not a helical engagement simulation. Assumed nut: AF5.5 × 2.4 mm, fit to 5.8 AF pocket and verify actual part. Shank bore Ø3.6; head recess Ø7.0 accommodates 0.30 mm shank play, 0.15 mm registration and 0.15 mm radial print error with 0.06 mm residual margin. Lid bearing is 1.2 mm nominal / 0.9 mm after axial print allowances. Nut-pocket roof is 4 mm thick. Nominal thread overlap is 2.4 mm, adverse geometric overlap 2.1 mm, approximately 1.7 mm after an additional 0.4 mm chamfer allowance. Blind-bore tip clearance remains **0.56 mm** with length/seat errors. These are fit checks, **not strength or torque ratings**.

No tightening torque is released. Qualify a low-preload snug closure on sacrificial prints, including repeated opening, pull-out, screw loosening, creep and shock. Do not use generic metal-joint M3 torque. Verify low-magnetic hardware with the assembled IMU; a material label alone does not establish magnetic suitability.

## Battery, insulation and harness

- Candidate body: **30×20×3 mm**. Admission reserve: **31×21×4.3 mm** for the **complete protected pack**, including pouch seals, tabs and PCM. No actual supplier pack, protection, current rating, thermal behavior or swelling allowance has been qualified. If the complete pack is larger, stop and revise the pocket; no compression or unapproved third panel.
- Pack nominal lower face Z1.8. A 0.2 mm smooth insulating floor liner lies above the 1.6 mm body-facing floor. Acceptance-pack top Z6.1 leaves **0.50 mm** below the integral ceiling at Z6.6. The ceiling is 0.8 mm thick, top Z7.4. Worst reserved USB tails start Z8.4: **1.0 mm nominal / 0.85 mm after 0.15 mm print error** above the ceiling. PCB never rests on the pouch.
- The ceiling, pocket walls, north stop and lid's front skirt retain the pack without clamping. Front-to-rear pack movement remains possible; the north stop limits the pack to Y38, still behind the RF boundary Y39. Inspect smooth walls, seams and liner edges. No sharp supports, residual print supports, foam compression, screws, adhesive preload or solder tails against the pouch.
- Two independent battery conductors: BAT+ native `(104.5,105.57)` and BAT− `(104.5,103.03)`, 2.54 mm pitch, 1 mm drills. Native nets/polarity unchanged. Insulated wire assumption **OD≤1.2 mm**, tinned bundle **≤0.7 mm**, top solder height **≤0.6 mm**, bottom trim **≤0.5 mm**. Actual wire ampacity and solder process remain qualification requirements.
- Wires exit the PTHs on top, make **R2 mm centerline bends** west beside the shielded module, then descend in the west bay and enter the pack side corridor. R2 is a geometric reserve, not an approved wire minimum bend radius. No wire crosses the antenna overhang. Separate nylon lacing through the two bridge eyelets restrains the insulated vertical leads, with knot reserves above the bridge. Fit/pull/flex-test it; do not pull on pouch tabs or use solder joints as strain relief.

## Assembly path (not the exploded display)

1. With **no USB power** and pack electrically isolated by an approved service procedure, inspect/deburr/gauge the two printed parts and install insulating liners. Accept smooth pocket surfaces and flat, coplanar PCB seats; reject warped, cracked or sharp prints.
2. With lid removed, insert the captured nut from the west. Slide the uncompressed battery **north through the open front** into the base tunnel. This is a straight translation, not a tilt or a squeeze. The maximum admission-envelope continuous swept volume was checked against the base. Guide insulated, isolated leads through the west side corridor; their handling/removal is a physical sample gate.
3. Lower the PCB vertically into the base seats and X/Y stops, underside toward body. Dress and terminate leads using a qualified isolated-pack procedure. Gauge trims and inspect polarity/shorts. Fit lacing. Do not solder or assemble an energized pouch pack in this enclosure; RESET does not isolate the battery.
4. Start the lid **1.5 mm south** of its final position, lower it to the base, then slide it **north 1.5 mm**. Two north tongues engage the wall pockets by 1 mm nominal / 0.5 mm adverse allowance. This path was checked against base, populated PCB, wires, pack and nut at the recorded samples. No snap flex is required.
5. Fit M3×8 **last**, in the west case-only bore, never H1. Reverse this sequence for servicing: remove screw, slide lid south before lifting. Verify board/pack are not clamped, USB plug fits, RGB is visible from above, and both buttons are reachable using a nonconductive tool.

STLs are supplied with base floor down and lid roof down. Use a nonconductive, non-metal/carbon-filled insulating print material; PETG is a prototype candidate, not a qualified thermal/skin-contact material. Screen 0.15–0.20 mm layers and sufficient wall perimeters with the fabricator. The integral battery ceiling has an approximately 21.8 mm bridge: actual sag, roughness and insulation integrity MUST be gauged before a battery is inserted. Removable process supports are not enclosure parts and must not remain in the pocket. No production print settings or material certification are claimed.

## RF and remaining release gates

The inherited all-layer/overhang exclusion is unchanged. No added battery, lead or metal hardware enters local `Y≥39` within the inherited RF volume. Modeled admission-pack margin is 1.5 mm, insulated-wire margin ≥2.43 mm; a freely shifted pack at the north stop retains 1 mm nominal. These are corridor checks only.

Espressif recommends a 15 mm antenna clearance region and warns about enclosure effects; this compact pack-under-board plastic enclosure **does not meet broad 15 mm clearance in all directions**. No metal shell, conductive coating or conductive filament is permitted. RF matching/range/efficiency and on-body detuning require measurement. [source](https://espressif.github.io/esp32-c3-book-en/chapter_5/5.3/5.3.4.html)

**Manufacturing, battery connection and charging remain on hold.** Required unresolved gates: complete protected-pack suitability and charger compatibility; bridge/seat dimensions and wear; rigidity, creep and qualified closure preload; wire strain relief and service handling; USB/button/RGB physical usability; RF, thermal and magnetic effects. No water/dust ingress, drop rating, skin compatibility, sensor accuracy or runtime guarantee. See the inherited [battery/charging constraints](../docs/revision-r2/integrated/RADIO-BATTERY.md); fitting the pouch does not approve powering or charging it.
