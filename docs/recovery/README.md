# Compact delivery recovery — workspace 022

## Result and limits

The compact native PCB, schematics, libraries, source scripts, FreeCAD assembly and exports are recovered from existing Git objects, **not redesigned or regenerated**. All **138 entries** of the recovered complete source/export manifest match their original SHA256 hashes. The two original PCB/housing manifests also pass in full (87 and 28 entries).

**The claimed original 152-path staged index is not present. Do not describe this as a proven restoration of all 152 original pathnames.** The original commit contains only 30 paths. Recovery restores 51 tracked modifications, 44 missing manifest-listed files, and 23 original reports/documents. Twenty report/document paths were correlated from recovered links, script inputs/outputs and report identity; three reports with uncertain original names are explicitly kept under `original-reports/`. All 1,004 initially unreachable Git objects are additionally preserved in `preserved-unreachable.pack`, including older variants and objects not assigned a current pathname. This preserves the evidence for further pathname reconciliation rather than guessing design contents.

No files, workspaces, refs or Git objects were deleted. No merge, push, hardware redesign, firmware work, manufacturing release or advisor activity was performed.

## Provenance

- Before ECO: `c1050a07339897e7203f43137aec96de5bbc41cc`.
- Partial delivery: `87913796a185f379374e7adadf464d674c40f12e`, **30 changed paths**.
- Main merge: `f7c6bc0cd1c727314fc17b57df88e27d1f8647bd`.
- The partial commit and merge have the **same tree**, `5abb41bdf736b86afe5b136d2c0ac3b9a8174c63`. The missing content was already absent from the delivery commit, not dropped by Git's tree merge.
- Orphaned old-workspace autostash: `a5e32962dd6f6561775f31e52b0cef898f6d3663`, directly parented by `87913796…`; recovered worktree tree `d335cd6dc690bb05a4014d4a0ec59af23648235f`.
- Its index parent `8a54357569f0ab25db3695c738830fc39b927478` has the partial 30-path tree, not a full 152-path index.
- Autostash adds 51 modifications and one deletion relative to the partial delivery. The deletion of the unused `PCB/main/smove-r2-main.pretty/Debug_5.kicad_mod` was **not applied**, because deletion was forbidden. The footprint is not placed in the recovered native board or schematic.
- The orphan blob `b4767a0d2e2fd8463130ff67ee8234fff10d200d` is the final 138-entry delivery manifest. Every listed content hash was located in the Git object database; none required reconstruction.
- Detailed path → Git blob → SHA256 evidence: `provenance.json`.
- The preserved-object pack was validated with `git index-pack`. It is evidence, **not an instruction to apply any historical tree**. It also preserves the autostash commit/tree and old variants for later inspection.

## Fresh verification

All tests operate on the recovered exact native files. Original reports and manifests are preserved; fresh results are under `checks/`.

- **1,214/1,214 electrical assertions pass**, including native ERC 0, DRC 0, opens 0 and schematic parity 0 under the unchanged configured severities and manufacturing rules. These are not checks of ignored KiCad defaults or physical electrical qualification.
- **657/657 source/export coherence checks pass**: exact 47-item BOM population/CPL/assembly poses and pad nets; Gerber outline; two M3 Excellon positions; byte-for-byte Gerber ZIP members; all manifest hashes.
- Native outline centreline bounds **25 × 39 mm**. KiCad's drawing bounding-box API includes the 0.05 mm stroke and returns 25.05 × 39.05; this is not a board-size redesign.
- **U2 ICM-20948** at native (112.5, 117.5) mm, −90 degrees: centred across width and 2 mm above the bounding-box centre. No J3 UART/service header or TP1–TP14 in the board or schematic. BOOT/RESET and USB programming remain.
- H1=(103.6,103.6), H2=(121.4,135.4) mm: diagonal **3.2 mm NPTH** holes for M3. Fresh four-layer bearing/copper audit passes.
- Fresh native FreeCAD recompute reproduces **2,087/2,088** mechanical checks, and the entire assertion list exactly equals the original report. Case L×W×H = **49.8 × 29.4 × 19.6 mm** nominal, including modelled recessed heads.
- The one retained failure is conservative `Main_J2_MatingInsertion` / PCB overlap **2.16 mm³**. This is a conservative reservation, not proof of actual PHR-2 plastic interference. J2 remains `S2B-PH-SM4-TB(LF)(SN)`; the user-supplied connector investigation identifies mating housing `PHR-2` and official reference https://www.jst-mfg.com/product/pdf/eng/ePH.pdf. No new hardware geometry, connector change or warning suppression was made. Exact purchased mate/wiring and physical fit remain qualification gates.
- All 160 protected source/export/historical report files stayed byte-identical through verification.
- **Inherited stale evidence:** `housing/validation/input-geometry.json` was not updated by the prior compact delivery. It remains unchanged for provenance, not current compact evidence. Use `checks/current-input-geometry.json` and the fresh mechanical report. Historical carrier/body-layout documents also remain archival, not current assembly instructions.

