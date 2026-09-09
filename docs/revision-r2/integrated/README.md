> **Historical two-M3/JST revision.** Current PTH battery-wire design, dimensions and verification are in [the solder-wire handoff](../solder-wire/README.md). Reports/manifests below describe the previous tree, not current approvals.

# Centered-IMU / two-M3 redesign — UNMERGED prototype

Latest revision supersedes the earlier 14-testpad / J3 / side-screw layout. Native CAD and current reports below are the deliverables; historical reports are not current approvals.

## Implemented

- Same **ESP32-C3-MINI-1-N4** and actual **ICM-20948 / PCA9306 / AP2112-1.8** circuitry. No sensor or battery/charger substitution.
- **U2 on F.Cu at native (112.50, 117.50)mm**, rotation **−90°**. From the PCB northwest bounding corner: **(12.50, 17.50)mm**, exactly centred across width and **2.00mm above** the 25×39mm bounding-box centre. In assembled FreeCAD: **(12.50,21.50,11.80)mm at the package seating plane**.
- Actual signed **accelerometer/gyro +Z outward**, underside toward body. Raw magnetometer +Z inward. `sensor_frame` in [interface.json](../../../PCB/main/interface.json) retains the signed AG/MAG transforms and original package-axis evidence, not a guessed generic IMU axis.
- **ALL TP1–TP14 removed**; external **J3 UART/service header removed**, including its BOOT/EN branches. U1 UART pins30/31 deliberately NC; ICM INT1 pin12 restored NC. Functional BOOT/RESET buttons and silk retained. **USB D±/CC/ESD and native USB programming remain connected.** Dedicated wired IMU page, visible hierarchy wires, single RGB symbol, top LED aperture retained.
- **Two diagonal 3.2mm NPTH M3 holes:** H1=(103.60,103.60), H2=(121.40,135.40)mm. 3.45mm-radius four-layer copper/track/via reserves; 3.4mm-radius insulating bearing surfaces. No external ears, no plated mounting rings.
- USB now points east from the ESP shoulder; PH2 points south into an internal board notch. Components packed using unchanged native courtyards and explicit package envelopes. 47 fitted electronic BOM/CPL items plus two non-BOM holes.
- Revised base/lid/divider, protected raised nut shelves, independently movable FreeCAD Base/Lid/Main/Divider/Battery/Cables/Hardware groups.

## Measured geometry and unresolved gates

**Native CAD outside bounds, including modelled recessed screw heads: 49.8 L × 29.4 W × 19.6 H mm.** This nominal model is strictly below 50×30×20mm. It has only **0.2mm length margin**; it is **not a guarantee for a printed part, purchased screws or completed protected pack**.

