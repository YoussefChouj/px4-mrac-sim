#!/usr/bin/env python3
"""CI: merge every arms.json under DIR into one table (mean [min..max] per arm) as Markdown, plus all.json.

Usage: collect.py DIR > summary.md
"""
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
res, want = {}, {}
for f in sorted(root.rglob('arms.json')):
    j = json.loads(f.read_text())
    for name, runs in j['results'].items():
        res.setdefault(name, []).extend(runs)
        want[name] = want.get(name, 0) + j['runs']  # intended runs: a lost job still counts against pass
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
