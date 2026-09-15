# U4 thermal layout ECO — workspace delivery

## Result and scope

Implemented in `/home/azero/.okbrain/workspaces/smove-files/045`, branch
`okbrain/smove-files/045-ebca5b6f`, based on `main` at **43ee2ea**. No commit or
base-branch modification was made. All ignored/untracked lock, backup,
`docs/revision-r2/` and `housing/` content was left alone.

- Board: eight **GND / net 18** plated through vias, **0.6 mm land / 0.3 mm drill**, and two solid GND pours.
- `smove-r2-main.kicad_dru`: six appended lines defining a **0.21 mm clearance rule scoped only to the two named new zones**. The pre-existing global 0.15 mm rule overrides the zone-local clearance, so setting the zone property alone is insufficient. The original rules are unchanged.
- No new tracks; no moved/deleted tracks, vias, pads, footprints, outlines or existing zones. **Every existing board UUID object, including all four complete zones and their filled polygons, is byte-identical.**
- No schematic, symbol, footprint-library, project-settings or fabrication-output file changed. `dist/jlcpcb/*` was not regenerated.
- U6 was intentionally left untouched. Its exposed-pad cooling warrants a separate layout/assembly review; a drilled cluster under that SMD pad must not be casually treated as standard no-via-in-pad construction.

## Preflight, exact output

`git log --oneline -3`:

```text
43ee2ea board: user routing + direct C11 ground path (thermal-ECO baseline)
5c86d78 Merge okbrain/smove-files/043-2e05b855 into main
267618d fab: regenerate JLCPCB assembly/fab outputs for the routed board
```

`git status --porcelain -- PCB/`:

```text
?? PCB/main/smove-r2-main-backups/
?? PCB/main/~smove-r2-main.kicad_pcb.lck
?? PCB/main/~smove-r2-main.kicad_sch.lck
```

`git merge-base --is-ancestor 43ee2ea HEAD` returned 0. No tracked PCB changes;
only the allowed untracked noise. The base directory was checked again at the
end and still had exactly this HEAD and PCB status.

## Measured geometry — not thermal performance

Measurements are from native copper geometry in millimetres. Saved zone
polygons are unioned, other connected components excluded, and actual drill
voids subtracted. Pads/tracks use KiCad polygonization with maximum 0.001 mm
curve error; circular holes use 1024-sided polygons. Values are reported to
0.001 mm², not with a claim of fabricated-board dimensional accuracy.

### Copper area

| Metric | Before | After |
|---|---:|---:|
| F.Cu same-layer contiguous GND copper containing U4 pin 2, including pads/tracks/via lands, minus holes | 1.058 mm² | 27.802 mm² |
| Directly attached F.Cu zone-only copper, minus cutouts/other components/drills | 0 | **26.008 mm²** |
| B.Cu same-layer contiguous copper reached from U4's original via, minus holes | 0.212 mm² | 50.281 mm² |
| New B.Cu zone-only copper, minus cutouts/drills | 0 | **50.025 mm²** |
| Existing In1.Cu GND filled polygon (before subtracting drilled voids) | 680.173 mm² | 680.173 mm², unchanged |

**Important baseline correction:** the saved board does NOT have 15 mm² of
contiguous front copper on pin 2 or no interlayer path. It already has a
0.6/0.3 mm through via at **(110.3, 119.7)**, UUID
`84533de4-9e53-4210-9cdf-38a20bf1c6b0`, connected by a 0.2 mm track to pin 2
and to the existing In1.Cu plane. Its bottom copper was only an annular land,
not a spreader. The ECO improves an existing narrow connection; it does not
create the first interlayer connection. Electrically connected board-wide GND
area is not interchangeable with thermally effective area.

### Polygon area proof

Both new outlines are the same rectangle:

```text
(104.5,117.0) → (113.2,117.0) → (113.2,123.2) → (104.5,123.2)
gross area = 8.7 × 6.2 = 53.940000 mm²
```

