# Current R2 deliverables and reproduction

**Engineering prototype; manufacturing_release=false.** The current work implements a unified D1 schematic symbol and an actual coplanar/body-outward enclosure redesign. This supersedes the old cleanup-only/perpendicular-assembly status, not electrical, physical-fit or charging qualification limits. [Change record](../rgb-body/README.md), [main](../../../PCB/main/README.md), [carrier](../../../PCB/imu-carrier/README.md), [housing / GUI](../../../housing/README.md).

## Electrical and retention regression

Run from the repository root with the system interpreter providing pcbnew:

```sh
/usr/bin/python3 scripts/r2/main/unify_rgb.py --check
/usr/bin/python3 scripts/r2/main/verify_rgb.py
/usr/bin/python3 scripts/r2/main/verify_button_labels.py
/usr/bin/python3 scripts/r2/imu-carrier/verify.py
/usr/bin/python3 scripts/r2/enclosure/extract.py
/usr/bin/python3 scripts/r2/enclosure/contact_audit.py
/usr/bin/python3 scripts/r2/enclosure/audit_body_frame.py
```

The RGB verifier compares exact hierarchical net names/pin attributes and component UUIDs with saved pre-edit XML, reruns both boards' configured ERC/DRC/parity and verifies unchanged PCB/fabrication bytes. The four-page main schematic retains wired overview, USB, Power and Compute sheets. Carrier remains a separate single-root design. No DRC rule/severity changes or exclusions were added.

The legacy `main/verify.py` has **three inherited hierarchy-name assertion failures**; the pre/post result is recorded rather than silently normalizing net scopes. `package.py` also fails on inherited missing historical Markdown links. The scoped checks do not claim these full legacy scripts pass. Carrier standalone verification passes.

`contact_audit.py` screens pads, actual track/via shapes and stored copper fills against main retention lands and actual carrier annular seats. No new refill or inferred zero-sized components. The compact native mechanical receipt retains category counts, key checks and all failures; detailed zero-intersection rows are in ignored `.cache/housing/verification.json`.

## Regenerate only affected electrical presentation

```sh
/usr/bin/python3 scripts/r2/main/unify_rgb.py
/usr/bin/python3 scripts/r2/main/render_rgb.py
```

Local/embedded symbols update together. The crop is from KiCad's real SVG, not redrawn wiring. PDFs and SVG/PNGs contain all four main sheets. `scripts/r2/final/export.py` was corrected to retain all main pages and hash child/library sources; unrelated board fabrication/STEP outputs were not rebuilt for this ECO because the boards are byte-identical.

## Native FreeCAD regeneration and verification

The pinned official runtime is defined by `housing/toolchain.lock.json`. It was downloaded and verified in this workspace using publisher sidecar + official release metadata + pinned SHA256. No system package/version replacement was made.

```sh
/usr/bin/python3 scripts/freecad/bootstrap.py --verify-only
# On a fresh workspace without the pinned runtime, omit --verify-only to install it.
/usr/bin/python3 scripts/r2/enclosure/extract.py
/usr/bin/python3 scripts/freecad/run.py housing/entry.py generate
/usr/bin/python3 scripts/freecad/run.py housing/entry.py verify
```

Generation overwrites FCStd, two-part printable STEP/STLs and separate-solid assembly STEP; the source parameters and canonical PCB inputs are authoritative. Major case dimensions are editable in the spreadsheet; frozen outlines, fits and harness routes live in the generator. Arbitrary edits are not automatically requalified. Verification reopens/recomputes native solids and freshly imports STEP/STLs; ZIP CRC is not a substitute.

## FreeCAD GUI / review rendering

For ordinary inspection, open `housing/smove-r2-enclosure.FCStd`, then explicitly run `housing/InspectAssembly.FCMacro` from FreeCAD's Macro dialog. No downloads, saves, fabrication exports or fixed-source placement changes occur. Native MOVE THESE groups have lift/explode/restore, transparency and per-group XYZ controls. The shipped file defaults to **assembled**. [Instructions and screenshot](../../../housing/PRINTING-ASSEMBLY.md).

To rebuild the styled native document and review images after generation, close existing copies of the enclosure, then in the **real FreeCAD GUI Python console**:

```python
import sys
sys.path.insert(0, '/absolute/path/to/this/repository/scripts/r2/enclosure')
import present
document, panel = present.main()
```

This intentionally saves styled FCStd at assembled poses, renders `assembled/exploded/top/body-side/section/freecad-inspection.png`, and activates the delivered macro's actual Qt buttons for a GUI smoke test. `present.py` requires a real OpenGL display: the pinned headless Python runner's Qt offscreen backend cannot render this viewport. In this run the actual FreeCAD GUI was available on Xwayland; desktop-agent capture was inhibited, so no mouse-driven desktop review is claimed. Captured GUI and viewport images were visually inspected. Exploded offsets never change fixed CSG used for native checks/exports.

After GUI rendering, rerun native verify and `audit_body_frame.py` so receipts hash the styled FCStd, then reseal intended outputs:

```sh
/usr/bin/python3 scripts/freecad/run.py housing/entry.py verify
/usr/bin/python3 scripts/r2/enclosure/audit_body_frame.py
/usr/bin/python3 scripts/r2/final/package.py --seal
/usr/bin/python3 scripts/r2/main/verify_rgb.py
```

Keep disposable FreeCAD backups outside the deliverable tree before sealing. The package command seals design inventories before its inherited missing-link failure; this does **not** turn that command into a passing release check. No whole-repository ZIP, merge or manufacturing release.

All actual cable/crimp/slack, fit/preload/strength, magnetic/RF/thermal/USB/bench and on-body acceptance gates remain open. Qualified protected pack, supervised off-body charging and no TS cell-temperature monitoring remain required.
