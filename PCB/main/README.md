# Main PCB — 25 × 30 mm keyed compact prototype

Canonical editable sources: `smove-r2-main.kicad_pcb`, hierarchical schematic sheets, project/rules and local libraries. Four layers, 1 mm nominal thickness; no signal tracks on In1 GND reference plane. **46 fitted electronics**, unchanged part selections and electrical endpoint sets from f8c7ef6.

- Both XUNPU BOOT/RESET switches rotate from 90° to 0° with verified contact numbering; 17 actual footprint positions change. J2 moves upward 6.1 mm. The lower region (native Y ≥122) is 40.7% smaller.
- U2 remains ICM-20948 at (112.5,117.5), F.Cu, −90°: width-centred, 2.5 mm south of substrate bounding centre, in the central region. Accel/gyro +Z outward; raw magnetometer +Z inward; signed transforms in `interface.json`.
- One top RGB, USB programming and labelled BOOT/RESET. No UART, debug connector or testpoints.
- J2: BAT+ `/Power/PACK_P`, BAT− GND, **2.54 mm centre pitch, 1 mm drill, 2 mm pads**, no paste or fitted connector. Fit qualified insulated leads and housing lacing strain relief; never solder on a pouch.
- H1: 3.2 mm NPTH M3 hole, unchanged 3.45 mm all-layer copper exclusion. H2 removed. Two 1×1 mm copper-free lower corners accept insulating positive registration shoes and lid bearings.
- `dist/`: complete Gerber/drill ZIP and individual layers, schematic/assembly PDFs, SVG/PNG, BOM/CPL, installed-model and conservative-envelope STEP. Installed-model renders omit unavailable component models; conservative assembly contains every fitted envelope, not vendor-exact solids.

[Measurements, candidates, validations and limitations](../../docs/revision-r2/compact-placement/README.md). **Prototype only; manufacturing_release=false.** Native DRC is not controlled-impedance, current/thermal, or physical assembly certification. Clearance settings, severities and exclusions are unchanged from f8c7ef6.