**F.Cu** (`U4_THERMAL_F.Cu`):

```text
53.940000  gross polygon
-26.448115 clearance cutouts / unfilled regions
 -0.777169 other F.Cu component (not counted towards the requirement)
 -0.706854 drilled voids in the directly attached component
=26.007862 mm² directly attached to U4 pin 2 — exceeds 25 mm² by 1.008 mm²
```

**B.Cu** (`U4_THERMAL_B.Cu`):

```text
53.940000 - 3.145030 clearance/unfilled cutouts - 0.769796 drilled voids
=50.025175 mm², one contiguous spreader
```

All eight new via centres lie in both the **same directly attached F.Cu
component** and the B.Cu spreader. U4 pin 2 inherits the zone's **solid/full
connection**, not a thermal relief; its footprint/pad record was not edited.
Both zones use priority 1, 0.2 mm minimum fill thickness, 0.21 mm clearance and
unconnected-island removal. All original zone definitions and fills remain
verbatim. The new rectangles are **17.000 mm** from the antenna keep-out.

### New vias and measured clearances

All are ordinary F.Cu–B.Cu through vias spanning the four-copper-layer board,
GND/net 18, diameter **0.600 mm**, drill **0.300 mm**, no via-in-pad. Coordinates
are absolute KiCad board coordinates, not fabrication-origin offsets.

| X mm | Y mm | Minimum gap to ANY existing track/via/pad, all copper layers |
|---:|---:|---:|
| 108.500 | 121.400 | 0.215887 mm |
| 108.600 | 119.700 | 0.267680 mm |
| 110.200 | 120.600 | 0.300000 mm |
| 111.400 | 121.900 | 0.236396 mm |
| 111.700 | 119.500 | 0.233773 mm |
| 112.100 | 120.300 | 0.300000 mm |
| 112.100 | 121.200 | 0.300005 mm |
| 112.900 | 121.600 | 0.237500 mm |

Minimum new-via/new-via edge gap: **0.294427 mm**. The array is staggered around
existing routing rather than forcing a regular grid through it. Zone/foreign
copper minimum gaps: **0.209490 mm F.Cu**, **0.209585 mm B.Cu**. These additional
geometric checks are important because the board-wide rule permits 0.15 mm.

### Counts and preservation proof

| Board item | Before | After | Change |
|---|---:|---:|---:|
| Track segments | 426 | 426 | 0 |
| Vias | 77 | 85 | +8 GND |
| Zones, including 3 rule/keep-out areas | 4 | 6 | +2 GND |
| Footprints | 53 | 53 | 0 |

The PCB text diff is **243 insertions / 0 deletions**; the scoped rules diff
is **6 insertions / 0 deletions**. All **570 original UUID-bearing board
objects**, plus the board settings and net table, are identical. SHA-256 of
the sorted original-object contents, before AND after:

```text
2395968efe291f80d9d4094aeb9fcb709e6de5a6fb2a11288028f21f4feb7b15
```

C11's direct grounding path remains exactly:

```text
F.Cu, GND, width 0.2 mm:
(113.8,116.3) → (113.8,116.127486) → (113.987486,115.94)
0.6/0.3 mm GND through via at (113.987486,115.94)
```

Its two segments and terminal via have matching before/after individual
SHA-256 hashes, UUIDs and complete s-expressions in `geometry.json`:

| UUID | Before = after SHA-256 |
|---|---|
| d8e59a01-d4bc-4fee-9aa6-d1b957c9a084 | 3efd501127e1100831a573a04b7a733f456befd1b488be982abbc4ddbfa67016 |
| 772e4247-d55b-4c14-9ccd-2492ecce88d9 | cea57377c59c4c5105f0b803d8feb91c202f6ae6ba926a14cab701b00d2d21b4 |
| 8855345a-7815-4444-8592-dd19988b35d9 | 7880821dcc05619653ac3cdfea56daa081877ceac84ed72dd1585ad4da671673 |

