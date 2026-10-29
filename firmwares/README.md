# Firmwares

ESP-IDF firmware for `smove-r2-main` (U1 = ESP32-C3-MINI-1-N4, 4 MB flash,
native USB Serial/JTAG on `/dev/ttyACM0`).

| Dir | Purpose |
|-----|---------|
| [`01-blink/`](01-blink/README.md) | Bring-up / toolchain smoke test: cycles the on-board RGB LED (GPIO3 red, GPIO7 green, GPIO10 blue, active low) |

## Shared conventions

- One self-contained ESP-IDF project per directory (`idf.py build flash` works
  from inside the directory), plus `flash.sh` / `monitor.sh` wrappers:
  `./flash.sh` = build → flash → boot the new image, `./monitor.sh` = flash →
  stream the console.
- `sdkconfig.defaults` is committed; `sdkconfig` and `build/` are not.
- Board pin map lives in each project's `main/smove_board.h` — derive pins from
  `PCB/main/smove-r2-main.kicad_pcb`, not from guesswork.
- **Never rely on `idf.py monitor` for this board.** It asserts DTR/RTS, which
  drives EN/GPIO9 over USB-Serial/JTAG and drops the C3 back into download mode
  (`boot:0x7 DOWNLOAD`, so the app never runs). The scripts keep both lines
  deasserted and pulse EN themselves to boot the flashed image.

## Toolchain

ESP-IDF v5.5 lives in the git-ignored `.tools/esp-idf` at the repository root:

```bash
cd .tools/esp-idf && . ./export.sh     # then cd to a firmware dir
```

If the first build stalls on "Initialising new submodule ... lib", the binary
blobs are being cloned with full history — pre-fetch them shallow:

```bash
cd .tools/esp-idf
git submodule update --init --recursive --depth 1 -j 8
```
