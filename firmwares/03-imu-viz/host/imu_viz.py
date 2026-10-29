#!/usr/bin/env python3
"""
imu_viz.py — host bridge for sMove `03-imu-viz`.

Reads the accel + gyro lines the firmware prints on the USB Serial/JTAG console

    S,<uptime_us>,<ax>,<ay>,<az>,<gx>,<gy>,<gz>
    C,<sample_period_ms>

and serves a 3D web view of the stream on http://localhost:3000.

Nothing is buffered in files: the last sample is broadcast to every connected
browser over Server-Sent Events, so the page is live as soon as it opens.

    python3 host/imu_viz.py                     # /dev/ttyACM0, port 3000
    python3 host/imu_viz.py --serial-port /dev/ttyACM1
    python3 host/imu_viz.py --http-port 8080
    python3 host/imu_viz.py --mock              # synthetic data, no board

The board is a native-USB CDC device: opening the port must NOT assert DTR/RTS,
otherwise the C3 re-enters ROM download mode (same trap as `idf.py monitor`,
see firmwares/README.md). Both lines are explicitly deasserted after opening.

Standard library + pyserial only.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import queue
import re
import socket
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

try:
    import serial  # pyserial
except ImportError:  # pragma: no cover - only hit on a broken host
    serial = None

HERE = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.normpath(os.path.join(HERE, "..", "web"))

MIME = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
}


# --------------------------------------------------------------------------- hub


class Hub:
    """Fan-out of samples to SSE subscribers, plus the latest state."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._subs: dict[int, queue.Queue] = {}
        self._next_id = 0
        self.latest: dict | None = None
        self.period_ms = 20
        self.status = "waiting"          # waiting | live
        self.detail = "starting"
        self.count = 0
        self._times: list[float] = []

    # -- subscribers -------------------------------------------------------
    def subscribe(self) -> tuple[int, queue.Queue]:
        q: queue.Queue = queue.Queue(maxsize=256)
        with self._lock:
            self._next_id += 1
            sid = self._next_id
            self._subs[sid] = q
        return sid, q

    def unsubscribe(self, sid: int) -> None:
        with self._lock:
            self._subs.pop(sid, None)

    def _fanout(self, payload: bytes) -> None:
        with self._lock:
            subs = list(self._subs.values())
        for q in subs:
            try:
                q.put_nowait(payload)
            except queue.Full:
                # Slow client: drop its oldest frame, keep the newest.
                try:
                    q.get_nowait()
                    q.put_nowait(payload)
                except queue.Empty:
                    pass

    # -- producers ---------------------------------------------------------
    def set_status(self, status: str, detail: str = "") -> None:
        with self._lock:
            changed = status != self.status or detail != self.detail
            self.status = status
            self.detail = detail
        if changed:
            self._fanout(self.event({"type": "status", "serial": status, "detail": detail}))

    def set_period(self, period_ms: int) -> None:
        with self._lock:
            self.period_ms = period_ms
        self._fanout(self.event({"type": "config", "periodMs": period_ms}))

    def publish(self, t_us: int, accel, gyro) -> None:
        s = {
            "type": "sample",
            "t": t_us,
            "a": [round(v, 4) for v in accel],
            "g": [round(v, 3) for v in gyro],
        }
        now = time.monotonic()
        with self._lock:
            self.latest = s
            self.count += 1
            self._times.append(now)
            if len(self._times) > 400:
                del self._times[: len(self._times) - 400]
        self._fanout(self.event(s))

    def rate_hz(self) -> float:
        with self._lock:
            times = self._times
            if len(times) < 2:
                return 0.0
            span = times[-1] - times[0]
            return (len(times) - 1) / span if span > 0 else 0.0

    def broadcast_status(self) -> None:
        self._fanout(self.event(self.snapshot()))

    def snapshot(self) -> dict:
        return {
            "type": "status",
            "serial": self.status,
            "detail": self.detail,
            "periodMs": self.period_ms,
            "rateHz": round(self.rate_hz(), 1),
            "count": self.count,
            "latest": self.latest,
        }

    @staticmethod
    def event(obj: dict) -> bytes:
        return b"data: " + json.dumps(obj, separators=(",", ":")).encode() + b"\n\n"


