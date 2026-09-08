# Repository cleanup evidence

Source-cleanup baseline: former main `9c7bb84cde1e7ee5842be48dd34e0169e0914b47`, isolated workspace 016. That source-cleanup phase performed no commits, history rewrites, branch/workspace deletion, advisors, sourcing or GUI probing. The subsequent local Git-maintenance phase consolidates this tree into one parentless `main` commit; saved CodeChat workspaces, their branch histories and the remote are retained. No remote fetch/push, shared reflog expiry or garbage collection is performed.

[evidence.json](evidence.json) records the BEFORE SHA256 and old-to-new file mapping captured before moves. All 282 baseline entries were independently checked against the baseline Git blobs after recovery from an interrupted provider response. Native projects, models, FCStd, STL/STEP, fabrication ZIPs, BOM and renamed CPL have byte parity; no native path repairs or engineering changes were necessary. Local relative library/model references travel with the boards.

## Retired checks — NOT PASSED

CFIX archival immutability, pre-R22 reference-board comparison, pre-ECO placement preservation, old carrier export preservation and whole-release bundle smoke tests no longer define current validity. Those inputs/checkpoints are not part of the current root snapshot; saved CodeChat workspaces and retained remote history remain available. No unsafe/reference KiCad files are retained just to satisfy obsolete tests.

Current equivalents are native configured ERC/DRC/net exports, main pin/net/fitted/outline/antenna/retention invariants, carrier independent pin/land/geometry audit, combined electrical/connector/endpoint checks, canonical housing extraction/contact checks, native BOM/CPL/CID/placement validation and before/after SHA256 parity. Historical test counts are not recycled as new results.

## Layout and scope

`PCB/main` and `PCB/imu-carrier` each own one native project and their own dist. `housing` owns one editable FCStd and printable/reference outputs in dist. Fabrication ZIPs contain only Gerber/drill fabrication files, with separate BOM and pick-and-place CSVs. No top-level release/mega ZIP or archive junk folder.

Current source evidence, exact Samsung curves, footprint/pin audits, original models/licenses and historical stock retrieval receipts remain. Reports written by checks are disposable `.cache/` files. Old snapshots, synthetic fixtures, build/reroute/ECO scripts and historical entrypoints are removed.

## Limitations

GUI review remains blocked/not performed. No new visual approval, manufacturing or charge approval. FreeCAD native reopen/regeneration and the former 1938 geometric checks are not claimed as rerun without the pinned runtime. FCStd ZIP integrity and byte parity are not equivalent to recomputation. Optional heavyweight export/bootstrap commands are documented separately from read-only checks.

## Actual cleanup results

Seven read-only verification commands passed in a new project-local clean copy with all legacy directories physically absent. Fresh configured ERC/DRC: both boards zero violations, opens and parity issues; main 17 checks; combined electrical 96; carrier independent audit PASS (no invented assertion count). Standalone CSV/ZIP/manifest/library/link audit: 262 checks. Python syntax: 15 files. Byte parity: 28 critical CAD/model/fabrication/geometry files, and 260 of 282 retained baseline files overall. Support-script/document edits account for the remainder.

Five **external, unbundled model references remain unavailable** in this runtime: Espressif ESP32-C3-MINI-1, JST PH two- and four-pin headers, HRO USB-C and LiteOn LED. These are explicit non-passing model availability gaps, not missing moved local models; exact unavailable paths are recorded in evidence.json. All supplied project-local models resolve. Preserved populated STEP includes labelled conservative envelopes. No substitute models or native path edits were made. FreeCAD pinned runtime is absent; no reopen/regeneration or heavyweight export was run.
