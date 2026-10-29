#!/usr/bin/env python3
"""espnow_monitor.py — live link + IMU view for the sMove ESP-NOW receiver.

Reads the receiver's UART console (/dev/ttyUSB0 by default) and turns the
`S,...` frame lines into a fixed status block, so you can see at a glance
whether the radio link is healthy and what the IMU is doing.

    ./monitor.sh                    # /dev/ttyUSB0, 115200
    ./monitor.sh /dev/ttyACM0       # explicit port
    python3 host/espnow_monitor.py --raw     # just echo the firmware lines

Line format produced by firmwares/05-espnow-imu/rx:

    S,<seq>,<tx_us>,<rx_us>,<ax>,<ay>,<az>,<gx>,<gy>,<gz>,<rssi>
    T,<rssi>,<received>,<lost>,<age_ms>

tx_us and rx_us are microsecond counters from two different chips with two
different epochs, so their absolute difference means nothing. The monitor keeps
the running minimum of (rx_us - tx_us) as the epoch offset and reports the
*spread* above it: that is the honest end-to-end delay variation of the link.
"""

import argparse
import collections
import sys
import time

try:
    import serial  # pyserial
except ImportError:  # pragma: no cover - environment problem, not a code path
    sys.exit("pyserial is missing:  python3 -m pip install pyserial")


class Unwrap32:
    """32-bit microsecond counter -> monotonic 64-bit (the tx t_us wraps ~71 min)."""

    def __init__(self):
        self._last = None
        self._base = 0

    def __call__(self, raw):
        if self._last is not None and raw < self._last and (self._last - raw) > 0x7FFFFFFF:
            self._base += 1 << 32
        self._last = raw
        return self._base + raw


def parse_sample(line):
    """'S,...' -> dict, or None when the line is not a complete sample."""
    parts = line.split(",")
    if len(parts) != 11 or parts[0] != "S":
        return None
    try:
        return {
            "seq": int(parts[1]),
            "tx_us": int(parts[2]),
            "rx_us": int(parts[3]),
            "accel": [float(parts[4]), float(parts[5]), float(parts[6])],
            "gyro": [float(parts[7]), float(parts[8]), float(parts[9])],
            "rssi": int(parts[10]),
        }
    except ValueError:
        return None


def parse_status(line):
    """'T,...' -> dict, or None."""
    parts = line.split(",")
    if len(parts) != 5 or parts[0] != "T":
        return None
    try:
        return {
            "rssi": int(parts[1]),
            "received": int(parts[2]),
            "lost": int(parts[3]),
            "age_ms": int(parts[4]),
        }
    except ValueError:
        return None


def fmt3(v):
    return f"{v:+7.3f}"


def fmt2(v):
    return f"{v:+6.2f}"


