#!/usr/bin/env bash
#
# viz.sh — flash 03-imu-viz and watch the accel + gyro stream in 3D.
#
#   ./viz.sh                     # flash /dev/ttyACM0, serve http://localhost:3000
#   ./viz.sh --port /dev/ttyACM1 # explicit board
#   ./viz.sh --no-flash          # board already running the stream, just serve
#   ./viz.sh --mock              # no board at all: synthetic motion for UI work
#   ./viz.sh --http-port 8080    # different web port
#   OPEN=1 ./viz.sh              # also open the page in the default browser
#
# It always frees TCP port 3000 first (any leftover server from a previous run
# is killed), then:
#   1. builds + flashes the firmware (see ./flash.sh for the ESP-IDF details),
#   2. starts host/imu_viz.py, which reads the `S,...` sample lines from the
#      board's USB-Serial/JTAG console and pushes them to the browser over SSE,
#   3. prints the URL. Ctrl+C stops the web app; the board keeps streaming.
#
set -euo pipefail

HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

SERIAL_PORT="${PORT:-/dev/ttyACM0}"
HTTP_PORT="${HTTP_PORT:-3000}"
NO_FLASH=0
MOCK=0

usage() {
    sed -n '2,18p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --port)       SERIAL_PORT="${2:?--port needs a device}"; shift 2 ;;
        --http-port)  HTTP_PORT="${2:?--http-port needs a number}"; shift 2 ;;
        --no-flash)   NO_FLASH=1; shift ;;
        --mock)       MOCK=1; NO_FLASH=1; shift ;;
        -h|--help)    usage; exit 0 ;;
        -*)           echo "unknown option: $1" >&2; usage; exit 2 ;;
        *)            SERIAL_PORT="$1"; shift ;;
    esac
done

# --- free the web port --------------------------------------------------------
port_busy() {
    python3 - "$1" <<'PY'
import socket, sys
port = int(sys.argv[1])
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try:
    s.bind(("0.0.0.0", port))
except OSError:
    sys.exit(1)
finally:
    s.close()
sys.exit(0)
PY
}

if ! port_busy "$HTTP_PORT"; then
    echo "==> port $HTTP_PORT is busy — freeing it"
    if command -v fuser >/dev/null 2>&1; then
        fuser -k -n tcp "$HTTP_PORT" >/dev/null 2>&1 || true
    fi
    if ! port_busy "$HTTP_PORT" && command -v lsof >/dev/null 2>&1; then
        pids="$(lsof -ti "tcp:$HTTP_PORT" || true)"
        [[ -n "$pids" ]] && kill $pids 2>/dev/null || true
    fi
    for _ in $(seq 1 30); do
        port_busy "$HTTP_PORT" && break
        sleep 0.1
    done
    if ! port_busy "$HTTP_PORT"; then
        echo "error: port $HTTP_PORT is still in use — free it and retry" >&2
        exit 1
    fi
fi

# --- flash --------------------------------------------------------------------
if [[ "$MOCK" == "1" ]]; then
    echo "==> mock mode: no flashing, synthetic samples"
elif [[ "$NO_FLASH" == "1" ]]; then
    echo "==> --no-flash: using whatever is already running on $SERIAL_PORT"
else
    "$HERE/flash.sh" "$SERIAL_PORT"
    echo
fi

# --- web app ------------------------------------------------------------------
ARGS=(--http-port "$HTTP_PORT")
if [[ "$MOCK" == "1" ]]; then
    ARGS+=(--mock)
else
    ARGS+=(--serial-port "$SERIAL_PORT")
fi

if [[ "${OPEN:-0}" == "1" ]] && command -v xdg-open >/dev/null 2>&1; then
    ( sleep 1.5; xdg-open "http://localhost:$HTTP_PORT" >/dev/null 2>&1 || true ) &
fi

exec python3 -u "$HERE/host/imu_viz.py" "${ARGS[@]}"
