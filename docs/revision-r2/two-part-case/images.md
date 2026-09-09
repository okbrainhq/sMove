# Actual GUI screenshot evidence

These URLs were returned by native Ubuntu desktop observation/input tools while inspecting the generated FreeCAD assembly. Tool input receipts were **dispatched**, not semantic success claims; the resulting images were visually inspected for the shown state.

- **Assembled, opaque Base + Lid:** [/uploads/a97508ce-7815-465a-9007-c9d3d223f3c5.webp](/uploads/a97508ce-7815-465a-9007-c9d3d223f3c5.webp)
- **Assembled, transparent case showing repaired PCB, battery separation and off-board M3:** [/uploads/4c87f20a-98d3-4c20-96aa-ff0886e2ca6f.webp](/uploads/4c87f20a-98d3-4c20-96aa-ff0886e2ca6f.webp)
- **Exploded after clicking the actual InspectAssembly “Explode all parts” button:** [/uploads/09513933-8ee7-4a99-a851-3da99a2b5b2c.webp](/uploads/09513933-8ee7-4a99-a851-3da99a2b5b2c.webp)

Exploded positions are display offsets, not collision-free assembly trajectories. The battery is shown outside the front entry, and the front closure skirt is integral to the lid, **not a third panel**. Component boxes, pouch, wires and hardware are conservative models; small items can be occluded in this view. Inspect the live native groups and the geometric report for fit, not the explosion spacing.

Committed real-FreeCAD viewport exports are `housing/dist/assembled.png`, `exploded.png` and `section.png`. Uploaded copies of the first two were also visually checked:

- [Assembled viewport](/uploads/16757e62-a958-4063-bb3a-31836f2fbca2.webp)
- [Exploded viewport](/uploads/30393965-2dca-4b80-bc66-90706a02d631.webp)

No PCB authorship or physical manufacturing test is implied by these mechanical screenshots. Inherited native KiCad evidence remains in `../pcb-repair/images/README.md`.