def render(state, window):
    now = time.monotonic()
    last = state["last"]
    span = state["window_span"] or 0.0
    count = state["window_count"]

    rate = (count - 1) / span if span > 0 else 0.0
    total = state["received"] + state["lost"]
    loss_pct = 100.0 * state["lost"] / total if total else 0.0

    age_ms = (now - state["last_host"]) * 1000.0 if state["last_host"] else float("nan")
    stalled = state["last_host"] is None or age_ms > 1000.0

    bulb = "\033[31m●\033[0m" if stalled else ("\033[32m●\033[0m" if rate > 0.5 else "\033[33m●\033[0m")

    spread = (state["max_delta"] - state["min_delta"]) / 1000.0 if state["max_delta"] is not None else 0.0
    offset_ms = state["min_delta"] / 1000.0 if state["min_delta"] is not None else 0.0

    out = []
    out.append("\033[1m sMove → ESP-NOW → receiver\033[0m"
               f"    port {state['port']} @ {state['baud']}    window {window:.1f} s")
    out.append("")
    if stalled:
        out.append(f" link      {bulb}  \033[31mNO DATA\033[0m"
                   + (f" — last frame {age_ms/1000:.1f} s ago" if state["last_host"] else " — waiting"))
    else:
        out.append(f" link      {bulb}  {rate:5.2f} Hz   {count} frames in {span:.2f} s")
    out.append(f" frames    {state['received']} received, {state['lost']} lost ({loss_pct:.2f} %), "
               f"{state['dup']} dup/late")
    out.append(f" rssi      {state['rssi']:4d} dBm"
               + ("   (no frame yet)" if state["rssi"] == 0 and last is None else ""))
    out.append(f" delay     spread {spread:5.2f} ms   epoch offset {offset_ms:9.1f} ms   "
               f"seq {state['seq']}")
    out.append("")
    if last is None:
        out.append(" IMU       (no samples yet)")
    else:
        a, g = last["accel"], last["gyro"]
        out.append(f" accel [g]    x {fmt3(a[0])}   y {fmt3(a[1])}   z {fmt3(a[2])}")
        out.append(f" gyro [dps]   x {fmt2(g[0])}   y {fmt2(g[1])}   z {fmt2(g[2])}")
    out.append("")
    out.append(f" board     {state['note']}")
    out.append("\033[2m Ctrl-C to quit\033[0m")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="Live ESP-NOW IMU link monitor.")
    ap.add_argument("port", nargs="?", default="/dev/ttyUSB0")
    ap.add_argument("-b", "--baud", type=int, default=115200)
    ap.add_argument("-w", "--window", type=float, default=2.0,
                    help="averaging window in seconds (default 2.0)")
    ap.add_argument("--raw", action="store_true",
                    help="echo the firmware lines instead of drawing the status block")
    args = ap.parse_args()

    try:
        link = serial.Serial(args.port, args.baud, timeout=0.05)
    except serial.SerialException as exc:
        sys.exit(f"cannot open {args.port}: {exc}")

    # Opening the port asserts DTR/RTS, which on the devkit's USB-UART bridge is
    # wired to the boot strap and EN — that would hold the receiver in reset.
    # Both lines deasserted = "run the app we flashed".
    link.dtr = False
    link.rts = False
    time.sleep(0.05)
    link.reset_input_buffer()

    state = {
        "port": args.port,
        "baud": args.baud,
        "received": 0,
        "lost": 0,
        "dup": 0,
        "seq": 0,
        "rssi": 0,
        "last": None,
        "last_host": None,
        "min_delta": None,
        "max_delta": None,
        "window_count": 0,
        "window_span": 0.0,
        "note": "(no board messages yet)",
        "_last_seq": None,
        "_arrivals": collections.deque(),
    }
    unwrap = Unwrap32()
    next_draw = 0.0
    interactive = sys.stdout.isatty() and not args.raw
    if not sys.stdout.isatty() and not args.raw:
        # Piped to a file or another tool: the ANSI block would be noise, so
        # behave like --raw instead of printing nothing.
        args.raw = True

    if interactive:
        sys.stdout.write("\033[?25l\033[2J")  # hide cursor, clear
        sys.stdout.flush()

    try:
        while True:
            raw = link.readline()
            if raw:
                line = raw.decode("utf-8", "replace").strip()
                if line:
                    if line.startswith("#"):
                        state["note"] = line
                        if args.raw:
                            print(line)
                    elif line.startswith("T,"):
                        st = parse_status(line)
                        if st:
                            state["rssi"] = st["rssi"]
                            if args.raw:
                                print(line)
                    else:
                        sample = parse_sample(line)
                        if sample is not None:
                            now = time.monotonic()
                            seq = sample["seq"]

                            if state["_last_seq"] is not None:
                                delta = (seq - state["_last_seq"]) & 0xFFFF
                                if delta == 0 or delta >= 0x8000:
                                    state["dup"] += 1
                                elif delta > 1:
                                    state["lost"] += delta - 1
                            state["_last_seq"] = seq
                            state["received"] += 1
                            state["seq"] = seq
                            state["rssi"] = sample["rssi"]
                            state["last"] = sample
                            state["last_host"] = now

                            tx_us = unwrap(sample["tx_us"])
                            delta_us = sample["rx_us"] - tx_us
                            state["min_delta"] = delta_us if state["min_delta"] is None \
                                else min(state["min_delta"], delta_us)
                            state["max_delta"] = delta_us if state["max_delta"] is None \
                                else max(state["max_delta"], delta_us)

                            arrivals = state["_arrivals"]
                            arrivals.append(now)
                            while arrivals and now - arrivals[0] > args.window:
                                arrivals.popleft()
                            state["window_count"] = len(arrivals)
                            state["window_span"] = (arrivals[-1] - arrivals[0]) if len(arrivals) > 1 else 0.0

                            if args.raw:
                                print(line)

                    if args.raw:
                        sys.stdout.flush()

            now = time.monotonic()
            if interactive and now >= next_draw:
                next_draw = now + 0.2
                sys.stdout.write("\033[H" + render(state, args.window) + "\n")
                sys.stdout.flush()
    except KeyboardInterrupt:
        pass
    finally:
        if interactive:
            sys.stdout.write("\033[?25h\n")  # show cursor
        link.close()


if __name__ == "__main__":
    main()
