#!/usr/bin/env python3
"""ULog -> Rerun recording (.rrd) for one run: scrub the whole flight on one sim-time axis.

Usage: rrd.py RUN_DIR... (each holds flight.ulg; writes RUN_DIR/flight.rrd). Open with `rerun FILE.rrd`.
3D view: the preset path (trajectory_setpoint, orange) and the whole flown path (blue) are both static, so
the trail persists at every scrub position; the drone box moves along it. Plots: position/height vs
setpoint, attitude vs setpoint, body rates vs setpoint, motors, MRAC u_ad/theta per layer. Events (nav
mode, takeoff/landing, parameter changes, as in report.py) go to a text log on the same time axis.
"""
import os
import sys

import numpy as np
import rerun as rr

import report

report.TOPICS += ['mrac_rate_status', 'mrac_att_status', 'mrac_pos_status', 'mrac_xy_status']
T = 'sim'


def col(path, t, y):
    ok = np.isfinite(y)
    if ok.any():
        rr.send_columns(path, indexes=[rr.TimeColumn(T, duration=t[ok])],
                        columns=rr.Scalars.columns(scalars=np.asarray(y, float)[ok]))


def path_xyz(s, x='x', y='y', z='z'):
    p = np.column_stack([s[x], s[y], s[z]]).astype(float)
    return p[np.isfinite(p).all(axis=1)]


def one(run):
    d, dur, _, params = report.load(os.path.join(run, 'flight.ulg'))
    out = os.path.join(run, 'flight.rrd')
    rr.init(os.path.basename(os.path.normpath(run)), spawn=False)
    rr.save(out)
    rr.log('world', rr.ViewCoordinates.RIGHT_HAND_Z_DOWN, static=True)
    rr.log('world/drone/body', rr.Boxes3D(half_sizes=[[0.25, 0.25, 0.04]], colors=[[230, 120, 40]]), static=True)
    rr.log('world/drone/body/nose', rr.Arrows3D(vectors=[[0.5, 0, 0]], colors=[[255, 40, 40]]), static=True)
    lp, sp = d.get('vehicle_local_position'), d.get('trajectory_setpoint')
    if sp is not None:
        p = path_xyz(sp, 'position[0]', 'position[1]', 'position[2]')
        if len(p) > 1:
            rr.log('world/preset_path', rr.LineStrips3D([p], colors=[[255, 160, 40]], radii=0.02), static=True)
    if lp is not None:
        rr.log('world/flown_path', rr.LineStrips3D([path_xyz(lp)], colors=[[60, 140, 255]], radii=0.015), static=True)
        att = d.get('vehicle_attitude')
        t = lp['t']
        q = np.tile([0.0, 0.0, 0.0, 1.0], (len(t), 1))
        if att is not None:  # PX4 q is wxyz; rerun wants xyzw, sampled at the position times
            for i, k in enumerate((1, 2, 3, 0)):
                q[:, i] = np.interp(t, att['t'], att[f'q[{k}]'])
        rr.send_columns('world/drone', indexes=[rr.TimeColumn(T, duration=t)],
                        columns=rr.Transform3D.columns(translation=np.nan_to_num(
                            np.column_stack([lp['x'], lp['y'], lp['z']]).astype(float)), quaternion=q))
        for k in ('x', 'y', 'z', 'vx', 'vy', 'vz'):
            col(f'plots/pos/{k}', t, lp[k])
    if sp is not None:
        for i, k in enumerate('xyz'):
            col(f'plots/pos/{k}_sp', sp['t'], sp[f'position[{i}]'])
    for topic, tag in (('vehicle_attitude', ''), ('vehicle_attitude_setpoint', '_sp')):
        a = d.get(topic)
        if a is not None:
            qk = 'q' if topic == 'vehicle_attitude' else 'q_d'
            for n, v in zip(('roll', 'pitch', 'yaw'), report.euler(*(a[f'{qk}[{i}]'] for i in range(4)))):
                col(f'plots/att_deg/{n}{tag}', a['t'], v)
    w, ws = d.get('vehicle_angular_velocity'), d.get('vehicle_rates_setpoint')
    for i, n in enumerate(('p', 'q', 'r')):
        if w is not None:
            col(f'plots/rates/{n}', w['t'], w[f'xyz[{i}]'])
        if ws is not None:
            col(f'plots/rates/{n}_sp', ws['t'], ws[('roll', 'pitch', 'yaw')[i]])
    m = d.get('actuator_motors')
    if m is not None:
        for i in range(4):
            col(f'plots/motors/m{i}', m['t'], m[f'control[{i}]'])
    for topic in ('mrac_rate_status', 'mrac_att_status', 'mrac_pos_status', 'mrac_xy_status'):
        s = d.get(topic)
        if s is not None:
            L = topic.split('_')[1]
            for i in range(3):
                col(f'plots/mrac_{L}/u_ad{i}', s['t'], s[f'u_ad[{i}]'])
                col(f'plots/mrac_{L}/e{i}', s['t'], s[f'e[{i}]'])
    for t, txt, _ in report.events(d, params):
        t = float(t)
        if not 0 <= t <= dur:  # report.events keeps everything; a bad stamp would overflow the timeline
            continue
        rr.set_time(T, duration=t)
        rr.log('events', rr.TextLog(txt))
    rr.disconnect() if hasattr(rr, 'disconnect') else None
    return out


if __name__ == '__main__':
    for r in sys.argv[1:]:
        print(one(r), f'{os.path.getsize(os.path.join(r, "flight.rrd")) / 1e6:.1f} MB')
