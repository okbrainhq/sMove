# Review delivery — repaired PCB + simpler central-screw case

The user accepted retaining the current central-screw/battery layout and requested simpler printing. This revision **implements that simplification now**, superseding the side-screw case in `b49ade5` and the uncommitted thin-feature central draft. **No merge, cleanup, firmware work, advisor or extra chat.**

## Complete PCB repair preserved

Main baseline: `554e4fe387748bcd6bc3a2d5a674fdfb1e0a80cb`. Complete committed repair `e033031` was safely cherry-picked as **`0610d60`** before any case work; their complete trees are identical. No reconstruction or destructive reset.

All **89 files in PCB/main remain byte-identical** to the recovered repair, including native PCB/schematic/rules, parts/contract/interface, Gerbers/drills, BOM/CPL, PDF and STEP. Fresh native KiCad reports: **0 ERC / 0 DRC / 0 opens / 0 schematic parity issues**, all severities/all-track errors enabled. The inherited read-only verifier again passed 170 checks with unchanged USB routes, rules and nets. Its historical old-bearing release hold remains preserved; it is not the new case's geometry report.

PCB: **25×30×1 mm**; existing Ø3.2 NPTH H1 at `(111.8,125.65)` below IMU, unchanged BAT+ `(104.5,105.57)` and BAT− `(104.5,103.03)` beside the shielded ESP side. No rerouting or copper ECO.

[Recovered repair report](../pcb-repair/README.md) · [Mechanical handoff](../pcb-repair/mechanical-handoff.md) · [Inherited routing diff](../pcb-repair/review/critical-diff.md).

## Current two-part design

| Complete L × W × H, mm | Dimensions |
|---|---|
| Committed side-screw case b49ade5 | 42.0 × 36.8 × 16.6 |
| Accepted central draft | 42.0 × 28.8 × 19.6 |
| **Simplified current case** | **42.0 × 28.8 × 19.6** |

- **Base + Lid only**. Four stout wall-rooted corner blocks replace small posts/webs/fences; broad lid pads replace thin lips. No hooks, undercut hook pockets, snap tabs or lid slide. Front nut stop is integrated into the entry skirt.
- **One central M3×8 through H1**, no side ear/screw. Head bears on insulating lid; captured nut and blind screw tip are above the sealed battery ceiling. PCB is groove-retained, not a compressed spacer.
- Same 30×20×3 candidate / **31×21×4.3 complete-pack allowance**, no squeeze. Main underside body-facing, IMU +Z outward, USB/buttons/RGB retained. No wires, channels or reserved lead volume; user routes leads and no fit is claimed.
- Battery remains behind the inherited antenna exclusion. It cannot be moved directly underneath the antenna without violating that exclusion; full-pack motion to its stop leaves 1 mm at the forward boundary. Broad RF compliance is not established.
- Height is intentionally retained: at the prior side-screw under-head Z13.2, an 8 mm central screw would end at Z5.2 inside the pack. The current tip is Z8.4 above the barrier. No unapproved PCB-hole move or shorter battery substitution.

## Verification and physical holds

**374 passing mechanical checks**, including valid single-solid prints, no nominal case/PCB/component/pack/hardware interference, vertical PCB/lid/screw insertion, pack swept insertion, nut insertion, STEP solid counts/volume, manifold STL checks and current-only feature assertions. Movable GUI controls passed; source placements stayed fixed. Checks are nominal geometry and explicit additive tolerances, **not FEA or print qualification**.

Central thread overlap: **2.40 nominal / 2.01 adverse geometric mm**, approximately **1.61 mm after chamfer reserve**. Adverse tip-floor clearance **0.56 mm**. The R2.2 non-contact plastic H1 stop retains **0.542612 mm** radial copper budget. Only 0.10 mm nominal M3-to-NPTH radial play: actual smooth alignment is mandatory, never force the PCB.

**Release remains false:** bridge/slot print quality, nut roof/beam/lid stiffness and low-preload creep, far-edge lid lift without hooks, insulating seats/FR4 wear, actual protected pack/charger, user-routed leads, and existing RF/thermal/magnetic qualification. The 21.8 mm battery-ceiling bridge remains; no unconditional support-free claim. See [printing and assembly](../../../housing/PRINTING-ASSEMBLY.md).

## Review files and integration

- [Print-only / assembled / exploded screenshots](images.md).
- [Critical change summary](critical-diff.md), [case revision source diff](case-revision.patch), [combined main-to-current source diff](critical-source.patch).
- [Complete manifest](manifest.json): current file set and SHA-256, including full inherited repair and explicitly archival files. Only `PCB/main` and `housing` are current design inputs.
- [Integration and cleanup inventory](integration-cleanup.md). Primary is **main**, no master exists; no branch was invented or renamed.

Integrate the **whole reviewed branch `okbrain/smove-files/028-91691739`**, including `0610d60` and its subsequent casing commits—not merely the final case delta onto main. Later approved cleanup is working-tree removal only: preserve Git history and unrelated/untracked user files. Wait for latest design review and explicit integration authorization.

Final read-only check: `/usr/bin/python3 scripts/r2/enclosure/seal_delivery.py --check`.
