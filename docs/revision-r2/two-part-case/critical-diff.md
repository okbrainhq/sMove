# Critical source diff — review the combined branch

Baseline: main `554e4fe`. Complete repair recovered as `0610d60` from `e033031`, followed by the new casing commit. **Do not apply the casing alone.** `critical-source.patch` is a review excerpt; the actual two commits are the integration unit.

| Area | Before / inherited condition | Delivered condition |
|---|---|---|
| PCB repair | Main has old BAT/H1 placement | Complete repaired native board from e033031, matching parts/contract/interface and all inherited manufacturing exports |
| Electrical rules | Existing four-layer rules and schematic | Unchanged; fresh 0 ERC / DRC / opens / parity, no new exclusions or weakened severities |
| PCB delta during casing | Unsafe old mount, repaired copper already clean | **Zero** PCB/main file changes after recovery; no copper ECO or rerouting |
| Housing part count | Base, lid, separate divider | **Base + Lid only**, integral battery ceiling and integral front-entry skirt |
| Closure | M3 through PCB H1; bearing R3.4, copper margin 0.042612 | M3 in isolated west bay at X−5; PCB and pack outside clamp path; no metal through H1 |
| H1 support | Loaded metal/screw bearing assumption | Non-contact R2.2 plastic deflection stop; nominal Z gap0.35, adverse gap0.05; residual copper radius budget0.542612 |
| PCB retention | Screw clamp and corner keys | Four insulated lower seats, four lid groove lips, separated positive X/Y stops; no screw preload |
| Battery | Separate removable barrier | Integral0.8 ceiling; 30×20×3 candidate, 31×21×4.3 full-pack reserve; no pouch compression |
| Leads | Old terminal coordinates/path | Correct repaired BAT positions, top-exit R2 bends into west bay, separate lacing/knots; no RF-overhang crossing |
| Frame | Legacy Y origin potentially misleading | Explicit X=nativeX−100, Y=139−nativeY, PCB Y9..39, bottomZ9.6 |
| Case bounds | 44.8×29.4×19.6 LWH | 42.0×36.8×16.6 LWH; broader west isolation bay, lower height; no assumed 12/120 mm height |
| Native/exports | Old housing and obsolete audits | Regenerated FCStd, two manifold STLs, two-solid printable STEP, full assembly STEP, current viewport images; retired stale artifacts/checkers |
| Inspection | Divider display group | Separate Base/Lid/Main/Battery/Cables/Hardware/Insulation groups with preserved explode/restore/XYZ controls |
| Release | PCB-only old-case hold | Geometric prototype verified; physical insulation/print/creep/pack/charging/wire/RF/thermal/magnetic holds retained |

Important source locations:

- `PCB/main/smove-r2-main.kicad_pcb`, `parts-main.json`, `native-layout-contract.json`, `interface.json`: complete inherited PCB repair, unchanged during casing.
- `scripts/r2/enclosure/generate.py`: two-part geometry, integral battery tunnel, off-PCB screw/nut load path, grooves, hooks, access and true swept wire envelopes. Does not write PCB/.
- `scripts/r2/enclosure/verify.py`: saved-native checks and measured tolerance stack; no rule changes and no PCB save.
- `scripts/r2/enclosure/inspection.py`, `present.py`, `housing/InspectAssembly.FCMacro`: movable display groups, fixed engineering source preservation and actual GUI verification.
- `housing/PRINTING-ASSEMBLY.md`, `BOM.csv`, `status.json`: physical acceptance criteria and honest remaining release gates.

The original repaired PCB's full routing diff is preserved in the recovered commit, not duplicated into this already focused patch. Its historic failed routing candidates remain under `docs/revision-r2/pcb-repair/review/attempts/` and must never be fabricated.
