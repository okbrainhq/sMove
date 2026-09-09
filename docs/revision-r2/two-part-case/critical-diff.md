# Critical changes — central H1 closure and simpler printing

**Review the complete branch, including PCB repair `0610d60`. No merge/cleanup yet.**

## Latest simplification relative to accepted central draft

| Feature | Central draft | Current |
|---|---|---|
| Overall L×W×H mm | 42×28.8×19.6 | **Unchanged** |
| Lower PCB supports | Four slender seats + webs + separate 0.3mm fences | **Four wall-rooted, stepped 2.6mm corner blocks**; positive X/Y location |
| Upper groove features | Four 0.6mm thin lips | **Broad integral pads, at least 1.4×1.4mm** |
| Lid mounting | Two undercut hooks; lower offset and slide | **Plain vertical drop-on lid**, no hooks/snaps/slide |
| Nut retention tab | Thin freestanding tab | **Thicker stop continuous with front skirt** |
| Print count | Two; full assembly shows many component proxies | **Two only**; print-only image and explicit GUI note distinguish references |
| Required bridge/cavity | Full battery ceiling and captive-nut slot | Retained for pouch/screw separation; **not proven support-free** |
| Pack/PCB/screw stack | 30×20×3 candidate, repaired board, central M3×8 | **Unchanged**; no new wire or RF geometry |

Removing hooks simplifies fabrication/assembly but removes their far-end retention. Single-screw closure needs a physical far-edge lift/warpage check. Stronger locating blocks do not prove clamp stiffness or safety. Base/Lid volumes increase modestly with stronger features; this is not a minimum-material optimization.

## Full case delta relative to b49ade5

- Side screw at X−5 and its width bay removed. **ONLY central H1 at local (11.8,13.35)**, existing Ø3.2 NPTH.
- Dimensions **42×36.8×16.6 → 42×28.8×19.6 mm**. Width −8; height +3 is retained to keep the M3×8 tip/nut above the uncompressed pack.
- Screw under-head Z16.4, tip Z8.4; nut Z8.6..11.0, battery ceiling Z6.6..7.4, PCB bottom Z12.6. No metal washer on PCB; head/nut are insulated by case plastic and gaps. PCB is captured in grooves, never used as a loaded spacer.
- **2.40 nominal / 2.01 adverse geometric mm** thread overlap; **~1.61 mm after chamfer reserve**. Adverse tip-floor clearance **0.56 mm**. R2.2 normally non-contact stop radial copper budget **0.542612 mm**; old R3.4/0.042612 interface not reused.
- Removed all dedicated wires, solder, lacing, wire bays/channels/exits and lead reserves. **No lead fit or strain relief verification claimed.** User routes away from RF/fastener/pouch/pinch points.
- Battery candidate/reserve retained, behind the antenna exclusion. No overlap beneath antenna; no PCB hole relocation. IMU +Z outward, RGB/USB/button access preserved.

## Electrical inheritance and files

**All 89 PCB/main files unchanged from complete e033031 repair recovered as 0610d60.** Fresh 0 ERC/DRC/opens/parity; inherited verifier 170 passes. No copper, pad, rule, route or firmware edit.

Authoritative case sources: `scripts/r2/enclosure/generate.py`, `verify.py`, `inspection.py`, `present.py`, `seal_delivery.py`, `housing/InspectAssembly.FCMacro`. Native FCStd, two STLs, two STEPs, GUI images, BOM, safety docs and manifests regenerated consistently. **374 CAD checks pass.**

`case-revision.patch` is the focused source delta from b49ade5. `critical-source.patch` includes selected critical sources from main 554e4fe, supplemented by the preserved inherited routing diff. These are review excerpts, not replacement integration units. `manifest.json` inventories the entire current tree and inherited repair files with SHA-256. After changes, seal and run `seal_delivery.py --check`.

## Honest remaining blockers

Actual print/bridge/sag and slot gauges; small NPTH coaxial fit (only 0.10 nominal radial allowance); low-preload roof/beam/lid stiffness, far-edge lift and creep; insulation/FR4 wear; actual protected pack and charging; user-routed lead safety; existing RF/thermal/magnetic qualifications. No forced H1 enlargement or production torque assumption. **Review prototype, not manufacturing release.** Cleanup inventory is advisory only; no archive/history/workspace deletion occurred.
