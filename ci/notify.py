#!/usr/bin/env python3
"""CI: Markdown summary of one finished arms run - per-deck medians and the plus-mrac / alone track ratio.

Used as the issue comment of notify.yml (which prepends the @mention) and as summary.md on the results branch.
Reads meta.json next to ALL_JSON when present (wave label, branch, lost jobs, plan error, results folder).
Usage: notify.py ALL_JSON RUN_URL CONCLUSION > body.md
"""
import json
import math
import statistics
import sys
from pathlib import Path

path, url, concl = sys.argv[1:4]
p = Path(path)
mp = p.parent / 'meta.json'
meta = json.loads(mp.read_text()) if mp.exists() else {}
wave = f" wave **{meta['label']}** on `{meta.get('branch')}`" if meta.get('label') else ''
notes = []
if meta.get('error'):
    notes.append(f"Plan error: {meta['error']}")
if meta.get('build') == 'failure':
    notes.append('Build failed: see build-tail.log in the results folder.')
elif meta.get('lost'):
    notes.append(f"{len(meta['lost'])} job(s) reported nothing (infra, not a gate fail): " + ', '.join(meta['lost'][:20]))
if meta.get('results_url'):
    notes.append(f"Files: {meta['results_url']}")
if not p.exists():
    print('\n\n'.join([f'arms run {url}{wave} finished: **{concl}**, no all.json (the collect job failed or was '
                       'skipped).'] + notes))
    sys.exit()
d = json.loads(p.read_text())
COLS = [('rms_track_err_m', 'track rms m'), ('max_hold_err_m', 'hold max m'), ('max_tilt_deg', 'tilt max deg'),
        ('att_track_rms_deg', 'att rms deg')]


def med(recs, k):
    v = [r[k] for r in recs if isinstance(r.get(k), (int, float)) and math.isfinite(r[k])]
    return statistics.median(v) if v else None


def fmt(x):
    return '-' if x is None else f'{x:.3f}'


npass = sum(bool(r.get('pass')) for v in d.values() for r in v)
out = [f'arms run {url}{wave} finished: **{concl}**, {npass}/{sum(map(len, d.values()))} flights pass, '
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
        'divided by its alone deck, below 1 = MRAC better.']
for n in notes:
    out += ['', n]
print('\n'.join(out))
