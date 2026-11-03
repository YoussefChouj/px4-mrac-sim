#!/usr/bin/env python3
"""One-command experiment report: summary first, then full-rate synced plots, then a flight video.

Usage: report.py RUN_DIR [--no-video] [--fps N]   (video plays at 2x sim time)
RUN_DIR is a scenario output (metrics.json + flight.ulg) or a ladder output (ladder.json + one folder
per scenario). Writes RUN_DIR/report.html (and flight.mp4 next to it); for a ladder, one report per
scenario plus RUN_DIR/index.html. Plots use every ULog sample (no decimation), share one time axis
(seconds since boot, sim time) and carry markers for mode changes, takeoff/landing and parameter
changes, all taken from the ULog itself.
"""
import html
import json
import math
import os
import sys

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pyulog import ULog

TOPICS = ['vehicle_local_position', 'trajectory_setpoint', 'vehicle_attitude', 'vehicle_attitude_setpoint',
          'vehicle_angular_velocity', 'vehicle_rates_setpoint', 'actuator_motors', 'vehicle_status',
          'vehicle_land_detected']
NAV = {0: 'MANUAL', 2: 'POSCTL', 3: 'AUTO_MISSION', 4: 'AUTO_LOITER', 5: 'AUTO_RTL', 14: 'OFFBOARD',
       17: 'AUTO_TAKEOFF', 18: 'AUTO_LAND', 1: 'ALTCTL', 15: 'STAB'}


def euler(q0, q1, q2, q3):
    roll = np.degrees(np.arctan2(2 * (q0 * q1 + q2 * q3), 1 - 2 * (q1 ** 2 + q2 ** 2)))
    pitch = np.degrees(np.arcsin(np.clip(2 * (q0 * q2 - q3 * q1), -1, 1)))
    yaw = np.degrees(np.arctan2(2 * (q0 * q3 + q1 * q2), 1 - 2 * (q2 ** 2 + q3 ** 2)))
    return roll, pitch, yaw


def load(path):
    ulog = ULog(path, TOPICS)
    t0 = ulog.start_timestamp
    d = {}
    for ds in ulog.data_list:
        if ds.multi_id == 0:
            d[ds.name] = {k: v for k, v in ds.data.items()}
            d[ds.name]['t'] = (ds.data['timestamp'] - t0) / 1e6
    dur = (ulog.last_timestamp - t0) / 1e6
    rates = sorted(((ds.name, len(ds.data['timestamp']) / max(dur, 1e-6)) for ds in ulog.data_list
                    if ds.multi_id == 0), key=lambda r: -r[1])
    params = [((t - t0) / 1e6, n, v) for t, n, v in ulog.changed_parameters if t > t0]
    return d, dur, rates, params


def events(d, params):
    ev = []
    st = d.get('vehicle_status')
    if st is not None:
        prev = None
        for t, n in zip(st['t'], st['nav_state']):
            if n != prev:
                ev.append((t, NAV.get(int(n), f'nav {int(n)}'), '#888'))
                prev = n
    ld = d.get('vehicle_land_detected')
    if ld is not None:
        prev = None
        for t, l in zip(ld['t'], ld['landed']):
            if prev is not None and l != prev:
                ev.append((t, 'landed' if l else 'takeoff', '#2a9d8f'))
            prev = l
    ev += [(t, f'{n}={v:g}', '#e76f51') for t, n, v in params]
    return ev


