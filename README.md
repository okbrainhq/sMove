# sMove — compact PTH battery-wire prototype

Actual ICM-20948 integrated on the ESP32-C3 board, top-centred with accel/gyro +Z outward and PCB underside toward the body. Dedicated wired IMU page, single RGB symbol/top-visible LED, USB programming and BOOT/RESET retained; **no testpoints or UART connector**.

- [Current handoff, before/after measurements, checks and limitations](docs/revision-r2/solder-wire/README.md)
- [PCB/schematic/BOM/exports](PCB/main/README.md): **25 × 35.5 × 1 mm**, 46 fitted electronic parts; J2 is **two 2.54 mm centre-pitch PTH battery-wire pads**, no fitted JST/header.
- [Housing and movable FreeCAD assembly](housing/README.md): **46.8 × 29.4 × 19.6 mm**, nominal CAD including two recessed M3×8 screws.
- [One-hour / ten 30-second burst budget and battery gates](docs/revision-r2/integrated/RADIO-BATTERY.md)

**Engineering prototype only; manufacturing and charging release=false.** Complete protected-pack suitability, physical wiring/strain relief, printed fit/rigidity, USB/RF/magnetic/thermal performance remain unqualified. No firmware work or merge. Prior revisions/recovery files are archival evidence, not current assembly instructions.
