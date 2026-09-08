# Compact two-M3 enclosure / movable FreeCAD assembly

**Measured nominal outer CAD: 49.8 L × 29.4 W × 19.6 H mm**, including assumed recessed M3×8 heads. Numerically below 50×30×20, with only 0.2mm length margin. Actual printed/screw/pack tolerance fit is **not qualified**.

Open [smove-r2-enclosure.FCStd](smove-r2-enclosure.FCStd). Editable base/lid, removable insulating divider, main PCB with centred IMU and diagonal 3.2mm holes, conservative components, candidate cell, lead reserve and two M3×8/nut sets. No ears, separate carrier, UART connector or testpads.

Run [InspectAssembly.FCMacro](InspectAssembly.FCMacro) explicitly. **Base, Lid, Main, Divider, Battery, Cables and Hardware** are independently movable display groups. Lift lid / explode / individual XYZ / transparency / restore never change fixed engineering geometry. [PresentAssembly.FCMacro](PresentAssembly.FCMacro) is the separate optional GUI test/export macro; it saves styled CAD and images.

- [Stack, assembly and qualification gates](PRINTING-ASSEMBLY.md)
- [Dimensions](dist/dimensions.png), [assembled](dist/assembled.png), [exploded](dist/exploded.png), [section](dist/section.png), [FreeCAD UI](dist/freecad-inspection.png)
- [STEP assembly](dist/smove-r2-assembly.step), [printable STEP](dist/smove-r2-printable.step), [base](dist/base.stl), [lid](dist/lid.stl), [divider](dist/divider.stl)
- [Mechanical checks](validation/mechanical.json), [nominal rigid battery insertion](validation/battery-insertion.json), [GUI test](validation/gui-inspection.json)

Main underside faces body; actual AG +Z outward and raw magnetometer +Z inward. **Prototype only:** conservative PH2/PCB overlap still fails; protected battery and real hardware/printing/rigidity remain unqualified. The nominal pouch insertion path does not qualify PCM, tabs or the larger installed envelope. Never force a pouch.