def figure(d, ev):
    rows = [('Position N/E (m)', 'm'), ('Height (m)', 'm'), ('Velocity (m/s)', 'm/s'), ('Roll / pitch (deg)', 'deg'),
            ('Yaw (deg)', 'deg'), ('Body rates (deg/s)', 'deg/s'), ('Motor commands (0-1)', ''), ('Tracking error (m)', 'm')]
    fig = make_subplots(rows=len(rows), cols=1, shared_xaxes=True, vertical_spacing=0.012,
                        subplot_titles=[r[0] for r in rows])

    def line(r, t, y, name, dash=None, color=None):
        # A setpoint (dash given) is a wide translucent band: a dotted line in the same colour hides under the
        # flown trace whenever tracking is good.
        sp_style = dict(width=5, color=color) if dash else dict(width=1.2, color=color)
        fig.add_trace(go.Scattergl(x=t, y=y, name=name, mode='lines', legendgroup=str(r), line=sp_style,
                                   opacity=0.3 if dash else 1.0), row=r, col=1)
    lp, sp = d.get('vehicle_local_position'), d.get('trajectory_setpoint')
    if lp is not None:
        line(1, lp['t'], lp['x'], 'N', color='#1f77b4')
        line(1, lp['t'], lp['y'], 'E', color='#ff7f0e')
        line(2, lp['t'], -lp['z'], 'height', color='#2ca02c')
        for k, c in (('vx', '#1f77b4'), ('vy', '#ff7f0e'), ('vz', '#2ca02c')):
            line(3, lp['t'], lp[k], k, color=c)
    if sp is not None:
        line(1, sp['t'], sp['position[0]'], 'N sp', 'dot', '#1f77b4')
        line(1, sp['t'], sp['position[1]'], 'E sp', 'dot', '#ff7f0e')
        line(2, sp['t'], -sp['position[2]'], 'height sp', 'dot', '#2ca02c')
        if lp is not None:
            n = np.interp(sp['t'], lp['t'], lp['x'])
            e = np.interp(sp['t'], lp['t'], lp['y'])
            err = np.hypot(n - sp['position[0]'], e - sp['position[1]'])
            line(8, sp['t'], err, 'horizontal err', color='#d62728')
    att, asp = d.get('vehicle_attitude'), d.get('vehicle_attitude_setpoint')
    if att is not None:
        r_, p_, y_ = euler(*(att[f'q[{i}]'] for i in range(4)))
        line(4, att['t'], r_, 'roll', color='#9467bd')
        line(4, att['t'], p_, 'pitch', color='#8c564b')
        line(5, att['t'], y_, 'yaw', color='#17becf')
    if asp is not None:
        r_, p_, y_ = euler(*(asp[f'q_d[{i}]'] for i in range(4)))
        line(4, asp['t'], r_, 'roll sp', 'dot', '#9467bd')
        line(4, asp['t'], p_, 'pitch sp', 'dot', '#8c564b')
        line(5, asp['t'], y_, 'yaw sp', 'dot', '#17becf')
    av, rsp = d.get('vehicle_angular_velocity'), d.get('vehicle_rates_setpoint')
    for i, (k, c) in enumerate((('p', '#9467bd'), ('q', '#8c564b'), ('r', '#17becf'))):
        if av is not None:
            line(6, av['t'], np.degrees(av[f'xyz[{i}]']), k, color=c)
        if rsp is not None:
            line(6, rsp['t'], np.degrees(rsp[('roll', 'pitch', 'yaw')[i]]), k + ' sp', 'dot', c)
    am = d.get('actuator_motors')
    if am is not None:
        for i in range(12):
            y = am.get(f'control[{i}]')
            if y is not None and np.isfinite(y).any():
                line(7, am['t'], y, f'm{i + 1}')
    for t, label, color in ev:
        fig.add_vline(x=t, line=dict(color=color, width=1, dash='dash'))
        fig.add_annotation(x=t, y=1.0, yref='paper', text=label, showarrow=False, textangle=-90,
                           font=dict(size=9, color=color), xanchor='left', yanchor='top')
    fig.update_xaxes(showspikes=True, spikemode='across', spikethickness=1)
    fig.update_xaxes(title_text='sim time since boot (s)', row=len(rows), col=1)
    fig.update_layout(height=230 * len(rows), hovermode='x unified', template='plotly_dark',
                      paper_bgcolor='#000', plot_bgcolor='#000', margin=dict(l=60, r=20, t=40, b=40), legend=dict(groupclick='toggleitem'))
    return fig


