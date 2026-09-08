# sMove main — centered integrated IMU / two-M3 revision

Native **25×39×1mm bounding substrate, four copper layers**, with east USB and south PH2 access reliefs. U2 **ICM-20948** is on F.Cu at **(112.50,117.50)mm**, −90°, upper centre; signed AG +Z outward, raw magnetometer +Z inward. Original PCA9306/U5/C5–C9/R16–R20 circuitry retained. No J3/UART header, J4/J5 harness or TP footprints. U1 UART pins30/31 and U2 INT1 restored NC; USB programming and BOOT/RESET remain functional connections.

47 fitted electronic BOM/CPL entries; two non-BOM **H1/H2 M3 3.2mm NPTH holes** at (103.60,103.60)/(121.40,135.40)mm. Copper reserves radius3.45mm on every layer. See [full handoff and intentional net migrations](../../docs/revision-r2/integrated/README.md).

- [Root schematic](smove-r2-main.kicad_sch), [dedicated IMU page](imu.kicad_sch), [native PCB](smove-r2-main.kicad_pcb)
- [PDF schematic](dist/schematic.pdf), [wired IMU image](dist/schematic-imu.png), [top PCB image](dist/top-3d.png), [assembly drawing](dist/assembly-top.pdf)
- [BOM](dist/BOM.csv), [pick-and-place](dist/pick-and-place.csv), [assembly guide](dist/ASSEMBLY.md), [Gerbers/drills](dist/gerbers.zip)
- [Current mechanical interface](interface.json), [actual native layout contract](native-layout-contract.json), [current electrical report](../../docs/revision-r2/integrated/validation/electrical.json)

**Manufacturing release=false.** Native rules pass, but impedance/USB downloads, RF, sensor noise/magnetic bias, rail transients, actual package assembly and PH2 mate fit still need qualification. No claim of native GUI routing: locked desktop prevented that; current routing used the existing constrained toolchain and native DRC.

`parts-main.json` and routed native CAD are canonical. Geometry source JSON files preserve original package envelopes/poses for migration only; never use them as current placements. The documented rebuild exports from the native board rather than rerunning destructive historical ECO placement helpers.
