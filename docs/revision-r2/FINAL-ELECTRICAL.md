> **Historical/superseded topology.** Current integrated main-PCB design and release gates: [integrated ECO](integrated/README.md). Carrier/PH4/old enclosure/count/hash claims below are archival, not current build instructions.

# R2 FINAL ELECTRICAL — source/CAD handoff ready

**Engineering prototype only. No manufacturing, charging or physical qualification granted.** Main and carrier remain separate, fully wired single-page native KiCad projects. No advisors/delegates, commits, orders or uploads. Final exports now available: [integration handoff](final-export/README.md).

## Closed source/design gates

- Both boards: **ERC0 errors/0 warnings; DRC0 violations/0 opens; native schematic parity0**, configured severities checked (ignored KiCad defaults are not enabled). Cleanup rerun: 17 main invariant checks, carrier independent primary pin/land/BOM audit, and 96 combined checks PASS. Historical preservation checks were retired, not counted as passes. No new DRC exclusion or lowered design rule.
- Exact MLCC bias/tolerance/X5R/stability audit: **C2/C13 replaced**, all other requested caps retained. Primary pin/function/footprint/connector-order audit closed; details in `electrical-completion/PRIMARY-AUDIT.md` and machine checks.
- PH2.0 connector decision resolved: J2 **S2B-PH-SM4-TB(LF)(SN),C295747**; J4/J5 **S4B-PH-SM4-TB(LF)(SN),C265102**. All these SMT headers are fitted by JLC. No manual-SMT variant; sourcing board headers yourself requires a future THT redesign, not substitution.
- User purchases PHR-2/PHR-4 precrimped mates. Carrier cable **1=3.3V,2=GND,3=SDA,4=SCL; <=50mm,1:1**. Verify continuity/polarity/crimps yourself; no AliExpress listing is promised genuine or correctly polarized. J2 pin1=protected PACK+,pin2=GND.

## Final capacitor decisions

| References | Final MPN / LCSC | Bias screened | Screened uF* |
|---|---|---:|---:|
| Main C1 | CL10A475KO8NNNC / C19666 | USB5.25V |1.551|
| Main C2 | **CL21A476MQYNNNE / C16780** | BAT4.23V |10.382|
| Main C13 | **CL21A476MQYNNNE / C16780** | SYS4.50V |9.717|
| Main C3 | CL21A226MPQNNNE / C29277 |3.30V /3.60V ceiling |6.036 /5.560|
| Carrier C5 | CL10A475KO8NNNC / C19666 |3.30V /3.60V ceiling |2.251 /2.132|
| Carrier C6 | CL10A475KO8NNNC / C19666 |1.80V /1.95V ceiling |2.858 /2.803|

*Exact Samsung typical DC-bias curves, initial tolerance,0.85 X5R and0.90 engineering age allocation. **Not guaranteed lot lower bounds or a combined-stress guarantee.** AP2112 supports1uF ceramic. TI recommends nominal IN1..10uF and BAT/OUT4.7..47uF; it does not specify a separate guaranteed derated minimum. Comparison with4.7uF is a conservative sizing screen, not an invented TI stability law. Old C2/C13 CL21A106KAYNNNE fell to4.422/4.189uF even before the age allocation; the same-footprint47uF replacement removes that known margin deficiency. Do not copy legacy regulator-specific bulk targets.

C2/C13 are47uF,6.3V,X5R,20%,0805. **Maximum body height above PCB=1.45mm; maximum Z from main board bottom=2.45mm**, unchanged reserve. Primary package2.00±0.20 x1.25±0.20 x1.25±0.20mm. C16780 was observed stocked in the archived JLC page, not reserved. No added fitted parts:35 main+14 carrier. Replacement pair costs0.2864USD at the observed1–99 tier; this is not an assembly quote. The earlier 12–15USD figure was a planning estimate, not a user-imposed budget or guaranteed delivered price.

## Current layout limits

**Presentation-only update:** the main schematic now has a wired overview and USB / Power / Compute children. [Baseline/post-change electrical and alignment evidence](hierarchy-alignment/README.md) covers preserved pin groups/UUIDs, explicit internal-net scope and PCB path metadata changes, unchanged physical layout, and fresh rendered/native checks. Statements below about cleanup byte preservation describe that historical cleanup; they are not the current schematic/PCB-file hashes. No electrical qualification gate was waived.

Cleanup changes no circuitry, placement, outlines, routing or native source bytes. Existing routing is not certified differential-impedance/SI/ESD performance. L2 is signal-free ground. Typical-cap screens are not bench measurements. Existing previews are retained; GUI review remains blocked/not performed.

## Remaining physical/firmware acceptance gates

- Qualified protected 1S 4.2V pack, documented121mA programmed upper-bound acceptance and4.23V charging limit. Supervised off-body charging only. TS10k bias means **NO cell-temperature sensing**; no added protector/fuse/TVS/thermal subsystem.
- USB100 input budget/inrush; loaded SYS/headroom,3V3 startup/brownout/radio load steps; battery absent/present, DPPM, charge termination, temperatures and actual current. Typical-cap screens are not measured rail stability.
- USB enumeration/reset/suspend, host-off/detach/backfeed; PGOOD firmware detach and ROM/crash conditions remain hardware-unisolated. Both USB orientations, signal quality and ESD behaviour are unqualified.
- Harness continuity/polarity/crimp retention/length, purchased mating clearance, strain relief and non-stress keyed carrier seating. Enclosure/pack/plug fit is not inferred from CAD.
- Carrier3.0–3.6V startup/rundown/backpower;100kHz I2C rise/VOL/throughput,400kHz only after timing/loading checks. ICM plus internal magnetometer identity/FIFO/data-ready/overflow, six-face accel,gyro signs, separate mag transform and final-case magnetic calibration.

## Handoff / hashes

| File | SHA256 |
|---|---|
| main PCB | `8a8fcdcb835654f137e984420b3b601c1f27adddac62a32c3f4d79ee5b803ff8` |
| main interface | `92bb81c4db396dff5c6bee8accaabc6c472d03eeb2b029408f93a182c5d092ba` |
| carrier PCB | `c9848c265e3002c91836c12b921f81c09929de486f18651b46f4fe70ff783fb8` |
| carrier interface | `8f7dfeb40c027448a9655cd69fe066390b340119e5d59ec9bd267e309ab90872` |

Current executable checks and cache report locations: [reproduction](final-export/README.md). Cleanup baseline and retired preservation checks: [evidence](../cleanup/README.md). Local `main` contains only the current root snapshot. Saved CodeChat workspaces and the remote retain historical work, not alternate fabrication inputs.
