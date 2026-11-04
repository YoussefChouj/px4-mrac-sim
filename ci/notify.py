#!/usr/bin/env python3
"""CI: one Markdown comment per finished arms run - per-deck medians and the plus-mrac / alone track ratio.

Usage: notify.py ALL_JSON RUN_URL CONCLUSION > body.md
"""
import json
import math
import statistics
import sys
from pathlib import Path

path, url, concl = sys.argv[1:4]
if not Path(path).exists():
    print(f'@YoussefChouj arms run {url} finished: **{concl}**, no all.json (the collect job failed or was skipped).')
    sys.exit()
d = json.loads(Path(path).read_text())
COLS = [('rms_track_err_m', 'track rms m'), ('max_hold_err_m', 'hold max m'), ('max_tilt_deg', 'tilt max deg'),
        ('att_track_rms_deg', 'att rms deg')]


def med(recs, k):
    v = [r[k] for r in recs if isinstance(r.get(k), (int, float)) and math.isfinite(r[k])]
    return statistics.median(v) if v else None


def fmt(x):
    return '-' if x is None else f'{x:.3f}'


npass = sum(bool(r.get('pass')) for v in d.values() for r in v)
out = [f'@YoussefChouj arms run {url} finished: **{concl}**, {npass}/{sum(map(len, d.values()))} flights pass, '
       f'{len(d)} decks.', '',
       '| deck | n | pass | ' + ' | '.join(c[1] for c in COLS) + ' | track vs alone |', '|---' * (len(COLS) + 4) + '|']
for name, recs in d.items():
    m = [med(recs, k) for k, _ in COLS]
    alone, ratio = name.replace('plus-mrac', 'alone'), ''
    base = med(d[alone], COLS[0][0]) if alone != name and alone in d else None
    if base and m[0] is not None:
        ratio = f'{m[0] / base:.2f}x'
    out.append(f'| {name} | {len(recs)} | {sum(bool(r.get("pass")) for r in recs)} | '
               + ' | '.join(map(fmt, m)) + f' | {ratio} |')
out += ['', 'Medians over runs (n = flights that reported). "track vs alone": median track rms of a plus-mrac deck '
        'divided by its alone deck, below 1 = MRAC better. Raw: the run\'s `all` artifact.']
print('\n'.join(out))
