# Sports tracker PCB

- **Active:** [main](main/README.md), now includes the actual ICM-20948/PCA9306/1.8V circuitry, 47 fitted electronic parts, two diagonal M3 mounting holes, no external UART or testpoints.
- **Frozen provenance only:** [imu-carrier](imu-carrier/README.md). Do not order/assemble this board or PH4 harness for the integrated design.

Open `main/smove-r2-main.kicad_pro`; overview + USB/Power/Compute/IMU pages are wired hierarchically. Project-local IMU libraries are supplied. Installed 3D models are incomplete; conservative FreeCAD component envelopes are not exact populated STEP models.

Main `dist/gerbers.zip`, `BOM.csv`, `pick-and-place.csv` are separate prototype fabrication/assembly inputs, not release approval. See [current gates](../docs/revision-r2/integrated/README.md).
