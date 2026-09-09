# Two simpler prints — central H1 screw

**42.0 L × 28.8 W × 19.6 H mm. Print only Base + Lid.** The accepted battery/central-screw layout is retained; this revision simplifies its small features rather than changing the PCB or pack.

- Four **solid, wall-rooted stepped corners** replace skinny seats, webs and separate fences. They locate the PCB positively without screw clamping.
- Four **broad integral lid pads** replace the thin lips. Removed both hooks and their undercut pockets: **lid drops straight down**, no sliding or snapping.
- Nut-retaining stop is integrated into the front skirt, not a separate thin tab. Battery ceiling, pocket and screw socket are integral to Base; entry skirt is integral to Lid.
- **ONLY M3×8 through existing H1**, with an insulating head bearing and captured nut above the battery ceiling. No side screw, ear or wire bay. No modeled wires or reserved lead space; BAT pads unchanged.
- Candidate **30×20×3 mm**, full-pack allowance **31×21×4.3 mm**, unqualified. PCB sits above it in insulated corner grooves; no PCB/pouch clamp load. Battery does not overlap the antenna keepout. Main underside faces body; IMU +Z outward. RGB/USB/button access remains.

## What to print and what not to print

- **`dist/base.stl`** — floor down; one connected, closed manifold part.
- **`dist/lid.stl`** — already roof down; one connected, closed manifold part.
- `dist/print-pair.png` shows just those two pieces. The many small electronic envelopes, screw/nut and film in the full assembly are **not additional prints**. Native CSG construction features are not separate parts to fabricate.

The **21.8 mm battery-ceiling bridge**, small nut-slot roof and lid bore/recess edges still need a physical print trial and gauges. **Simpler does not mean proven support-free.** Avoid trapped supports; reject sag, rough pocket surfaces, binding H1 or lid warpage. Printed preload/creep, pack/charging suitability and user-routed leads remain unqualified. No torque rating or manufacturing release.

## Native, exports and checks

`smove-r2-enclosure.FCStd` has fixed engineering sources and **six movable inspection groups**. Run `InspectAssembly.FCMacro` explicitly for restore/explode/offsets. Only Base/Lid are prints. The GUI opens opaque and assembled; display offsets are not assembly paths.

- `dist/smove-r2-printable.step`: exactly two printed solids.
- `dist/smove-r2-assembly.step`: nominal full assembly, no wires; conservative component/hardware envelopes.
- `validation/mechanical.json`: **374 passing CAD checks**, independent STEP/STL consistency, vertical PCB/lid/screw paths and nut/pack insertion.
- `validation/print-simplification.json`: before/after features and remaining print gates.
- `validation/gui-inspection.json`: actual GUI controls and native hash.

```sh
/usr/bin/python3 scripts/r2/enclosure/extract.py
/usr/bin/python3 scripts/freecad/run.py housing/entry.py generate
# Explicitly run housing/PresentAssembly.FCMacro in the pinned real FreeCAD GUI.
/usr/bin/python3 scripts/freecad/run.py housing/entry.py verify
/usr/bin/python3 scripts/r2/enclosure/seal_delivery.py --check
```

The last command verifies a sealed delivery; after deliberate changes, stage intended files and run the sealer without `--check`, then stage generated reports/manifests and recheck. Do not run legacy routing generators over the recovered board. CSG dimensions are authoritative; the spreadsheet exposes core parameters, not a fully generalized constraint solver.

[Assembly/insulation/print gates](PRINTING-ASSEMBLY.md) · [Current screenshots](../docs/revision-r2/two-part-case/images.md) · [Combined delivery](../docs/revision-r2/two-part-case/README.md). **Review only; no merge or archive cleanup yet.**
