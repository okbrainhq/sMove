# Reusable PCB routing tools

Run from the repository root with `PYTHONPATH=scripts /usr/bin/python3 -m pcb_tools ...`.
Requires the installed KiCad `pcbnew` Python bindings and `kicad-cli`; image previews also use `python3-cairo`.

## Manual routing first for difficult areas

`waypoints` places **exact coordinates**, without a router changing the path. Units are mm in native board coordinates. Repeat the same position on the other outer layer to request a through via:

```sh
PYTHONPATH=scripts /usr/bin/python3 -m pcb_tools waypoints INPUT.kicad_pcb \
  --net '/SIGNAL' --width .2 \
  --points '[[10,10,"F.Cu"],[12,10,"F.Cu"],[12,10,"B.Cu"],[16,14,"B.Cu"],[16,14,"F.Cu"],[18,14,"F.Cu"]]' \
  --output-dir .cache/manual-candidate
```

Coordinates/net above are illustrative, not a recipe for this board. Output directory must be new. Unknown nets, internal trace layers, malformed layer transitions, nonfinite coordinates, obstructed edges, via/paste overlaps and hole conflicts are rejected before insertion. Rejections identify blocking pads/tracks; no half-route is inserted. Explicit `--ripup-id UUID` or `--ripup-net NET` removes selected copper **only in the candidate copy**.

For several coordinated manual edits:

```sh
PYTHONPATH=scripts /usr/bin/python3 -m pcb_tools.recipe INPUT.kicad_pcb edits.json .cache/candidate
```

JSON accepts `remove_ids`, `remove_nets`, `routes` (`net`, `width`, `points`, optional `rules`), optional `zones` (`name`, `net`, `layer`, `priority`, polygon `points`), and optional `move_footprints` (`reference`, `expected_rotation`, `rotation`, optional absolute `position`). Explicit copper invalidation is required for footprint movement; it does **not** automatically reroute stale connections. Recipes in `scripts/r2/main-routing/` record reviewed intermediate edits and contain revision-specific UUIDs: they are examples/audit records, **not an idempotent final-board generator**.

Every saved candidate receives a native DRC/parity report. A saved candidate is not necessarily acceptable: inspect its DRC counts, connectivity, copper fill and image before adopting it. No command overwrites the input board or modifies the input project's rules. Failed recipe geometry leaves the initial candidate copy unchanged.

## Two-point routing

```sh
PYTHONPATH=scripts /usr/bin/python3 -m pcb_tools route INPUT.kicad_pcb U1:26 R3:2 \
  --width .2 --layers top --output-dir .cache/two-point
```

Omit `--output-dir` for a read-only plan. Endpoint pads must belong to the same net; duplicate pad numbers are rejected as ambiguous. Routing tries exact-endpoint straight/45-degree/orthogonal patterns, simple corridors and deliberate bottom-layer fanouts, then bounded, bend-penalized weighted A*. Visibility simplification rechecks every replacement segment at full width. It penalizes bends and vias, rather than optimizing distance alone. Only F.Cu/B.Cu are available for tracks; internal planes are never used for signal detours. Python API: `Router(board, Rules(...)).plan(...)`, `.apply(plan)`, or `.connect(...)`.

Use a coarser grid (e.g. `Rules(grid=.2)`) for long open corridors and finer grids for fine-pitch escape planning. A fine global grid can exhaust the node budget without finding an otherwise simple route. A node-limit failure is **not proof that a route is impossible**. Inspect, place manual waypoints or move the obstructing copper instead of endlessly increasing the search budget. This is not a shove router and does not guarantee shortest paths or optimal placement.

## Rotation / placement previews

```sh
PYTHONPATH=scripts /usr/bin/python3 -m pcb_tools rotate INPUT.kicad_pcb U8 \
  --angles 0 90 180 270 --positions '113.5,113.5' \
  --ripup-connected-nets --output-dir .cache/u8-comparison
```

Refuses locked footprints or connected copper unless explicit preview rip-up is requested. The rip-up flag removes **all tracks on the footprint's connected nets**, including GND, in each isolated preview, not just nearby stubs. Candidates have separate boards, top PNGs, native DRC reports and a ranked `comparison.json`. The approximate connection-length score is topology-only: it is not routing completion, signal-integrity analysis or proof of optimality. Each orientation uses a separate worker process because the installed native bindings showed registry/lifetime failures when loading multiple boards after removals in one process. Keep the full KiCad project beside the input board for schematic parity.

## Safe copper cleanup

```sh
PYTHONPATH=scripts /usr/bin/python3 -m pcb_tools.polish INPUT.kicad_pcb .cache/polished
```

Simplifies degree-two chains while retaining pad/via anchors and protected USB data nets. Each accepted chain passes a fresh native DRC/connectivity check; rejected changes are rolled back. `CopperTransaction` also exposes explicit in-memory rip-up/rollback for other tools. It covers copper only, not footprint/zone transactions.

## Tests and limits

```sh
PYTHONPATH=scripts /usr/bin/python3 -m unittest pcb_tools.test_tools -v
```

Tests cover exact endpoints, deterministic patterns, staircase cleanup, full-width collisions, pad-paste exclusion, both outer layers/vias, bend-aware search, stale-plan rejection, no partial insertion, locked copper, rollback, and output/source guards.

The geometry model is conservative, not a replacement for KiCad's custom-rule engine. Copper zones are refilled after insertion; connectivity can change even when individual segments clear obstacles. Always check native DRC, unconnected items and schematic parity with the original project rules. Do not suppress rule violations to make a route pass. Impedance, differential skew, return-current paths, thermal/current capacity, assembly and fabrication remain separate engineering gates. Runtime SWIG leak warnings can occur on removed objects; tools preserve source files and use isolated candidates/workers to limit that native-binding risk.
