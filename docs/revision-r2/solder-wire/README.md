# Compact PTH battery-wire revision — engineering prototype

Based on current main **4cb3c32193bda18d624b7974b65162a7a44f69a0**, in isolated workspace **023**. No merge, push, advisor, other-chat work, purchase or firmware changes.

## Implemented and measured

| Nominal CAD measurement | Before | After | Reduction |
|---|---:|---:|---:|
| PCB bounding substrate, W × L | 25 × 39 mm | **25 × 35.5 mm** | 3.5 mm length; **8.97% bounding area** |
| Actual outline area, before drills | 911.57 mm² | **881.67 mm²** | **3.28%** |
| Complete housing, L × W × H, including recessed M3×8 hardware | 49.8 × 29.4 × 19.6 mm | **46.8 × 29.4 × 19.6 mm** | 3.0 mm length; **6.02% bounding volume** |

[Measured geometry](validation/dimensions.json). The smaller percentage for real outline area is deliberate: the obsolete deep connector notch is filled in. These are not printed-part or purchased-hardware tolerance guarantees.

- **J2 was actually an SMT JST S2B-PH-SM4-TB**, not a through-hole connector. The family documentation also identifies the surface-mount variant. [source](https://www.jst-mfg.com/product/pdf/eng/ePH.pdf)
- J2 is now **two plated through-hole wire solder pads at exactly 2.54 mm (0.1 inch) centre-to-centre pitch**, as clarified by the user. **No fitted JST, pin header, mating body or connector BOM/CPL item.** The old footprint, two MP hold-down pads and schematic MP pin/ground stub are removed.
- **2.0 mm copper pad diameters, 1.0 mm finished-hole target, 0.5 mm nominal annular ring**, 0.54 mm copper separation and **0.44 mm nominal mask web** with 0.05 mm mask expansion. No paste. BAT+ and BAT- are visible on top silk.
- Engineering wire envelope: **tinned conductor bundle ≤0.7 mm diameter**, insulation **≤1.2 mm OD**. A **0.9–1.1 mm finished-hole acceptance screen** leaves ≥0.2 mm diametral threading clearance at the smallest hole and ≥0.45 mm radial annulus at the largest. **No exact wire gauge was supplied or asserted.** Measure the finished plated hole and prepared wire; qualify strand area, insulation, flexibility, current and temperature. Do not drill out a plated hole to fit a wire.
- Solder accessible from the top, wires threaded from below; top lead/fillet protrusion reserved to **0.6 mm maximum**. Main J2 launch is widened to 0.5 mm where clear; the established 0.2 mm power/fine-pin fanout remains, and the separate battery-voltage-sense branch may use 0.15 mm. This is not a certified current rating: measure peak load drop and heating on the real stackup/pack/wires.
- **SW3, D1 and R11–R13 are physically relocated and rerouted into the freed connector area**, H2 moves inward by 3.5 mm, and the board is shortened. Not an outline-only crop. U1, U2, regulators, charger, USB and all decoupling capacitor placements stay unchanged.
- U2 remains the **actual ICM-20948 at (112.5,117.5) mm, F.Cu, −90°**: width-centred and 0.25 mm north of the new board bounding centre. Actual **accelerometer/gyro +Z outward**, raw magnetometer +Z inward; underside of the ESP PCB faces the body. Signed sensor transforms and package evidence are retained.
- Dedicated **wired IMU sheet**, single placed RGB symbol, top-visible RGB aperture, USB programming and BOOT/RESET silk retained. **No testpoints or UART connector**. In1 remains a GND reference plane without signal tracks; the original all-layer RF exclusion is unchanged.
- **46 fitted electronic BOM/CPL entries**; J2 and two NPTH mounting holes are PCB features, not assembly purchases.

## Mechanical retention and wiring

Two separated **3.2 mm NPTH M3 holes** remain for positive antirotation and rigid registration: H1=(103.6,103.6), H2=(121.4,131.9) mm. The two-screw arrangement avoids relying on a lone screw's friction. 3.45 mm all-layer copper reserves surround 3.4 mm insulating bearing faces. No contact with U2 or antenna; no screw or PCB load goes through the battery.

The same verified nominal vertical screw stack is retained: M3×8 underhead Z15.4, tip Z7.4, captured nut Z7.6–10.0 (2.4 mm engagement), PCB Z10.8–11.8, recessed head top Z18.4, outer roof Z19.6. The **measured 7.9–8.1 mm underhead-length screen** is narrow and must be checked on real screws, nuts and prints. See [full assembly instructions](../../../housing/PRINTING-ASSEMBLY.md).

The smaller case has a **dedicated paired-wire bay**, two 1.6 mm guide bores and two **1.2 mm lacing bores in an integral insulating bridge**. Fit nonconductive lacing around the insulated leads through these bores; leave a service loop above the divider. CAD models two independent 1.2 mm OD wire envelopes with R2 centreline bends, not a phantom connector reserve. Straight lacing passages and knot space are screened; **actual lacing/knot/preload and pull/flex resistance are not qualified or fully modelled**. Solder joints alone are not strain relief. No clamp presses on the pouch.

A nominal rigid **20×30×3 mm** body insertion path passes **630 sampled poses**, including entry from above, tilt about −Y and XY translations; no bending/compression. This does **not** establish insertion/removal of the complete 21×31×4.3 reservation or an actual protected pack with PCM, tabs and wires. Try an inert dummy first and never force a pouch.

## Verification

- **Baseline and post: ERC 0, DRC 0, opens 0, schematic parity 0**, under unchanged configured rules/severities, no new exclusions. Ignored KiCad defaults remain disclosed in the export report.
- [Electrical assertions](validation/electrical.json): **1256 pass**, including exact retained endpoint sets, the sole J2.MP removal, critical placements, signed axes, RF, pad/hole/mask geometry and BOM.
- [Net migration](validation/net-migrations.json): only J2.MP is intentionally removed; J2.1 protected PACK_P and J2.2 GND endpoints and all retained electrical architecture are unchanged.
- [Mechanical checks](../../../housing/validation/mechanical.json): **2314 pass**; current native solids, assembly bounds, hardware/PCB/pack/RF/USB/wire collision screens, nut insertion, screw engagement, bearing contacts, STL/STEP and independent display groups. The **obsolete PH2 mate check is removed because the part is removed**, not suppressed; its 2.16 mm³ baseline failure remains in the baseline report.
- [Bearing/copper audit](validation/retention.json): both physical bearing areas free of pads, tracks, vias and filled copper on all four layers.
- [Nominal insertion](../../../housing/validation/battery-insertion.json); [FreeCAD GUI control tests](../../../housing/validation/gui-inspection.json). `InspectAssembly.FCMacro` retained; real desktop Explode/Restore was also visually checked. Base, Lid, Main, Divider, Battery, Cables and Hardware remain independent movable groups.
- [Source/export coherence](validation/coherence.json): **400 checks pass**; [commit handoff instructions](HANDOFF.md), and complete delivery manifest/hash verification cover native CAD, libraries, generators, exports, BOM, documentation and reports.

## Battery/runtime and remaining limits

**Actual cell suitability is still gated.** The 150 mAh / 30×20×3 listing is not a qualified protected battery specification. Preserve the **BQ24074 → AP2112 3.3 V → AP2112 1.8 V** architecture and external protected-pack requirement; R21 ISET, R22 ILIM and R23 TS bias are unchanged. No automatic cell-temperature sensing. Do not connect/charge a candidate merely because it fits.

Retain the **one-hour session with ten 30-second bursts** (300 s active, 3300 s standby). [Existing what-if budget and qualification gates](../integrated/RADIO-BATTERY.md) are unchanged, not a runtime promise. No firmware was implemented. Direct soldering removes convenient battery unplugging; there is still **no latching master OFF switch**. RESET does not isolate the pack or charger.

Physical gates remain: full protected-pack envelope/insertion, current/ESR/charge acceptance, real hole/wire/solder fit and strain relief, print/hardware tolerances, torque/rigidity/creep, magnetic bias, radio/on-body detuning, thermals, USB download reliability and controlled impedance. Native DRC does not certify USB signal integrity. KiCad installed-model renders omit some component models; the housing's complete component bodies are conservative envelopes, not vendor-exact solids. **Manufacturing release=false.**

## Current images

- [PCB top](/uploads/affa7739-2cb2-41de-a6d8-bc5b959e94e7.webp)
- [Power schematic / J2](/uploads/9b5bdd6d-a0ea-4af8-bc6d-db4bad226110.webp)
- [Dedicated wired IMU schematic](/uploads/9a4a96c2-1345-4f35-9fb5-a6689980eeff.webp)
- [Housing exploded](/uploads/37ebcfaa-a060-4ff5-87e2-ec7d9e834bde.webp)
- [Measured housing](/uploads/b14dbb23-9e6c-436b-8fcc-e7d46cc0d2af.webp)
- [Live desktop Explode](/uploads/0beae6ef-4f15-4944-8319-3dd63456cf03.webp), [Restore](/uploads/9949a2b5-adea-46c5-ad0f-6fecbacd4433.webp)

## Safe rebuild

Native routed PCB + parts/interface JSON are canonical. `solder_wire.py --apply` is a one-shot ECO record, not a release rebuild; do not replay it on routed output. Historical placement scripts are likewise not current rebuild entrypoints. After a deliberate native edit:

```sh
/usr/bin/python3 scripts/r2/integrated/sync.py
/usr/bin/python3 scripts/r2/enclosure/extract.py
/usr/bin/python3 scripts/freecad/run.py housing/entry.py generate
/usr/bin/python3 scripts/freecad/run.py housing/entry.py verify
/usr/bin/python3 scripts/freecad/run.py housing/insertion-check.py
/usr/bin/python3 scripts/r2/enclosure/contact_audit.py
/usr/bin/python3 scripts/r2/final/export.py
/usr/bin/python3 scripts/r2/integrated/verify_wire.py
/usr/bin/python3 scripts/r2/integrated/coherence_wire.py
```

Run `PresentAssembly.FCMacro` explicitly in FreeCAD only when refreshing GUI styling/images, then rerun mechanical verification to record the final native hash. The pinned local runtime was reused; no downloaded runtime/substitution or other workspace edits. Older integrated/recovery reports and the backup ZIP are historical provenance, not approvals for this revision.
