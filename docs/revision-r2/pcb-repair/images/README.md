# Native GUI evidence

Screenshots are tool-returned native Ubuntu images, not generated renders.

## Corrected C7 + refill/save of manual attempt (15 opens)
<img src="/uploads/769041f0-9a6c-477a-b309-03030a1e7634.webp" alt="KiCad corrected C7 and saved manual routing attempt" />

## Selected final PCB, KiCad editor, zero unrouted
<img src="/uploads/d1527ace-a349-4146-961a-2fc402ca5f1b.webp" alt="Final selected 25x30 PCB in native KiCad, zero unrouted" />

## Selected final PCB, native 3D top view
<img src="/uploads/22f1fe7f-c4e9-443e-8741-1becaa646ad3.webp" alt="Native KiCad 3D top view with BAT holes, IMU plus Z and M3 hole" />

The native 3D viewer uses installed models only: ESP32, IMU, USB and some other component models are unavailable/omitted. Empty-looking footprints are not absent parts. See footprint/native files and conservative STEP for complete envelopes. Original interactive-route and placement screenshots are indexed in `../validation/manual-evidence.json`. The manual attempt was preserved, not presented as the selected final routing.
