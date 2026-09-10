# Simplified central-H1 two-part case — assembly and release hold

## What to print

Print **only `dist/base.stl` and `dist/lid.stl`**. Each is one connected part. The PCB components, battery, screw, nut and thin insulating films shown in FreeCAD are purchased/reference items, not extra 3D prints. Internal CSG boxes and cylinders are editable construction features, not a parts list.

The latest simplification keeps the accepted central-screw layout and battery choice:
- Four **2.6 mm wide wall-rooted corner blocks** replace skinny seats, webs and separate 0.3 mm fences. Their stepped surfaces locate the PCB without screw preload.
- Four integral lid pads are now **at least 1.4 × 1.4 mm**, replacing 0.6 mm-wide lips.
- Removed both hooks and their undercut pockets. Lid now drops **straight down**; no slide, snap tabs or separate clips. The front nut stop is joined into the broad front skirt instead of a freestanding thin tab.
- The insulated central nut socket and battery ceiling remain necessary. This is simpler, **not certified support-free**. No new small printed part was added.

## Current revision and dimensions

**Base + Lid only. One M3×8 socket-cap screw through the existing PCB H1. No side screw, ear, wire bay, wire channels, lead exits, lacing, solder or modeled/reserved leads.** The integral battery ceiling and lid entry skirt are not separate parts.

| Overall L × W × H (mm), including hardware | Preserved b49ade5 | Current |
|---|---:|---:|
| Length | 42.0 | 42.0 |
| Width | 36.8 | **28.8** |
| Height | 16.6 | **19.6** |

The accepted central draft and this simpler revision are both **42.0 × 28.8 × 19.6 mm**. Width is 8.0 mm smaller and below 30 mm without reducing the battery envelope. Height increases 3.0 mm to keep the central M3×8 tip/nut entirely **above** the sealed battery ceiling. Reusing the old under-head plane Z13.2 would put the tip at Z5.2, inside the maximum battery Z1.8..6.1: **that old-height central stack is blocked**. No side-screw fallback or longer screw was added. Neither 120 mm nor an unconfirmed 12 mm target is assumed.

Coordinates: X=nativeX−100, Y=139−nativeY. PCB bounds X0..25, Y9..39, bottom Z12.6, top Z13.6. Main underside faces the body; IMU accel/gyro +Z points outward. No PCB placement, orientation, pad, routing, rule or firmware changes.

## Central insulated interface and load path

H1 stays Ø3.2 **NPTH**, at native (111.8,125.65), local **(11.8,13.35)**. ONLY this axis has a screw.

- Screw head bears on the **integral insulating lid bearing**, not a metal washer on the PCB. Nut is inside a raised base boss above the battery ceiling, retained against rotation by its hex pocket and against front escape by the integrated front skirt/stop.
- Closure preload travels from head → lid bearing/roof → case perimeter → base structure/transverse beam → captive nut. The beam connects to the insulating pocket walls. The battery and PCB are **not clamp spacers**. The central screw passes through H1 while split edge grooves capture the PCB inside the closed base/lid.
- Four insulated stepped corner seats and four broad lid pads preserve positive antirotation. Groove height 1.55 mm around the nominal 1 mm board; thickness/print/liner budget leaves **0.20 mm minimum axial freedom**. Nominal lateral play is 0.30 mm per side; ±0.15 print and 0.10 board-edge allowance leave 0.05 mm minimum.
- An **annular R2.2 mm plastic stop** below H1 is initially 0.35 mm below the board (0.05 mm after adverse ±0.15 seat/stop errors). The wide nut-boss roof stays 0.70 mm below PCB (0.40 mm adverse). These are abnormal-deflection stops, not a screw clamp or supports resting on the pouch.
- The inherited minimum filled-copper radius around H1 is 3.442612 mm. R2.2 stop margin is 1.242612 nominal; subtract 0.30 board play +0.15 placement +0.15 radius +0.10 registration = **0.542612 mm residual**. The retired R3.4 loaded bearing's 0.042612 mm margin is not reused.
- There is **no fictitious printed sleeve** in the 0.10 mm nominal radial space between M3 and Ø3.2 H1. The hole wall is insulating, unplated FR4. The shank can touch that FR4 at the float limit; it must not touch copper. Even using Ø3.25 maximum hole and 0.10 copper registration, the radial copper separation beyond the hole is **1.717612 mm**. Head and nut are axially isolated by plastic and gaps, not solder mask.

**Alignment acceptance is mandatory, not proven by nominal CAD.** Gauge the finished NPTH (screen Ø3.15..3.25), use a shank ≤3.00 mm, and prove a smooth Ø3.00 gauge passes the assembled stack without forcing or bending PCB. At Ø3.15 the centered radial allowance is only 0.075 mm. Board/nut float may be used for hand alignment, but the independent ±0.15 print registration budgets do NOT guarantee every manufactured combination will align. Reject a binding assembly; do not drill the PCB larger, force the screw, or use tightening to pull holes into alignment.

## M3×8 stack and tolerances

