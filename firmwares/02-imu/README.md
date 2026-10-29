# 02-imu — ICM-20948 bring-up firmware

Reads the on-board 9-axis IMU and prints one line per sample on the USB console,
**every 100 ms** by default. It is the second firmware for `smove-r2-main` and
the software half of the IMU bring-up (the first is [`01-blink`](../01-blink/README.md)).
For a live 3D view of the same sensor, see [`03-imu-viz`](../03-imu-viz/README.md).

- **MCU:** U1 = `ESP32-C3-MINI-1-N4` (RISC-V, 4 MB embedded flash, revision v0.4)
- **Framework:** ESP-IDF v5.5, target `esp32c3`
- **IMU:** U2 = TDK InvenSense `ICM-20948` (accel + gyro + AK09916 magnetometer die)
- **Bus:** I2C on GPIO5 (SDA) / GPIO4 (SCL), 400 kHz, 1.8 V side level-shifted by U3 (PCA9306)

## Quick start

```bash
cd firmwares/02-imu
./monitor.sh      # flash + stream the IMU log (Ctrl+C to quit)
./flash.sh        # build + flash + boot, without attaching the reader
```

Both scripts default to `/dev/ttyACM0`; pass another port as `$1`
(`./monitor.sh /dev/ttyACM1`) or via `PORT=...`. Useful switches:
`SKIP_BUILD=1 ./flash.sh` (flash the existing binary) and
`NO_FLASH=1 ./monitor.sh` (attach to a running app without reflashing).

`IMU_SAMPLE_PERIOD_MS` changes the cadence at build time (it is always passed to
CMake, so a stale cached value cannot linger):

```bash
IMU_SAMPLE_PERIOD_MS=20  ./flash.sh     # 50 Hz
IMU_SAMPLE_PERIOD_MS=500 ./flash.sh     # 2 Hz
./flash.sh                              # back to the 100 ms default
```

## What the log looks like

Captured from the board at the default 100 ms cadence:

```
I (80) smove-imu: boot: sMove 02-imu, ESP32-C3 rev v0.4, 1 core(s), reset: USB peripheral
I (81) smove-imu: IMU: ICM-20948 (U2) on SDA=GPIO5 SCL=GPIO4 @ 400 kHz, one sample every 100 ms
I (81) smove-imu: accel g | gyro deg/s | die temp °C | mag µT — board axes, +Z outward
I (82) smove-imu: I2C probe 0x68 -> ESP_OK
I (318) icm20948: ICM-20948 ready at 0x68: WHO_AM_I=0xea, accel ±2 g (16384 LSB/g), gyro ±250 dps (131 LSB/dps), DLPF ~50 Hz, mag 100 Hz (unavailable)
I (350) smove-imu: #00001 | accel[g] -0.026 +0.089 +1.001 | gyro[dps] +0.26 -1.06 -0.53 | T  33.0 C | mag[uT] ~+0.0 +0.0 +0.0
I (450) smove-imu: #00002 | accel[g] -0.017 +0.078 +1.008 | gyro[dps] -2.40 -0.44 -1.40 | T  33.2 C | mag[uT] ~+0.0 +0.0 +0.0
I (550) smove-imu: #00003 | accel[g] -0.020 +0.087 +1.004 | gyro[dps] +0.86 -0.21 +1.18 | T  33.0 C | mag[uT] ~+0.0 +0.0 +0.0
...
I (11550) smove-imu: #00113 | accel[g] -0.012 +0.084 +1.019 | gyro[dps] +0.31 +2.34 -0.64 | T  33.0 C | mag[uT] ~+0.0 +0.0 +0.0
```

