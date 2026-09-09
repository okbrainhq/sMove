# Main PCB — 25 × 30mm electrical review candidate

**Not released for manufacture/assembly.** Native sources and `dist/` geometry are selectively recovered from `96e081b`, independently checked against `554e4fe`; no housing changes imported.

- Final ERC/DRC: zero issues, opens, dangling items and parity mismatches; net equivalence and USB geometry retained.
- Four layers, 1mm nominal substrate; In1 GND reference has no signal tracks. Top IMU, outward accel/gyro +Z, body-facing underside; USB/buttons/RGB retained, no UART/testpoints.
- BAT+ (104.5,105.57), BAT− (104.5,103.03)mm; 2.54mm pitch, 1mm drill, 2mm pads. H1 (111.8,125.65)mm, 3.2mm NPTH, 3.45mm nominal copper keepout.
- **Mounting blocker:** old radius-3.4mm bearing has only 0.042612mm minimum filled-copper margin. NOT robust insulation, no approved tolerance stack. Do not use the old case/bearing.
- `dist/` contains matching inherited Gerbers/drills, BOM/CPL, PDFs, STEP and renders. Its manifest records exact provenance; these are review artifacts, not released manufacturing instructions. Installed-model renders omit unavailable models.
- Native PCB is authoritative. Do not regenerate over its routing. Placement metadata and guarded sync policy are coherent; casing is incompatible/unvalidated.

[Complete PCB-only report and evidence](../../docs/revision-r2/pcb-repair/README.md).
