#!/usr/bin/env python3
"""CI: merge every arms.json under DIR into one table (mean [min..max] per arm) as Markdown, plus all.json.

A record from a cloud job dir run-<scen>-<run> gets `run` (the run index = seed) and records are sorted by it,
so arms pair by seed. Every record gets `landed` (scenario.py's metrics.landed; null = no readable metrics.json), so a
must_land failure shows in all.json. Usage: collect.py DIR > summary.md
"""
import json
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
res, want = {}, {}


def run_index(f):
    for p in f.relative_to(root).parents:
        m = re.fullmatch(r'run-.+-(\d+)', p.name)
        if m:
            return int(m.group(1))
    return None


def landed(f, j, name, rec, k, n):
    """scenario.py's metrics.landed for one record: True/False, or None when its metrics.json is missing or unreadable.

    The record's flight folder is the last attempt of its arm and run (rc 2/3 = no run or infra retry, no record).
    Never raises: a bad file must not stop collect, or the publish step after it is skipped."""
    try:
        ok = [a for a in j.get('attempts', []) if a.get('arm') == name and a.get('rc') not in (2, 3)]
        if 'run' in rec:
            ok = [a for a in ok if a.get('run') == rec['run']][-1:]
        elif len(ok) == n:  # local multi-run file: one record per kept attempt, in run order
            ok = ok[k:k + 1]
        else:
            return None
        m = f.parent / ok[0]['dir'] / 'metrics.json'
        return bool(json.loads(m.read_text())['metrics'].get('landed', False)) if ok and m.is_file() else None
    except Exception:
        return None


for f in sorted(root.rglob('arms.json')):
    j = json.loads(f.read_text())
    i = run_index(f)
    for name, runs in j['results'].items():
        if i is not None and len(runs) == 1:
            runs[0]['run'] = i
        for k, m in enumerate(runs):  # arms.py writes it since 2026-11-04; older records get it from metrics.json
            if 'landed' not in m:
                m['landed'] = landed(f, j, name, m, k, len(runs))
        res.setdefault(name, []).extend(runs)
        want[name] = want.get(name, 0) + j['runs']  # intended runs: a lost job still counts against pass
for v in res.values():
    if all('run' in m for m in v):
        v.sort(key=lambda m: m['run'])
(root / 'all.json').write_text(json.dumps(res, indent=1))
keys = sorted({k for v in res.values() for m in v for k, x in m.items() if isinstance(x, float)})
print('| metric | ' + ' | '.join(res) + ' |')
print('|---|' + '---|' * len(res))
for k in keys:
    cells = []
    for n in res:
        v = [m[k] for m in res[n] if k in m]
        cells.append(f'{sum(v) / len(v):.3f} [{min(v):.3f}..{max(v):.3f}]' if v else '-')
    print(f'| {k} | ' + ' | '.join(cells) + ' |')
print('| pass | ' + ' | '.join(f'{sum(m["pass"] for m in v)}/{want[n]}' for n, v in res.items()) + ' |')
