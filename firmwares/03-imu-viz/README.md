# 03-imu-viz — live 3D view of the IMU (accel + gyro)

Streams the on-board ICM-20948's **accelerometer and gyroscope** over the USB
console and renders them in a small 3D web view on **http://localhost:3000**:
the board model rotates with the unit, with arrows for the accel and gyro
vectors, numeric readouts and 4 s strip charts.

Same sensor path as [`02-imu`](../02-imu/README.md) (U2, TDK InvenSense
ICM-20948 behind the PCA9306), but a different output: 02-imu prints a
human-readable log with temperature and magnetometer, 03-imu-viz prints one
compact machine-readable line per sample and drops everything the web view does
not need.

- **MCU:** U1 = `ESP32-C3-MINI-1-N4` (RISC-V, 4 MB embedded flash)
- **Framework:** ESP-IDF v5.5, target `esp32c3`, console on USB Serial/JTAG
- **Sensors:** accel ±2 g, gyro ±250 dps, DLPF ≈ 50 Hz — **no** mag, **no** temp
- **Cadence:** 20 ms (50 Hz) by default, `IMU_SAMPLE_PERIOD_MS=<ms>` to change

## Quick start

```bash
cd firmwares/03-imu-viz
./viz.sh                 # free :3000, flash /dev/ttyACM0, serve the 3D view
```

Open <http://localhost:3000>. Ctrl+C stops the web app; the board keeps
streaming.

| Command | What it does |
|---------|--------------|
| `./viz.sh` | Kill whatever holds the web port, `build + flash + reset`, then serve |
| `./viz.sh --port /dev/ttyACM1` | Different board (`PORT=...` also works) |
| `./viz.sh --no-flash` | Board already running the stream — only start the web app |
| `./viz.sh --mock` | No board: synthetic motion, for UI work |
| `./viz.sh --http-port 8080` | Different web port |
| `OPEN=1 ./viz.sh` | Also open the page in the default browser |
| `./flash.sh` | Build + flash + boot, without the web app |
| `SKIP_BUILD=1 ./viz.sh` | Flash the existing `build/` instead of rebuilding |

`viz.sh` always frees TCP port 3000 first (`fuser -k`), waits until the socket
is bindable again and fails loudly if something else grabs it. It refuses to
start on a port it could not free, rather than silently serving elsewhere.

## Serial protocol

One line per sample, no ESP-IDF log prefix, LF terminated:

```
C,20
S,271447,-0.031,0.072,1.020,0.43,1.92,-2.03
```

| Field | Meaning |
|-------|---------|
| `C,<ms>` | Config line, printed at boot and after a re-attach: sample period |
| `S,<t_us>` | Sample; `t_us` = `esp_timer_get_time()`, monotonic since boot |
| `ax,ay,az` | Accelerometer, g, board axes (`+Z` outward reads ≈ `+1.0` at rest) |
| `gx,gy,gz` | Gyroscope, deg/s, board axes |

The line is written with a single `fflush`, so a slow reader never sees half a
sample. Boot/attach/error messages still go through `ESP_LOG*` and are ignored
by the bridge.

## The web view

- **3D board** — 25 × 30 mm outline (the real `smove-r2-main` edge cut) with the
  IMU package marked; it rotates with the unit on a ground grid.
- **Orientation** — complementary filter in the browser: gyro integration for
  fast motion, slow pull towards the measured gravity vector (τ ≈ 0.55 s) so
  the model does not drift. Gyro bias is learned while the unit is still.
- **Amber arrow** = accelerometer vector (length ≈ |a|), **cyan arrow** = gyro
  rate vector (length saturates), plus a fading trail of the accel tip.
- **Readouts** — per-axis values with ± bars, |a|, |g|, and pitch/roll/yaw
  relative to the flat rest pose.
- **Charts** — the last 4 s of accel and gyro, three traces each.
- **Mouse** — drag to orbit, wheel to zoom, double-click to reset the view.

The page needs no network access and no libraries: the renderer is a small
painter's-algorithm projection on a 2D canvas, and the data arrives over
Server-Sent Events from the local bridge.

## Files

```text
03-imu-viz/
  viz.sh              flash + serve the 3D view (the entry point)
  flash.sh            build + flash + reset into the app
  main/imu_stream.c   sampling loop, CSV output, LED state
  main/icm20948.c/.h  ICM-20948 driver (copied from 02-imu)
  main/smove_board.h  pin map (copied from 02-imu)
  host/imu_viz.py     serial reader -> SSE + static file server (stdlib + pyserial)
  web/index.html      page shell
  web/app.js          renderer, filter, HUD
  web/style.css       styling
```

## Ports and processes

| Port | Owner |
|------|-------|
| 3000 (default) | `host/imu_viz.py` — `GET /`, `/app.js`, `/style.css`, `/events` (SSE), `/api/status` |
| `/dev/ttyACM0` | the board (`--no-flash`/`--mock` do not touch it) |

`/api/status` is handy for scripting and for checking the bridge without a
browser:

```bash
curl -s localhost:3000/api/status
```

## Stop or change things

```bash
# stop the web app only (the board is unaffected)
pkill -f host/imu_viz.py

# different cadence: 100 Hz streaming (line rate ~4 kB/s)
IMU_SAMPLE_PERIOD_MS=10 ./viz.sh
```

## Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| Page says *waiting for the board* | Port busy or wrong device: check `--port`, `ls /dev/ttyACM*`, and that nothing else (a stale `monitor.sh`) holds it |
| Page says *web server connection lost* | The bridge exited — look at the `viz.sh` terminal |
| Board silent / no `S,` lines | Never use `idf.py monitor` on this board: it asserts DTR/RTS and drops the C3 into download mode. Tap RESET (EN) or re-run `./flash.sh` |
| Everything is flat after start | Normal — the filter converges in well under a second once accel data flows |
| Model slowly rotates while the unit is still | Gyro bias not yet learned; it settles after a second or two of rest |
| `port 3000 is busy` | Another server; `./viz.sh` kills it, or pass `--http-port 8080` |
| `port 3000 is still in use` | Something ignores SIGKILL-free cleanup (a root process?); free it manually |

## Limits

- **6-axis attitude only.** There is no magnetometer on this unit (see
  [02-imu](../02-imu/README.md#measured-bring-up-result)), so **yaw drifts** and
  the yaw readout is relative, not a compass heading.
- No linear-acceleration rejection: shoving the unit tilts the model until the
  filter settles again.
- The view is a convenience instrument, not a calibrated measurement: accel/gyro
  are raw (no bias calibration on the device) and the firmware configures
  ±2 g / ±250 dps, so hard knocks will clip.
- One browser-side filter instance per tab; nothing is recorded — reload to
  reset.
