#!/usr/bin/env python3
"""CI: merge every arms.json under DIR into one table (mean [min..max] per arm) as Markdown, plus all.json.

Usage: collect.py DIR > summary.md
"""
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
res = {}
for f in sorted(root.rglob('arms.json')):
    for name, runs in json.loads(f.read_text())['results'].items():
        res.setdefault(name, []).extend(runs)
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
print('| pass | ' + ' | '.join(f'{sum(m["pass"] for m in v)}/{len(v)}' for v in res.values()) + ' |')