C11's entire footprint and all other nets' geometry are also covered by the
byte-equality assertions. Added objects are restricted to eight GND vias
and two GND zones; nothing was silently deleted or reserialized.

## DRC and refill evidence

Baseline command, before any change:

```sh
kicad-cli pcb drc --exit-code-violations --format json --output /tmp/smove-u4-eco-045/before-drc.json PCB/main/smove-r2-main.kicad_pcb
```

Result: **0 violations, 0 unconnected items**, exit 0; archived as
`baseline-drc.json` (default errors/warnings).

Final command, KiCad **9.0.8**, all severities including exclusions:

```sh
kicad-cli pcb drc --exit-code-violations --severity-all --all-track-errors --format json --output docs/u4-thermal-eco/drc.json PCB/main/smove-r2-main.kicad_pcb
```

Result: **0 violations, 0 unrouted/unconnected**, exit 0. No rule suppression
or DRC exclusions were added. Schematic parity was not requested/tested.

A full second refill was also run on an isolated copy with the actual
`.kicad_pro` and `.kicad_dru`. The geometric symmetric difference for **each
of the three copper zones was exactly 0 mm²**, including the original In1.Cu
plane (`refill-check.json`). The copied project files are essential: refilling
a standalone PCB with default project rules gives different copper clearances.

## Estimated thermal result — conditional, not measured

**This ECO is not thermal sign-off for sustained 470–700 mW.** Neither
junction temperature nor thetaJA was measured. The baseline review's
220–250 °C/W is not independently validated, especially given the existing
via/inner-plane path found above. A claim of ~130 °C/W or halving the RF peak
rise would be unsupported.

### Datasheet reference

