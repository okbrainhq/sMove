# 05-espnow-imu — sMove IMU over ESP-NOW to a bench ESP32

Two firmwares, one folder: the sMove board streams its ICM-20948 over ESP-NOW,
a second ESP32 sitting on the USB cable catches the frames and relays them to
the PC as plain text lines.

```
  smove-r2-main (ESP32-C3)                     bench ESP32-D0WD devkit
  ┌──────────────────────────┐   ESP-NOW      ┌──────────────────────────┐
  │ ICM-20948 ── I2C ── tx/  │ ─ 2.4 GHz ch1 ─▶│ rx/ ── UART0 ── CP210x ──▶│── /dev/ttyUSB0
  └──────────────────────────┘   10 Hz, 36 B   └──────────────────────────┘   monitor.sh
```

| Dir | Target | Role |
|-----|--------|------|
| [`tx/`](tx/README.md) | ESP32-C3-MINI-1-N4 (sMove U1) | reads the IMU every 100 ms, transmits one frame per sample |
| [`rx/`](rx/README.md) | ESP32-D0WD devkit (CP210x) | receives the frames, prints `S,...` lines, beacons a 1 Hz HELLO |
| `host/espnow_monitor.py` | PC | live rate / loss / RSSI / jitter + latest IMU values |

## Quick start

```bash
./flash-tx.sh              # sMove on /dev/ttyACM0
./flash-rx.sh              # bench ESP32 on /dev/ttyUSB0
./monitor.sh               # live view
```

Both scripts source the repo-local ESP-IDF (`.tools/esp-idf`) the same way the
other firmware folders do. Expected result: the sMove LED turns **blue** while
it broadcasts, then **green** once the receiver's HELLO pairs it, and the
monitor shows ~10 Hz.

## Wire format

`tx/main/espnow_proto.h` and `rx/main/espnow_proto.h` are byte-identical.
Both chips are little-endian, so the packed structs go straight on the radio.

```c
/* tx -> rx, 36 B, one per sample */
struct { u32 magic; u8 version; u8 type; u16 seq; u32 t_us;
         f32 ax, ay, az;          /* g   */
         f32 gx, gy, gz; }        /* dps */

/* rx -> tx, 12 B, 1 Hz */
struct { u32 magic; u8 version; u8 type; u16 period_ms; u32 uptime_s; }
```

Console lines out of the receiver (`115200 8N1`):

```
# sMove ESP-NOW IMU receiver — MAC a4:f0:0f:53:40:78, channel 1
S,<seq>,<tx_us>,<rx_us>,<ax>,<ay>,<az>,<gx>,<gy>,<gz>,<rssi>
T,<rssi>,<received>,<lost>,<age_ms>
```

`tx_us` / `rx_us` come from two different chips with two different epochs;
only their *differences* are meaningful, and `espnow_monitor.py` reports the
spread above the running minimum.

## Pairing, channel, cadence

- **Channel 1, fixed.** Neither end joins an AP; both are unassociated STAs
  parked on channel 1 with `WIFI_PS_NONE` so the radio never dozes between the
  100 ms frames. Change `SMOVE_ESPNOW_CHANNEL` in both `espnow_proto.h` copies
  if 1 is crowded.
- **Auto-pairing.** The receiver broadcasts its HELLO every second; the
  transmitter pins the first HELLO's MAC as a unicast peer (broadcast sends are
  always reported as "success", unicast is not). Losing the ACKs for 2.5 s drops
  the peer and falls back to broadcast, so swapping the bench board needs no
  reflash.
- **Cadence.** `IMU_SAMPLE_PERIOD_MS` — 100 ms (10 Hz) by default:

  ```bash
  IMU_SAMPLE_PERIOD_MS=50 ./flash-tx.sh     # 20 Hz
  ```

  10 Hz × 36 B is nothing for ESP-NOW; the practical ceiling here is the
  115200 UART on the receiver (~100 lines/s), not the radio.

## Troubleshooting

| Symptom | Check |
|---------|-------|
| monitor: `NO DATA`, sMove LED stays blue | receiver not powered / wrong channel / HELLO blocked — is `rx/` really flashed on the *other* board? |
| sMove LED red | no IMU answered on I2C: U2, the 1V8 rail, U3 level shifter |
| frames arrive but `lost` climbs | distance / antenna orientation; RSSI below ≈ −85 dBm is the practical limit indoors |
| garbage on the port | two readers on `/dev/ttyUSB0` (close `idf.py monitor` first) |
| `flash-rx.sh` fails at 460800 | `FLASH_BAUD=115200 ./flash-rx.sh` |
| reading `/dev/ttyACM0` restarts the sMove | that is the C3's USB-Serial/JTAG: opening the device asserts DTR/RTS, which are wired to GPIO9/EN. Harmless (the app reboots and re-pairs within a second) — just do not expect a continuous log while poking at it |