- `#NNNNN` is the sample counter (1 per period, so it is also the age in periods).
- `accel[g]` — board axes. The unit resting on its back reads **≈ +1.0 g on Z**
  (the IMU +Z faces outward through the board's underside), X/Y near 0.
- `gyro[dps]` — raw, **uncalibrated**: a few ±1–3 dps of zero-rate offset is
  normal until a bias calibration is added.
- `T … C` — the ICM-20948 die temperature (first sample after reset can be low).
- `mag[uT]` — `~` marks "no fresh magnetometer sample" (see the note below).
- Every 100 samples a summary line reports measured rate and read-error count:

```
I (10350) smove-imu: -- 100 samples in 10000 ms (10.00 Hz), 0 read error(s) total
```

## Wiring (from `PCB/main/smove-r2-main.kicad_pcb`)

| Signal | U2 (ICM-20948) | Via | U1 (ESP32-C3) |
|--------|----------------|-----|---------------|
| SDA    | pad 24 | `/IMU/SDA_1V8` → U3 pad 4 ∥ pad 5 → `/SDA_HOST` | GPIO5 (pad 19) |
| SCL    | pad 23 | `/IMU/SCL_1V8` → U3 pad 3 ∥ pad 6 → `/SCL_HOST` | GPIO4 (pad 18) |
| INT1   | pad 12 | not connected — the demo polls instead | — |
| REGOUT | pad 10 | C10 1uF, internal regulator | — |
| Supply | pads 8/13/22 | `1V8_IMU` from U5 (AP2112K-1V8) | — |

Pull-ups: R16/R17 4.7k to `1V8_IMU` (IMU side), R18/R19 4.7k to `3V3_MAIN`
(host side). U3 (PCA9306) translates between the two domains; the IMU is the
only device on this bus.

`main/smove_board.h` holds the pin map, the address and the speed — use it
rather than hard-coding pin numbers in new firmware.

## Configuration the driver applies

| Item | Value | Notes |
|------|-------|-------|
| Address | **0x68** (probe fallback 0x69) | measured on the assembled board (AD0 low) |
| Accel | ±2 g, 16384 LSB/g | `ACCEL_CONFIG` = DLPF ≈ 50 Hz, FS = 0 |
| Gyro | ±250 dps, 131 LSB/dps | `GYRO_CONFIG_1` = DLPF ≈ 50 Hz, FS = 0 |
| Temperature | 333.87 LSB/°C, +21 °C offset | datasheet formula |
| Magnetometer | AK09916, 100 Hz continuous | read via internal I²C master (SLV0), 0.15 µT/LSB |
| Sample read | one 23-byte burst from 0x2D | accel + gyro + temp + mag in one transaction |

`icm20948.c` owns the register map and the bank switching (bank select and the
register access are separate transactions); `imu_demo.c` owns only the cadence,
the formatting and the LED state.

Ranges are compile-time constants at the top of `icm20948.c`
(`GYRO_FS_SEL_*`, `ACCEL_FS_SEL_*` and the matching `*_LSB_PER_*` scale) — widen
the accelerometer to ±16 g if you start swinging the unit around.

## Measured bring-up result

| Sensor | Status |
|--------|--------|
| Accel | working — Z ≈ +1.0 g at rest, noise ≈ ±0.01 g |
| Gyro | working — noise ≈ ±2 dps raw, no bias calibration applied |
| Die temperature | working — 33 °C at idle, settles quickly after reset |
| Magnetometer | **not responding on this unit**: AK09916 `WIA2` (0x01) reads 0x00 and `I2C_MST_STATUS` shows no NACK while `USER_CTRL` = 0x20 and SLV0 is programmed (`0x8C / 0x01 / 0x81`). The 6-axis data is unaffected and the driver reports `mag unavailability` instead of faking values |

If a mag-equipped unit is fitted, the same code path should light it up: the
driver configures CNTL3 soft reset → CNTL2 = 0x08 (100 Hz) and leaves SLV0
reading `ST1..ST2` into `EXT_SLV_SENS_DATA_00..08`, then verifies that ST1.DRDY
comes back before claiming the mag works. `icm20948_read()` only trusts the mag
bytes when ST1.DRDY is set and ST2.HOFL is clear.

## Behaviour on failure

- No IMU on the bus at boot → the red LED flashes and the attach is retried every
  2 s forever; the log explains what was probed.
- Bus errors while streaming → warnings are rate-limited, and after 10
  consecutive failures the driver detaches and re-attaches the device
  (green LED = streaming, red = not).
- Green LED on solid means samples are flowing.

## Manual flash / monitor

```bash
idf.py -p /dev/ttyACM0 build flash      # does NOT boot the app afterwards
idf.py -p /dev/ttyACM0 monitor          # asserts DTR/RTS -> can re-enter download mode
```

If the board ends up in download mode (`boot:0x7 (DOWNLOAD…)` / `waiting for
download`), run `./flash.sh` (it resets for you) or tap RESET (EN) once. Never
use `idf.py monitor` on this board — see [firmwares/README.md](../README.md).

## Limits

- Polled, no FIFO, no DMP, no interrupt pin (INT1 is not routed on this PCB).
- 100 ms cadence means one I²C transaction per period; the sensor's own ODR is
  1.125 kHz, so faster logging only needs a smaller `IMU_SAMPLE_PERIOD_MS`.
- Values are raw: no gyro/accel bias calibration, no axis remap, no temperature
  compensation, no magnetometer hard/soft-iron calibration.
- Absolute accuracy is not characterised; this is a bring-up / sanity firmware,
  not a motion-tracking stack.
