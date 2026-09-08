# sMove R2 — engineering prototype

**No manufacturing or charge approval (`manufacturing_release=false`).** Current design is R2 at policy baseline `9c7bb84`. Unsafe CFIX and obsolete revisions are removed from this tree; Local `main` contains only the current parentless root snapshot; saved CodeChat workspaces and the remote are retained with their histories.

- [PCB projects](PCB/README.md): [main](PCB/main/README.md), **35 JLC-fitted parts**, and [IMU carrier](PCB/imu-carrier/README.md), **14 JLC-fitted parts**.
- [Editable housing and printable exports](housing/README.md).
- [Verification and reproduction](docs/revision-r2/final-export/README.md).
- [Connector/cable policy](docs/revision-r2/CONNECTORS.md), [electrical qualification gates](docs/revision-r2/FINAL-ELECTRICAL.md), [historical stock evidence](docs/revision-r2/final-export/STOCK.md).
- [Cleanup evidence and limitations](docs/cleanup/README.md).

Each board has its own `dist/gerbers.zip`, `dist/BOM.csv`, and `dist/pick-and-place.csv`: **three separate files**. ZIPs contain fabrication files only. No whole-project release bundle or top-level duplicate dist.

JLC fits **all SMT headers J2/J4/J5**. No manual-SMT alternative. Sourcing board connectors yourself requires a future THT redesign, not an interchangeable part substitution. User-sourced mating cables still require polarity/continuity/crimp checks.

Use only a qualified protected **1S 4.2V** pack, with **121mA / 4.23V acceptance**, supervised off-body charging and **no TS cell-temperature monitoring**. Cable, fit, radio, thermal, USB and bench gates remain open.

The main schematic now has a **wired overview plus USB / Power / Compute child pages**. See [the hierarchy and alignment change record](docs/revision-r2/hierarchy-alignment/README.md) for baseline/post electrical equivalence, preserved identifiers/physical layout, fresh rendered views and native enclosure checks. No nested IMU sheets or physical relocation. Rendered artifacts were inspected; interactive GUI, physical-fit and sensor/body calibration approval remain unclaimed.
