# Converged compact hardware — f8c7ef6 baseline

Isolated workspace 024, branch `okbrain/smove-files/024-e429101b`. No advisors, merge, push, other-chat edits, firmware changes or unrelated audits. **Engineering prototype; manufacturing/charging release=false.**

## Before / after

| Nominal measured CAD | Before | After |
|---|---:|---:|
| PCB substrate W × L × T | 25 × 35.5 × 1 mm | **25 × 30 × 1 mm** |
| Bounding PCB area | 887.5 mm² | **750 mm² (−15.49%)** |
| Actual outline area before drills | 881.67 mm² | **744.17 mm² (−15.60%)** |
| Lower substrate region, native Y ≥122 | 337.5 mm² | **200 mm² (−40.74%)** |
| Complete housing L × W × H, including recessed M3×8 hardware | 46.8 × 29.4 × 19.6 mm | **44.8 × 29.4 × 19.6 mm** |

[Measured dimensions](validation/dimensions.json). Housing length/volume reduction is **4.27%**, not the PCB's 15.49%. The battery reserve, wire/lacing bay, antenna/module overhang, walls and M3×8 vertical stack set separate housing limits. Nominal pouch remains **30×20×3 mm**, without compression, inside a separate 31×21×4.3 mm acceptance reservation. This is not a claim of globally minimum packing or guaranteed printed dimensions.

## Placement work and selection

Sources and actual baseline layout were inspected before editing. [Three arrangements](validation/placement-study.json) were screened **before full routing** using actual courtyard polygons, conservative bounds, assembly-to-edge reserve and unchanged 3.45 mm M3 bearing clearance:

- **32 mm / two M3:** rejected: second bearing conflicts with RESET; additional courtyard conflicts.
- **30 mm / one M3 plus positive keys:** selected: no courtyard/bearing/assembly-edge conflicts. Lower courtyard AABB occupancy ≈60.6% before routing; remaining area includes routing, copper/assembly/edge spacing rather than removable empty solid.
- **29 mm / compressed single-M3 arrangement:** rejected: overlapping switches, charger/LED/passive courtyards and a lower edge conflict. This rejected arrangement is not proof that every possible 29 mm design is impossible.

Seventeen actual footprint positions change, not just the outline. **Both BOOT/RESET footprints rotate 90°→0°**; J2 moves up **6.1 mm**, C1 up **4.5 mm**, RGB and lower passives are repacked. The complete before/after placement list is in [electrical verification](validation/electrical.json) and [placement diff](review/placements.csv). BOOT itself moves slightly downward within the new compact rows; not every component was shifted upward. After routing exposed an escape bottleneck, R22 moved 0.95 mm left, keeping the same part, orientation, outline and clearance rules.

The XUNPU drawing labels the two SPST contacts left=1/right=2 in its top view and shows 5.50 mm outer pad span, 3.40 mm inner gap, 2.00 mm pad height: 1.05×2 mm pads on 4.45 mm centres, matching the native footprint. Rotation preserves SW2.1=MCU_EN and SW3.1=BOOT; both contact 2 pads remain GND. [source](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2304140030_XUNPU-TS-1088-AR02016_C720477.pdf)

## Preserved function and assembly

- Same 46 fitted electronic parts and **exact baseline net endpoint sets**; schematic pages and symbol libraries unchanged. Dedicated wired IMU sheet, single RGB symbol/top-visible LED, USB, RESET and BOOT retained. No UART/debug/testpoints.
- Actual ICM-20948 remains at native **(112.5,117.5), F.Cu, −90°**: width-centred, **2.5 mm south of new substrate bounding centre**, within its central region—not exactly geometrically centred. Accel/gyro +Z outward, raw magnetometer +Z inward; signed transforms and package evidence retained. Main bottom faces body.
- USB connector/ESD/series components, MCU and RF exclusion, IMU and local decoupling placements retained. C1/C2 charger decouplers are relocated with equal or better nearest matching non-ground pad proximity; that metric is not routed-loop/current/SI certification.
- Two **2.54 mm centre-pitch** BAT+/BAT− plated holes, **1 mm drill / 2 mm copper pads**, same polarity, no paste and no fitted connector. Hand-solder and trim top protrusion ≤0.6 mm. Wire/finished-hole/strain-relief assumptions and qualification requirements are in [assembly instructions](../../../housing/PRINTING-ASSEMBLY.md).
- Ordinary vias remain outside SMT paste pads; **no filled/capped via-in-pad process substitution** is required by the compact revision.

## Positive mounting and lid correction

One unchanged **H1 3.2 mm NPTH M3×8 clamp** replaces the two-screw arrangement. H2 is removed; its released area enables real packing. Two separated insulating lower corner supports/XY stops and upper lid bearings contact **new all-layer copper-free 1×1 mm corners**, 24 mm apart. Rotation is stopped by geometry, not screw friction. Two rigid front-wall hooks capture the far end of the lid; H1 screw prevents reverse movement. No clamp contacts U2 or loads the pouch.

