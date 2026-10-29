# 01-blink — sMove bring-up firmware

Minimal ESP-IDF firmware that blinks the on-board RGB LED. It is the first
firmware for `smove-r2-main` and doubles as a toolchain / flash-path smoke test.

- **MCU:** U1 = `ESP32-C3-MINI-1-N4` (RISC-V, 4 MB embedded flash, revision v0.4)
- **Framework:** ESP-IDF v5.5, target `esp32c3`
- **Transport:** native USB Serial/JTAG only — the board has no USB-UART bridge
  (`/dev/ttyACM0`)

## Quick start

```bash
cd firmwares/01-blink
./flash.sh        # build + flash + boot the new image
./monitor.sh      # flash + stream the console log (Ctrl+C to quit)
```

Both scripts default to `/dev/ttyACM0`; pass another port as `$1`
(`./flash.sh /dev/ttyACM1`) or via `PORT=...`. Useful switches:
`SKIP_BUILD=1 ./flash.sh` (flash the existing binary) and
`NO_FLASH=1 ./monitor.sh` (attach to a running app without reflashing).

`./flash.sh` also **boots the image** for you: after `esptool` the C3 is left in
USB download mode, so the script pulses EN over the same CDC lines
(RTS → EN, DTR → GPIO9 boot strap) and the app starts without touching the board.
The boot log shows `reset: USB peripheral` when that path was used.

## What it does

Cycles **red → green → blue**, 500 ms on / 500 ms off per colour, forever, and
logs every transition on the USB console at 115200 baud:

```
I (74) smove-blink: boot: sMove 01-blink, ESP32-C3 rev v0.4, 1 core(s), reset: USB peripheral
I (74) smove-blink: LED: red=GPIO3 green=GPIO7 blue=GPIO10 (common anode, active low), 500 ms on / 500 ms off per colour
I (74) smove-blink: cycle 1: red on
I (1074) smove-blink: cycle 1: green on
I (2074) smove-blink: cycle 1: blue on
I (3074) smove-blink: cycle 1 complete (red -> green -> blue)
I (3074) smove-blink: cycle 2: red on
...
```

The `... <colour> off` transitions are logged at `DEBUG` level, so the default
INFO console shows one line per colour per cycle. To see both edges of every
blink, raise the level for this tag or build with
`CONFIG_LOG_MAXIMUM_LEVEL_DEBUG` (menuconfig → *Component config → Log output*).

## LED wiring (from `PCB/main/smove-r2-main.kicad_pcb`)

D1 = LiteOn `LTST-C19HE1WT`, a **common-anode** RGB LED:

| Colour | U1 pin | Series R | Net |
|--------|--------|----------|-----|
| red    | GPIO3  | R11 1k   | `LED_R` |
| green  | GPIO7  | R12 1k   | `LED_G` |
| blue   | GPIO10 | R13 1k   | `LED_B` |

The common anode (D1 pad 4) sits on `3V3_MAIN`, so the GPIOs **sink** current:

```
level 0 (low)  -> colour ON
level 1 (high) -> colour OFF
```

All three pins idle HIGH, so the LED stays dark from reset until the GPIO matrix
is configured. `main/smove_board.h` holds the pin map and the polarity macros —
use it rather than hard-coding GPIO numbers in new firmware.

## Toolchain (one-time)

ESP-IDF v5.5 lives in the git-ignored `.tools/esp-idf` at the repository root;
`flash.sh`/`monitor.sh` source it automatically when `idf.py` is not on `PATH`.

```bash
git clone -b v5.5 --depth 1 https://github.com/espressif/esp-idf.git .tools/esp-idf
cd .tools/esp-idf
git submodule update --init --recursive --depth 1 -j 8   # skip the full-history blob clone
./install.sh esp32c3
```

Never cloned the submodules shallow? The first `idf.py build` then stalls on
`Initialising new submodule ... lib` while it fetches the wifi/phy/bt binaries
with full history — pre-fetching as above avoids that wait.

## Manual flash / monitor

```bash
idf.py -p /dev/ttyACM0 build flash      # does NOT boot the app afterwards
idf.py -p /dev/ttyACM0 monitor          # asserts DTR/RTS -> can re-enter download mode
```

If the board ends up in download mode
(`boot:0x7 (DOWNLOAD(USB/UART0/1))` / `waiting for download`), either run
`./flash.sh` (it resets for you) or **tap the RESET (EN) button** once. If it
keeps landing there, hold **BOOT** while tapping **RESET**, then release BOOT.

Binary: `build/smove-blink.bin` (~171 kB). `sdkconfig.defaults` pins the target,
4 MB flash, single-app partition table, console on USB Serial/JTAG and BT off.

## Tuning

`BLINK_HALF_PERIOD_MS` (default 500) sets the on and off time per colour. It is
wired through to the compiler by `main/CMakeLists.txt`:

```bash
BLINK_HALF_PERIOD_MS=1000 ./flash.sh      # slow, 1 s on / 1 s off
BLINK_HALF_PERIOD_MS=100  ./flash.sh      # fast
./flash.sh                                # back to the 500 ms default
```

Runtime log verbosity is standard ESP-IDF: `idf.py menuconfig` →
*Component config → Log output*, or `esp_log_level_set("smove-blink", ...)`.
