# Critical review excerpts

- Main `554e4fe` unchanged; no merge. Native PCB selected exactly from `96e081b`.
- BAT source pose: {'baseline': [121.3, 126.5, 0.0], 'final': [104.5, 104.3, 90.0]}
- H1: (103.6,103.6) -> (111.8,125.65)mm. Outline still 25x30mm.
- C7 final selected position (111.25,120.25)mm. Manual correction and attempted route are archived.
- Project/rules/schematic/board stack/setup: byte/semantic equal to baseline; no exclusions or severity edits. SHA-256 proofs in final-checks.json.
- Four USB data-net route geometries exactly retained; no In1 signal tracks.
- Added explicit manufacturing hold and incompatible/unvalidated housing policy; sync reapplies it without saving PCB.
- Capped FreeRouting candidate rejected for 3 opens, 4 dangling violations and 45 In1 segments.

Complete placement delta: placement-diff.json. Focused metadata/source patch: critical-diff.patch.
