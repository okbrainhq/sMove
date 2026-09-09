# sMove — compact keyed 30 mm PCB prototype

Actual top-mounted ICM-20948, accel/gyro +Z outward; main PCB bottom faces the body. USB, BOOT/RESET and one top-visible RGB retained; no UART or debug/test points.

- [Current handoff, measurements and validation](docs/revision-r2/compact-placement/README.md)
- [PCB sources/BOM/manufacturing exports](PCB/main/README.md): **25 × 30 × 1 mm**, 46 fitted electronic parts; two PCB-only **2.54 mm centre-pitch BAT+/BAT− PTH wire holes**.
- [Housing and movable FreeCAD assembly](housing/README.md): **44.8 × 29.4 × 19.6 mm including recessed M3×8**, one screw plus positive corner keys and captured lid hooks.
- [Battery/runtime qualification gates](docs/revision-r2/integrated/RADIO-BATTERY.md) remain unchanged.

**Engineering prototype; manufacturing/charging release=false.** Physical print rigidity, complete protected-pack suitability, strain relief, RF/USB/magnetic/thermal performance remain unqualified. Prior revision folders are archival, not current build instructions. No firmware changes or merge.