# ------------------------------------------------------------------------ parsing

SAMPLE_RE = re.compile(r"^S,(-?\d+),(-?[\d.]+),(-?[\d.]+),(-?[\d.]+),(-?[\d.]+),(-?[\d.]+),(-?[\d.]+)$")


def handle_line(hub: Hub, line: bytes) -> None:
    try:
        text = line.decode("utf-8", "replace").strip()
    except Exception:
        return
    if not text:
        return
    if text[0] == "S":
        m = SAMPLE_RE.match(text)
        if not m:
            return
        vals = [float(x) for x in m.groups()[1:]]
        hub.publish(int(m.group(1)), vals[0:3], vals[3:6])
    elif text.startswith("C,"):
        try:
            hub.set_period(int(float(text[2:])))
        except ValueError:
            pass


# ------------------------------------------------------------------------ readers


def serial_reader(hub: Hub, port: str, baud: int) -> None:
    if serial is None:
        hub.set_status("offline", "pyserial is not installed (pip install pyserial)")
        return

    while True:
        try:
            s = serial.Serial(port, baud, timeout=0.5)
        except Exception as exc:  # noqa: BLE001 - surface anything as "waiting"
            hub.set_status("waiting", f"{port}: {exc}")
            time.sleep(1.0)
            continue

        try:
            # Keep the normal-boot strap and do not hold the chip in reset.
            s.dtr = False
            s.rts = False
            s.reset_input_buffer()
        except Exception:
            pass

        hub.set_status("live", port)
        try:
            while True:
                line = s.readline()
                if line:
                    handle_line(hub, line)
        except Exception as exc:  # noqa: BLE001 - unplugged / USB reset
            hub.set_status("waiting", f"{port}: {exc}")
        finally:
            try:
                s.close()
            except Exception:
                pass
        time.sleep(0.5)


def _rot(q, v):
    """Rotate v by quaternion q (w, x, y, z)."""
    w, x, y, z = q
    vx, vy, vz = v
    # t = 2 * cross(q.xyz, v)
    tx = 2 * (y * vz - z * vy)
    ty = 2 * (z * vx - x * vz)
    tz = 2 * (x * vy - y * vx)
    return (
        vx + w * tx + (y * tz - z * ty),
        vy + w * ty + (z * tx - x * tz),
        vz + w * tz + (x * ty - y * tx),
    )


def _qmul(a, b):
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return (
        aw * bw - ax * bx - ay * by - az * bz,
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
    )


def _qnorm(q):
    n = math.sqrt(sum(c * c for c in q)) or 1.0
    return tuple(c / n for c in q)


def mock_reader(hub: Hub, period_ms: int = 20) -> None:
    """Synthetic motion so the page can be exercised without hardware."""
    hub.set_status("mock", "synthetic samples (--mock)")
    hub.set_period(period_ms)
    dt = period_ms / 1000.0

    # Body -> world, starting flat on its back (body +Z = world up).
    q = (math.cos(-math.pi / 4), math.sin(-math.pi / 4), 0.0, 0.0)  # -90 deg about X
    t_us = 0
    t0 = time.monotonic()
    n = 0
    while True:
        t = n * dt
        n += 1
        # Wobble: slow yaw about world up + roll/pitch oscillation in body frame.
        omega = (
            35.0 * math.sin(0.9 * t),
            55.0 * math.sin(0.5 * t + 1.1),
            20.0 * math.sin(0.3 * t + 2.0),
        )
        ang = [math.radians(w) * dt for w in omega]
        half = [a / 2 for a in ang]
        dq = (1.0, half[0], half[1], half[2])
        q = _qnorm(_qmul(q, dq))

        # Gravity measured in the body frame: R^T * (0, 1, 0).
        up_world = (0.0, 1.0, 0.0)
        qi = (q[0], -q[1], -q[2], -q[3])
        accel = _rot(qi, up_world)
        gyro = list(omega)

        hub.publish(t_us, accel, gyro)
        t_us += period_ms * 1000

        target = t0 + n * dt
        delay = target - time.monotonic()
        if delay > 0:
            time.sleep(delay)


