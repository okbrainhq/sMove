# R2 housing — coplanar boards, simple base + lid

**Implemented engineering prototype; not a physical-fit or manufacturing release.** Main PCB **BOTTOM faces the body through the flat base**. Main and IMU substrates are coplanar, with accel/gyro +Z and the main RGB LED facing outward. The old perpendicular/stepped enclosure is superseded.

- [Native editable FreeCAD assembly](smove-r2-enclosure.FCStd): separate named base, lid, boards, pack, harnesses and hardware; Parameters spreadsheet + CSG sources, with movable inspection groups at assembled default placements.
- [Inspection macro/UI](InspectAssembly.FCMacro): lift lid, explode/restore, transparency and per-group XYZ movement. No automatic source-geometry edits or exports. [GUI screenshot](dist/freecad-inspection.png).
- [Assembled internals / outward axis](dist/assembled.png), [exploded display](dist/exploded.png), [top / RGB access](dist/top.png), [body-side](dist/body-side.png), [real Y=30 section](dist/section.png).
- [Base STL](dist/base.stl), [lid STL](dist/lid.stl), [two-solid printable STEP](dist/smove-r2-printable.step), [separate-solid assembly STEP](dist/smove-r2-assembly.step).
- [Printing, M3×8 assumptions, frame, assembly and GUI instructions](PRINTING-ASSEMBLY.md).
- [Mechanical checks](validation/mechanical.json), [GUI checks](validation/gui-inspection.json), [parameters/poses](validation/build.json), [source/output manifest](dist/manifest.json).

**109×48×14.5 mm**, or 17.5 mm including assumed socket heads. Deliberately wider/thinner than the old build: side-by-side battery removes the overhead cell barrier/bridge and stepped lid. Four M3×8 screws engage standard side-loaded M3 nuts, not printed threads; no M3 fastener touches either board. Verify the user's actual screws/head type/material and nuts before assembly.

The generator is `scripts/r2/enclosure/generate.py` through [entry.py](entry.py). It consumes canonical PCB/interface files via `extract.py`, not board copies. `verify.py` reopens FCStd and STEP/STLs. `present.py` styles/saves the actual assembled document, renders the real FreeCAD viewport and exercises the delivered inspection UI; rendering requires a live OpenGL GUI. [Reproduction](../docs/revision-r2/final-export/README.md).

Main/IMU PCB geometry, connectivity, components, BOOT/RESET silk and fabrication files remain unchanged. Fresh CAD screens do not establish print fit, clamp stiffness, screw strength/material, pouch/harness qualification, magnetic/RF performance, thermal/on-body comfort or skin suitability. Only a qualified protected pack and supervised off-body charging; no TS cell-temperature monitoring or manufacturing/charge approval.
