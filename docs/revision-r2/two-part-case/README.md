# Combined delivery: inherited PCB repair + secondary two-part case

**Review only. No merge, firmware change, advisor or extra chat. Manufacturing/charging release=false.** PCB routing repair was prioritized and recovered/verified before any casing change. At the user's cost checkpoint, work converged on documentation, delivery validation and commit only; no optional enhancement or extended design loop was added.

## Recovery and electrical delivery

- Main starting point: `554e4fe387748bcd6bc3a2d5a674fdfb1e0a80cb`.
- The **complete committed repair `e033031`** was found on `okbrain/smove-files/027-cfe55441`. Its parent was exactly main. Clean-workspace cherry-pick created **`0610d60`**, with a tree exactly equal to `e033031`. No destructive reset, reconstruction, partial-file substitute or merge.
- Entire `PCB/main` remains byte-identical to the recovered repair, including native PCB, schematic, rules, placement metadata, BOM/CPL, Gerbers/drills, PDFs, STEP and images. No new copper keepouts or routing changes were needed for the new off-board closure.
- Fresh native KiCad checks in `validation/inherited-drc.json` and `inherited-erc.json`: **0 ERC, 0 DRC, 0 opens, 0 schematic parity issues**, all severities/all-track errors enabled. Fresh schematic netlist semantically matches the repaired baseline. The inherited read-only verifier again passed **170 source/electrical/geometric checks**, with unchanged rules and USB routes.
- PCB remains **25×30×1 mm**. BAT+ `(104.5,105.57)`, BAT− `(104.5,103.03)` mm stay by the shielded ESP side. H1 `(111.8,125.65)` stays below IMU U2. Historical routing attempts are retained as evidence, **not manufacturing inputs**.

Read the untouched [PCB-only repair report](../pcb-repair/README.md), [mechanical handoff](../pcb-repair/mechanical-handoff.md) and [inherited critical diff](../pcb-repair/review/critical-diff.md). Their incompatible-housing statements refer to the old case and remain preserved; this new case is separately bound to the exact PCB hash and still under physical release hold.

## Secondary casing delivery

**42.0 L × 36.8 W × 16.6 H mm**, including recessed M3×8. Exactly **Base + Lid**, with integrated battery ceiling and integrated lid front skirt; no divider or optional third panel. Battery slides into the bottom base; PCB drops above it into split grooves. The closure uses one screw and two captive north hooks.

The critical old 0.042612 mm copper/bearing margin is not reused. **The M3 axis is moved completely outside the PCB and pack projections**, local `(−5,13.35)`, and clamp load bypasses both. H1 has only a normally non-contact insulating stop, radius 2.2 mm, with **0.542612 mm residual copper margin after the stated adverse lateral stack**. PCB screw preload is eliminated by design rather than relying on solder mask or a barely smaller metal washer. This increases width but keeps height modest without assuming either 120 mm or an unconfirmed 12 mm target.

Nominal **30×20×3 mm** battery candidate; **31×21×4.3 mm complete-pack** reserve. No actual pack is qualified. PCB/USB solder cannot rest on the pouch: 0.8 mm integral plastic barrier, 0.5 mm clearance above the admission pack, and 1.0 mm nominal / 0.85 mm print-screened clearance below USB-tail reserve. Leads have a west corridor, R2 bends and lacing reserves. Main underside faces the body, accel/gyro +Z outward; RGB/USB/BOOT/RESET access remains.

## Verification and boundaries

- Saved FCStd reopened independently: **569 passing geometric checks**; base and lid each one valid solid, no nominal assembly penetrations, maximum-pack continuous insertion sweep clear, PCB/lid/nut insertion samples clear, screw/nut engagement and critical tolerance arithmetic recorded.
- Both STLs are closed/manifold and consistently oriented; volumes match native parts within the verifier tolerance. Printable STEP contains exactly two valid solids and matches native volume. Assembly STEP carries the complete nominal conservative assembly.
- Actual FreeCAD GUI executed the delivered inspection macro; explode, restore, lid display lift and independent battery movement were checked without changing engineering placements. [GUI assembled/exploded URLs](images.md) show actual desktop observations, not fabricated screenshots.
- No physical printer, pouch sample, torque/creep, pull/flex, RF, magnetic, thermal, ingress, drop or on-body test occurred. Nominal no-overlap is **not** physical qualification. Groove float, ceiling bridging, isolated-pack assembly and complete protected-pack/charger suitability remain explicit blockers.

See [housing overview](../../../housing/README.md), [detailed assembly and tolerance requirements](../../../housing/PRINTING-ASSEMBLY.md), `housing/validation/mechanical.json` and `housing/status.json`.

## Critical diffs, manifest and integration

- [Critical source changes](critical-diff.md) and `critical-source.patch`: focused source diff against main, covering the inherited placement/repair policy plus active casing sources. This excerpt is not a standalone integration patch.
- `validation/delivery-checks.json`: recovery tree proof, fresh ERC/DRC/net parity, unchanged inherited PCB subtree, CAD/export checks and unchanged main.
- `manifest.json`: **complete final repository-file manifest**, including every inherited repair path and its original hash, all current source/native/manufacturing/doc files, and retired paths. It excludes only its own self-hash. Historical files are explicitly not all fabrication inputs.
- `housing/dist/manifest.json`: current housing source/artifact hashes. Inherited `PCB/main/dist/manifest.json` remains untouched.

The review branch is `okbrain/smove-files/028-91691739`. **Later integration must include both commits in order: `0610d60` (complete inherited repair), then the casing delivery commit.** Do not cherry-pick only the casing onto main. Review the whole branch; merge only when explicitly approved. Neither the committed state nor the geometric checks release the pack or case for use.

Repeat the final package check with `/usr/bin/python3 scripts/r2/enclosure/seal_delivery.py --check`; it verifies hashes without changing CAD or PCB. The generation commands are in `housing/README.md`.
