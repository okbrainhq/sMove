# Current R2 PCB projects

- [Main](main/README.md): one editable KiCad project, 35 fitted parts.
- [IMU carrier](imu-carrier/README.md): one editable KiCad project, 14 fitted parts.

Open each native `.kicad_pro` in its own directory. Local symbol/footprint libraries travel with the project; source model dependencies live in `models/` where supplied. Standard main-board models require the installed KiCad model library.

Each board owns its own `dist/`: Gerber ZIP, BOM and pick-and-place CSV are separate JLC inputs. PDF, SVG, PNG and STEP are non-JLC reference outputs, not physical-fit approval. See [qualification](../docs/revision-r2/FINAL-ELECTRICAL.md). No manual-SMT variants; all headers are JLC-fitted.
