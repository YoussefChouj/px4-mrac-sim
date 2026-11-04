# P13b A/B figure: one row per seed (same wind for every arm). Columns: commanded wind speed (sim s since the wind
# step), horizontal hold error and tilt (wall s since the wind step, telemetry.csv), top-down track around the hold
# point. Reference = mean position over the 1 s before the wind step. Usage: p13bplot.py ARMS_DIR OUT.png
import csv, json, re, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.style.use('dark_background')
root, out = Path(sys.argv[1]), sys.argv[2]
ARMS = [('pid-alone', '#4fc3f7'), ('lqr-alone', '#ffb74d'), ('lqr-plus-mrac', '#81c784')]
fig, ax = plt.subplots(3, 4, figsize=(20, 12), gridspec_kw={'width_ratios': [1, 1.6, 1.6, 1]})
for i, seed in enumerate((1, 2, 3)):
    for arm, col in ARMS:
        d = root / f'p13-wind-{arm}-{seed}'
        ev = json.load(open(d / 'metrics.json'))['events']
        tw = next(float(re.match(r'\s*([\d.]+)s', e).group(1)) for e in ev if 'hold 5 s' in e)
        r = np.array([[float(x) for x in row] for row in list(csv.reader(open(d / 'telemetry.csv')))[1:]])
        t = r[:, 0] - tw
        pre = (t > -1) & (t < 0)
        n0, e0 = r[pre, 1].mean(), r[pre, 2].mean()
        k = (t > -5) & (r[:, 3] > 2.5)
        err = np.hypot(r[:, 1] - n0, r[:, 2] - e0)
        tilt = np.degrees(np.arccos(np.cos(np.radians(r[:, 6])) * np.cos(np.radians(r[:, 7]))))
        ax[i, 1].plot(t[k], err[k], color=col, lw=1.3, label=arm)
        ax[i, 2].plot(t[k], tilt[k], color=col, lw=1.0, label=arm)
        ax[i, 3].plot(r[k, 2] - e0, r[k, 1] - n0, color=col, lw=0.9, label=arm)
        if arm == 'pid-alone':
            w = np.array([[float(x) for x in row[:3]] for row in list(csv.reader(open(d / 'wind.csv')))[1:]])
            ax[i, 0].plot(w[:, 0], np.hypot(w[:, 1], w[:, 2]), color='#e0e0e0', lw=0.8)
    ax[i, 0].set_ylabel(f'seed {seed}\nwind speed m/s')
    ax[i, 1].set_ylabel('hold error m')
    ax[i, 1].axhline(3, color='#e57373', ls='--', lw=0.8)
    ax[i, 2].set_ylabel('tilt deg')
    ax[i, 3].set_aspect('equal')
    ax[i, 3].set_ylabel('north m')
    for a in ax[i]:
        a.grid(alpha=0.2)
ax[0, 0].set_title('commanded wind (sim s since wind step)')
ax[0, 1].set_title('horizontal hold error (wall s since wind step; red = 3 m limit)')
ax[0, 2].set_title('tilt (wall s since wind step)')
ax[0, 3].set_title('top-down track around hold point')
ax[0, 1].legend(loc='upper left')
ax[2, 3].set_xlabel('east m')
fig.suptitle('P13b gz wind A/B: mean 2.2 m/s + turbulence sigma 0.8 + gusts +3 m/s E (20 s) / N (40 s), research drone, hold 3 m',
             fontsize=13)
fig.tight_layout()
fig.savefig(out, dpi=110, facecolor='black')
print('saved', out)