### Repeat verification without replacing original evidence

```sh
/usr/bin/python3 scripts/freecad/recovery_verify.py electrical
/usr/bin/python3 scripts/r2/enclosure/extract.py
/usr/bin/python3 scripts/freecad/run.py scripts/freecad/recovery_verify.py mechanical
/usr/bin/python3 scripts/r2/enclosure/contact_audit.py
/usr/bin/python3 scripts/freecad/recovery_coherence.py
```

The mechanical command intentionally returns 1 while the conservative PH2 qualification gate remains open. The wrappers redirect report destinations only; recovered assertions are not weakened. Do not rerun destructive historical migration/layout scripts or `seal.py` over this evidence.

## FreeCAD assembly and desktop outcome

The recovered FCStd already has **7 independent movable `App::Part` display groups** — **Base, Lid, Main, Divider, Battery, Cables, Hardware** — containing **58 individually movable linked parts**. Fresh tests move each group and each individual link separately, confirm other groups/links and fixed engineering sources do not change, then restore without saving. All 65 movement checks pass (`checks/movement.json`). This is an inspection assembly, not a newly invented constrained mechanical redesign.

The actual desktop was initially visible, then capture failed with **PipeWire: Session creation inhibited**. A later native AX observation exposed **“Click or press a key to unlock”**. Therefore **the casing and controls were not opened/visually verified on the user's current desktop**. Do not treat the recovered screenshot as a new live capture. A FreeCAD `--help` startup probe was not a successful casing launch.

The existing local AppImage was SHA256-verified against the recovered runtime lock and extracted into this workspace without downloading or substituting a version. Runtime evidence is in `checks/runtime.json`.

Actual file:

```text
/home/azero/.okbrain/workspaces/smove-files/022/housing/smove-r2-enclosure.FCStd
```

After unlocking the desktop:

1. Open that FCStd in FreeCAD (the verified workspace launcher is `.tools/freecad/1.1.3/squashfs-root/AppRun`).
2. Use **Macro → Macros**, select `/home/azero/.okbrain/workspaces/smove-files/022/housing/InspectAssembly.FCMacro`, and **Execute**.
3. Click **Lift lid only**, **Explode all parts**, or choose a group, enter X/Y/Z offsets and click **Apply group offset**. Expand a display group to manipulate an individual linked part if needed.
4. Use **Restore ASSEMBLED** to reset display placements. Prefer a separate inspection copy if saving; do not overwrite the hash-preserved recovered original with an exploded pose.

Recovered original screenshot URL (historical, not a fresh desktop image):

`/uploads/7594e394-466d-4209-89a3-395642bcb4d2.webp`

Original image file: `housing/dist/freecad-inspection.png`.

Protected-cell charging/discharge/envelope, exact plug, print/fastener tolerances, stiffness, USB signal integrity, RF and thermal qualification remain open. This is a recovered engineering prototype, **not manufacturing approval**.
