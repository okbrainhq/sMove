#!/usr/bin/env bash
#
# monitor.sh — live link + IMU view of the ESP-NOW receiver.
#
#   ./monitor.sh                  # /dev/ttyUSB0, 115200
#   ./monitor.sh /dev/ttyUSB1     # explicit port
#   ./monitor.sh --raw            # echo the firmware's S/T lines instead
#
set -euo pipefail

HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PORT="${ESPNOW_PORT:-/dev/ttyUSB0}"

# First positional argument is a port when it looks like one.
if [[ $# -gt 0 && "$1" == /dev/* ]]; then
    PORT="$1"
    shift
fi

exec python3 "$HERE/host/espnow_monitor.py" "$PORT" "$@"
