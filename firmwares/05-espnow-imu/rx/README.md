# rx — bench ESP32 (ESP32-D0WD, CP210x) ESP-NOW receiver

Listens on `SMOVE_ESPNOW_CHANNEL` (1) for the sMove transmitter and prints one
line per frame on UART0 (→ CP210x → `/dev/ttyUSB0`, 115200 8N1).

```
# sMove ESP-NOW IMU receiver — MAC a4:f0:0f:53:40:78, channel 1
S,<seq>,<tx_us>,<rx_us>,<ax>,<ay>,<az>,<gx>,<gy>,<gz>,<rssi>
T,<rssi>,<received>,<lost>,<age_ms>          <- once a second
```

- Self-contained ESP-IDF project: `idf.py build flash -p /dev/ttyUSB0`, or use
  `../flash-rx.sh`.
- Frames are queued out of the Wi-Fi callback and formatted by a normal task,
  so a slow console cannot stall the radio.
- The 1 Hz HELLO beacon carries this board's MAC; that is what lets the
  transmitter switch from broadcast to unicast without a hard-coded address.
- Watch it with `../monitor.sh` (or `cat /dev/ttyUSB0` for the raw lines —
  close `idf.py monitor` first, only one reader at a time).
