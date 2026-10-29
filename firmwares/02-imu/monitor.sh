#!/usr/bin/env bash
#
# monitor.sh — flash 02-imu, then stream its USB-Serial/JTAG console (IMU data).
#
#   ./monitor.sh               # flash + monitor on /dev/ttyACM0 (Ctrl+C to quit)
#   ./monitor.sh /dev/ttyACM1  # explicit port
#   PORT=/dev/ttyACM1 ./monitor.sh
#   NO_FLASH=1 ./monitor.sh    # only attach to the running app, do not flash
#
# Note: this is a plain pyserial reader on purpose. `idf.py monitor` asserts DTR
# and RTS when it attaches, which on this board re-triggers the ROM download mode
# and the app never runs; the reader below keeps both lines deasserted, so the
# C3 keeps running the flashed image and keeps printing IMU samples.
#
set -euo pipefail

HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PORT="${1:-${PORT:-/dev/ttyACM0}}"
: "${NO_FLASH:=0}"

if [[ "$NO_FLASH" != "1" ]]; then
    "$HERE/flash.sh" "$PORT"
    echo
fi

echo "==> monitoring $PORT at 115200 (IMU samples, Ctrl+C to quit)"
exec python3 -u - "$PORT" <<'PY'
import sys, time
import serial

port = sys.argv[1]
s = serial.Serial()
s.port = port
s.baudrate = 115200
s.timeout = 0.1
s.open()
s.dtr = False          # keep the normal-boot strap
s.rts = False          # EN released, do not reset the chip

start = time.time()
silent_warned = False
try:
    while True:
        data = s.read(4096)
        if data:
            sys.stdout.buffer.write(data)
            sys.stdout.buffer.flush()
            silent_warned = True
        elif not silent_warned and time.time() - start > 3.0:
            silent_warned = True
            sys.stderr.write(
                "\n[no data yet] if the log stays empty, tap the RESET (EN) button.\n"
            )
            sys.stderr.flush()
except KeyboardInterrupt:
    pass
finally:
    s.close()
    print()
PY
