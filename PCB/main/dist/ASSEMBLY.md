# Assembly release HOLD

Matching PCB fabrication/assembly artifacts from exact native PCB source `96e081b9b29db2bb852a43be9e6060a8a99aadf9`. Independently rechecked electrically in this repair. **manufacturing_release=false.**

Do not assemble using the old case or radius-3.4mm bearing: its filled-copper margin is only 0.042612mm, not tolerance-qualified insulation. Housing files are unchanged and incompatible/unvalidated. PTH wire insulation/strain relief, M3 insulation and preload, antirotation, IMU strain/magnetic bias and RF-on-body testing remain release gates.

PCB bottom faces the body; top-side accel/gyro +Z points outward. Installed STEP/renders omit unavailable models; conservative component envelopes are not exact vendor solids. No casing compatibility is implied by historical STEP coordinates.

See `docs/revision-r2/pcb-repair/README.md` and `validation/final-checks.json` for current measurements and exact checks.
