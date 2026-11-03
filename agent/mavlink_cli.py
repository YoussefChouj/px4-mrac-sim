#!/usr/bin/env python3
"""Plain-text MAVLink access for agents: parameters, stream rates, live messages.

TARGET is a SITL instance 0..8 (its GCS link, UDP 18570+N) or any pymavlink URL,
for example serial:/dev/ttyACM0:57600 or udpin:0.0.0.0:14550 for a real board.

  mavlink_cli.py TARGET param get NAME [NAME...]
  mavlink_cli.py TARGET param set NAME VALUE      # live, no reboot; prints the read-back
  mavlink_cli.py TARGET stream MSG HZ             # HZ 0 stops the stream
  mavlink_cli.py TARGET watch MSG [SECONDS]       # count, rate, last message
  mavlink_cli.py TARGET rtf [SECONDS]             # real-time factor: sim seconds per wall second
Exit 0 on success, 1 when the vehicle did not answer or refused.
On a URL target (real hardware) `param set` and `stream` are refused unless --allow-write is given.
"""
import os
import sys
import time

os.environ.setdefault("MAVLINK20", "1")
from pymavlink import mavutil  # noqa: E402

TIMEOUT = 5.0


def connect(target):
    url = f"udpout:127.0.0.1:{18570 + int(target)}" if target.isdigit() else target
    m = mavutil.mavlink_connection(url, source_system=255, source_component=190)
    if target.isdigit():
        # PX4 keeps replying to the first partner address it saw, so every call
        # must come from the same port: 19570+N, fixed per instance.
        m.port.bind(("127.0.0.1", 19570 + int(target)))
    deadline = time.time() + 15
    while time.time() < deadline:
        # udpout needs a first packet before PX4 knows where to reply.
        m.mav.heartbeat_send(mavutil.mavlink.MAV_TYPE_GCS, mavutil.mavlink.MAV_AUTOPILOT_INVALID, 0, 0, 0)
        hb = m.recv_match(type="HEARTBEAT", blocking=True, timeout=1)
        if hb and hb.get_srcComponent() == 1:
            m.target_system, m.target_component = hb.get_srcSystem(), 1
            return m
    sys.exit(f"no heartbeat from {url}")


def param_get(m, name):
    m.mav.param_request_read_send(m.target_system, m.target_component, name.encode(), -1)
    deadline = time.time() + TIMEOUT
    while time.time() < deadline:
        p = m.recv_match(type="PARAM_VALUE", blocking=True, timeout=0.5)
        if p and p.param_id == name:
            return p
    return None


def fmt(p):
    v = p.param_value
    if p.param_type in (mavutil.mavlink.MAV_PARAM_TYPE_INT32, mavutil.mavlink.MAV_PARAM_TYPE_UINT8):
        # PX4 sends integers bytewise inside the float field.
        import struct
        v = struct.unpack("<i", struct.pack("<f", v))[0]
    else:
        v = round(v, 6)
    return f"{p.param_id} = {v}"


def param(m, args):
    if args[:1] == ["get"] and len(args) > 1:
        ok = True
        for name in args[1:]:
            p = param_get(m, name)
            print(fmt(p) if p else f"{name}: no answer")
            ok &= p is not None
        return ok
    if args[:1] == ["set"] and len(args) == 3:
        name, value = args[1], args[2]
        old = param_get(m, name)
        if old is None:
            print(f"{name}: unknown parameter")
            return False
        is_int = old.param_type in (mavutil.mavlink.MAV_PARAM_TYPE_INT32, mavutil.mavlink.MAV_PARAM_TYPE_UINT8)
        if is_int:
            import struct
            raw = struct.unpack("<f", struct.pack("<i", int(value)))[0]
        else:
            raw = float(value)
        m.mav.param_set_send(m.target_system, m.target_component, name.encode(), raw, old.param_type)
        time.sleep(0.3)
        new = param_get(m, name)
        print(f"was {fmt(old)}; now {fmt(new) if new else 'no answer'}")
        return new is not None and fmt(new).endswith(f" {int(value) if is_int else round(float(value), 6)}")
    sys.exit("usage: param get NAME... | param set NAME VALUE")


def msg_id(name):
    mid = getattr(mavutil.mavlink, f"MAVLINK_MSG_ID_{name.upper()}", None)
    if mid is None:
        sys.exit(f"unknown MAVLink message {name}")
    return mid


def stream(m, args):
    name, hz = args[0], float(args[1])
    interval = -1 if hz <= 0 else int(1e6 / hz)
    m.mav.command_long_send(m.target_system, m.target_component,
                            mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL, 0,
                            msg_id(name), interval, 0, 0, 0, 0, 0)
    ack = m.recv_match(type="COMMAND_ACK", blocking=True, timeout=TIMEOUT)
    ok = ack is not None and ack.result == mavutil.mavlink.MAV_RESULT_ACCEPTED
    print(f"{name.upper()} at {hz:g} Hz: {'accepted' if ok else 'refused or no answer'}")
    return ok


def watch(m, args):
    name, secs = args[0].upper(), float(args[1]) if len(args) > 1 else 5.0
    msg_id(name)
    n, last, t0 = 0, None, time.time()
    while time.time() - t0 < secs:
        msg = m.recv_match(type=name, blocking=True, timeout=0.5)
        if msg:
            n, last = n + 1, msg
    print(f"{name}: {n} msgs in {secs:g} s = {n / secs:.1f} Hz")
    if last:
        d = {k: v for k, v in last.to_dict().items() if k != "mavpackettype"}
        print(" ".join(f"{k}={round(v, 4) if isinstance(v, float) else v}" for k, v in d.items()))
    return n > 0


def rtf(m, args):
    # Real-time factor: vehicle boot time (ATTITUDE.time_boot_ms) advanced per wall second.
    secs = float(args[0]) if args else 10.0
    first = m.recv_match(type="ATTITUDE", blocking=True, timeout=5)
    if not first:
        print("rtf: no ATTITUDE")
        return False
    w0, b0 = time.time(), first.time_boot_ms
    last = first
    while time.time() - w0 < secs:
        msg = m.recv_match(type="ATTITUDE", blocking=True, timeout=0.5)
        if msg:
            last = msg
    wall = time.time() - w0
    print(f"rtf {(last.time_boot_ms - b0) / 1000 / wall:.2f} (sim {(last.time_boot_ms - b0) / 1000:.1f} s in wall {wall:.1f} s)")
    return True


def main():
    allow_write = "--allow-write" in sys.argv
    sys.argv = [a for a in sys.argv if a != "--allow-write"]
    if len(sys.argv) < 3 or sys.argv[2] not in ("param", "stream", "watch", "rtf"):
        sys.exit(__doc__)
    # Hardware guard: a URL target is a real board, so writes need an explicit --allow-write.
    writes = sys.argv[2] == "stream" or sys.argv[2:4] == ["param", "set"]
    if writes and not sys.argv[1].isdigit() and not allow_write:
        sys.exit(f"refused: {' '.join(sys.argv[2:])} on {sys.argv[1]} changes a real vehicle; "
                 "add --allow-write after confirming with the operator")
    m = connect(sys.argv[1])
    cmd, args = sys.argv[2], sys.argv[3:]
    ok = {"param": param, "stream": stream, "watch": watch, "rtf": rtf}[cmd](m, args)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
