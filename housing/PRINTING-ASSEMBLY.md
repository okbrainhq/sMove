# Printing and assembly — keyed compact prototype

**Not released for manufacture or charging.** Use an inert battery dummy first. CAD collision tests do not establish printed strength, tolerances, electrical insulation, lithium-cell suitability or safe charge current.

## Parts and frames

- One 25×30×1 mm populated main PCB; underside/body face at assembled Z10.8, component face Z11.8. Actual ICM accel/gyro +Z outward; raw magnetometer frame differs (see PCB interface).
- Printed base, hooked lid and removable rigid 0.8 mm divider. Flat base underside Z0 faces body. Outer dimensions 44.8×29.4×19.6 mm including hardware.
- One M3×8 socket-cap screw and one M3 nut. **Assumed** head ≤5.68 mm diameter ×3 mm, nut AF5.5×2.4 mm; measure supplied parts. No screw, boss or corner shoe loads the pouch.
- H1 insulating bearing radius 3.4 mm lies in the 3.45 mm all-layer copper reserve. Lower PCB corners each have 1×1 mm copper-free reserves, positive XY stops and top/bottom bearing lands separated by 24 mm. Do not cut away keys or insulate a missing copper clearance with tape as a substitute.

## Wire and battery gates

J2 is two PCB-only plated wire holes, **not a JST or header**. Pin 1 BAT+ = protected PACK_P; pin 2 BAT− = GND. Exactly 2.54 mm centre pitch, 1 mm target finished drill and 2 mm copper pads. Nominal copper gap 0.54 mm and mask web 0.44 mm with 0.05 mm mask expansion.

Engineering acceptance assumptions, not supplied wire specifications: finished hole 0.9–1.1 mm, tinned conductor bundle ≤0.7 mm, insulation OD ≤1.2 mm. Qualify conductor area/current/flex/temperature. Never drill out a plated hole. Thread leads from below, solder from top, trim lead/fillet to ≤0.6 mm above PCB. Individually insulate live ends; no USB connected during assembly. Never solder directly to a pouch or treat RESET as battery isolation.

The nominal 20×30×3 mm body occupies X2.5–22.5, Y7.5–37.5, Z1.8–4.8. The separate acceptance reservation is 21×31×4.3 mm, ending at Z6.1; divider bottom Z6.3 gives 0.2 mm clearance to that reserve. A complete protected pack, PCM, tabs, lead exit and tolerances must fit without compression; listing dimensions alone are not sufficient. Charge/discharge suitability and the existing BQ24074 settings remain unqualified. No automatic cell-temperature sensing or master OFF switch was added.

## Nominal assembly order

1. Deburr/inspect print and drilled PCB; verify copper-free keys, polarity, holes and component orientation. Fit an inert pack dummy, not a live pouch, for initial trials.
2. Insert battery body into the open base using the recorded tilt/translation path in `validation/battery-insertion.json`. It screens 630 discrete poses of the nominal rigid body only. Never bend or force a cell; complete protected-pack insertion is still a sample gate.
3. Install divider on its seats. Insert the M3 nut laterally at H1. Nominal nut Z7.6–10.0; PCB Z10.8–11.8.
4. Prepare and solder insulated leads to J2. Guides at X20.03/22.57, Y4.2 and lacing bores at X18.2/24.1, Y4.7 are actual holes in the integral bridge. Fit nonconductive lacing around the insulated leads and through both lacing bores; secure without flattening insulation. Provide slack above the divider. R2 swept routes are an engineering reserve, not a vendor bend-radius approval. Solder joints are not strain relief: physical pull/flex test is mandatory.
5. Lower PCB onto H1 and both keyed corner supports. Lid upper lands touch only copper-free corner areas. Keep wires clear of battery, screw and RF region.
6. **Hooked lid installation:** hold lid north edge raised 10°, relative to a transverse pivot at (0,1.8,18.4). With lid translated 1.2 mm north, lower into the clearance position; slide south to engage both front-wall hooks; lower north edge to the assembled plane. This is the reverse of `validation/closure-insertion.json` (141 sampled rigid poses). No snap flex is assumed. Do not force a binding print.
7. Fit the single M3×8 screw at H1. Nominal under-head Z15.4, tip Z7.4, 2.4 mm nut engagement, head top Z18.4 below roof Z19.6. The 7.9–8.1 mm under-head-length screen retains ≥0.2 mm tip/divider clearance; this is not a screw tolerance guarantee. No torque value is qualified. Tighten only after dummy fit and stiffness tests.

## Access / removal

USB remains on the east side with mating/insertion clearance; lid apertures expose RESET, BOOT and the single RGB. InspectAssembly's “Lift lid only” and “Explode” deliberately ignore hooks for viewing; **they are not physical disassembly instructions**. Remove the screw, raise north lid edge to 10°, translate north 1.2 mm to disengage hooks, then lift. Disconnect/isolate the battery as the actual pack permits before service. RESET does not disconnect pack power.

## Qualification still required

Printed fits and electrical insulation, hook/PCB rigidity and creep, nut capture and torque, full protected-pack fit/insertion and charge/discharge capability, wire preparation and lacing pull/flex, thermal/magnetic performance, radio/on-body detuning, USB download reliability and controlled impedance. No pouch compression or functional part substitution is authorized to obtain fit.
