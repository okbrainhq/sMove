# sMove sports tracker — centered integrated-IMU prototype

Current unmerged redesign: actual **ICM-20948 on the same ESP32-C3 PCB**, at upper centre on the top face; signed accel/gyro **+Z outward** and underside toward body. Dedicated wired IMU page, unified RGB, BOOT/RESET and USB programming retained. **No external UART header and no testpoints.** Two diagonal M3 PCB mounting holes replace peripheral edge clamps.

- [Engineering handoff, verification and open gates](docs/revision-r2/integrated/README.md)
- [PCB/schematics/BOM/manufacturing review exports](PCB/main/README.md)
- [Housing / movable FreeCAD](housing/README.md): **49.8 × 29.4 × 19.6mm measured nominal CAD**, including assumed recessed heads. Within the requested numbers nominally; **not a printed/assembled tolerance approval**.
- [One-hour session: ten 30-second bursts, BLE standby, sleep/off, unqualified battery](docs/revision-r2/integrated/RADIO-BATTERY.md)

**Prototype only. PH2 plug/PCB fit, protected-cell qualification, USB/radio/thermal performance and physical assembly remain release gates.** No merge or firmware implementation. The separate carrier and earlier engineering history are archival, not part of this assembly.
