# Two diagonal M3 mounting / assembly gates

**Engineering prototype, not a manufacturing/charging release.** All dimensions below are CAD mm, not measurements of the owner's screws or purchased battery. Main assembly frame: X right, Y toward antenna, Z outward; base underside Z0 faces body.

## Size, mounting and stack

Outside model: **46.8 × 29.4 × 19.6mm** including recessed assumed heads, no ears. Substrate bounding box25×35.5×1mm. H1/H2 assembly axes **(3.6,35.4)/(21.4,7.1)**; native holes(103.6,103.6)/(121.4,131.9). Native drill3.2mm; printed bores3.4mm. Verify printer shrink, actual screw diameter and positional tolerance before fitting.

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

First print/fit empty parts and a rigid 20×30×3 dummy, not an unknown live pouch. The current bounded rigid insertion screen found a tilt about **−Y**, with XY translation and **630 collision-free sampled poses including entry from above**. Final body X2.5–22.5, Y7.5–37.5, Z1.8–4.8. This is NOT a continuous swept-volume guarantee or qualification of the full 21×31×4.3 protected-pack reservation, PCM, seals, tabs and wires. Verify an easy real insertion/removal path; never force, fold or compress a pouch.

After pack/charge/wire qualification, with USB absent and using an appropriate isolated assembly procedure: install the uncompressed pack and divider; side-load both nuts; lower PCB onto H1/H2 bearings. Thread the individually insulated prepared leads from below through J2. **Pin1 / BAT+ = protected PACK_P; pin2 / BAT- = GND.** Solder from the accessible top, trim protrusion/fillet to ≤0.6mm. Never solder directly to an unqualified pouch. Prevent shorts between live pack leads, tools and adjacent pads; verify polarity before connection.

J2 has two 2.0mm plated pads, **2.54mm centre pitch**, 1.0mm finished-hole target. Acceptance screen: 0.9–1.1mm finished hole, prepared/tinned conductor bundle ≤0.7mm diameter, insulation ≤1.2mm OD. No exact wire gauge is claimed supplied. Insulation must stay below the hole, not jam into it; inspect both solder faces. Do not enlarge holes by drilling through plating. Select wire current/temperature/flex rating from supplier data and actual measurements.

Route the separate insulated wires above the divider then down the south wire bay. **Fit nonconductive lacing through the two 1.2mm bores in the integral bridge**, around the insulated pair, using the two 1.6mm guide bores to register the wires. The bridge is at Z5.1–6.1, far from PCB copper and the pouch. A 0.4mm cord passage and 1.2×1.2×1.3mm knot reservation are screened, not a supplied cord specification. Leave the upper service loop; no pull load should reach the solder joints. R2 centreline bends / 1.2mm OD are CAD fit assumptions, not approved wire bend ratings. Verify lacing accessibility, smooth edges, no insulation damage, pull/flex retention and no lead escape before closure. Actual lacing geometry/preload is not fully modelled.

Close lid sleeves onto the copper-free PCB bearings and fit both measured screws gently. Do not add washers, substitute countersunk heads, overtighten or clamp U2. The fixed insulating divider keeps ≥0.2mm nominal clearance above the reserved cell top; USB shell tails remain 2.5mm above the divider. Screw safety floors remain closed below each tip. The pouch must not support any fastening load.

## Open gates

The obsolete PH2 mate/PCB collision check is **removed with the connector**, not ignored. New independent checks cover the PTH bare-wire/solder envelopes, insulated routes, lacing passages, battery reserve, screws, PCB and case. Static CAD and nominal-body insertion pass; the actual full protected pack, lead preparation, solderability and lacing remain qualification gates.

The 150mAh / 30×20×3 listing remains unqualified for peak discharge, PCM and charging. Charge/ISET parts are unchanged; see [battery and duty-cycle gates](../docs/revision-r2/integrated/RADIO-BATTERY.md). No direct USB charging of an unqualified pack. Direct soldering removes convenient unplugging; no latching master OFF switch was added, and RESET does not isolate the battery or regulators.

BOOT, RESET and RGB retain top apertures; CAD visibility is not optical qualification or waterproofing. Test print tolerances, narrow screw-stack acceptance, nut capture, PCB warp, shell rigidity/creep, magnetic bias, RF range, USB downloads, load-step sag and temperature before sports/body use. STLs are separate watertight CAD meshes; printer-specific fit/support/orientation and real hardware are not certified by those checks.
