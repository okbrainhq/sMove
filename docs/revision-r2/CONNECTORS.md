# R2 connector and cable buying guide

**Engineering prototype only. Do not connect a battery or cable until pin-to-pin continuity and polarity are verified. No 5V on PH4; no hot-plug.**

## Board headers — exact selection

|Board / ref|Exact MPN|Per kit|Mate|Pin order|
|---|---|---:|---|---|
|Main J2|JST S2B-PH-SM4-TB(LF)(SN), C295747|1|PHR-2|1 = protected PACK+, 2 = GND|
|Main J4 + carrier J5|JST S4B-PH-SM4-TB(LF)(SN), C265102|2 total|PHR-4 at each end|1 = 3.3V, 2 = GND, 3 = SDA, 4 = SCL|

**AliExpress warning: PH2.0 through-hole headers are often marketed similarly to these SMT headers, but DO NOT fit these footprints. Require the exact S2B/S4B-PH-SM4-TB land pattern; THT substitutes are not acceptable.**

Both types are **2.0mm PH side-entry SMT**, factory-fitted by JLC. No local SMT soldering is recommended. If a connector must be sourced and fitted locally, use through-hole ONLY after a genuine THT footprint ECO before manufacturing; current boards do not accept THT substitutes. No such ECO is authorized or started.

Primary drawing already archived at `evidence/raw/jst-ph.body.gz`: [JST PH drawing](https://www.jst-mfg.com/product/pdf/eng/ePH.pdf). Match the exact suffix, footprint, entry direction and contact count; generic “JST 2.0” descriptions are insufficient.

## Current assembly policy — full JLC only

- **BOM.csv + CPL.csv** for each board: JLC fits ALL **35 main / 14 carrier** parts, including main J2/J4 and carrier J5. Keep each existing JLC-prototype.zip.
- Obsolete hand-solder-headers BOM/CPL and ManualParts.csv are withdrawn; old release/Git history is not a current manufacturing choice. Main J3 debug and carrier H1/H2 remain nonfitted/excluded.
- User buys ONLY PHR-2/PHR-4 cable assemblies and a qualified protected battery as external electrical items, not loose board headers. Separate mechanical hardware requirements below remain.
- [Historical two-connector stock and eligibility evidence](final-export/connector-policy/README.md): 29,056 C295747 versus 7 required; 35,961 C265102 versus 12 required. Public inventory, not reserved allocation; these are historical retrievals, not rechecked during cleanup.

## Cable shopping list per complete kit

- **1 short four-conductor PHR-4-to-PHR-4 cable**, straight **1→1, 2→2, 3→3, 4→4**, total contract length **≤50mm**. Nominal modeled corridor is **42.86mm**, not a demonstrated purchased-cable fit. Check insertion clearance, bend radius, strain relief and length on actual hardware.
- **1 PHR-2 protected-battery lead** with pin 1 PACK+ and pin 2 GND. A qualified protected 4.2V pack is mandatory; a two-wire lead does not provide protection.
- Precrimped assemblies recommended. Have the vendor confirm actual PH contact part numbers, compatible conductor gauge/insulation diameter and crimp tooling/retention. Do not assume wire colors prove polarity; measure every conductor and mate orientation.

Nonendorsed AliExpress search phrases (no stock, authenticity or vendor-quality claims):

- `PHR-4 PHR-4 2.0mm 4 pin precrimped 1 to 1 50mm cable`
- `PHR-2 2.0mm 2 pin protected battery precrimped lead`

Specify ≤50mm rather than accepting common long leads. Photographs and “JST compatible” labels do not establish genuine JST manufacture or pin correspondence. No account actions, quotes, uploads or orders were performed.

## Unclosed acceptance gates

TS uses a 10k bias: **NO cell-temperature monitoring**. Require the documented **121mA programmed upper-bound / 4.23V charge-limit qualification**, qualified protected pack, and **supervised off-body charging only**. USB/input power, thermal, RF, sensor/axis, cable/crimp and printed fit tests remain pending; see [electrical gates](FINAL-ELECTRICAL.md).

Carrier hardware is reduced-head **nylon M2×4, head OD ≤3.2mm**, two pieces for round/slot location. **Source/availability unverified**; ordinary larger M2 heads are not assumed to fit. Follow [printing and assembly](../../housing/PRINTING-ASSEMBLY.md), including the separate closure hardware. This guide does not authorize mechanical substitutions.

Source-yourself board connectors require a future THT redesign; they are not interchangeable with current SMT footprints. No manual-SMT alternative exists.
