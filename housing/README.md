# Enclosure-only — RF TEST PROTOTYPE

Three white rounded screwless prints: **Midframe + Top cover + Bottom cover**. Existing validated **25×30 mm PCB, schematic, routing, copper RF exclusions and native module remain unchanged**. No PCB shrinking or external antenna substitution. No manufacturing/charging release, no full Espressif housing-clearance compliance. Enlarge the housing if on-player testing requires it.

## Geometry and fit

- Default ordinary walls/roof/floor: **0.8 mm**, configurable through 1.2 mm. Main body including snap bands: **39.3 L ×34.3 W ×19.0 H mm**. Protected antenna extension makes overall **42.85 L ×34.3 W ×19.0 H mm**. At 1.2 mm: overall **43.65×35.1×19.4 mm**. Main-body length was reduced, not the PCB; the internal perimeter wire corridor adds width.
- Existing module end extends past the main compartment into a thin nonmetallic cap: floor integral with midframe, roof/skirt integral with top cover. No fourth print or bare exposed antenna. Cap floor/roof follow wall setting. This close plastic cap is explicitly an RF compromise, not a clearance-compliant housing or liquid seal.
- Battery candidate remains 30×20×3 mm; complete-pack allowance remains 31×21×4.3 mm (case XYZ 21×31×4.3). Pocket 21.4×31.4; separator gap 0.7. Optional qualified adhesive/insulating supports, no pouch compression. Hard perimeter stops take closure load.
- BAT wires now leave pads **upward +Z**, opposite the inherited below-board model, bend west and run along the **internal midframe perimeter**, descend around the separator's west edge, and return through a locator-only relief to the underside battery. The separator remains continuous over the entire pack. No wire hole through the separator. Exact two routes are in `validation/mechanical.json` and visible in `dist/assembled-wire-path.png` (orange wires, cyan module).
- Conditional wire OD≤1.2 mm, R2 centreline bends, 0.25 mm radial routing reserve; solder reserve radius 1.1 mm, height 0.55 mm above pads. Minimum nominal lead-to-print clearance 0.43 mm; reserve-to-print 0.18 mm, lead-to-lead 0.30 mm at both checked walls. Battery and wire reserves remain respectively 1.5 and 2.18 mm away from the retained forward RF exclusion. These are CAD measurements, not manufacturing tolerance guarantees.
- Sleeve clearance 0.18 mm; insertion flex 0.12 mm; groove radial clearance 0.12 mm. Snug covers require physical printer/material calibration. RESET/BOOT holes 2.9 mm, web 0.85 mm; LED aperture 3.8 mm retained.

## Source-derived flush USB-C

J1 is **HRO TYPE-C-31-M-12 / LCSC C165948**, retained native footprint. `sources/hro-type-c-31-m-12.pdf` is the supplier-hosted HRO drawing copied from workspace 032's mechanical evidence only, not its failed layout. `sources/usb-mechanical-evidence.json` preserves source URLs, drawing SHA256 and dimensional evidence; its prior proposed cutout is historical, superseded here.

Drawing nominal body W×D×H = 8.94×7.35×3.26 mm; maximum W/H = 9.09/3.36 mm. Native locator datum case X18.5 + drawing front distance 6.28 puts the metal mouth at **X24.78** (native X124.78), 0.03 mm beyond the inherited simplified envelope face. The local stepped exterior surround terminates at that exact nominal mouth plane; the plastic outside it is relieved. This is not a recessed insertion tunnel. Main lower shoulder remains wider.

Opening **10×4.3 mm** exceeds the source maximum plus **0.2 mm placement +0.2 mm print/fit allowance per side** (minimum 9.89×4.16). Nominal source body/mating aperture geometry is separately modeled; component collision checks also retain the conservative native envelope. Check the actual connector placement and selected cable overmould on a print: **no “any cable” guarantee**, and exact as-built flushness cannot be guaranteed from nominal CAD.

## Files and regeneration

`smove-r2-enclosure.FCStd` is editable native CSG with live `Parameters.Wall`. `dist/smove-r2-printable.step` contains exactly three solids; `dist/smove-r2-assembly.step` includes reference electronics, battery, insulation, wires and solder. Three STLs have print orientations; seven PNGs include opaque assembled, transparent wire-path, exploded and section views. Prints are white; transparent presentation is diagnostic only.

Edit `housing/screwless.json` → `outer_wall_mm` (default 0.8). From repository root:

```sh
/usr/bin/python3 scripts/freecad/bootstrap.py --verify-only
# If runtime absent, run bootstrap.py without --verify-only first.
/usr/bin/python3 scripts/r2/enclosure/extract.py
/usr/bin/python3 scripts/freecad/run.py housing/entry.py generate
/usr/bin/python3 scripts/freecad/run.py housing/entry.py generate 1.2
cp .cache/wall-1.2/validation/mechanical.json housing/validation/wall-1.2.json
/usr/bin/python3 scripts/freecad/run.py housing/check_native.py
/usr/bin/python3 scripts/freecad/run.py housing/qualify.py
# In an available authorized X11 display:
/usr/bin/python3 scripts/freecad/run.py housing/render.py
python3 housing/seal.py
python3 housing/seal.py --check
```

**Do not regenerate PCB exports.** Generation asserts hashes of retained PCB and board STEP. Alternate wall outputs stay in `.cache/wall-1.2`; default outputs remain 0.8. `check_native.py` and `qualify.py` expect the default 0.8 delivery and alternate 1.2 build. `entry.py verify` regenerates; it is not read-only. Other dimensions/route changes require deliberate source edits and complete revalidation, not just changing Wall.

## Evidence and qualification limits

`validation/mechanical.json` and `wall-1.2.json`: 819 nominal checks each, including three valid closed solids/STEP reimport, component/pack/wire interference, measured wall, accesses and sampled insertion. `native-parameter.json`: 16 reopened-native/live-wall checks. `prototype.json`: independent manifold/orientation checks of both sets of STLs, sampled cover travel without lead collision, cap coverage rays and outward USB opening. Sampled motion/coverage are not continuous physical simulations or waterproofness proofs. `pcb-preservation.json` hashes every tracked PCB file against the unchanged Git baseline. `dist/manifest.json` binds sources, CAD, exports and reports (self excluded).

Physical gates: actual pack lead exit and soldering process, wire bend rating/strain relief, print accuracy/support removal, snap force/creep/cycles, drop/body movement, skin contact, RF on-player in intended orientations, sweat ingress/abrasion, thermal and charging suitability. The vendor pack-to-modeled-entry connection remains conditional on the selected pack. Do not force fit, charge, or claim sweat resistance from these nominal checks. See `PRINTING-ASSEMBLY.md`.
