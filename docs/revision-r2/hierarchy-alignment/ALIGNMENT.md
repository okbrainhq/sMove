# IMU / PCB / enclosure alignment evidence

**CAD alignment verified; physical sensor calibration and wearer alignment are NOT verified. No physical layout or enclosure geometry was changed.** See the [machine audit](validation/alignment.json), [machine-readable frame reference](../../../housing/alignment-reference.json), [lid-off assembly](views/assembly-alignment.png), [carrier mount](views/carrier-mount-alignment.png), and [native carrier top render](views/carrier-top.png).

## Coordinate definitions — do not mix origins or viewing sides

All distances below are mm. Column vectors; `v_destination = R * v_source`. Position transforms additionally require translation.

| Frame | Origin / positive directions | Evidence |
|---|---|---|
| Enclosure E | Native FreeCAD origin. +X east, +Y antenna end, +Z from base toward lid | Reopened FCStd; main antenna keepout and native board placement |
| Main M | `x = KiCad_x - 100`, `y = 135 - KiCad_y`, `z = 0` at board bottom | Canonical main board/interface; main substrate bottom E_z = 12.4 |
| Carrier C | `x = KiCad_x - 100`, `y = 120 - KiCad_y`, `z = 0` at component face. +X along J5 pad 1 toward pad 4, +Y from connector into board, +Z out of component face | Actual J5 pads, keyed outline, U2 pads and carrier FCStd placement |
| Sensor S | Manufacturer package axes, separately for accel/gyro and magnetometer | Pin-1 top view and manufacturer axis figures, not generic STEP-box orientation |
| Wearer/body | **Unknown.** No confirmed belt/skin attachment datum or installation orientation in the inspected artifacts | No body transform is implemented or inferred |

The historical architecture document's intended “waist/right” and “away from body” wording is **not** a demonstrated mapping of the finished enclosure to a person. In particular, E+Z means toward the lid, not automatically away from the wearer.

## Mechanical pose and package evidence

The actual carrier PCB is perpendicular to the main PCB, on the west side, component face toward E-X. Its substrate bounds are E `[-9.3,0,1.5] … [-8.3,20,19.5]`. Main M-to-E is identity rotation plus `(0,0,12.4)`.

```text
p_E = R_CE * p_C + t_CE

R_CE = [ 0  0 -1 ]       t_CE = (-9.3, 0, 1.5) mm
       [ 0  1  0 ]
       [ 1  0  0 ]
```

This is the native carrier placement, not an inferred “fix.” The fresh audit evaluates FreeCAD's quaternion against all three signed basis vectors and checks substrate bounds. It also checks U2's actual PCB placement: **top side, 0 degrees, native anchor `(109.5,103.8)`, carrier `(9.5,16.2)`**. U2 pad 1 is native `(108.0,102.8)`, i.e. upper-left in the component-face view. Witness pads 1/6/7/13/18/19/24 match the manufacturer top-view numbering.

The ICM-20948 manufacturer diagram identifies pin 1 and gives different magnetometer Y/Z directions from accel/gyro. Reviewed evidence is **DS-000189 revision 1.3**, p19 Fig3 and p83 Figs12/13, downloaded from the SparkFun mirror; this is not a claim to the latest datasheet revision. The direct TDK revision-1.5 PDF fetch was blocked with HTTP 403. [source](https://cdn.sparkfun.com/assets/7/f/e/c/d/DS-000189-ICM-20948-v1.3.pdf)

Local evidence: [source receipt and full-PDF hash](evidence/icm-source.json), [pin-order page](evidence/icm-pinout.png), [axis page](evidence/icm-axes.png). Combined with the actual pad orientation, this supports the existing `accel/gyro -> C = I` and `mag -> C = diag(1,-1,-1)` contracts. No axis direction was guessed from the connector photograph, package text, cable colors or a conservative 3D envelope.

## Signed transforms for the inspected CAD pose

```text
v_E = R_AG_E * v_accel_or_gyro        v_E = R_MAG_E * v_magnetometer

R_AG_E  = [ 0  0 -1 ]               R_MAG_E = [ 0  0  1 ]
          [ 0  1  0 ]                         [ 0 -1  0 ]
          [ 1  0  0 ]                         [ 1  0  0 ]
```

| Sensor positive axis | Accel / gyro in E | Magnetometer in E |
|---|---|---|
| +X | +Z | +Z |
| +Y | +Y | -Y |
| +Z | -X | +X |

These are proper right-handed rotations. The magnetometer difference is **not** an electrical or PCB mirroring error. Applying the accel/gyro transform blindly to magnetic data would give the wrong Y/Z signs. The existing carrier `+X`, `+Y`, `ICM20948 +Z` silk is a carrier/accel-gyro reference, **not a promise that magnetometer +Z points out of the board**.

## Registration and location, not a claim of central mounting

- H1 round locator: C `(2.5,17.5)`, component-plane E `(-9.3,17.5,4.0)`; hole diameter 2.2.
- H2 relieved slot: C `(15.5,17.5)`, component-plane E `(-9.3,17.5,17.0)`; drill 2.7 by 2.2.
- The native chamfer key clears the intended board. A 180-degree reversed board at the same mounting center overlaps the actual key by **0.78125 mm³** in a fresh BRep Boolean test. This establishes a geometric anti-reversal feature, not printer tolerance or force-fit acceptance.
- U2's **component-plane footprint anchor** maps to E `(-9.3,16.2,11.0)`. The enclosure AABB center is `(8.35,12.65,10.9)`; anchor displacement is `(-17.65,3.55,0.1)`. The side carrier is deliberately **not centered**. This anchor is neither the MEMS die location nor the assembly center of mass.
- No demonstrated CAD axis sign/rotation error justified moving the sensor, carrier or housing. A centered sports-motion reference was not specified; do not claim center-of-body acceleration or silently recenter the layout.

## Safe changes and outstanding acceptance

Only **documentation and review-overlay axis markers** were added. Existing native PCB silk, pin-1 triangles, locator holes, chamfer, FCStd, STEP, STL and physical placement/routing were preserved. The new PNG/SVG annotations are not fabrication layers or added printable parts. The SVG review files embed depth-correct Blender/Cycles renders of actual FreeCAD tessellation plus vector annotations.

Before treating these CAD transforms as validated sensor installation data, physically establish: actual U2 pin-1 assembly orientation; repeatable non-stressed keyed seating; six-face accel signs; positive rotations about three axes; separate magnetic-axis checks and final-case hard/soft-iron calibration; operating-current magnetic offsets; thermal/RF performance; and the wearer attachment/body-frame mapping. None was performed here. No firmware source or body fixture was invented.

The [existing qualification limits](../FINAL-ELECTRICAL.md) still apply, including protected-pack, supervised off-body charging, no TS cell-temperature monitoring, harness polarity, physical fit and mechanical retention gates.