The original PH2 connector check was not hidden: conservative plug envelope intersected the original PCB by **1.35mm³**; the current rotated/notched geometry still reports **2.16mm³**. Moving the edge farther under that full-width envelope would remove support/clearance for real connector mounting pads. An exact mated drawing or sample is required before resolving the envelope or revising the connector. **Do not manufacture this as an approved fitted assembly.** The official PH-family drawing confirms the retained part family but does not qualify the actual purchased mate/wire route. [source](https://www.jst-mfg.com/product/pdf/eng/ePH.pdf)

See [mounting/assembly stack and constraints](../../../housing/PRINTING-ASSEMBLY.md). Nominal M3×8 model gives 2.4mm full nut engagement, with a documented **7.9–8.1mm measured-length acceptance screen**, not a claim about the user's actual screws. Closed insulating floors remain between screw tips and pouch. Prefer qualified low-magnetic hardware; stainless markings alone are not a magnetic-field qualification.

The **30×20×3mm / 150mAh** cell remains an **electrically unqualified candidate**. A 21×31×4.3mm installed reservation is not a supplier-approved protected-pack envelope. A rigid nominal 20×30×3mm insertion path was screened at **399 poses without compression or collision**; the larger reservation did not pass the simple tilt search. Protected cell, tabs, PCM and leads must be measured before fitting. Never force, bend or squeeze a pouch to install it.

## Verification

- Baseline for this ECO: **0 ERC / 0 DRC / 0 opens / 0 parity**. [Reports](validation/centered/)
- Current: **0 ERC / 0 DRC / 0 opens / 0 schematic-parity issues** under unchanged configured rules/severities. [Electrical report](validation/electrical.json): **1214 assertions pass**. Exact retained net endpoint sets, intended removals/NCs, supported sensor pad transforms, BOM, top side, M3 pad/component clearance and RF keepout transform checked.
- [Net migrations](validation/centered/net-migrations.json) distinguish intentional removals from harmless net-name scope changes. Current source pose/envelope hashes are checked against native CAD.
- [Mechanical report](../../../housing/validation/mechanical.json): **2087/2088 checks pass**; the one PH2/PCB overlap remains a failure. It includes case/board/component/fastener/battery/RF/USB/PH2 clearances, nut insertion, engagement, bearing contacts, native/STL/STEP and independent group movement.
- [Physical bearing audit](validation/retention.json): no tracks, pads or filled copper in either actual 3.4mm bearing area on any of four layers. The 3.45mm keepout boundary Boolean operation can have sub-0.000001mm² rounding slivers; physical bearings have a separate 0.05mm radial margin.
- [Nominal battery insertion screen](../../../housing/validation/battery-insertion.json) is rigid-body sampled CAD, not a purchased-pack or continuous-motion certification.
- Export/BOM/CPL hashes and intended staged-file scope are verified. No merge, commit, advisor or firmware implementation.

## Routing guidance and limitations

No installed **kiStack** or **KiCad** skill was returned by skill discovery, and no kiStack document was found in the project. Nothing was installed or fetched for execution. KiCad's documented clearance-aware interactive router and differential-pair/length-tuning workflow were reviewed. [source](https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html)

The current desktop was locked and PipeWire capture reported **Session creation inhibited**. **No native GUI routing is claimed.** Layout used the existing KiCad Python/native-board workflow, the already-present constrained router, explicit local REGOUT completion and ground stitching, followed by native DRC. In1 stays a GND reference layer, not a signal-routing layer. No USB/RF probe stubs exist; U2 REGOUT→C9 copper is 1.273mm on F.Cu.

USB routing is a short prototype route, **not certified 90Ω differential routing**: current D− has a roughly 2.02mm B.Cu segment; D+ is F.Cu, and the MCU D+ branch also uses In2. Native rule checks do not establish impedance, pair skew/return-path quality or an eye diagram. Confirm the fabricator's stackup and USB enumeration/download reliability on the prototype before release; controlled-impedance rerouting may be needed. Rail transient/voltage-drop, RF range/antenna detuning, magnetic bias, solder/package orientation, printed tolerances, torque/stiffness, shock and thermal/charging tests remain physical gates.

## Current deliverables / safe rebuild workflow

- [Main native PCB/schematics/BOM/exports](../../../PCB/main/README.md)
- [Housing/native FreeCAD/print exports](../../../housing/README.md)
- [Radio/battery architecture and ten-burst one-hour budget](RADIO-BATTERY.md)
- [Wired IMU page](../../../PCB/main/dist/schematic-imu.png), [root hierarchy](../../../PCB/main/dist/schematic.png), [PCB](../../../PCB/main/dist/top-3d.png), [dimensions](../../../housing/dist/dimensions.png), [GUI](../../../housing/dist/freecad-inspection.png)

**Canonical input is the delivered routed native PCB plus current `parts-main.json` and `interface.json`.** `mechanical-envelope-source.json` and `mechanical-pose-source.json` retain the pre-ECO package envelopes/poses only, enabling verified transforms without invented body sizes. `sync.py` publishes the current native pose; `extract.py` independently checks it. Old migration/layout/packing scripts are explicitly destructive historical ECO helpers, not the release rebuild entrypoint; do not rerun them on the final board.

```sh
/usr/bin/python3 scripts/r2/integrated/sync.py
/usr/bin/python3 scripts/r2/enclosure/extract.py
/usr/bin/python3 scripts/freecad/run.py housing/entry.py generate
/usr/bin/python3 scripts/freecad/run.py housing/entry.py verify
/usr/bin/python3 scripts/r2/enclosure/contact_audit.py
/usr/bin/python3 scripts/r2/final/export.py
/usr/bin/python3 scripts/r2/integrated/verify.py
```

Mechanical verification intentionally exits nonzero while PH2 fit is unresolved. `InspectAssembly.FCMacro` is display-only; `PresentAssembly.FCMacro` explicitly saves styled CAD and GUI evidence. Finish all writes/tests before `seal.py`; manifests explicitly keep manufacturing release false.