def video(d, out, fps=20, speed=2.0):
    # Playback at `speed` x sim time: matplotlib 3D renders ~5 frames/s here, so 1x at 25 fps took
    # 12 min for a 140 s flight.
    import matplotlib
    matplotlib.use('Agg')
    import imageio_ffmpeg
    import matplotlib.pyplot as plt
    from matplotlib import animation
    matplotlib.rcParams['animation.ffmpeg_path'] = imageio_ffmpeg.get_ffmpeg_exe()
    lp, att, sp = d['vehicle_local_position'], d['vehicle_attitude'], d.get('trajectory_setpoint')
    t = np.arange(lp['t'][0], lp['t'][-1], speed / fps)
    n, e, h = (np.interp(t, lp['t'], lp[k]) for k in ('x', 'y', 'z'))
    h = -h
    q = [np.interp(t, att['t'], att[f'q[{i}]']) for i in range(4)]
    span = max(np.ptp(n), np.ptp(e), np.ptp(h), 4.0)
    arm = max(1.1, span * 0.04)
    fig = plt.figure(figsize=(8, 6), dpi=100)
    ax = fig.add_subplot(projection='3d')
    ax.set_xlim(e.mean() - span / 2 - arm, e.mean() + span / 2 + arm)
    ax.set_ylim(n.mean() - span / 2 - arm, n.mean() + span / 2 + arm)
    ax.set_zlim(0, max(h.max() + arm, 2))
    ax.set_xlabel('east (m)'), ax.set_ylabel('north (m)'), ax.set_zlabel('height (m)')
    if sp is not None:
        ok = np.isfinite(sp['position[0]'])
        ax.plot(sp['position[1]'][ok], sp['position[0]'][ok], -sp['position[2]'][ok], ':', color='gray', lw=0.8,
                label='setpoint')
    trail, = ax.plot([], [], [], color='#1f77b4', lw=1.2, label='path')
    arms = [ax.plot([], [], [], color=c, lw=2.5)[0] for c in ('#d62728', '#d62728', '#333', '#333')]
    txt = ax.text2D(0.02, 0.95, '', transform=ax.transAxes)
    ax.legend(loc='upper right')
    body = np.array([[1, 1, 0], [1, -1, 0], [-1, -1, 0], [-1, 1, 0]]) * arm / math.sqrt(2)  # FRD, front two red

    def frame(k):
        w, x, y, z = (qi[k] for qi in q)
        R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                      [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                      [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]])
        for a, b in zip(arms, body @ R.T):  # body FRD -> NED; plot axes are E, N, up
            a.set_data_3d([e[k], e[k] + b[1]], [n[k], n[k] + b[0]], [h[k], h[k] - b[2]])
        i0 = max(0, k - int(fps * 20 / speed))  # 20 s trail
        trail.set_data_3d(e[i0:k + 1], n[i0:k + 1], h[i0:k + 1])
        txt.set_text(f't = {t[k]:6.1f} s   height {h[k]:5.1f} m')
        return arms + [trail, txt]
    anim = animation.FuncAnimation(fig, frame, frames=len(t), blit=False)
    anim.save(out, writer=animation.FFMpegWriter(fps=fps, bitrate=2500))
    plt.close(fig)


