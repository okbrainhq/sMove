#!/usr/bin/env bash
#
# flash-rx.sh — build + flash the ESP-NOW receiver onto the bench ESP32 devkit
#               (ESP32-D0WD, CP210x USB-UART bridge -> /dev/ttyUSB0).
#
#   ./flash-rx.sh                 # build + flash on /dev/ttyUSB0
#   ./flash-rx.sh /dev/ttyUSB1    # explicit port
#   PORT=/dev/ttyUSB1 ./flash-rx.sh
#   SKIP_BUILD=1 ./flash-rx.sh    # flash the existing build/ without rebuilding
#   MONITOR=1 ./flash-rx.sh       # flash, then open the live monitor
#
# No EN/DTR dance here: this board boots through a real USB-UART bridge whose
# DTR/RTS are wired to EN/GPIO0, so esptool's own hard reset starts the app.
#
set -euo pipefail

HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$HERE/../.." && pwd)"
IDF_PATH="${IDF_PATH:-$REPO_ROOT/.tools/esp-idf}"

PORT="${1:-${PORT:-/dev/ttyUSB0}}"
: "${SKIP_BUILD:=0}"
: "${MONITOR:=0}"
# 460800 is what idf.py uses anyway; drop it if the cable is unhappy
# (FLASH_BAUD=115200 ./flash-rx.sh).
FLASH_BAUD="${FLASH_BAUD:-460800}"

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

cd "$HERE/rx"

if [[ "$SKIP_BUILD" != "1" ]]; then
    echo "==> ESP-NOW rx: relay IMU frames to the console"
    echo "==> building (esp32)"
    idf.py build
fi

echo "==> flashing $PORT @ $FLASH_BAUD"
idf.py -p "$PORT" -b "$FLASH_BAUD" flash

echo "==> done — receiver is live on $PORT (115200 8N1)"
if [[ "$MONITOR" == "1" ]]; then
    exec python3 "$HERE/host/espnow_monitor.py" "$PORT"
fi
echo "    watch it with:  ./monitor.sh $PORT"
