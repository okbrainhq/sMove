# R2 main

Native editable project: [smove-r2-main.kicad_pro](smove-r2-main.kicad_pro), [board](smove-r2-main.kicad_pcb), [schematic](smove-r2-main.kicad_sch). Local libraries, parts data and mechanical interface are source dependencies; do not replace them with older revisions.

## Functional schematic hierarchy

The root is a **wired system-flow page** with three non-nested children: [USB](usb.kicad_sch), [Power](power.kicad_sch), and [Compute](compute.kicad_sch). Open the root through this project, not child sheets as standalone projects. Related child circuitry remains visibly wired. J4 connects the separate carrier PCB; its U2 IMU remains on that board's own root schematic, not a nested main-project sheet.

[Change record, images and validation](../../docs/revision-r2/hierarchy-alignment/README.md). All original schematic UUIDs/references and electrical pin groups are retained. PCB hierarchy paths and 23 internal net scope names changed, but physical layout bytes are unchanged after reversing only those exact metadata changes. Fabrication/BOM/CPL outputs remain the same circuit; historical internal net spellings map explicitly in the change record.

## Separate fabrication / assembly inputs

- [gerbers.zip](dist/gerbers.zip): fabrication only, with exact raw Gerbers/drills in `dist/gerbers/`.
- [BOM.csv](dist/BOM.csv): **35 fitted parts, all fitted by JLC**, including SMT headers.
- [pick-and-place.csv](dist/pick-and-place.csv): unchanged original CPL columns/data; filename only renamed.

## Non-JLC reference outputs

[Schematic PDF](dist/schematic.pdf), [assembly guide](dist/ASSEMBLY.md), SVG/PNG previews and STEP files in `dist/` are reference outputs, not JLC upload bundles. Conservative component envelopes are not exact connector/part fit models. [Manifest](dist/manifest.json) covers source dependencies and outputs.

**Engineering prototype, not manufacturing/charge approval.** No manual-SMT alternative or interchangeable THT headers. [Connector policy](../../docs/revision-r2/CONNECTORS.md) and [verification](../../docs/revision-r2/final-export/README.md).
