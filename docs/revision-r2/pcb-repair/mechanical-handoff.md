# Fresh focused mechanical handoff — authorized next task, NOT started here

Use the final native PCB in this review commit, not either rejected routing attempt. Board 25x30x1mm, source/interface/contract and matching STEP/CPL included; 0 ERC/DRC/opens/dangling, mounting release still blocked.

Latest requested concept: **simple two parts**: battery in bottom base, PCB above it, grooves retain PCB; lid secured by M3. A small additional panel is conditional only if a larger battery actually requires it, not permission for a complicated assembly. Reconfirm actual battery dimensions and wiring/strain relief before mechanical CAD.

Old casing is incompatible/unvalidated. H1=(111.8,125.65), 3.2mm NPTH; U2=(112.5,117.5), top/+Z outward, underside body-facing. BAT+ (104.5,105.57), BAT− (104.5,103.03), 2.54mm pitch and 1mm drills. Preserve USB/buttons/RGB access, RF keepout and no pressure on IMU or battery pouch.

**Hard release gate:** radius-3.4mm old bearing leaves only 0.042612mm nominal margin to copper; do not reuse it as qualified insulation. Review actual screw/head/nut/bearing and hole-play/tolerance stack, insulating contacts, preload, antirotation and magnetic effects. Any local PCB change needs repeated DRC/net/exports; do not regenerate over routing. No mechanical work has been performed or validated in this chat.