Torex's XC6220 datasheet, SOT-25 power-dissipation page 26, gives **166.67 °C/W**
for a **40 × 40 mm**, 1.6 mm FR-4 test board, approximately **800 mm² copper
on each face**, four 0.8 mm through holes, natural convection. Its 600 mW
rating at 25 °C uses **Tj = 125 °C**. That much larger reference fixture cannot
be substituted for this board. The unmounted 250 mW figure corresponds to
400 °C/W on the same 100 °C rise basis. [source](https://media.digikey.com/pdf/Data%20Sheets/Torex/XC6220.pdf)

### Transparent copper/connection adjustment

For an illustrative, deliberately limited estimate, use:

```text
thetaJA = 400 || (Rshared + Raccess + Rvia)
X || Y = X*Y/(X+Y)
```

- The 400 °C/W parallel bypass is an **assumed heuristic** based on the
  unmounted reference, not a measured package thetaJC or independently known
  heat-flow branch.
- Calibrate the before network to the review's **250 °C/W** upper estimate.
- **Measured/design geometry:** the old 0.2 mm neck has 0.341697 mm centreline
  outside the U4 pad and original via land. The specified copper is 35 µm;
  F.Cu-to-In1.Cu centre spacing is 0.315 mm. Importantly, the old via already
  reaches this inner plane; do NOT charge it the full 1 mm barrel resistance
  when modelling that path.
- **Assume** copper conductivity 390 W/(m·K) and 25 µm plated via walls.
  `R = L/(k*A)` gives **125.16 °C/W old neck**, **31.64 °C/W old via to In1**,
  and about 100.45 °C/W for a full-depth 1 mm barrel.
- The calibration leaves `Rshared = 509.86 °C/W`, representing the unknown
  die/lead/board path. This is fitted, not a datasheet parameter.
- After the solid F.Cu pour, **assume 60 °C/W spreading/access resistance**
  (~0.82 squares of 35 µm copper). Credit only **4.5 effective parallel vias**
  from the original one plus eight new ones, acknowledging non-isothermal
  access. The other existing vias now reached by the pour receive no credit.
- Keep the shared package/board resistance fixed: give **no additional
  board-to-air cooling credit** to the measured 50.025 mm² bottom spreader.
  This avoids inventing an area-to-thetaJA curve that the datasheet does not
  supply. It is a limited connection-improvement model, not an enclosure
  thermal simulation, and the assumptions are not guaranteed conservative.

```text
Before: 400 || (509.86 + 125.16 + 31.64) = 250.00 °C/W
After:  400 || (509.86 + 60.00 + 31.64/4.5) = 236.22 °C/W
Delta: -13.78 °C/W (~5.5%)

Relative to the 166.67 °C/W datasheet fixture:
assumed board/connection penalty +83.33 → +69.55 °C/W
```

Varying assumed access 40–120 °C/W and effective vias 2–9 gives **232–247 °C/W**
with the same 250 °C/W baseline. This is a model-sensitivity span, **not** a
confidence interval or a guaranteed bound; unknown die-to-GND coupling,
plating, assembly, U6 heating, airflow and enclosure conditions may dominate.

### Peak-power steady-state projections

Stated design scenario: **40 °C local board ambient**, Vin **5.3 V**, Vout
**3.3 V**. Treat peak dissipation as continuous for this deliberately severe
steady-state projection; quiescent power is neglected relative to the stated
470/700 mW. These are *pre-protection linear projections*, not actual measured
RF burst peaks.

| Peak-power scenario held continuously | Before thetaJA 250 | After estimated thetaJA 236.22 | Delta |
|---|---:|---:|---:|
| 235 mA, 470 mW: junction rise | 117.50 °C | 111.02 °C | **−6.48 °C** |
| 235 mA, 470 mW: junction temperature | 157.50 °C | 151.02 °C | **−6.48 °C** |
| 350 mA, 700 mW: junction rise | 175.00 °C | 165.35 °C | −9.65 °C |
| 350 mA, 700 mW: junction temperature | 215.00 °C | 205.35 °C | −9.65 °C |

These projections exceed the 125 °C power-rating basis and reach/exceed the
**typical 150 °C thermal shutdown** region; the device cannot be assumed to
remain regulating at those projected temperatures. Thermal shutdown is not
an operating target or a substitute for qualification. [source](https://media.digikey.com/pdf/Data%20Sheets/Torex/XC6220.pdf)

**Unverified:** actual transient RF peak temperature, duty-cycle response,
physical thetaJA, worst-case enclosure ambient/airflow, actual via plating,
and XC6220 die-to-pin-2 thermal coupling. Verify a populated board under the
real RF workload and charging conditions. If 470–700 mW is sustained at the
stated ambient, use a lower-loss supply/thermally stronger regulator solution
rather than treating this copper ECO as sufficient.

## Reproduction and artifacts

`verify.py` reads the baseline with `git show 43ee2ea:...`, asserts byte-level
preservation, measures net copper area and checks clearances/connectivity.
It never writes a PCB/project file. `thermal-model.py` separately calculates
the labelled conditional model; it does not conflate geometric and thermal
measurements. Both require KiCad's Python `pcbnew` module and Shapely 2.x.

The commands used with the temporary dependency directory were:

```sh
PYTHONPATH=/tmp/smove-u4-eco-045/pylibs /usr/bin/python3 docs/u4-thermal-eco/verify.py > docs/u4-thermal-eco/geometry.json
PYTHONPATH=/tmp/smove-u4-eco-045/pylibs /usr/bin/python3 docs/u4-thermal-eco/thermal-model.py > docs/u4-thermal-eco/thermal-model.json
```

With Shapely installed in the same Python environment, omit `PYTHONPATH`.
No project trick was silently saved.

- `geometry.json`: counts, positions, clearances, area arithmetic, individual and aggregate preservation hashes.
- `drc.json`, `baseline-drc.json`: CLI DRC reports.
- `refill-check.json`: all copper fills reproduce with zero symmetric difference.
- `thermal-model.json`: input geometry, assumptions, network values and temperature projections.
- `after-front.png`, `after-back.png`: native-copper review diagrams, **not fabrication artwork**.
