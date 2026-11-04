# P16 part 3 figure: SIH wind A/B, one row per seed (same turbulence for every arm). Columns: horizontal hold error and
# tilt vs wall s since the wind step (telemetry.csv; speed 5, so 1 wall s = 5 sim s). Reference = mean position over the
# 0.5 wall s before the wind. Usage: p16_sihwind_plot.py OUT.png DIR [DIR...] (later dirs win for the same run name)
import csv, json, re, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.style.use('dark_background')
out, dirs = sys.argv[1], [Path(d) for d in sys.argv[2:]]
ARMS = [('pid-alone', '#4fc3f7'), ('pid-tuned', '#e57373'), ('lqr-alone', '#ffb74d'), ('lqr-plus-mrac', '#81c784')]
fig, ax = plt.subplots(3, 2, figsize=(16, 11), sharex=True)
for i, seed in enumerate((1, 2, 3)):
    for arm, col in ARMS:
        # a flown run (wind param event logged); retries are named RUN-retryN
        d = next((y for x in reversed(dirs) for y in sorted(x.glob(f'p16-sihwind-{arm}-{seed}*'), reverse=True)
                  if (y / 'metrics.json').exists() and 'SIH_WIND_E' in (y / 'metrics.json').read_text()), None)
        if d is None:
            continue
        ev = json.load(open(d / 'metrics.json'))['events']
        tw = next(float(re.match(r'\s*([\d.]+)s', e).group(1)) for e in ev if 'SIH_WIND_E' in e)
        r = np.array([[float(x) for x in row] for row in list(csv.reader(open(d / 'telemetry.csv')))[1:]])
        t = r[:, 0] - tw
        pre = (t > -0.5) & (t < 0)
        n0, e0 = r[pre, 1].mean(), r[pre, 2].mean()
        k = (t > -1) & (r[:, 3] > 2.5)
        tilt = np.degrees(np.arccos(np.cos(np.radians(r[:, 6])) * np.cos(np.radians(r[:, 7]))))
        ax[i, 0].plot(t[k], np.hypot(r[k, 1] - n0, r[k, 2] - e0), color=col, lw=1.3, label=arm)
        ax[i, 1].plot(t[k], tilt[k], color=col, lw=1.0, label=arm)
    ax[i, 0].set_ylabel(f'seed {seed}\nhold error m')
    ax[i, 1].set_ylabel('tilt deg')
    for a in ax[i]:
        a.grid(alpha=0.2)
        a.axvspan(4.0, 5.6, color='#ffffff', alpha=0.07)  # E 5 m/s gust: sim 20..28 s after the wind step
ax[0, 0].set_title('horizontal hold error (shaded = 5 m/s east gust)')
ax[0, 1].set_title('tilt')
ax[0, 0].legend(loc='upper left')
ax[2, 0].set_xlabel('wall s since wind step (speed 5)')
ax[2, 1].set_xlabel('wall s since wind step (speed 5)')
fig.suptitle('P16 SIH wind A/B: N 1 / E 2 m/s + turbulence sigma 0.8, gust E 5 m/s, drag 0.455 1/s, research drone, hold 3 m',
             fontsize=13)
fig.tight_layout()
fig.savefig(out, dpi=110, facecolor='black')
print('saved', out)
