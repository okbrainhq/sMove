# Compact keyed enclosure / movable FreeCAD assembly

Nominal complete bounds **44.8 L × 29.4 W × 19.6 H mm**, including one recessed M3×8 screw and one M3 nut; before 46.8 × 29.4 × 19.6 mm. PCB reduction is independent of the battery/RF/wire-bay case floor.

- `smove-r2-enclosure.FCStd`: editable native CSG and parameter spreadsheet; separate movable **Base, Lid, Main, Divider, Battery, Cables, Hardware** inspection groups.
- Run `InspectAssembly.FCMacro` explicitly for Explode, Restore, lid-only lift, visibility and group XYZ controls. These are **display offsets**, not physical installation trajectories.
- Positive retention: H1 M3 clamp, two separated nonconductive corner shoes and upper bearings, two captured front-wall lid hooks. No friction-only antirotation and no pouch clamping.
- Uncompressed nominal battery body **30×20×3 mm** with separate **31×21×4.3 mm** acceptance reserve; real protected pack/PCM/tabs/leads still require qualification.
- `dist/`: printable base/lid/divider STL, printable/assembly STEP, current assembled/exploded/section/dimension images. `BOM.csv` lists housing hardware/materials.

[Assembly and safe operation](PRINTING-ASSEMBLY.md). [Current validation/handoff](../docs/revision-r2/compact-placement/README.md). Manufacturing/charging release=false. No print, torque, creep, battery, strain-relief pull/flex or on-body RF qualification has been performed.
