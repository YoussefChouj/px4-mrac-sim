#!/usr/bin/env python3
"""CI: merge every arms.json under DIR into one table (mean [min..max] per arm) as Markdown, plus all.json.

A record from a cloud job dir run-<scen>-<run> gets `run` (the run index = seed) and records are sorted by it,
so arms pair by seed. Usage: collect.py DIR > summary.md
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


for f in sorted(root.rglob('arms.json')):
    j = json.loads(f.read_text())
    i = run_index(f)
    for name, runs in j['results'].items():
        if i is not None and len(runs) == 1:
            runs[0]['run'] = i
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
