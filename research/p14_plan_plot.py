# P14 figure: top view of the obstacle course (worlds/obstacles.json), obstacles inflated by drone radius + margin,
# the A* legs the deck logged (metrics['plan']) and the flown track per arm (telemetry.csv, in air).
# Usage: p14_plan_plot.py OBST.json OUT.png DIR (run dirs p14-plan-<arm>-*)
import csv, json, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle

plt.style.use('dark_background')
tab, out, root = json.load(open(sys.argv[1])), sys.argv[2], Path(sys.argv[3])
ARMS = [('pid-alone', '#4fc3f7'), ('lqr-alone', '#ffb74d'), ('lqr-plus-mrac', '#81c784')]
fig, ax = plt.subplots(figsize=(15, 7))
rad = tab.get('drone_radius_m', 0)
margin = None
for arm, col in ARMS:
    d = next((y for y in sorted(root.glob(f'p14-plan-{arm}-*'), reverse=True) if (y / 'metrics.json').exists()), None)
    if d is None:
        continue
    m = json.load(open(d / 'metrics.json'))
    margin = margin or next((s.get('margin') for s in json.load(open(d / 'scenario.json'))['steps'] if s['do'] == 'plan'), None) \
        if (d / 'scenario.json').exists() else margin
    r = np.array([[float(x) for x in row] for row in list(csv.reader(open(d / 'telemetry.csv')))[1:]])
    k = r[:, 3] > 0.3
    mm = m['metrics']
    ax.plot(r[k, 1], r[k, 2], color=col, lw=1.6,
            label=f'{arm} flown (clearance {mm.get("min_clearance_m", float("nan")):.2f} m, pass {m.get("pass")})')
    for legs in mm.get('plan', []):
        p = np.array([[0, 0]] + legs)
        ax.plot(p[:, 0], p[:, 1], '--o', color=col, lw=0.8, ms=4, alpha=0.7)
need = rad + (margin if margin is not None else 0.3)
for o in tab['obstacles']:
    if o['kind'] == 'pole':
        ax.add_patch(Circle((o['n'], o['e']), o['r'], color='#bdbdbd'))
        ax.add_patch(Circle((o['n'], o['e']), o['r'] + need, fill=False, ls=':', color='#e57373'))
    else:
        ax.add_patch(Rectangle((o['n'] - o['dn'] / 2, o['e'] - o['de'] / 2), o['dn'], o['de'], color='#bdbdbd'))
        ax.add_patch(Rectangle((o['n'] - o['dn'] / 2 - need, o['e'] - o['de'] / 2 - need), o['dn'] + 2 * need,
                               o['de'] + 2 * need, fill=False, ls=':', color='#e57373'))
ax.set_aspect('equal')
ax.set_xlabel('north m')
ax.set_ylabel('east m')
ax.grid(alpha=0.2)
ax.legend(loc='upper left', fontsize=9)
ax.set_title(f'P14 known-map A* planner on the P13 course: dashed = planned legs, red dotted = keep-out '
             f'(drone radius {rad} m + margin), solid = flown')
fig.tight_layout()
fig.savefig(out, dpi=110, facecolor='black')
print('saved', out)
