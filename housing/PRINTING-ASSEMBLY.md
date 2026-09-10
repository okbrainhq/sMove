# Screwless prototype: print, insulate, fit, then qualify

**RF TEST PROTOTYPE. No proven physical fit, strength, sealing, RF performance or charging release.** Three prints only: white Midframe, Top cover, Bottom cover. No fasteners, threaded features, inserts or enclosure mounting holes in the PCB.

## Print plan and limitations

- Candidate process: nonconductive white PETG, 0.4 mm nozzle, approximately 0.2 mm layers; configure wall lines to achieve the actual 0.8 mm CAD wall. These are starting settings, not a validated material/profile. Do not use metal/carbon/conductive filament near the antenna or pouch.
- Covers are exported exterior face down. Inspect the internal groove and cover PCB-stop overhangs in the slicer; use removable supports where needed. Protect all mating lands from support scars and elephant-foot growth.
- Midframe is exported **east edge down**. Use a brim and carefully placed removable supports under the separator and locating features. It is not claimed support-free. Do not force an unsupported 21 mm ceiling bridge; an alternate orientation needs its own support/removal review. Smooth every pouch-facing edge after support removal.
- Cut a local sleeve/snap sample in the slicer before spending material on the entire set. The full delivery still contains exactly three printable parts, not an extra insert or latch. Test both assembly and non-destructive disassembly; repeated cycle retention, creep, temperature and impact remain gates.
- Default wall is 0.8 mm, not a recommendation to reduce inner structural features to 0.8 mm. Separator and sleeve stock are 1.2 mm; groove reinforcement preserves the ordinary outer wall thickness. Optional 1.2 mm outer walls were also checked; dimensions grow outward (floor grows up), not into component-side clearance.
- 2.9 mm recessed RESET/BOOT holes have a 0.85 mm web. Verify sliced continuity and access with a blunt insulating tool. Do not assume unsupported sub-nozzle details print. USB is a conservative rectangular plug aperture; gauge it with the actual plug/overmold.

## Datums and clearance budget (mm)

Case X=nativeX−100; Y=139−nativeY. PCB outline spans X0..25, Y9..39, including the actual east USB recess. Exact exported KiCad substrate face/holes are mapped from drill origin (100,135) to this case frame; the STEP's dielectric-only 0.91 mm thickness is expanded to the accepted **1.0 mm total board envelope**. Component envelopes remain conservative contract AABBs, not exact vendor solids.

| Feature | Nominal allocation |
|---|---|
| PCB bottom / top | Z12.6 / 13.6 |
| Underside support land top | Z12.2 |
| Land insulation / adhesive or shim | 0.2 + 0.2, bringing support to Z12.6 |
| Cover PCB travel stop bottom | Z13.85: 0.25 free lift, no clamp preload |
| Lateral/end PCB locating clearance | Nominal 0.25 at fences/end stops; inspect actual outline |
| Battery allowance | X2..23, Y6.5..37.5, Z1.8..6.1 |
| Battery flat pocket | X1.8..23.2, Y6.3..37.7; 0.2 nominal per side |
| Separator | Z6.8..8.0; 0.7 above complete-pack allowance |
| Worst USB shell-tail underside | Z11.4: 3.4 above separator |
| Body-side pack liner | Z1.4..1.6; 0.2 nominal adhesive/air allocation to pack bottom |
| North antenna exclusion boundary | Y39; allowance and lead reserve stop at Y37.5 or earlier |
| Sleeve radial gap / insertion flex | 0.18 / 0.12 nominal |
| Seated groove radial clearance | 0.12 nominal, axial clearance 0.12 each side |

Dimensions are not an accumulated manufacturing tolerance analysis. Check maximum board thickness, warp, surface copper/solder, film compression and actual pack dimensions before fitting. **Do not make the pouch a structural shim or force the covers shut.** The 0.7 mm gap is a geometry allowance, not an approved swelling specification. If the pack manufacturer requires more, enlarge/requalify the design.

## Assembly sequence (unpowered)