def one(run, make_video=True, fps=20):
    m = json.load(open(os.path.join(run, 'metrics.json')))
    spec = m.get('spec', {})
    ulg = os.path.join(run, 'flight.ulg')
    head = [f'<h1>{html.escape(m["scenario"])}: <span class="{"ok" if m["pass"] else "bad"}">'
            f'{"PASS" if m["pass"] else "FAIL"}</span></h1>']
    if spec.get('expect'):
        head.append(f'<p><b>Expected:</b> {spec["expect"]}. {html.escape(spec.get("why", ""))}</p>')
    head.append('<table><tr><th>check</th></tr>' + ''.join(
        f'<tr><td class="{"ok" if c.startswith("PASS") else "bad"}">{html.escape(c)}</td></tr>'
        for c in m['checks']) + '</table>')
    head.append('<p>' + ', '.join(f'{k} <b>{v:.2f}</b>' for k, v in m['metrics'].items()
                                  if isinstance(v, float)) + '</p>')
    head.append('<details><summary>Scenario log</summary><pre>' + html.escape('\n'.join(
        str(e) for e in m.get('events', []))) + '</pre></details>')
    body = ''
    if os.path.exists(ulg):
        d, dur, rates, params = load(ulg)
        if make_video and 'vehicle_local_position' in d and 'vehicle_attitude' in d:
            video(d, os.path.join(run, 'flight.mp4'), fps)
        if os.path.exists(os.path.join(run, 'flight.mp4')):  # --no-video keeps a video rendered earlier
            head.append('<video src="flight.mp4" controls width="640"></video>')
        for f in sorted(os.listdir(run)):  # Gazebo cameras of a "video" gz run, gazebo-CAM.mp4, sim time
            if f.startswith('gazebo') and f.endswith('.mp4'):
                head.append(f'<video src="{f}" controls width="640" title="Gazebo camera {f[7:-4].strip("-")}, '
                            'sim time"></video>')
        body = figure(d, events(d, params)).to_html(full_html=False, include_plotlyjs=True)
        body += ('<h2>Logged topic rates (ULog, sim time)</h2><table><tr><th>topic</th><th>Hz</th></tr>'
                 + ''.join(f'<tr><td>{n}</td><td>{r:.0f}</td></tr>' for n, r in rates) + '</table>'
                 + f'<p>Log length {dur:.1f} s.</p>')
    else:
        body = '<p>No flight.ulg in this run (older scenario.py); only the summary is available.</p>'
    page = (f'<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(m["scenario"])}</title>'
            '<style>body{font:14px system-ui;margin:16px;max-width:1400px;background:#000;color:#ddd}a{color:#6cf}.ok{color:#2a9d8f}.bad{color:#d62728}'
            'td,th{padding:2px 8px;text-align:left}</style></head><body>' + ''.join(head) + body + '</body></html>')
    open(os.path.join(run, 'report.html'), 'w').write(page)
    return os.path.join(run, 'report.html')


def ladder(root, make_video, fps):
    rows = json.load(open(os.path.join(root, 'ladder.json')))
    out = ['<!doctype html><html><head><meta charset="utf-8"><title>Scenario ladder</title><style>'
           'body{font:14px system-ui;margin:16px;background:#000;color:#ddd}a{color:#6cf}.ok{color:#2a9d8f}.bad{color:#d62728}td,th{padding:3px 8px;'
           'text-align:left;vertical-align:top}</style></head><body><h1>Scenario ladder: '
           f'{sum(r["match"] for r in rows)}/{len(rows)} verdicts as predicted</h1><table><tr><th>scenario</th>'
           '<th>expect</th><th>got</th><th>as predicted</th><th>key metrics</th><th>prediction</th></tr>']
    for r in rows:
        link = r['name']
        if os.path.exists(os.path.join(r['dir'], 'metrics.json')):
            one(r['dir'], make_video, fps)
            link = f'<a href="{os.path.relpath(r["dir"], root)}/report.html">{r["name"]}</a>'
        out.append(f'<tr><td>{link}</td><td>{r["expect"]}</td><td>{r["got"]}</td>'
                   f'<td class="{"ok" if r["match"] else "bad"}">{"yes" if r["match"] else "NO"}</td><td>'
                   + ', '.join(f'{k} {v}' for k, v in r['metrics'].items()) + f'</td><td>{html.escape(r["why"])}</td></tr>')
    open(os.path.join(root, 'index.html'), 'w').write(''.join(out) + '</table></body></html>')
    return os.path.join(root, 'index.html')


if __name__ == '__main__':
    run = sys.argv[1]
    fps = int(sys.argv[sys.argv.index('--fps') + 1]) if '--fps' in sys.argv else 20
    vid = '--no-video' not in sys.argv
    print(ladder(run, vid, fps) if os.path.exists(os.path.join(run, 'ladder.json')) else one(run, vid, fps))
