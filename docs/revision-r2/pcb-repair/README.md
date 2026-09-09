# PCB-only bounded recovery — electrically clean, mounting release blocked

**Review only; not merged, not released for manufacture/assembly. Board remains 25 × 30 mm.**

## Recovery and bounded routing outcome

- Main baseline: `554e4fe`. The failed `faf335b` object was recoverable. Four PCB placement/source files were extracted, not cherry-picked; no housing work was recovered.
- Real native KiCad Computer Use was available. C7 was moved in its properties dialog and two B.Cu 1.8V segments were interactively routed and saved. The attempted 0.25mm C7 move caused a courtyard overlap; C7 was manually returned to Y120.25 and zones refilled/saved. This attempt reduced 16 to 15 opens, without weakening any rules.
- One FreeRouting invocation, maximum eight autorouting passes / 120-second wall cap / one optimizer thread, completed within the cap. Exact input, session and log are preserved. Candidate import plus fixed-route restoration and removal of 12 rounded duplicate vias left **3 opens and 4 dangling violations**, but added **45 signal segments on In1**, the intended GND reference plane. **Rejected**, not represented as successful routing or copied to the final PCB. No second routing invocation or generation loop was run.
- The subsequently supplied clean commit `96e081b9b29db2bb852a43be9e6060a8a99aadf9` was inspected and selectively reused: PCB/main sources and associated PCB exports, plus the placement-sync script only. **No merge, casing files or enclosure scripts.** The final native PCB is byte-identical to that commit. The manual/FreeRouting attempts remain archived under `review/attempts/`; they are NOT fabrication inputs. Manual routing evidence describes the attempt, not authorship of the selected final routes.

## Independent final checks

`validation/final-checks.json` records 170 passing electrical/source/geometry checks, alongside a separate **blocked mechanical-release gate**:

- Native KiCad final ERC: 0 issues. DRC with all severities, all track errors and schematic parity: 0 violations, **0 unconnected items, 0 dangling items, 0 parity issues**.
- Baseline/final schematic netlists and native pad-to-net assignments equivalent; parts, side and pad geometry retained. All four USB data-net routing geometries exactly equal baseline, not merely endpoint-equivalent.
- Native project, rule file, schematic and stack/setup unchanged from baseline, with SHA-256 proof. **No severity downgrades or new exclusions.** No In1 signal routing in the selected PCB.
- Placement sources/native-layout contract match the selected native PCB. Gerbers/drills, CPL/BOM, schematic/assembly PDFs, STEP and renders were reused from the exact same native PCB source; not regenerated over manual routing. `PCB/main/dist/manifest.json` identifies provenance and release status.
- J2 BAT+ `(104.5,105.57)`, BAT− `(104.5,103.03)` mm: 2.54mm pitch, 1mm drill, 2mm pads. Minimum BAT copper gap to the RF exclusion: **2.03mm**. This is a geometric corridor check, not RF certification. Wire routing and on-body RF performance remain unqualified.
- H1 `(111.8,125.65)` mm: 3.2mm NPTH, 3.45mm nominal all-layer copper exclusion; **8.180006mm** from U2 centre (8.15mm below in native Y). U2 remains `(112.5,117.5)`, top side, −90°. Accel/gyro +Z outward, PCB underside body-facing. USB, buttons and RGB retained; no UART/testpoints added.

## Precise unresolved release blocker

The existing keepout is polygonal. Actual minimum filled-copper radius is **3.442612mm**, not an ideal 3.45mm circle. The previous bearing radius was **3.4mm**, leaving only **0.042612mm** nominal clearance. Nearest track copper is at radius **3.478167mm**. These margins are **not robust insulation** and do not include shank/hole play, eccentricity, print/fabrication tolerances, preload or wear. Solder mask is not accepted as the missing tolerance allowance.

The board is electrically clean but **do not assemble using the prior bearing/case**. A tolerance-qualified insulating mounting interface (or a local copper/placement revision with repeat DRC) must be reviewed before release. No new hardware specification, smaller bearing, casing fix or mechanical robustness claim is silently substituted here. Magnetometer bias, IMU strain, RF on-body performance, current/thermal and impedance qualification remain prototype tests.

**All old housing is incompatible/unvalidated for this PCB placement.** Existing housing files are unchanged. Historical mechanical coordinates/STEP frames are not proof of fit. No casing generation or assembly validation was done in this repair.

## Evidence and repeatability

- [Native GUI screenshot evidence](images/README.md)
- `validation/`: baseline/recovered/manual/refilled/FreeRouting/final DRC; baseline/final ERC and actual XML netlists; recovery, selection, geometry/rule/net checks and router log.
- `review/critical-diff.md` and `review/critical-diff.patch`: selected placement and source-policy changes; no weaker rules.
- `manifest.json`: source, attempt, validation and export hashes; exact reusable provenance.
- Run `/usr/bin/python3 scripts/r2/integrated/verify_pcb_repair.py` after the recorded CLI checks. This verifier does not save the PCB. `sync.py` only publishes placement metadata and now reapplies the explicit PCB-only/no-housing-release policy. **Do not run board generators or route helpers over this native PCB.**
