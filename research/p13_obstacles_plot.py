# P13 obstacle figure: top-down tracks (east x, north y) over the obstacle footprints, drone radius as a halo;
# left = calm arms, right = windy runs. Usage: p13oplot.py CALM_DIR WIND_DIR OBST.json OUT.png
import csv, json, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
plt.style.use('dark_background')
calm, wind, ob, out = Path(sys.argv[1]), Path(sys.argv[2]), json.load(open(sys.argv[3])), sys.argv[4]
COL = {'pid-alone': '#4fc3f7', 'lqr-alone': '#ffb74d', 'lqr-plus-mrac': '#81c784'}
fig, axs = plt.subplots(1, 2, figsize=(16, 11))
for ax, root, title in ((axs[0], calm, 'calm'), (axs[1], wind, 'wind 1.5 m/s E + turbulence 0.5')):
    rr = ob['drone_radius_m']
    for o in ob['obstacles']:
        if o['kind'] == 'pole':
            ax.add_patch(Circle((o['e'], o['n']), o['r'], color='#ff7043'))
            ax.add_patch(Circle((o['e'], o['n']), o['r'] + rr, fill=False, ls=':', color='#ff7043'))
        else:
            ax.add_patch(Rectangle((o['e'] - o['de'] / 2, o['n'] - o['dn'] / 2), o['de'], o['dn'], color='#ff7043'))
        ax.text(o['e'] + 0.25, o['n'], o['name'], fontsize=8, color='#ffab91')
    rt = np.array(ob['route'])
    ax.plot(rt[:, 1], rt[:, 0], 'w+', ms=12, mew=2, label='route points')
    for d in sorted(root.glob('*')):
        if not (d / 'telemetry.csv').exists() or 'retry' in d.name:
            continue
        arm = next(a for a in COL if a in d.name)
        m = json.load(open(d / 'metrics.json'))
        r = np.array([[float(x) for x in row] for row in list(csv.reader(open(d / 'telemetry.csv')))[1:]])
        k = r[:, 3] > 0.3
        cl = m['metrics'].get('min_clearance_m', float('nan'))
        ax.plot(r[k, 2], r[k, 1], color=COL[arm], lw=1.2,
                label=f"{d.name.replace('p13-obst-', '')}: {'PASS' if m['pass'] else 'FAIL'}, min clearance {cl:.2f} m")
    ax.set_aspect('equal'); ax.set_xlim(-4, 4); ax.set_ylim(-1, 20); ax.grid(alpha=0.2)
    ax.set_xlabel('east m'); ax.set_ylabel('north m'); ax.set_title(f'P13 obstacle course, {title}')
    ax.legend(loc='lower left', fontsize=8)
fig.suptitle('dotted ring = pole radius + drone radius 0.21 m: a track inside it is a collision', fontsize=11)
fig.tight_layout(); fig.savefig(out, dpi=100, facecolor='black'); print('saved', out)
