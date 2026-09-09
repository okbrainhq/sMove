# Current simplified two-print case — real FreeCAD evidence

These images supersede the older side-screw and thin-feature central draft views.

- **Only the two printable pieces, in print orientations:** [Base + Lid](/uploads/2c6bd76b-5a19-4a17-9aee-d5e4dfaec79c.webp). Real FreeCAD viewport export, fetched from `housing/dist/print-pair.png`. Base floor down; Lid roof down. Corners/pads/nut socket/skirt are integral—not separately printed pieces.
- **Actual desktop GUI, opaque assembled:** [Assembled](/uploads/7dba4a60-9fab-4bf9-b7c7-9140355a1a84.webp).
- **Actual desktop GUI after clicking Explode:** [Exploded](/uploads/9477022a-b95a-4d61-8932-4ac8d37617e9.webp).
- **Desktop restored assembled after inspection:** [Restored](/uploads/f8164e20-aed5-44fd-9874-87e9be3867f6.webp).

Desktop tool receipts were **dispatched**, not semantic success claims; resulting images were visually inspected. Full assembled/exploded/section/print-pair viewport exports are committed under `housing/dist/`. `housing/validation/gui-inspection.json` records the explicit GUI macro/control checks and saved-native SHA-256.

The many small dark objects in the full assembly are **electronic component envelopes**, not pieces to 3D-print. Battery, purchased M3 screw/nut and cut insulating films are also references. ONLY `base.stl` and `lid.stl` are print inputs.

Exploded offsets are display aids, not insertion trajectories. CAD fit checks use fixed engineering placements and the actual straight-down lid path. Images do not certify bridge quality, strength, battery/wire safety or RF behavior. No wire geometry is present. Original KiCad repair evidence remains in `../pcb-repair/images/README.md`.
