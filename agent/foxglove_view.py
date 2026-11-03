#!/usr/bin/env python3
"""Live MAVLink -> Foxglove WebSocket: every message type becomes a topic /mavlink/<NAME>.

Usage: foxglove_view.py TARGET [PORT] [SECONDS]. TARGET is a SITL instance 0..8 or a pymavlink URL
(same as mavlink_cli, so a real board works unchanged). Open Foxglove on Windows and connect to
ws://localhost:PORT (default 8765). Nothing is decimated: each message is forwarded as it arrives.
SECONDS (default: run until Ctrl+C) stops it and prints per-topic rates, used as the self-test.
It holds the instance's GCS port, so `px4ctl param|watch` on the same instance waits until it stops.
"""
import math
import sys
import time

import foxglove
from foxglove.messages import FrameTransform, Quaternion, Vector3

from mavlink_cli import connect


def quat_rpy(r, p, y):
    cr, sr, cp, sp, cy, sy = (f(a / 2) for a in (r, p, y) for f in (math.cos, math.sin))
    return Quaternion(x=sr * cp * cy - cr * sp * sy, y=cr * sp * cy + sr * cp * sy,
                      z=cr * cp * sy - sr * sp * cy, w=cr * cp * cy + sr * sp * sy)


# The 3D panel needs a typed pose: /tf carries world -> base_link in ENU/FLU, built from
# LOCAL_POSITION_NED and ATTITUDE (NED/FRD), so the vehicle shows as a moving frame.
pos, att = (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)

m = connect(sys.argv[1])
port = int(sys.argv[2]) if len(sys.argv) > 2 else 8765
secs = float(sys.argv[3]) if len(sys.argv) > 3 else float('inf')
server = foxglove.start_server(host='0.0.0.0', port=port)
print(f'foxglove: ws://localhost:{port} (MAVLink from {sys.argv[1]})', flush=True)
channels, counts, t0, last_hb = {}, {}, time.time(), 0.0
try:
    while time.time() - t0 < secs:
        if time.time() - last_hb > 1:
            # A GCS heartbeat keeps PX4 streaming to this link.
            m.mav.heartbeat_send(6, 8, 0, 0, 0)
            last_hb = time.time()
        msg = m.recv_match(blocking=True, timeout=0.5)
        if msg is None or msg.get_type() == 'BAD_DATA':
            continue
        name = msg.get_type()
        if name not in channels:
            channels[name] = foxglove.Channel(f'/mavlink/{name}', message_encoding='json')
        d = msg.to_dict()
        d.pop('mavpackettype', None)
        channels[name].log({k: (list(v) if isinstance(v, (bytes, bytearray)) else v) for k, v in d.items()})
        counts[name] = counts.get(name, 0) + 1
        if name in ('LOCAL_POSITION_NED', 'ATTITUDE'):
            if name == 'LOCAL_POSITION_NED':
                pos = (d['y'], d['x'], -d['z'])
            else:
                att = (d['roll'], -d['pitch'], math.pi / 2 - d['yaw'])
            foxglove.log('/tf', FrameTransform(parent_frame_id='world', child_frame_id='base_link',
                                               translation=Vector3(x=pos[0], y=pos[1], z=pos[2]),
                                               rotation=quat_rpy(*att)))
except KeyboardInterrupt:
    pass
wall = time.time() - t0
server.stop()
top = sorted(counts.items(), key=lambda kv: -kv[1])[:8]
print(f'{len(channels)} topics; ' + ', '.join(f'{k} {v / wall:.0f} Hz' for k, v in top))
