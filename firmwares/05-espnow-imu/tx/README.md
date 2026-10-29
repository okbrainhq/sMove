# tx — sMove (ESP32-C3) ESP-NOW transmitter

Reads the ICM-20948 (U2, I2C SDA GPIO5 / SCL GPIO4) every `IMU_SAMPLE_PERIOD_MS`
(100 ms = 10 Hz) and transmits one 36-byte frame per sample on
`SMOVE_ESPNOW_CHANNEL` (1).

- Self-contained ESP-IDF project: `idf.py build flash` works from here, or use
  `../flash-tx.sh` (adds the EN pulse that the C3's native USB needs).
- LED: green = paired + unicast, blue = broadcasting (no HELLO yet), red = no IMU.
- Logs a 5 s summary: `unicast: N sent, N acked, N nacked, N send errors`.

Pairing is learned from the receiver's 1 Hz HELLO broadcast — there is no
hard-coded MAC anywhere, so either board can be swapped.
