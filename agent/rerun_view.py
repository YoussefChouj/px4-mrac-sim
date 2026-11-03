#!/usr/bin/env python3
"""Live MAVLink -> Rerun viewer with a scrubbable history: each message type becomes a multi-series plot
mavlink/<NAME> (one line per numeric field), plus a 3D drone pose with a trail.

Usage: rerun_view.py TARGET [WEB_PORT] [SECONDS]. TARGET is a SITL instance 0..8 or a pymavlink URL
(same as mavlink_cli, so a real board works unchanged). Open http://localhost:WEB_PORT (default 9090)
in a Windows browser. Drag the timeline back to replay any moment since start (the viewer keeps the
whole session, up to its memory limit); click "follow" to return to live. SECONDS (default: run until
Ctrl+C) stops it and prints per-message rates, used as the self-test.
It holds the instance's GCS port, like foxglove_view, so `px4ctl param|watch` waits until it stops.
"""
import math
import sys
import time

import rerun as rr

from mavlink_cli import connect


def set_t(s):  # rerun >= 0.23 has set_time(duration=); older ones set_time_seconds
    rr.set_time('boot', duration=s) if hasattr(rr, 'set_time') else rr.set_time_seconds('boot', s)


def scalar(v):
    return rr.Scalars(v) if hasattr(rr, 'Scalars') else rr.Scalar(v)


def quat_xyzw(r, p, y):  # FRD roll/pitch/yaw in NED -> quaternion, rotating body into the NED world
    cr, sr, cp, sp, cy, sy = (f(a / 2) for a in (r, p, y) for f in (math.cos, math.sin))
    return [sr * cp * cy - cr * sp * sy, cr * sp * cy + sr * cp * sy,
            cr * cp * sy - sr * sp * cy, cr * cp * cy + sr * sp * sy]


m = connect(sys.argv[1])
web = int(sys.argv[2]) if len(sys.argv) > 2 else 9090
secs = float(sys.argv[3]) if len(sys.argv) > 3 else float('inf')
rr.init('px4-live')
url = rr.serve_grpc(server_memory_limit='1GiB')
rr.serve_web_viewer(web_port=web, open_browser=False, connect_to=url)
# The world is NED (x north, y east, z down) so positions are logged as PX4 reports them.
rr.log('world', rr.ViewCoordinates.RIGHT_HAND_Z_DOWN, static=True)
rr.log('world/drone/body', rr.Boxes3D(half_sizes=[[0.25, 0.25, 0.04]], colors=[[230, 120, 40]]), static=True)
rr.log('world/drone/body/nose', rr.Arrows3D(vectors=[[0.5, 0, 0]], colors=[[255, 40, 40]]), static=True)
print(f'rerun: http://localhost:{web} (MAVLink from {sys.argv[1]})', flush=True)
counts, fields, t0, last_hb, trail = {}, {}, time.time(), 0.0, []
try:
    while time.time() - t0 < secs:
        if time.time() - last_hb > 1:
            m.mav.heartbeat_send(6, 8, 0, 0, 0)  # a GCS heartbeat keeps PX4 streaming to this link
            last_hb = time.time()
        msg = m.recv_match(blocking=True, timeout=0.5)
        if msg is None or msg.get_type() == 'BAD_DATA':
            continue
        name, d = msg.get_type(), msg.to_dict()
        counts[name] = counts.get(name, 0) + 1
        # Vehicle boot time where the message has it, so the timeline is the sim's clock
        tb = d.get('time_boot_ms', d.get('time_usec', 0) / 1e3 if 'time_usec' in d else None)
        if tb is not None:
            set_t(tb / 1e3)
        # One multi-series entity per message type (its numeric fields, fixed at first sight): a log call per
        # field was ~5000 calls/s and starved a real-time SIH run enough to fail its hold check [S].
        if name not in fields:
            fields[name] = [k for k, v in d.items() if isinstance(v, (int, float)) and not isinstance(v, bool)
                            and k not in ('time_boot_ms', 'time_usec')]
            if fields[name] and hasattr(rr, 'SeriesLines'):
                rr.log(f'mavlink/{name}', rr.SeriesLines(names=fields[name]), static=True)
        if fields[name]:
            rr.log(f'mavlink/{name}', scalar([float(d.get(k, math.nan)) for k in fields[name]]))
        if name == 'LOCAL_POSITION_NED':
            p = [d['x'], d['y'], d['z']]
            rr.log('world/drone', rr.Transform3D(translation=p))
            trail = (trail + [p])[-600:]  # about 20 s at 30 Hz
            rr.log('world/trail', rr.LineStrips3D([trail], colors=[[60, 140, 255]]))
        elif name == 'ATTITUDE':
            rr.log('world/drone/body', rr.Transform3D(
                quaternion=rr.Quaternion(xyzw=quat_xyzw(d['roll'], d['pitch'], d['yaw']))))
except KeyboardInterrupt:
    pass
wall = time.time() - t0
top = sorted(counts.items(), key=lambda kv: -kv[1])[:8]
print(f'{len(counts)} message types; ' + ', '.join(f'{k} {v / wall:.0f} Hz' for k, v in top))
