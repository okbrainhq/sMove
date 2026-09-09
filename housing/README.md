# Compact two-M3 housing / PTH battery-wire assembly

**Measured nominal outer CAD: 46.8 L × 29.4 W × 19.6 H mm**, including modelled recessed M3×8 hardware; 3mm shorter than the previous 49.8mm case. Actual prints, screws, full protected pack and lacing are not qualified.

Open [smove-r2-enclosure.FCStd](smove-r2-enclosure.FCStd), then explicitly run [InspectAssembly.FCMacro](InspectAssembly.FCMacro). Base, Lid, Main, Divider, Battery, Cables and Hardware are independently movable; explode/lift/XYZ/restore modify display links, not engineering source placements. The real GUI macro and desktop Explode/Restore were checked.

- [Stack, wire threading/lacing, insertion and qualification gates](PRINTING-ASSEMBLY.md)
- [Dimensions](dist/dimensions.png), [assembled](dist/assembled.png), [exploded](dist/exploded.png), [FreeCAD controls](dist/freecad-inspection.png)
- [Assembly STEP](dist/smove-r2-assembly.step), [printable STEP](dist/smove-r2-printable.step), [base](dist/base.stl), [lid](dist/lid.stl), [divider](dist/divider.stl)
- [Current mechanical report](validation/mechanical.json), [rigid nominal insertion screen](validation/battery-insertion.json), [GUI tests](validation/gui-inspection.json)

No JST/header or PH2 mating reserve. Two separate PTH wire/solder envelopes, lower wire bay and insulating lacing bridge replace it. **Prototype only:** CAD clearances do not qualify the purchased pack, wiring, printing, fastening or rigidity. No battery compression permitted; actual accel/gyro +Z outward, ESP PCB underside toward body. Full [revision handoff](../docs/revision-r2/solder-wire/README.md).
