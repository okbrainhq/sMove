# Integration and working-tree cleanup — pending review

**No merge or cleanup has been performed.** Existing primary is `main` at `554e4fe`; only remote `origin/main` was found, not master. Do not invent or rename a branch.

Latest requested outcome after approval: one current design/required-file set in the working tree, **keep Git history**, and preserve unrelated files. The current review branch contains the complete PCB repair recovered as `0610d60`, the superseded side-case ancestor `b49ade5`, and the final simplified central-case revision. Integrate the complete branch, not only the last case delta. Superseded commits may remain in history without old designs being active build inputs.

## Bounded inventory already collected

`cleanup-inventory.json` records exact paths/hashes, no deletions:

| Candidate group | Files | Proposed handling after approval |
|---|---:|---|
| `PCB/imu-carrier/dist/` | 29 | Obsolete generated carrier exports; remove from working tree once dependent references/manifests are updated |
| Old compact-placement comparison images | 8 | Obsolete renders; retain required source-reference drawing |
| Old RGB-body views | 2 | Obsolete generated views |
| Historical repair attempts | 5 | Require explicit review before removing inherited evidence from working tree; Git history remains |
| Backup under PCB/main | 1 | Requires explicit approval; currently preserved for complete repair byte identity |

This is a **candidate inventory, not a complete approved deletion plan**. Older source variants/generators may have reference dependencies; finish the required-file dependency check before removing them. Do not blanket-delete revision directories, workspaces or branches. Current fabrication inputs are only the repaired `PCB/main` and simplified `housing` outputs.

## Unrelated/untracked primary-worktree files — preserve

The primary worktree contains untracked `PCB/imu-carrier/fp-info-cache`, `housing/smove-r2-enclosure/`, `housing/smove-r2-enclosure (2)/`, and `housing/smove-r2-enclosure (3)/`. Ownership/content is not established; **do not delete them merely because their names look duplicated**. Later review must identify whether any are user files before bounded cleanup.

After latest design review and explicit integration authorization: recheck primary/worktree state, preserve unrelated changes, integrate the whole repaired-PCB-plus-case history, remove only the approved obsolete tracked paths, update links/manifests/verification dependencies and verify the resulting current design. Keep all Git history. No reset, force push, branch/workspace purge or automatic removal is authorized here.
