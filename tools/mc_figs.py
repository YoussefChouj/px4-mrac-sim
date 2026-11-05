#!/usr/bin/env python3
"""Monte Carlo wave summary figure from a results folder's all.json (decks DECK-ARM, paired by `run`).

Left: per-seed paired change of METRIC for each arm vs the control arm, one dot per seed, with the median and a
bootstrap 95 % interval of the median; one panel per deck. Right: sensitivity, Spearman rank correlation between the
paired change of the TARGET arm and every drawn parameter (d_* fields), top 10 by |rho|, with the n-based 5 % level.
Usage: mc_figs.py RESULTS_DIR OUT.png TITLE --decks mc,mcf --control alone --arms mrac,l1r6,l1r6t --target l1r6t
       [--metric max_hold_err_m] [--labels alone=PX4 PID,mrac=old MRAC,...]
Writes OUT.png (300 dpi) and OUT.pdf.
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np

COL = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100']
# colour follows the arm (same in key_flight_plots.py): control blue, old MRAC orange, L1 aqua, L1 + tilt budget yellow
ARM_COL = {'alone': COL[0], 'mrac': COL[1], 'l1r6': COL[2], 'l1r6t': COL[3]}
INK, INK2, GRID, SURF = '#0b0b0b', '#52514e', '#e4e3df', '#fcfcfb'


def opt(name, dflt=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else dflt


def rank(x):
    o = np.argsort(x, kind='mergesort')
    r = np.empty(len(x))
    r[o] = np.arange(len(x))
    return r


def spearman(a, b):
    ra, rb = rank(a), rank(b)
    return float(np.corrcoef(ra, rb)[0, 1])


def main():
    res, out, title = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    decks = opt('--decks').split(',')
    ctl, arms, tgt = opt('--control', 'alone'), opt('--arms').split(','), opt('--target')
    metric = opt('--metric', 'max_hold_err_m')
    lab = dict(kv.split('=', 1) for kv in opt('--labels', '').split(',') if '=' in kv)
    d = json.loads((res / 'all.json').read_text())
    rng = np.random.default_rng(0)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9})
    fig = plt.figure(figsize=(12, 3.4 * len(decks) + 0.6), facecolor=SURF)
    gs = fig.add_gridspec(len(decks), 2, width_ratios=[1.5, 1], hspace=0.55, wspace=0.35)
    for r, deck in enumerate(decks):
        c = {x['run']: x for x in d[f'{deck}-{ctl}']}
        ax = fig.add_subplot(gs[r, 0])
        ax.set_facecolor(SURF)
        ax.grid(True, axis='y', color=GRID, lw=0.6)
        for s in ('top', 'right'):
            ax.spines[s].set_visible(False)
        ax.axhline(0, color=INK2, lw=0.9)
        for i, arm in enumerate(arms):
            t = {x['run']: x for x in d[f'{deck}-{arm}']}
            runs = sorted(k for k in t if k in c and np.isfinite(t[k].get(metric, np.nan)) and np.isfinite(c[k].get(metric, np.nan)))
            diff = np.array([t[k][metric] - c[k][metric] for k in runs])
            if not len(diff):
                continue
            x = i + rng.uniform(-0.18, 0.18, len(diff))
            ax.plot(x, diff, 'o', ms=4, mfc=ARM_COL.get(arm, COL[(i + 1) % 4]), mec=SURF, mew=0.6, alpha=0.9)
            med = np.median(diff)
            boots = np.median(rng.choice(diff, (4000, len(diff))), 1)
            lo, hi = np.percentile(boots, [2.5, 97.5])
            ax.plot([i - 0.3, i + 0.3], [med, med], color=INK, lw=1.8)
            ax.plot([i, i], [lo, hi], color=INK, lw=1.0)
            better = int(np.sum(diff < 0))
            npass = sum(bool(x.get('pass')) for x in t.values())
            ax.text(i, 1.02, f'median {med:+.2f} m\n[{lo:+.2f}, {hi:+.2f}]\nbetter in {better}/{len(diff)}'
                    f'\npasses gates {npass}/{len(t)}',
                    fontsize=7, color=INK, va='bottom', ha='center', transform=ax.get_xaxis_transform())
        ax.set_yscale('symlog', linthresh=1.0, linscale=1.5)
        ax.yaxis.set_major_locator(matplotlib.ticker.FixedLocator([-2, -1, -0.5, 0, 0.5, 1, 2, 5, 10, 50, 100]))
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f'{v:g}'))
        ax.set_xticks(range(len(arms)))
        ax.set_xticklabels([lab.get(a, a) for a in arms])
        ax.set_xlim(-0.5, len(arms) - 0.1)
        ax.set_ylabel(f'{metric} minus {lab.get(ctl, ctl)}\n(same seed; < 0 = better)', fontsize=8)
        ax.set_title(f'({chr(97 + 2 * r)}) {deck}: paired change per seed', loc='left', fontsize=10, color=INK, pad=44)
        # sensitivity of the target arm's paired change to the drawn parameters
        ax2 = fig.add_subplot(gs[r, 1])
        ax2.set_facecolor(SURF)
        for s in ('top', 'right'):
            ax2.spines[s].set_visible(False)
        t = {x['run']: x for x in d[f'{deck}-{tgt}']}
        runs = sorted(k for k in t if k in c and np.isfinite(t[k].get(metric, np.nan)) and np.isfinite(c[k].get(metric, np.nan)))
        diff = np.array([t[k][metric] - c[k][metric] for k in runs])
        keys = sorted({k for k in c[runs[0]] if k.startswith('d_')}) if runs else []
        rho = []
        for k in keys:
            v = np.array([c[r_].get(k, np.nan) for r_ in runs])
            if np.all(np.isfinite(v)) and np.ptp(v) > 0:
                rho.append((spearman(v, diff), k[2:]))
        rho = sorted(rho, key=lambda z: -abs(z[0]))[:10][::-1]
        y = np.arange(len(rho))
        ax2.barh(y, [z[0] for z in rho], color=ARM_COL.get(tgt, COL[0]), height=0.6)
        ax2.set_yticks(y)
        ax2.set_yticklabels([z[1] for z in rho], fontsize=7.5)
        lim = 1.96 / np.sqrt(max(len(runs) - 1, 1))
        for v in (-lim, lim):
            ax2.axvline(v, color=INK2, lw=0.8, ls=(0, (3, 2)))
        ax2.axvline(0, color=INK2, lw=0.8)
        ax2.set_xlim(-1, 1)
        ax2.set_xlabel(f'Spearman rho with the paired change ({lab.get(tgt, tgt)}); dashed = 5 % level', fontsize=8)
        ax2.set_title(f'({chr(98 + 2 * r)}) what drives the gain, {deck}', loc='left', fontsize=10, color=INK)
    fig.suptitle(title, x=0.01, ha='left', fontsize=12, color=INK, weight='bold')
    fig.text(0.01, -0.02, 'Each dot is one seed: the same drawn vehicle, sensors and scene flown by both arms. Bars: '
             'median and its bootstrap 95 % interval. Log-like axis beyond +-1. Sensitivity: rank correlation over '
             'seeds; negative rho = a larger parameter value goes with a larger improvement.', fontsize=7.5, color=INK2)
    fig.savefig(out, dpi=300, bbox_inches='tight', facecolor=SURF)
    fig.savefig(out.with_suffix('.pdf'), bbox_inches='tight', facecolor=SURF)
    print(out)


if __name__ == '__main__':
    main()
