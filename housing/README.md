# Simple two-part case — review prototype

**42.0 L × 36.8 W × 16.6 H mm**, including the recessed M3×8 socket-cap screw. Exactly **two printed parts: Base + Lid**. No removable divider or third battery panel.

- Battery slides into the base's front opening, below an **integral insulating ceiling**. The lid's integral front skirt closes that opening.
- The unchanged repaired **25×30×1 mm PCB** sits above the battery on insulated seats, retained in four split edge grooves. Separated edge stops provide positive antirotation; the screw does not clamp the PCB.
- One M3×8 and captured M3 nut close the case **outside the PCB and battery projections**. Two rigid north hooks retain the far end. H1 remains below the IMU but is **not a screw path**; a smaller, normally non-contact plastic deflection stop is beneath it.
- Nominal candidate **30×20×3 mm**; complete protected pack admission envelope **31×21×4.3 mm**, excluding only leads accommodated in the separate west bay. These are allowances, not supplier approval.
- Main underside faces the body; IMU accel/gyro +Z points outward. RGB, USB, BOOT and RESET remain accessible. BOOT/RESET use a nonconductive service tool through the lid.

## Files and repeatability

- `smove-r2-enclosure.FCStd`: editable native CSG, core parameter spreadsheet, fixed engineering sources and seven movable inspection groups.
- `InspectAssembly.FCMacro`: explicitly run in FreeCAD for explode/restore, lid display lift, transparency and group XYZ offsets. Display movements are **not assembly paths**. Group visibility is available in the native tree.
- `dist/base.stl`, `dist/lid.stl`: print-oriented, closed manifold meshes; only these two are printed.
- `dist/smove-r2-printable.step`, `dist/smove-r2-assembly.step`: two printed solids and complete nominal engineering assembly respectively. Component, cell, wire and hardware models are conservative envelopes, not vendor-exact CAD.
- `dist/assembled.png`, `exploded.png`, `section.png`: real FreeCAD viewport exports.
- `validation/mechanical.json`: 569 passing geometric checks, including actual dimensions, sampled assembly paths, maximum-pack continuous insertion sweep, tolerance calculations and STEP/STL consistency.

```sh
/usr/bin/python3 scripts/r2/enclosure/extract.py
/usr/bin/python3 scripts/freecad/run.py housing/entry.py generate
/usr/bin/python3 scripts/freecad/run.py housing/entry.py verify
```

Use the pinned runtime in `toolchain.lock.json`; bootstrap with `scripts/freecad/bootstrap.py` if absent. Run `PresentAssembly.FCMacro` explicitly in the real GUI to refresh presentation and verify inspection controls. Core spreadsheet dimensions and native CSG are editable, but derived fixed dimensions live in the generator: any dimensional change requires regeneration and revalidation. Do not run historic PCB layout/routing/export generators over the recovered PCB.

[Assembly and safety requirements](PRINTING-ASSEMBLY.md) · [Combined PCB/case delivery, critical diffs and complete manifest](../docs/revision-r2/two-part-case/README.md) · [Actual GUI screenshot URLs](../docs/revision-r2/two-part-case/images.md)

**Manufacturing/charging release=false.** CAD fit is not physical print, torque/creep, insulation wear, battery, harness, magnetic, RF or thermal qualification. Inherited PCB-only mounting warnings refer to the retired case; they remain preserved as historical evidence, not silently rewritten as approval of this new prototype.
