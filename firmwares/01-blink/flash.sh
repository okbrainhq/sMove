#!/usr/bin/env bash
#
# flash.sh — build + flash 01-blink onto smove-r2-main (ESP32-C3-MINI-1-N4).
#
#   ./flash.sh                 # build + flash on /dev/ttyACM0, then reset into the app
#   ./flash.sh /dev/ttyACM1    # explicit port
#   PORT=/dev/ttyACM1 ./flash.sh
#   SKIP_BUILD=1 ./flash.sh    # flash the existing build/ without rebuilding
#
# Why the trailing reset: esptool drives the C3 over its native USB Serial/JTAG
# peripheral and leaves it in USB download mode (boot:0x7 DOWNLOAD), so the app
# does NOT start after flashing. We pulse EN over the same CDC lines (RTS -> EN,
# DTR -> GPIO9 boot strap) to boot the freshly flashed image.
#
set -euo pipefail

HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$HERE/../.." && pwd)"
IDF_PATH="${IDF_PATH:-$REPO_ROOT/.tools/esp-idf}"

PORT="${1:-${PORT:-/dev/ttyACM0}}"
: "${SKIP_BUILD:=0}"

# --- ESP-IDF environment ------------------------------------------------------
if ! command -v idf.py >/dev/null 2>&1; then
    if [[ -f "$IDF_PATH/export.sh" ]]; then
        # shellcheck disable=SC1091
        . "$IDF_PATH/export.sh" >/dev/null 2>&1
    else
        echo "error: ESP-IDF not found (expected $IDF_PATH) and idf.py is not on PATH" >&2
        echo "       see firmwares/README.md for the one-time toolchain setup" >&2
        exit 1
    fi
fi

cd "$HERE"

# --- build --------------------------------------------------------------------
if [[ "$SKIP_BUILD" != "1" ]]; then
    build_args=()
    # Optional: BLINK_HALF_PERIOD_MS=250 ./flash.sh  -> compile-time half period.
    # Always passed explicitly: idf.py caches -D values in build/CMakeCache.txt, so
    # leaving it out after one custom build would silently keep the old period.
    build_args+=("-DBLINK_HALF_PERIOD_MS=${BLINK_HALF_PERIOD_MS:-500}")
    echo "==> blinking with BLINK_HALF_PERIOD_MS=${BLINK_HALF_PERIOD_MS:-500}"
    echo "==> building (esp32c3)"
    idf.py "${build_args[@]}" build
fi

# --- flash --------------------------------------------------------------------
echo "==> flashing $PORT"
idf.py -p "$PORT" flash

# --- boot the new image -------------------------------------------------------
echo "==> resetting into the application"
python3 - "$PORT" <<'PY'
import sys, time
import serial

port = sys.argv[1]
s = serial.Serial()
s.port = port
s.baudrate = 115200
s.timeout = 0.2
s.open()
try:
    s.dtr = False          # DTR deasserted -> GPIO9 high -> boot from flash
    time.sleep(0.05)
    s.rts = True           # assert EN (reset)
    time.sleep(0.15)
    s.rts = False          # release EN -> run
    time.sleep(0.05)
finally:
    s.close()
PY

echo "==> done — app running on $PORT (use ./monitor.sh to watch the log)"