Screen actual M3×8 hardware against the stated maximum envelope: head Ø5.68 × 3 mm, 0.5 mm pitch, length 7.71..8.29 mm, 2.5 mm hex drive. Reference dimensions are from ISO 4762. [source](https://www.fasteners.eu/standards/ISO/4762/)

| Interface | Nominal Z / dimension (mm) | Adverse check |
|---|---|---|
| Max pack top / ceiling underside / ceiling top | 6.1 / 6.6 / 7.4 | Pack gap 0.20 after 0.15 print +0.15 liner error |
| Blind-bore floor / screw tip | 7.4 / 8.4 | **0.56** tip-floor clearance after 0.29 length +0.15 seat error |
| Screw tip to maximum pack | 2.30 | **1.86**, in addition to intact barrier; no pouch penetration |
| Nut (AF5.5 × 2.4 envelope) | 8.6..11.0 | Pocket AF5.8, Z8.3..11.0; gauge actual fit |
| Nut roof / PCB bottom | 11.9 / 12.6 | Roof 0.90 nominal / **0.60** minimum thickness |
| Stop top / PCB bottom | 12.25 / 12.6 | 0.35 nominal / **0.05** initial gap |
| Lid bearing bottom / screw under-head | 15.1 / 16.4 | Bearing 1.30 nominal / **1.00** minimum |
| Screw head top / lid top | 19.4 / 19.6 | Head recessed 0.20 nominal |
| Thread overlap | **2.40** | **2.01** geometric; **1.61** after additional 0.40 combined chamfer reserve |

CAD threads are cylindrical envelopes, not helices. The Ø3.6 case bores and Ø7.0 recess allow an additive head eccentricity/radius budget with 0.06 mm residual. Actual head access and nut-pocket fit must be gauged. The small RGB opening intersects the recess edge locally; the screw head does not obstruct its optical axis. Do not add a metal washer at H1.

**No tightening torque or strength rating is released.** The 0.9 mm nominal captive-pocket roof, beam, lid bearing and printed walls need proof-load, creep and repeated-opening tests. Tighten only under an approved low-preload prototype procedure, never a generic metal-joint M3 torque. After closure, verify the PCB remains unbowed/free of clamp preload and the ceiling remains clear of the pouch. Low-magnetic hardware suitability is unqualified. Dimensional clearance does not establish stiffness, fatigue or insulation-wear safety.

## Battery and user-routed leads

Candidate **30×20×3 mm**; complete protected-pack allowance **31×21×4.3 mm**, including seals, tabs and PCM (leads excluded and entirely user-managed). No supplier pack or charging suitability is approved. The pocket was not narrowed to reach the width target. Stop if the complete pack exceeds the admission envelope; no squeezing, foam preload or battery compression.

Pack lower face Z1.8 rests on 0.2 mm smooth insulating film above the 1.6 mm body-facing floor. The integral 0.8 mm ceiling retains the pack with side walls, north stop and the lid's integral front skirt. PCB sits on separate plastic/film seats, never on the battery. The battery may translate within the pocket; at the north stop it stays 1 mm behind local RF boundary Y39. No screw bore or nut pocket opens into the battery tunnel.

**All dedicated lead geometry was removed. BAT+ and BAT− pads are unchanged.** Soldering, wire choice, actual route, bend radius, strain relief, trim, polarity and closure/pinch inspection belong to the user's physical assembly. No space is dedicated/reserved and no lead fit, insertion, strain relief or RF route is claimed verified. A user-chosen route may not fit this closed case; do not pinch a lead to make it close. Stop for review if it cannot be routed safely. User-routed leads must avoid the antenna/all-layer RF area, screw, pouch pressure and sharp edges. No powered-pack soldering or live-cell handling procedure is provided.

## Mechanical assembly (not exploded display offsets)

1. With power disconnected and pack safely isolated, gauge/deburr the two insulating prints. Fit smooth floor/seat films and verify coplanar seats, intact ceiling and no bridge sag or sharp edges. Use nonconductive, non-metal/carbon-filled material only.
2. Insert the hex nut from the **front interior**, above the battery ceiling, before PCB/lid. It sits against the pocket roof. Slide the uncompressed pack north through the front tunnel opening with lid off. This maximum-envelope continuous translation was checked against the base.
3. Lower the populated PCB vertically into its seats/positive edge stops, aligning H1. User handles leads independently; they were deliberately absent from all CAD collision/path checks.
4. Lower the lid **vertically at its final XY location**. The integral front skirt closes battery entry and its thicker central extension retains the nut. There are no hooks, latches or sliding sequence. Screw is still absent. Check all perimeter edges seat; the single screw is not permission to force a warped lid flat.
5. Verify smooth gauge passage and insert ONLY M3×8 from the top through H1, last. Reverse for servicing: screw out, then lift vertically. Never use screw preload to flatten the board, close a trapped lead or compress the pouch.

STLs are already **floor-down Base and roof-down Lid**. Broad corner blocks grow from the base floor and lid pads grow from the lid roof; there are no hook undercuts or detached islands. Both meshes are closed manifold single parts.

**Remaining print limitations:** the battery-ceiling bridge spans **21.8 mm** and the captive-nut slot is about **5.8 mm across flats**. Those retained safety features still require a real bridge/slot trial, sag inspection and dimensional gauges. Do not blindly generate inaccessible supports inside the battery slot or nut pocket; if the printer cannot bridge cleanly, stop for process/design review rather than leave trapped support or shorten battery clearance. Lid screw-bore/recess and access holes also require clean bridging/edges in the delivered orientation. No universal support-free claim, slicer profile, production material or torque rating is supplied. The far lid edge no longer has a hook: verify single-screw closure does not lift/warp there during handling.

Top RGB, USB and nonconductive-tool BOOT/RESET access are retained. Conservative component models are not vendor-exact connectors/buttons. Broad RF clearance limitations from the inherited design remain; this compact enclosure does not meet a broad 15 mm antenna clearance in every direction and has no RF certification. No new wire qualification or RF study was performed.

**Manufacturing/charging release remains false.** Remaining gates: physical coaxial fit, print stiffness/creep/preload, seat/insulation wear, complete protected-pack/charger suitability, user lead routing, access usability and existing RF/thermal/magnetic qualifications. These are real blockers to physical release, not missing CAD files. See the inherited [battery/charging constraints](../docs/revision-r2/integrated/RADIO-BATTERY.md).
