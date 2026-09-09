# Complete-commit integration handoff

This work is based on main `4cb3c32193bda18d624b7974b65162a7a44f69a0`, branch `okbrain/smove-files/023-b6a2a21d`, preserved workspace `/home/azero/.okbrain/workspaces/smove-files/023`.

**Do not merge a selected subset of files.** Native PCB/schematic/library changes, generators, BOM, Gerbers/drills, STEP/STL, FreeCAD native assembly, images, interfaces and documentation/reports form one revision. Integrate the entire committed revision, including the deleted obsolete JST footprint. No merge or push was performed by this task.

## Authoritative delivery inventory

- `commit-paths.txt`: exact complete changed pathname set, including this handoff, manifests and the removed connector footprint.
- `delivery-manifest.json`: baseline commit, branch, complete changed-path count, A/M/D status, before hashes, after hashes, and SHA256 for the complete scoped source/export/report set (including unchanged required inputs).
- `PCB/main/dist/manifest.json` and `housing/dist/manifest.json`: refreshed subtree manifests. Historical manifests in earlier revision/recovery directories describe their old trees and are not current validation.
- The master manifest cannot hash itself recursively. Its independent SHA256 and the verified Git commit ID are reported at task completion; its committed blob is separately compared byte-for-byte with the preserved workspace.

`seal_wire.py seal` explicitly stages all intended files and deletions and verifies the complete index path set and blob bytes. The task then makes a normal Git commit and independently verifies committed blobs, not merely working-tree content. No autostash is the delivery mechanism.

## Verification after fetching the complete revision

```sh
# In the delivered workspace / checked-out revision:
/usr/bin/python3 scripts/r2/integrated/seal_wire.py verify HEAD

# After an eventual full integration, validate delivery bytes against the manifest:
/usr/bin/python3 scripts/r2/integrated/seal_wire.py verify --worktree

# Confirm exactly which files the delivered commit changes:
git diff --name-status --no-renames 4cb3c32193bda18d624b7974b65162a7a44f69a0 HEAD
```

The first verification compares the revision's exact changed path set with the manifest and verifies all manifest-covered committed blobs plus intended deletions. The worktree form checks preserved delivery contents after integration; additional unrelated base changes are not mistaken for missing deliverables. If an intentional integration edit changes covered content, investigate and regenerate/revalidate relevant native exports rather than overwriting the hash to conceal a mismatch.

## Current checks and release limits

Baseline and post ERC/DRC/opens/parity are zero under unchanged configured severities. Electrical assertions, mechanical geometry/fastener/wire screens, full four-layer bearing audit, source/export consistency and native GUI assembly controls pass. A rigid nominal-body insertion route is sampled without compression; a complete protected pack and wire/lacing assembly still require physical qualification.

No physical battery approval, manufacturing/charging release, firmware, advisor work or merge. Runtime binaries, local caches and temporary routing intermediates are ignored workspace state, not committed deliverables. The native files and the documented rebuild scripts are included; historical source snapshots remain provenance, not current placements.
