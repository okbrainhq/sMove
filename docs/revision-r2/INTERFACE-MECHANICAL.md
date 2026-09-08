# Reusable IMU carrier contract / two-piece case handoff

**No CAD or physical fit is implemented.** This document freezes electrical interface meaning, not unplaced dimensions. Main-board iterations must retain this interface without moving the carrier's voltage translation onto the host.

## Connector / cable contract v1

| Pin, both board headers | Function | Constraint |
|---|---|---|
| 1 | 3V3 host supply | Nominal 3.3V; permitted carrier input 3.0–3.6V. NOT battery or USB 5V |
| 2 | GND | Common signal/power return; protected battery negative on sMove main |
| 3 | SDA | 3.3V-domain open-drain I2C; carrier owns pull-up |
| 4 | SCL | 3.3V-domain open-drain I2C; carrier owns pull-up |

- Exact board part on main J4 and carrier J5: **JST S4B-PH-SM4-TB(LF)(SN), C265102**, four-position **2.0mm** side-entry SMT, with mounting anchors. The captured JLC exact part has 35,961 public stock units. Manufacturer PH drawing is captured in `evidence/raw/jst-ph.body.gz`. [source](https://jlcpcb.com/partdetail/JST-S4B_PH_SM4_TB_LF_SN/C265102) [source](https://www.jst-mfg.com/product/pdf/eng/ePH.pdf)
- Manual cable: **two PHR-4 family housings**, four correctly crimped contacts per end suitable for the actual insulated wire, four conductors **<=50mm finished connection length**. 26AWG is a supplier lead, not a verified acceptance requirement; select contact/wire insulation and strain relief from the genuine PH drawing. No bare twist joints or 200mm coiled harness in the antenna zone.
- Harness continuity must be **1-to-1, 2-to-2, 3-to-3, 4-to-4** with no shorts. Mark pin1 triangle/square pad and the full `3V3 GND SDA SCL` order on both PCBs. Check manufacturer mating-face versus solder-side views; a connector photograph or wire color does not define numbering.
- The PH housing has mating keying/friction retention, **not guaranteed circuit polarity**. A wrongly populated/reversed cable can still be dangerous. There is no extra connector reverse-polarity protection circuit. Use an incoming continuity/polarity check before connecting either board.
- No hot-plug promise. Power both boards together from the host 3.3V tree; host I2C outputs remain high-impedance/open-drain through shutdown. Do not drive an unpowered carrier from another powered host. No 5V host, independent external pull-up rail, IRQ cable, auxiliary SPI header or additional carrier power source.
- Start **100kHz**, <=50mm internal cable, carrier-only 4.7k pull-ups on both domains. Disable ESP internal pull-ups. Other 3.3V hosts must remove/disable duplicate pulls or requalify sink current/rise time. 400kHz only after the measured limits in `ELECTRICAL.md`; longer external cables need a new interface review, not assumed compatibility.

## Sri Lankan leads: provenance and acceptance, not inventory claims

The orchestrator relayed these narrowly scoped leads from Flash; this handoff does not promote them to direct numeric stock or manufacturer-authenticity evidence:

- [Alphatronic PH-like listing](https://alphatronic.lk/product/jst-xh-2-0mm-connector-cable-base-2-6-pin/): title/body reportedly PH 2.0mm despite XH in URL, selector 2–6 positions including 4, cable + base, 200mm/26AWG. Exact four-pin option stock, actual dimensions, brand and crimp/polarity are unverified. Potential cable sourcing lead only; **not a substitute for the selected SMT header footprint**.
- [Alphatronic XH-like alternative](https://alphatronic.lk/product/2-10-pin-jst-xh-2-54-pitch-connector-cable-and-base/): marketed as 2.54mm XH; genuine JST XH nominal pitch is not PH 2.0mm. Do not substitute or force-mate. Not selected.
- [Duino four-pin single-head lead](https://www.duino.lk/product/jst-connector-4-pin-single-head/): search-index lead only, direct fetch reportedly blocked. A single-ended cable is not the complete inter-board harness.

Acceptance requires vendor/physical confirmation of **four-position PH 2.0mm**, correct mating geometry, assembled pin polarity, secure crimps and measured length. Two preterminated leads may require a qualified short harness fabrication; do not silently count an unverified cable as available. If no accepted PH4 harness can be obtained, hold assembly and revise both board connector footprints together while preserving the four electrical pin meanings. No orders or supplier contacts were made here.

## Physical mount and axes

- Main PCB target **25x35mm or smaller only after placement**. Carrier starting study **20x20mm** includes PH4 courtyard and two mounting features; the IC alone is not the carrier size. Anticipate approximately 250–350mm² of carrier component/connector/hole keepout demand, versus a 400mm² starting outline; this is a rough packing allowance, not completed placement.
- The main's component/courtyard study is roughly **650–800mm²** before full routing/antenna/edge-support resolution. A 25x30mm main is tight; 25x35mm gives 875mm² but is still provisional. A large PH4 connector can offset much of the area removed with 13 sensor-circuit parts.
- Use a **rigid registered carrier seat** molded/printed into the base or lid near the mechanically stable center. Two small mounting features plus positive edge registration prevent yaw/translation; avoid suspending it on wire or a soft pouch. Prefer nonconductive posts/clips/fasteners, not steel beside a magnetometer.
- Starting datum concept: two approximately 2mm clearance features, one round locator and one slightly relieved/slot locator, separated as far as reasonable on the carrier. Add an asymmetric plastic register or keyed board corner so 180° reversed assembly is visibly impossible. Dimensions/hole separation are **not frozen before placement**. Do not overspecify a stress-inducing interference fit or torque a tiny screw against the IMU.
- Support at small peripheral nonconductive ledges, not beneath the sensor package. Reserve routing/copper clearances at supports/holes and inspect mask abrasion. Keep button actuation, USB insertion and main-board bending out of the carrier's load path. A rigid seat is not permission to clamp a stressed board.
- Define enclosure frame: +X across waist/right when installed, +Y toward the designated top/antenna end, +Z away from body. Define carrier datum independently: +X along its PH pin1-to-pin4 direction, +Y away from the connector edge into the board, +Z out of its component face. Print arrows and pin1 on the carrier, plus a matching case register mark.
- Record the actual signed package-to-carrier and carrier-to-enclosure rotation matrices **after orientation/placement is chosen**. Do not assume the ICM package axes follow the connector edge. Require repeatable orientation after removal/reinstallation, and verify all three accelerometer/gyro/magnetic axes physically. No loose reversible 4-wire board that silently changes sensor axes.
- Place the ICM away from USB insertion/button loads, main LDO/charger heat, protected-pack PCM magnets/steel, battery leads and charge/current loops. The selected design has no power inductor, but still has magnetic current interference. Keep high-current positive/return runs close together and away from the carrier. Validate hard/soft-iron and current-dependent offsets in the finished case, not just on a bare module.

## Base + lid, battery and RF stack

- Aim for **two printed structural parts**: base and lid, with integral board supports, carrier register and battery barrier. Do not carry over CFIX's nine-piece arrangement. Snap/edge-retention and any lid screw choice remain mechanical gates, not implemented geometry.
- Accept only a complete insulated **21x32x6.5mm** protected pack assembly (including PCM/wrap) into a **23x34x8mm** bay, with additional PH mating and strain-relieved lead cavities. Dimensions are design acceptance limits, **not measurements of Duino BAT0493**. No compression of pouch/seals to fit.
- Battery below main board only where a rigid nonconductive barrier and verified clearance protect the pouch from PCB edges, pads, connectors and service tools. Carrier gets its own seat; no adhesive-only attachment directly to the cell. Keep solder protrusions inaccessible to the pack.
- Preserve the module manufacturer's exact **all-layer** antenna copper/trace/via/component keepout. Prefer antenna overhang at a board edge. Reserve the recommended approximately **15mm antenna environmental clearance**, especially from foil cell, pack PCM, connectors and all cable loops; a plastic barrier does not provide RF separation. [source](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32c3/pcb-layout-design.html)
- A 34mm bay plus a real RF setback is unlikely to fit entirely under a 35mm main footprint without extending the case. A preliminary **29–33 x 50–57 x 17–22mm** enclosure study is more honest than promising 25x35 overall. Carrier/PH overlap may increase height or width; exact antenna overhang, walls, print tolerances and lead exits decide it. Nothing here is a fit guarantee.
- Four layers/top-side assembly per board preferred: uninterrupted reference ground near I2C/USB, power distribution with short returns, antenna exclusion overriding all copper layers. Separate local project libraries and fabrication outputs; no shared board edge origin assumptions between projects.

## Next-worker deliverable boundaries

Create isolated `main` and `imu-carrier` KiCad projects only in the next implementation phase, each with one readable fully wired A3 schematic, its own PCB/BOM/CPL/DRC/ERC and local symbols/footprints as needed. Generate and validate a single matching base/lid assembly with the mounted carrier and accepted real harness/battery envelopes. Do not overwrite CFIX or claim its validation applies. This architecture handoff intentionally stops before those files exist.
