# Current IMU / PCB / body alignment

**The old perpendicular-placement rationale is superseded.** The owner clarified main PCB **BOTTOM toward the body through the base**, both boards parallel/coplanar to this contact plane, sensor accel/gyro +Z outward. Worn-up antenna/USB direction is explicitly not important. Actual native enclosure/carrier mounts, not only axis labels, have now been redesigned.

Authoritative implementation: [current assembly guide](../../../housing/PRINTING-ASSEMBLY.md), [native FCStd](../../../housing/smove-r2-enclosure.FCStd), [body/package-axis audit](../rgb-body/validation/mechanical-audit.json), [native mechanical checks](../../../housing/validation/mechanical.json). The prior 90-degree installation was geometrically consistent with its old design but did not satisfy this clarified requirement.

## Explicit right-handed device/body frame

Column vectors; `v_body = R * v_sensor`. Position transforms also include translation. Flat base underside **Z=0** is body-facing; the body is on the negative-Z side. +Z is outward, +Y is toward the main antenna, +X follows main native PCB +X. X/Y are convenient device axes, **not anatomical right/up**.

| Native design frame | Installed translation, mm | Installed rotation |
|---|---|---|
| Main: `(KiCad_x−100, 135−KiCad_y, z_from_bottom)` | `(0,0,4)` | Identity |
| Carrier: `(KiCad_x−100, 120−KiCad_y, z_from_component_face)` | `(-27.5,16,5)` | Identity |

Both substrates occupy **Z=4…5 mm**. Their outward normals are `(0,0,1)`, dot product 1 and plane angle 0 degrees. D1 is still on the main PCB's TOP and has a direct outward optical aperture in the lid. Neither PCB was mirrored or electrically redesigned.

## Package evidence and signs

ICM-20948 U2 remains top-side, 0-degree footprint orientation, at native `(109.5,103.8)` mm. The audit independently matches **all 24 pads**, including top-view pin 1 at `(108.0,102.8)`, against the manufacturer's pin-order drawing. Package diagrams, not the generic component envelope, establish signs. [Pin page](../rgb-body/evidence/icm-pinout.png), [axis page](../rgb-body/evidence/icm-axes.png), [retrieval/hash receipt](../rgb-body/evidence/sources.json).

DS-000189 revision 1.3 p19 Fig3 and p83 Figs12/13 show accel/gyro +Z out of the package top, with magnetometer +Y/+Z opposite to the accel/gyro directions; this is not a claim to the latest datasheet revision. [source](https://cdn.sparkfun.com/assets/7/f/e/c/d/DS-000189-ICM-20948-v1.3.pdf)

```text
Accel / gyro to body = [[1,0,0], [0,1,0], [0,0,1]]
Magnetometer to body = [[1,0,0], [0,-1,0], [0,0,-1]]
```

Keep these transforms separate. Positive gyro rotations follow the manufacturer's right-hand arrows; these matrices transform vectors, not arbitrary Euler-angle triplets. U2's component-plane anchor is `(-18,32.2,5)` mm in the case, not the MEMS die or a body-centre point.

## Real mount, GUI and limits

The carrier now sits on peripheral plastic annuli with round/slot locators, matching lid bearings and its positive chamfer key; no supporting post is beneath the sensor. Main uses its existing copper-free retention lands. Four M3×8 screws and side-loaded standard M3 nuts fasten the simple base/lid, not the boards. Battery is in a separate side bay; connectors, full insertion/bend reserves, cable length and RF exclusion are screened.

[Assembled alignment render](../../../housing/dist/assembled.png), [body-side](../../../housing/dist/body-side.png), [top/RGB](../../../housing/dist/top.png), [FreeCAD inspection UI](../../../housing/dist/freecad-inspection.png). The native assembly has separate movable inspection groups and restore controls; exploded display is never validation geometry. Labels are display annotations, not fabricated surfaces.

CAD/package evidence does not establish physical sensor placement accuracy, print fit/preload, seating repeatability, hardware magnetic bias, current-dependent offsets, RF/thermal performance, skin/on-body suitability or attachment. Six-face accel, positive gyro rotation, separate magnetometer signs and final-case calibration remain required. Existing protected-pack/off-body charging restrictions remain unchanged.
