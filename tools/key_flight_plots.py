#!/usr/bin/env python3
"""Publication-quality figure of one key flight flown by 2-3 arms on the same seed (paired), from their ULogs.

Panels (shared time axis, t = 0 at takeoff): (a) top-down path vs the setpoint path, (b) horizontal position error,
(c) altitude error, (d) tilt with the gate, (e) highest motor command (saturation). Mission events come from the
ULog's changed parameters (payload SIH_MASS, motor fault SIH_MOT1_EFF, gust = the largest SIH_WIND_E step, battery
sag SIH_T_MAX), so they are where the sim applied them, not where the script asked. Colours: validated categorical
slots 1-3 (dataviz palette), each line also dashed differently and direct-labelled.
Usage: key_flight_plots.py OUT.png TITLE LABEL=FLIGHT.ulg LABEL=FLIGHT.ulg [LABEL=FLIGHT.ulg] [--gate 45]
Writes OUT.png (300 dpi) and OUT.pdf.
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from pyulog import ULog

COL = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100']  # categorical slots 1-4, validated (light surface #fcfcfb)
# colour follows the arm, as in mc_figs.py; a label starting with the key picks it, else the slot order
ARM_COL = {'PX4': COL[0], 'old MRAC': COL[1], 'L1 roles': COL[2], 'L1 +': COL[3]}
DASH = ['-', (0, (5, 2)), (0, (1.5, 1.5))]
INK, INK2, GRID, SURF = '#0b0b0b', '#52514e', '#e4e3df', '#fcfcfb'
TOPICS = ['vehicle_local_position', 'trajectory_setpoint', 'vehicle_attitude', 'actuator_motors', 'vehicle_land_detected',
          'vehicle_status']


TO_END = '--to-end' in sys.argv  # plot past the land command (to show behaviour on the ground)


def load(path):
    u = ULog(str(path), TOPICS)
    t = {d.name: d.data for d in u.data_list if d.multi_id == 0}
    ld = t['vehicle_land_detected']
    air = ld['timestamp'][~ld['landed'].astype(bool)]
    t0 = (air[0] if len(air) else ld['timestamp'][0]) * 1e-6
    lp, sp = t['vehicle_local_position'], t['trajectory_setpoint']
    ts = lp['timestamp'] * 1e-6 - t0
    spt = sp['timestamp'] * 1e-6 - t0
    # setpoint between its samples: linear while it moves (track), held across a jump of > 2 m (a goto is a step)
    ix = np.clip(np.searchsorted(spt, ts, side='right') - 1, 0, len(spt) - 2)
    P = np.stack([sp['position[0]'], sp['position[1]'], sp['position[2]']], 1)
    a, b = P[ix], P[ix + 1]
    w = np.clip((ts - spt[ix]) / np.maximum(spt[ix + 1] - spt[ix], 1e-6), 0, 1)[:, None]
    far = (np.linalg.norm(b[:, :2] - a[:, :2], axis=1) > 2.0)[:, None]
    S = np.where(far, a, a + w * (b - a))
    S[ts < spt[0]] = np.nan
    spx, spy, spz = S[:, 0], S[:, 1], S[:, 2]
    at = t['vehicle_attitude']
    q = np.stack([at[f'q[{i}]'] for i in range(4)], 1)
    tilt = np.degrees(np.arccos(np.clip(1 - 2 * (q[:, 1] ** 2 + q[:, 2] ** 2), -1, 1)))
    am = t['actuator_motors']
    mot = np.max(np.stack([am[f'control[{i}]'] for i in range(4)], 1), 1)
    ev = []
    wind = [(ts_ * 1e-6 - t0, v) for ts_, n, v in u.changed_parameters if n == 'SIH_WIND_E']
    if len(wind) > 1:
        steps = [(abs(wind[i][1] - wind[i - 1][1]), wind[i][0]) for i in range(1, len(wind))]
        ev.append((max(steps)[1], 'gust'))
    for ts_, n, v in u.changed_parameters:
        tt = ts_ * 1e-6 - t0
        if tt <= 0:
            continue
        if n == 'SIH_MASS':
            ev.append((tt, 'payload'))
        elif n == 'SIH_MOT1_EFF' and v < 0.9:
            ev.append((tt, 'motor fault'))
        elif n == 'SIH_T_MAX':
            ev.append((tt, 'battery sag'))
    st = t['vehicle_status']
    tl = st['timestamp'][st['nav_state'] == 18] * 1e-6 - t0          # AUTO_LAND
    has_land = bool(np.any(tl > 5))
    t_land = tl[tl > 5][0] if has_land else ts[-1]
    t_end = min(ts[-1], t_land + 60.0) if TO_END else t_land   # 60 s on the ground is enough to see it
    if TO_END:
        ev.append((t_land, 'land command'))
    keep = (ts >= -1) & (ts <= t_end)
    first = {}
    for a, b in sorted(ev):                                           # one mark per event, inside the flight
        if 0 < a < t_end + 1 and b not in first:
            first[b] = a
    # goto transits: the setpoint jumps to a far target; that error is distance to go, not tracking error
    t_, ex, ey = ts[keep], (lp['x'] - spx)[keep], (lp['y'] - spy)[keep]
    eh = np.hypot(ex, ey)
    jump = np.hypot(np.diff(spx[keep], prepend=np.nan), np.diff(spy[keep], prepend=np.nan)) > 2.0
    transit = np.zeros(len(t_), bool)
    for j in np.flatnonzero(jump):
        k = j
        while k < len(t_) and (eh[k] > 0.5 or t_[k] - t_[j] < 1.0) and t_[k] - t_[j] < 20:
            k += 1
        transit[j:k] = True
    transit = transit | (t_ > t_land)   # after the land command the setpoint descends into the ground: not tracking
    return dict(has_land=has_land, t_land=t_land, t=t_, x=lp['x'][keep], y=lp['y'][keep], z=lp['z'][keep], spx=spx[keep], spy=spy[keep],
                spz=spz[keep], tt=at['timestamp'] * 1e-6 - t0, tilt=tilt, tm=am['timestamp'] * 1e-6 - t0, mot=mot,
                ev=sorted((a, b) for b, a in first.items()), t_end=t_end, transit=transit)


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
    fig = plt.figure(figsize=(12, 7.2), facecolor=SURF)
    gs = fig.add_gridspec(4, 2, width_ratios=[1, 1.55], hspace=0.38, wspace=0.18)
    axp = fig.add_subplot(gs[:, 0])
    axs = [fig.add_subplot(gs[i, 1]) for i in range(4)]
    for ax in axs[1:]:
        ax.sharex(axs[0])
    for ax in [axp] + axs:
        style(ax)
    d0 = data[0][1]
    axp.plot(d0['spy'], d0['spx'], color=INK2, lw=1.0, ls=(0, (1, 2)), label='setpoint path')
    # the axis follows the first (control) arm; an arm that lasts much longer is cut and says so in the legend
    t_end = data[0][1]['t_end']
    for i, (lab, d) in enumerate(data):
        c, ls = next((v for k, v in ARM_COL.items() if lab.startswith(k)), COL[i]), DASH[i]
        eh = np.where(d['transit'], np.nan, np.hypot(d['x'] - d['spx'], d['y'] - d['spy']))
        note = '' if d['t_end'] <= t_end + 10 else f' (cut: its flight ran to {d["t_end"]:.0f} s)'
        axp.plot(d['y'], d['x'], color=c, lw=1.6, ls=ls,
                 label=f'{lab}: error rms {np.sqrt(np.nanmean(eh ** 2)):.2f} m, peak {np.nanmax(eh):.2f} m{note}')
        ez = np.where(d['transit'], np.nan, -(d['z'] - d['spz']))
        axs[0].plot(d['t'], eh, color=c, lw=1.4, ls=ls)
        axs[1].plot(d['t'], ez, color=c, lw=1.4, ls=ls)
        axs[2].plot(d['tt'], d['tilt'], color=c, lw=1.2, ls=ls)
        axs[3].plot(d['tm'], d['mot'], color=c, lw=1.0, ls=ls)
        k = np.nanargmax(eh)  # mark each arm's own peak error
        axs[0].plot(d['t'][k], eh[k], 'o', ms=4, mfc=SURF, mec=c, mew=1.2)
    axs[2].axhline(gate, color=INK2, lw=0.9, ls=(0, (4, 2)))
    axs[2].text(1, gate + 1, f'gate {gate:.0f} deg', fontsize=7.5, color=INK2)
    axs[3].axhline(1.0, color=INK2, lw=0.9, ls=(0, (4, 2)))
    spans = []
    for _, d in data:   # every arm's own transits (arms reach each step at slightly different times)
        tr = d['transit']
        edges = np.flatnonzero(np.diff(np.r_[0, tr.astype(int), 0]))
        spans += [(d['t'][a], d['t'][min(b, len(tr)) - 1]) for a, b in zip(edges[::2], edges[1::2])]
    for ax in axs:
        for te, name in d0['ev']:
            ax.axvline(te, color=INK2, lw=0.7, alpha=0.6)
        for a, b in spans:
            ax.axvspan(a, b, color=GRID, alpha=0.7, lw=0)
        ax.set_xlim(-1, t_end + 1)
    top = axs[0].get_ylim()[1]
    for te, name in d0['ev']:
        axs[0].text(te + 0.6, top * 0.97, name, fontsize=7, color=INK2, va='top', rotation=90)
    axp.set_aspect('equal', adjustable='datalim')
    axp.set_xlabel('east [m]')
    axp.set_ylabel('north [m]')
    axp.set_title('(a) path seen from above', loc='left', color=INK)
    axp.legend(loc='lower left', fontsize=7, frameon=True, facecolor=SURF, edgecolor=GRID, framealpha=0.95)
    for ax, ttl, yl in zip(axs, ('(b) horizontal position error', '(c) altitude error', '(d) tilt',
                                 '(e) highest motor command'), ('m', 'm', 'deg', '0-1')):
        ax.set_title(ttl, loc='left', color=INK)
        ax.set_ylabel(yl)
    for ax in axs[:-1]:
        plt.setp(ax.get_xticklabels(), visible=False)
    axs[-1].set_xlabel('time since takeoff [s, sim]')
    fig.text(0.01, -0.03, 'Same seed for every arm (same wind, vehicle and events). Grey bands: goto transits, where the '
             'error is the distance still to fly, not tracking error; they are left out of (b) and (c). Vertical lines: '
             'mission events as applied in the sim. ' + ('The plot runs to the end of the log.' if TO_END else 'The plot ends at the land command.'), fontsize=7.5, color=INK2)
    fig.suptitle(title, x=0.01, ha='left', fontsize=12, color=INK, weight='bold')
    fig.savefig(out, dpi=300, bbox_inches='tight', facecolor=SURF)
    fig.savefig(out.with_suffix('.pdf'), bbox_inches='tight', facecolor=SURF)
    print(out)


if __name__ == '__main__':
    main()
