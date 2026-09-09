# sMove main — compact PTH battery-wire revision

**25 × 35.5 × 1 mm**, four copper layers. J2: two 2.0mm plated pads / 1.0mm hole target, **2.54mm centre-to-centre pitch**, BAT+/BAT- silk, no fitted connector/header and no BOM/CPL purchase. Prepared-wire assumption ≤0.7mm tinned bundle / ≤1.2mm insulated OD, not a claimed supplied gauge. Exact polarity/protection/charge architecture unchanged.

SW3, D1 and R11–R13 moved inward and rerouted. U2 ICM-20948 remains F.Cu (112.5,117.5)mm, −90°; width-centred, 0.25mm north of centre; signed AG +Z outward, raw MAG +Z inward. Actual USB, charger/regulator/decoupling placements retained. No testpoints or UART connector.

46 fitted electronic BOM/CPL items. Two 3.2mm NPTH mounting holes H1=(103.6,103.6), H2=(121.4,131.9)mm with 3.45mm all-layer reserves. Two M3 clamps provide antirotation; physical fit/rigidity remains a gate.

- [Root schematic](smove-r2-main.kicad_sch), [dedicated wired IMU](imu.kicad_sch), [native PCB](smove-r2-main.kicad_pcb)
- [PDF schematic](dist/schematic.pdf), [power/J2 image](dist/schematic-power.png), [IMU image](dist/schematic-imu.png), [PCB top](dist/top-3d.png)
- [BOM](dist/BOM.csv), [pick-and-place](dist/pick-and-place.csv), [assembly guide](dist/ASSEMBLY.md), [Gerbers/drills](dist/gerbers.zip)
- [Current interface](interface.json), [native layout contract](native-layout-contract.json), [validation and limitations](../../docs/revision-r2/solder-wire/README.md)

**Manufacturing release=false.** Native rules pass, but battery/wire/charge acceptance, physical assembly, USB SI/downloads, RF/noise and thermals need qualification. KiCad renders lack some vendor models; the conservative populated-board STEP is explicitly not vendor-exact. Historical source envelope/pose JSON and backup ZIP are provenance only. Native routed CAD and current parts/interface are canonical; use the documented safe rebuild, never replay historical placement helpers.