The first proposed lid trajectory failed. That [rejected-path evidence](validation/rejected-hook-path.json) is retained. The correction uses the **front roof edge pivot (0,1.8,18.4)** and increases the hook pocket height from 1.30 to **1.55 mm**, rather than reducing PCB electrical clearances or pretending a collision passed. The final [141-pose rigid hook path](../../../housing/validation/closure-insertion.json) passes: remove screw, tilt north edge 10°, translate north 1.2 mm, lift; install in reverse. Positive lift retention and ±1° PCB rotation-stop tests also pass. Print stiffness, fit, torque and creep remain physical gates.

## Evidence

- Baseline and final **ERC 0, DRC 0, opens 0, schematic parity 0**. `--severity-all`, `--all-track-errors`, `--schematic-parity`; configured rules/severities/exclusions unchanged byte-for-byte. Existing ignored defaults remain disclosed in [exports report](validation/exports.json); no new waiver.
- [Electrical verification](validation/electrical.json): **251 assertions pass**, exact retained endpoint sets, part/pad geometry, switch mapping, axes/RF, via/paste separation, source/interface coherence and decoupling proximity.
- [Mechanical native/STEP/STL checks](../../../housing/validation/mechanical.json): **2129 pass**, including source component envelopes, screw engagement, physical bearing contacts, all-installed bounds, RF/USB/wire/pack separation, positive keys/hooks and independent movable display groups.
- [Copper contact audit](validation/retention.json): H1 annulus and both corner contact areas free of pads/tracks/vias/filled copper on all four layers.
- [Battery insertion](../../../housing/validation/battery-insertion.json): **630 sampled poses**, nominal rigid body only. Complete protected pack/PCM/tabs/leads remain unqualified.
- [Real FreeCAD GUI controls](../../../housing/validation/gui-inspection.json): delivered InspectAssembly macro, Explode/Restore, lid display and individual group controls exercised with actual Qt widgets. Display “Lift lid”/“Explode” are **not physical hook-disassembly paths**.
- [Delivery/source-export coherence](validation/delivery.json), [complete SHA-256 manifest](delivery-manifest.json), [Git diff summary](review/diff-stat.txt), [critical source diff](review/critical-source.diff), [full native PCB diff](review/native-pcb.diff). Do not merge based on a truncated changed-file preview.

## Images

Accessible chat copies: [PCB before/after](/uploads/6450ccac-61f3-40fa-8f60-34c138cb033b.webp), [housing before/after](/uploads/c630d58d-4bba-4bcb-9263-8415bd1ca5ab.webp).

- [Before PCB](images/before-pcb.png), [after PCB](../../../PCB/main/dist/top-3d.png), [PCB comparison](images/pcb-comparison.png).
- [Before housing](images/before-housing.png), [after housing](../../../housing/dist/exploded.png), [housing comparison](images/housing-comparison.png).
- [Housing dimensions](../../../housing/dist/dimensions.png), [section](../../../housing/dist/section.png), [FreeCAD inspection](../../../housing/dist/freecad-inspection.png).

KiCad installed-model renders omit unavailable vendor models; native board pads/outline remain genuine. The complete housing uses conservative component envelopes, not vendor-exact solids. Comparison captions disclose scaling.

## Remaining blockers / release limits

**No unresolved nominal CAD/ERC/DRC blocker.** Physical print tolerance, hook rigidity/creep and torque, complete protected-pack envelope/insertion and charging/discharge suitability, wire preparation/lacing pull and flex, thermal/magnetic/RF/on-body behaviour, USB download reliability and controlled impedance are unqualified. Existing battery/runtime assumptions remain in [RADIO-BATTERY.md](../integrated/RADIO-BATTERY.md); no runtime, charge safety, waterproofing or manufacturing release is claimed.

## Rebuild and handoff

Native routed PCB is authoritative. `compact.py` records a one-shot placement study/ECO; **do not replay it or historical placement scripts onto routed output**. Local KiCad Python/CLI and Freerouting 1.9 GUI/CLI were used (analytics disabled), with bounded Python route completion; no native KiCad GUI routing claim. FreeCAD uses the unchanged pinned local runtime, hash-verified from the installed official archive and publisher metadata. No shared workspace was used.

After a deliberate native edit, run `sync.py`, `enclosure/extract.py`, FreeCAD `housing/entry.py generate`, `verify`, `closure-check.py`, `insertion-check.py`, `contact_audit.py`, `final/export.py`, `verify_compact.py`. Run `PresentAssembly.FCMacro` explicitly for GUI images, then repeat mechanical/path checks and `seal_compact.py`. Scripts are under `scripts/r2/`; FreeCAD scripts run through `scripts/freecad/run.py`.

**All deliverables must be staged and committed. No merge is performed.** Review the complete manifest/commit rather than tools that only see uncommitted paths or cap previews at 30. The final chat provides commit ID, changed-file/full-delivery counts and manifest hash; the manifest excludes only itself to avoid self-hashing.
