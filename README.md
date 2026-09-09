# sMove — repaired PCB + two simpler case prints

**Current review design: 42.0 L × 28.8 W × 19.6 H mm. Print only Base + Lid. ONLY M3×8 through existing PCB H1.**

- [Current two-part case](housing/README.md): solid stepped corner supports, broad lid pads, plain vertical drop-on lid; no hooks, snaps, side screw/ear or tiny separate printed parts. Battery slot and insulated screw socket are integral.
- [Complete delivery and critical diffs](docs/revision-r2/two-part-case/README.md): full PCB repair e033031 safely recovered as 0610d60; latest simple central case supersedes b49ade5. No PCB rerouting.
- [Repaired PCB](PCB/main/README.md): unchanged 25×30×1 mm; fresh 0 ERC / DRC / opens / parity issues, BAT pads preserved.
- [Only-two-prints / actual GUI images](docs/revision-r2/two-part-case/images.md), editable native `housing/smove-r2-enclosure.FCStd`, movable inspection macro, manifold STLs and matching STEPs.
- [Integration/cleanup review](docs/revision-r2/two-part-case/integration-cleanup.md): main exists, not master. No merge or cleanup yet; preserve history and unrelated files.

Keep the accepted 30×20×3 mm battery candidate / 31×21×4.3 mm full-pack allowance behind the antenna exclusion. PCB underside faces body; IMU +Z outward; RGB/USB/buttons accessible. No modeled wires, channels or reserved lead space; user routes leads and fit is not verified.

**Manufacturing/charging release=false.** Simpler does not mean proven support-free: the 21.8 mm battery-ceiling bridge and nut socket still need a print trial/gauges. H1 alignment, preload/creep/lid warpage, insulation, pack/charger and user-routed leads remain physical gates. Review before integrating the complete branch. No firmware work.