1. Inspect and deburr the prints, especially all pouch-facing surfaces, internal wire corridor and snap edges. Check snap coupons and bare three-part fit without electronics; perimeter hard stops must close without the pack. Service by flexing the cover near the side rails using a nonmetal tool; no service-force or cycle life is established.
2. Fit 0.2 mm dielectric film on the four PCB lands (west contact width 0.7, east 0.9; length 2). Use a controlled 0.2 mm dielectric shim for the no-glue option or qualified 0.2 mm nonconductive removable adhesive. Do not bond over vias, bare pads, solder or components. Optional adhesive must not wick into the electronics or create new load paths. Button pressing must not bend the unsupported PCB excessively; bench-test displacement.
3. Seat the PCB from above on the midframe, facing components outward. Four cover-integral broad stops capture the board loosely when the top is installed. No screw load, no pressure on IMU/module/switch bodies, no claim of a perfectly rigid sensor mount. If adequate rigidity cannot be obtained without stress, stop and revise the support design.
4. Measure the **complete qualified pack**, including protection, seals, tabs and lead exit. The nominal candidate is not a purchased/approved pack. Insert from below into the frame pocket, with smooth 0.2 mm floor insulation and optional qualified removable PSA on the flat body-side contact area. The midframe locates the pack laterally and separates it from electronics; the bottom cover captures it vertically. The smaller 3 mm candidate may rattle without a qualified low-stress retention method; do not fill the gap with compressed foam or press on a pouch seal. The pocket dimensions are for the full allowance, not a custom cradle for an unknown actual pack.
5. Route two individually insulated OD≤1.2 mm leads UP (+Z) from unchanged BAT pads, not below the PCB. R2 centreline bends turn west at Z16.4, follow the INTERNAL perimeter at X−1.5 and X−3.0, descend at Y22 and Y25 around the separator's west edge to Z3.2, then return east to X1.95 through the battery locator-only relief. The separator remains continuous over the complete pack. See orange paths in `dist/assembled-wire-path.png` and exact coordinates in `validation/mechanical.json`. Do not cut a wire hole through the separator.
6. Keep the complete 0.25 mm radial extra route reserve clear. Nominal minimum lead-to-print gap is 0.43 mm; no physical pinch tolerance is guaranteed. Optional qualified nonconductive strain relief may use the west land at X−4.4..−3.9, Y28..31, Z3..6, but no bond thickness or adhesive process is qualified. Actual pack lead exit to the modeled battery entry remains a pack-selection gate. Stiffer/larger wires or different bend limits require rerouting and revalidation. Keep slack away from snap joints, antenna and USB.
7. BAT+ is J2.1 at native (104.5,105.57); BAT− is J2.2 at (104.5,103.03). No pad/drill/routing edits. The enclosure reserves solder radius 1.1 mm and height 0.55 mm above the top pad plus an upward wire bend. The actual through-hole termination and opposite-face solder/trim must be inspected for insulation and fit; wire gauge/termination process is not qualified. Do not solder directly to a pouch or connect USB during assembly.
8. Fit covers only after confirming wire slack cannot be pinched and the pack has no preload. Use the blunt-tool RESET/BOOT accesses, LED window and actual USB plug as gauges. Do not power or charge merely because the case closes.

## Remaining physical release gates

- Actual full pack, lead exit, protection, cell charge limits, charger compatibility and swelling/thermal allowance.
- Print dimensional accuracy, local supports/removal quality, snap insertion/extraction force, fatigue/creep, drops and skin-contact/material suitability.
- Board/film/adhesive coplanarity, insulation abrasion, button-induced bending and IMU stability; adhesive serviceability and chemical compatibility.
- Lead bend rating, pack-to-entry connection, solder clearance, pull/flex strain relief, pinch checks and polarity.
- Physical USB/RESET/BOOT/LED access, RF on-body performance, magnetometer bias and temperature. The existing compact housing **does not meet a full 15 mm all-direction RF clearance recommendation**; retaining the accepted forward exclusion is not RF compliance.

No charging, manufacturing or physical-fit release. No merge. Prior screw/two-part records remain historical only.

## Protected extension and USB

Keep the original module antenna end inside the thin integral cap; use no metal/conductive coating. Cap floor is part of the midframe; top skirt/roof is part of the top cover. No external antenna substitution. This is not full Espressif housing-clearance compliance; run on-player RF tests and enlarge if needed. No sweat seal is claimed.

HRO TYPE-C-31-M-12 nominal mouth and local exterior surround coincide at case X24.78. Opening 10×4.3 mm uses source maxima and explicit placement/print allowance; inspect the selected plug overmould. No universal cable fit guarantee. See source drawing and tolerance derivation in README.