# ------------------------------------------------------------------------ server


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "sMoveImuViz/1.0"

    # -- helpers -----------------------------------------------------------
    def log_message(self, fmt, *args):  # noqa: A003 - stdlib signature
        msg = fmt % args
        if " 404 " in msg or " 403 " in msg:
            sys.stderr.write("[http] %s\n" % msg)

    def _send_json(self, obj, code: int = 200) -> None:
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: str) -> None:
        try:
            with open(path, "rb") as fh:
                body = fh.read()
        except OSError:
            self._send_json({"error": "not found"}, 404)
            return
        ext = os.path.splitext(path)[1].lower()
        self.send_response(200)
        self.send_header("Content-Type", MIME.get(ext, "application/octet-stream"))
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _chunk(self, data: bytes) -> None:
        self.wfile.write(b"%x\r\n" % len(data) + data + b"\r\n")
        self.wfile.flush()

    # -- routes ------------------------------------------------------------
    def do_GET(self):  # noqa: N802 - stdlib signature
        path = unquote(urlparse(self.path).path)
        hub: Hub = self.server.hub  # type: ignore[attr-defined]

        if path == "/events":
            self._stream(hub)
        elif path == "/api/status":
            self._send_json(hub.snapshot())
        else:
            if path in ("/", ""):
                path = "/index.html"
            target = os.path.normpath(os.path.join(WEB_DIR, path.lstrip("/")))
            if not target.startswith(WEB_DIR + os.sep):
                self._send_json({"error": "forbidden"}, 403)
                return
            self._send_file(target)

    def _stream(self, hub: Hub) -> None:
        sid, q = hub.subscribe()
        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache, no-store")
            self.send_header("Connection", "keep-alive")
            self.send_header("X-Accel-Buffering", "no")
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()

            self._chunk(hub.event(hub.snapshot()))
            last_keepalive = time.monotonic()
            while True:
                try:
                    msg = q.get(timeout=5.0)
                except queue.Empty:
                    if time.monotonic() - last_keepalive > 10.0:
                        self._chunk(b": keepalive\n\n")
                        last_keepalive = time.monotonic()
                    continue
                self._chunk(msg)
                last_keepalive = time.monotonic()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            hub.unsubscribe(sid)


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def _lan_ip() -> str | None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="sMove IMU 3D view (USB serial -> web).")
    ap.add_argument("--serial-port", default=os.environ.get("PORT", "/dev/ttyACM0"),
                    help="serial device of the board (default /dev/ttyACM0)")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--http-port", type=int, default=3000)
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--mock", action="store_true", help="synthetic data, no board")
    args = ap.parse_args(argv)

    hub = Hub()

    if args.mock:
        threading.Thread(target=mock_reader, args=(hub,), daemon=True).start()
    else:
        threading.Thread(target=serial_reader, args=(hub, args.serial_port, args.baud),
                         daemon=True).start()

    httpd = Server((args.host, args.http_port), Handler)
    httpd.hub = hub  # type: ignore[attr-defined]

    def reporter() -> None:
        while True:
            time.sleep(2.0)
            if hub.status in ("live", "mock"):
                sys.stdout.write("\r[imu] %5.1f Hz  %7d samples   " % (hub.rate_hz(), hub.count))
                sys.stdout.flush()
            hub.broadcast_status()

    threading.Thread(target=reporter, daemon=True).start()

    ip = _lan_ip()
    print("sMove IMU 3D view")
    print("  source : %s" % ("synthetic (--mock)" if args.mock else args.serial_port))
    print("  local  : http://localhost:%d" % args.http_port)
    if ip:
        print("  network: http://%s:%d" % (ip, args.http_port))
    print("  Ctrl+C to stop")
    sys.stdout.flush()

    try:
        httpd.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        print("\n[imu] stopped")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
