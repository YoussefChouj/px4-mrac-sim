#!/usr/bin/env python3
"""Publication-quality figure of one dense-waypoint flight (scenario step 'dense') flown by 2-4 arms on the same seed.

Panels: (a) top-down path of each arm over the waypoint path, with a zoom on the slalom; (b) cross-track error vs
time (distance to the waypoint polyline, horizontal), laps shaded; (c) height error; (d) tilt with the gate.
The waypoints come from the flight folder's dense_path.csv (written by the step), the vehicle from the ULog
(vehicle_local_position), so the error is the estimator's position against the commanded path, as in the step's metric.
Usage: dense_plots.py OUT.png TITLE LABEL=FLIGHT_DIR [LABEL=FLIGHT_DIR ...] [--gate 45]
Writes OUT.png (300 dpi) and OUT.pdf.
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from pyulog import ULog

COL = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100']
ARM_COL = {'PX4': COL[0], 'old MRAC': COL[1], 'L1 + tilt': COL[2], 'L1 + budget': COL[3], 'L1 all loops': COL[3], 'L1 outer loops': COL[2]}
DASH = ['-', (0, (5, 2)), (0, (1.5, 1.5)), (0, (6, 2, 1.5, 2))]
INK, INK2, GRID, SURF = '#0b0b0b', '#52514e', '#e4e3df', '#fcfcfb'


def seg_dist(P, A, B):
    d = B - A
    t = np.clip(np.sum((P - A) * d, 1) / np.maximum(np.sum(d * d, 1), 1e-12), 0, 1)
    return np.linalg.norm(P - (A + d * t[:, None]), axis=1)


def load(d):
    d = Path(d)
    W = np.loadtxt(d / 'dense_path.csv', delimiter=',', skiprows=1)        # n, e, up
    u = ULog(str(d / 'flight.ulg'), ['vehicle_local_position', 'trajectory_setpoint', 'vehicle_attitude'])
    t = {x.name: x.data for x in u.data_list if x.multi_id == 0}
    lp, sp, at = t['vehicle_local_position'], t['trajectory_setpoint'], t['vehicle_attitude']
    # the dense step is where the setpoint carries a velocity feed-forward
    vs = np.hypot(np.nan_to_num(sp['velocity[0]']), np.nan_to_num(sp['velocity[1]']))
    on = sp['timestamp'][vs > 0.05] * 1e-6
    gap = np.where(np.diff(on) > 1.0)[0]                                    # stray later setpoints (return, land)
    t0, t1 = on[0], (on[gap[0]] if len(gap) else on[-1])
    T = lp['timestamp'] * 1e-6
    m = (T >= t0) & (T <= t1)
    P = np.stack([lp['x'][m], lp['y'][m], -lp['z'][m]], 1)
    A, B = W, np.roll(W, -1, 0)
    xt, zt = np.empty(len(P)), np.empty(len(P))
    for i, p in enumerate(P):
        k = np.argsort(np.hypot(*(W[:, :2] - p[:2]).T))[:6]                  # nearest waypoints, then their segments
        dd = seg_dist(np.repeat(p[None, :2], len(k), 0), A[k, :2], B[k, :2])
        j = k[np.argmin(dd)]
        xt[i], zt[i] = dd.min(), p[2] - W[j, 2]
    # lap boundary: the commanded waypoint returns to the start
    spn = sp['position[0]'][(sp['timestamp'] * 1e-6 >= t0) & (sp['timestamp'] * 1e-6 <= t1)]
    spe = sp['position[1]'][(sp['timestamp'] * 1e-6 >= t0) & (sp['timestamp'] * 1e-6 <= t1)]
    spt = sp['timestamp'][(sp['timestamp'] * 1e-6 >= t0) & (sp['timestamp'] * 1e-6 <= t1)] * 1e-6
    near = np.hypot(spn - W[0, 0], spe - W[0, 1]) < 0.3
    laps = spt[near & (spt > t0 + 10)]
    tlap = laps[0] - t0 if len(laps) else None
    q = np.stack([at[f'q[{i}]'] for i in range(4)], 1)
    Ta = at['timestamp'] * 1e-6
    ma = (Ta >= t0) & (Ta <= t1)
    tilt = np.degrees(np.arccos(np.clip(1 - 2 * (q[ma, 1] ** 2 + q[ma, 2] ** 2), -1, 1)))
    return dict(W=W, t=T[m] - t0, P=P, xt=xt, zt=zt, tlap=tlap, ta=Ta[ma] - t0, tilt=tilt, dur=t1 - t0)


def style(ax):
    ax.set_facecolor(SURF)
    ax.grid(True, color=GRID, lw=0.6)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'):
        ax.spines[s].set_color(INK2)
    ax.tick_params(colors=INK2, labelsize=8)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    gate = float(sys.argv[sys.argv.index('--gate') + 1]) if '--gate' in sys.argv else 45.0
    if '--gate' in sys.argv:
        args.remove(sys.argv[sys.argv.index('--gate') + 1])
    out, title, flights = Path(args[0]), args[1], [a.split('=', 1) for a in args[2:]]
    data = [(lab, load(p)) for lab, p in flights]
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.titlesize': 10, 'axes.labelsize': 9})
    fig = plt.figure(figsize=(12, 7.4), facecolor=SURF)
    gs = fig.add_gridspec(3, 3, width_ratios=[1, 0.62, 1.5], hspace=0.42, wspace=0.28)
    axp, axz = fig.add_subplot(gs[:, 0]), fig.add_subplot(gs[:, 1])
    axs = [fig.add_subplot(gs[i, 2]) for i in range(3)]
    for ax in axs[1:]:
        ax.sharex(axs[0])
    for ax in [axp, axz] + axs:
        style(ax)
    W = data[0][1]['W']
    for ax in (axp, axz):
        ax.plot(W[:, 1], W[:, 0], '.', ms=1.2, color=INK2, label='waypoints (5 cm apart)')
    for i, (lab, d) in enumerate(data):
        c, ls = next((v for k, v in ARM_COL.items() if lab.startswith(k)), COL[i]), DASH[i % 4]
        rms = np.sqrt(np.mean(d['xt'] ** 2))
        for ax in (axp, axz):
            ax.plot(d['P'][:, 1], d['P'][:, 0], color=c, lw=1.3, ls=ls,
                    label=f'{lab}: cross-track rms {100 * rms:.1f} cm, peak {100 * d["xt"].max():.1f} cm')
        axs[0].plot(d['t'], 100 * d['xt'], color=c, lw=1.2, ls=ls)
        axs[1].plot(d['t'], 100 * d['zt'], color=c, lw=1.2, ls=ls)
        axs[2].plot(d['ta'], d['tilt'], color=c, lw=1.0, ls=ls)
    tl = data[0][1]['tlap']
    for ax in axs:
        if tl:
            ax.axvspan(tl, data[0][1]['dur'], color=GRID, alpha=0.6, lw=0)
        ax.set_xlim(0, max(d['dur'] for _, d in data))
    if tl:
        axs[0].text(tl / 2, 0.97, 'lap 1, 1.5 m/s', transform=axs[0].get_xaxis_transform(), ha='center', va='top', fontsize=7.5, color=INK2)
        axs[0].text((tl + data[0][1]['dur']) / 2, 0.97, 'lap 2, 3 m/s', transform=axs[0].get_xaxis_transform(), ha='center', va='top', fontsize=7.5, color=INK2)
    axs[2].axhline(gate, color=INK2, lw=0.9, ls=(0, (4, 2)))
    axs[2].text(1, gate + 0.8, f'gate {gate:.0f} deg', fontsize=7.5, color=INK2)
    axp.set_aspect('equal', adjustable='datalim')
    axp.set_xlabel('east [m]')
    axp.set_ylabel('north [m]')
    axp.set_title('(a) path seen from above', loc='left', color=INK)
    axp.legend(loc='upper center', bbox_to_anchor=(0.5, -0.09), fontsize=7, frameon=True, facecolor=SURF, edgecolor=GRID)
    # zoom: the slalom's first bump
    sl = (W[:, 1] > 4)
    n_c = W[sl, 0][np.argmax(W[sl, 1])]
    axz.set_xlim(4.6, 7.6)
    axz.set_ylim(n_c - 2.2, n_c + 2.2)
    axz.set_aspect('equal', adjustable='box')
    axz.set_xlabel('east [m]')
    axz.set_title('(b) zoom, slalom', loc='left', color=INK)
    for ax, ttl, yl in zip(axs, ('(c) cross-track error', '(d) height error', '(e) tilt'), ('cm', 'cm', 'deg')):
        ax.set_title(ttl, loc='left', color=INK)
        ax.set_ylabel(yl)
    for ax in axs[:-1]:
        plt.setp(ax.get_xticklabels(), visible=False)
    axs[-1].set_xlabel('time since the path started [s, sim]')
    fig.text(0.01, -0.06, 'Same seed for every arm (same vehicle, wind and sensors). Cross-track error: horizontal distance '
             'from the estimated position to the polyline through the waypoints; the waypoints stream as offboard '
             'setpoints with a velocity feed-forward from their differences. Shaded: the fast lap.', fontsize=7.5, color=INK2)
    fig.suptitle(title, x=0.01, ha='left', fontsize=12, color=INK, weight='bold')
    fig.savefig(out, dpi=300, bbox_inches='tight', facecolor=SURF)
    fig.savefig(out.with_suffix('.pdf'), bbox_inches='tight', facecolor=SURF)
    print(out)


if __name__ == '__main__':
    main()
