# sMove — repaired PCB with a simple two-part case

**Review branch only; not merged, not released for manufacture or charging.**

- [Combined delivery and critical diffs](docs/revision-r2/two-part-case/README.md): complete committed PCB repair `e033031` safely cherry-picked first as `0610d60`; new casing added afterward. Integrate both together only after review.
- [PCB sources and manufacturing exports](PCB/main/README.md): unchanged repaired **25×30×1 mm**, fresh **0 ERC / 0 DRC / 0 opens / 0 net-parity issues**. BAT pads remain beside the shielded ESP side; H1 remains below the IMU. No new routing, rules or copper edits.
- [Two-part housing](housing/README.md): **42.0 L × 36.8 W × 16.6 H mm**, Base + Lid only, integral battery tunnel, PCB grooves, case-only M3×8 closure and positive antirotation. No old divider or third panel.
- [Actual FreeCAD GUI assembled/exploded screenshots](docs/revision-r2/two-part-case/images.md) and movable native `housing/smove-r2-enclosure.FCStd` / `InspectAssembly.FCMacro`.

PCB underside faces the body; accel/gyro +Z points outward. USB, BOOT/RESET and top-visible RGB are retained. The 30×20×3 mm battery is a candidate only, with a 31×21×4.3 mm complete-pack reserve. Physical print, preload/creep, pack/charging, wire, RF, magnetic and thermal qualification remain open. The older PCB-only warnings and revision folders are preserved historical evidence, not instructions to assemble the retired case. No firmware work or merge.
