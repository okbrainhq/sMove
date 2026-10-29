# 01-blink — sMove bring-up firmware

Minimal ESP-IDF firmware that blinks the on-board RGB LED. It is the first
firmware for `smove-r2-main` and doubles as a toolchain / flash-path smoke test.

- **MCU:** U1 = `ESP32-C3-MINI-1-N4` (RISC-V, 4 MB embedded flash, revision v0.4)
- **Framework:** ESP-IDF v5.5, target `esp32c3`
- **Transport:** native USB Serial/JTAG only — the board has no USB-UART bridge
  (`/dev/ttyACM0`)

## What it does

Cycles **red → green → blue**, 250 ms on / 250 ms off per colour, and logs the
colour being lit on the USB console at 115200 baud. The cycle repeats forever.

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

## Build

```bash
# one-time toolchain setup (installs into .tools/, git-ignored)
git clone -b v5.5 --depth 1 https://github.com/espressif/esp-idf.git .tools/esp-idf
cd .tools/esp-idf && git submodule update --init --recursive --depth 1 -j 8
./install.sh esp32c3
. ./export.sh

# build
cd firmwares/01-blink
idf.py set-target esp32c3        # only needed once
idf.py build
```

Binary: `build/smove-blink.bin` (~171 kB). `sdkconfig.defaults` pins the target,
4 MB flash, single-app partition table, console on USB Serial/JTAG and BT off.

## Flash

```bash
idf.py -p /dev/ttyACM0 flash
```

### ⚠️ Reset after flashing

On this board `esptool` leaves the C3 in **download mode**
(`rst:0x15 (USB_UART_CHIP_RESET), boot:0x7 (DOWNLOAD(USB/UART0/1))` →
`waiting for download`), so the freshly flashed app does not start and neither
`idf.py monitor` nor `esptool run` reliably gets it out, because reopening the
CDC port re-asserts DTR (GPIO9 strap).

**Press the RESET (EN) button once after flashing** — the app then boots and
streams its log. If it lands in download mode again, hold **BOOT** while tapping
**RESET**, release BOOT.

## Verify without disturbing the board

Reading the console is enough to confirm the loop is running; no reset needed:

```bash
python3 -c "
import serial, time
s = serial.Serial(); s.port='/dev/ttyACM0'; s.baudrate=115200; s.timeout=0.2
s.dtr=False; s.rts=False; s.open()   # keep DTR low-asserted off: normal-boot strap
end=time.time()+3; buf=b''
while time.time()<end: buf+=s.read(4096)
print(buf.decode(errors='replace'))"
```

Expected output:

```
I (573) smove-blink: green on
I (1073) smove-blink: blue on
I (1573) smove-blink: red on
...
```

## Tuning

`BLINK_HALF_PERIOD_MS` (default 250) sets the on and off time per colour:

```bash
idf.py -DBLINK_HALF_PERIOD_MS=1000 build flash
```
