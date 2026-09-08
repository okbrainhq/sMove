# R2 main

Native editable project: [smove-r2-main.kicad_pro](smove-r2-main.kicad_pro), [board](smove-r2-main.kicad_pcb), [schematic](smove-r2-main.kicad_sch). Local libraries, parts data and mechanical interface are source dependencies; do not replace them with older revisions.

## Separate fabrication / assembly inputs

- [gerbers.zip](dist/gerbers.zip): fabrication only, with exact raw Gerbers/drills in `dist/gerbers/`.
- [BOM.csv](dist/BOM.csv): **35 fitted parts, all fitted by JLC**, including SMT headers.
- [pick-and-place.csv](dist/pick-and-place.csv): unchanged original CPL columns/data; filename only renamed.

## Non-JLC reference outputs

[Schematic PDF](dist/schematic.pdf), [assembly guide](dist/ASSEMBLY.md), SVG/PNG previews and STEP files in `dist/` are reference outputs, not JLC upload bundles. Conservative component envelopes are not exact connector/part fit models. [Manifest](dist/manifest.json) covers source dependencies and outputs.

**Engineering prototype, not manufacturing/charge approval.** No manual-SMT alternative or interchangeable THT headers. [Connector policy](../../docs/revision-r2/CONNECTORS.md) and [verification](../../docs/revision-r2/final-export/README.md).
