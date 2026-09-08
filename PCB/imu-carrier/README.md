> **Historical/superseded topology.** Current integrated main-PCB design and release gates: [integrated ECO](../../docs/revision-r2/integrated/README.md). Carrier/PH4/old enclosure/count/hash claims below are archival, not current build instructions.

# R2 imu-carrier

Native editable project: [smove-imu-carrier.kicad_pro](smove-imu-carrier.kicad_pro), [board](smove-imu-carrier.kicad_pcb), [schematic](smove-imu-carrier.kicad_sch). Local libraries, parts data and mechanical interface are source dependencies; do not replace them with older revisions.

## Separate fabrication / assembly inputs

- [gerbers.zip](dist/gerbers.zip): fabrication only, with exact raw Gerbers/drills in `dist/gerbers/`.
- [BOM.csv](dist/BOM.csv): **14 fitted parts, all fitted by JLC**, including SMT headers.
- [pick-and-place.csv](dist/pick-and-place.csv): unchanged original CPL columns/data; filename only renamed.

## Non-JLC reference outputs

[Schematic PDF](dist/schematic.pdf), [assembly guide](dist/ASSEMBLY.md), SVG/PNG previews and STEP files in `dist/` are reference outputs, not JLC upload bundles. Conservative component envelopes are not exact connector/part fit models. [Manifest](dist/manifest.json) covers source dependencies and outputs.

**Engineering prototype, not manufacturing/charge approval.** No manual-SMT alternative or interchangeable THT headers. [Connector policy](../../docs/revision-r2/CONNECTORS.md) and [verification](../../docs/revision-r2/final-export/README.md).
