# Two diagonal M3 mounting / assembly gates

**Engineering prototype, not a manufacturing/charging release.** All dimensions below are CAD mm, not measurements of the owner's screws or purchased battery. Main assembly frame: X right, Y toward antenna, Z outward; base underside Z0 faces body.

## Size, mounting and stack

Outside model: **49.8 × 29.4 × 19.6mm** including recessed assumed heads, no ears. Substrate bounding box25×39×1mm. H1/H2 assembly axes **(3.6,35.4)/(21.4,3.6)**; native holes(103.6,103.6)/(121.4,135.4). Native drill3.2mm; printed bores3.4mm. Verify printer shrink, actual screw diameter and positional tolerance before fitting.

| Interface | CAD Z / size |
|---|---|
| Base floor | Z0–1.6 |
| Nominal pouch | Z1.8–4.8; body20×30×3 |
| Installed acceptance reserve, NOT qualified pack | Z1.8–6.1;21×31×4.3 |
| Removable insulating divider | Z6.3–7.1, corner reliefs |
| Integral screw safety floor | Z6.4–7.2 solid below bore; radius2.05 |
| Nut shelf body | Z7.4–10.2; attached to side walls, no pouch preload |
| Captured M3 nut | Z7.6–10.0; assumed AF5.5×2.4 |
| Lower insulating PCB bearing | Z10.2–10.8; radius3.4 |
| PCB | Bottom10.8 / top11.8 |
| Lid insulating bearing sleeve | Bottom11.8; screw bearing at15.4 |
| M3×8 shank | Nominal tip7.4 / underhead15.4 |
| Assumed head envelope | Diameter5.68, height3; top18.4, recessed below19.6 |
| Lid roof | Z18.4–19.6 |

Nut pocket AF5.8, lateral entry6.6mm wide accommodates the nut's corners. Full nut engagement2.4mm nominal, screw protrusion0.2mm below nut. **Measured screw underhead length7.9–8.1mm** is the tested acceptance screen: shortest remains through full nut; longest tipZ7.3 stays0.2mm above divider and0.1mm above the blind safety-floor top. This is a narrow tolerance budget, not blanket M3×8 approval. Longer screws, extra washers, countersunk heads, different nuts or print errors invalidate it. Do not substitute or force. Trial-fit a nonconductive dummy first; no generic metal-fastener torque value is specified for printed plastic/1mm PCB.

M3 head nominal dimensions follow the socket-cap family reference; actual head/length/material still require measurement. [source](https://www.fasteners.eu/standards/ISO/4762/)

Both contacts are within independently audited 3.4mm copper-free bearing areas, inside native3.45mm keepouts. Copper/pads/components, nuts and screw heads are kept off the sensor/antenna. The board is positively located by two separated holes and side registration, rather than foam or adhesive. Do not clamp U2. Two-point registration is not a measured stiffness/shock/creep qualification; test vibration and acceleration noise at a conservative assembly torque.

Prefer verified low-magnetic screw/nut material near the magnetometer. Do not infer nonmagnetic behavior from “stainless” alone; measure bias with hardware fitted, rotated and under load, then calibrate/qualify. Avoid ferromagnetic straps, tools or battery tabs near the sensor.

## Assembly path — no squeezing

First print/fit **empty parts and a rigid20×30×3 dummy**, not an unqualified live pouch. With lid, PCB, divider and nuts removed, the nominal body can enter tipped around X, progressively lower/translate then lie flat. [399 sampled rigid poses](validation/battery-insertion.json) had no CAD collisions; final placement is X2.5–22.5,Y4–34,Z1.8–4.8. This is not a continuous swept-path certification and does not cover real PCM/tabs/leads. The larger21×31×4.3 installed reservation did not pass the simple insertion search: verify the actual complete protected pack and removal route; do not force it through shelves or bend it.

After pack/charger/fit qualification and with USB disconnected: gently install the insulated pack, route paired leads through the south notch away from the two screw columns, then lower the relieved divider onto its ledges. Slide the two nuts into their keyed side entries; check full seating. Lower PCB so H1/H2 rest on insulating annular supports. Connect the correctly polarized PH2 mate (pin1 PACK+, pin2 GND). Confirm no pad/lead contact with screws and no cell pressure. Close lid sleeves onto PCB, engage both verified screws gently, and check movement/LED/button access.

The divider's corner cutouts permit straight insertion; integral blind plastic floors remain directly under screw tips. Cell top reservation has at least0.2mm nominal clearance to divider. USB tails have2.5mm clearance above divider. No screw traverses the pouch volume. Unknown cell tolerances/swelling must not consume these clearances.

## Open gates

**PH2 mate/PCB overlap remains2.16mm³ in the conservative model** (original check1.35mm³). The full-width plug reservation extends0.3mm below the PCB top and0.8mm over supported PCB near connector mounting pads. It is not resolved by hiding an error or cutting real mounting pads away. Obtain an exact mated drawing/sample before approving this fit. The connector family's official drawing is evidence of the retained part, not a guarantee for an unknown compatible plug. [source](https://www.jst-mfg.com/product/pdf/eng/ePH.pdf)

Cell150mAh/30×20×3 listing is unqualified for peak discharge, protection and charging; charge/ISET components are unchanged. See [radio/battery gates](../docs/revision-r2/integrated/RADIO-BATTERY.md). No direct USB charging of an unqualified pack. Modelled lead bends/seal/PCM reserves are not supplier ratings.

BOOT, RESET and RGB have top apertures; the LED is line-of-sight visible in CAD, not optically qualified. No debug pads or UART connector remain. There is no new latching OFF switch: true disconnected OFF requires USB absent and pack disconnected. Apertures are not waterproofing.

Check thin roof/boss print quality, two-nut retention, PCB warp, shell stiffness, skin-facing finish, RF range, magnetic bias, USB downloads and temperature on prototypes before sports/body use. Base/lid/divider STLs are separate, watertight CAD meshes; support/orientation and printer-specific tolerance are not certified by a mesh check.
