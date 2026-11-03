#!/usr/bin/env python3
"""Fly a ladder of scenarios (easy -> hard) and check each verdict against its expectation.

Usage: ladder.py INSTANCE [DIR] [NAME_FILTER]. DIR defaults to scenarios/ladder. Each scenario JSON
carries "expect": "pass" | "fail" and "why" (the predicted outcome and how it fails). A run that ends
in a sim fault (scenario.py exit 3) is rerun up to twice. Prints one row per scenario and writes
ladder.json and ladder.md to ~/.cache/px4-ladder/<time>/. Exit 0 when every verdict matched.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
inst = sys.argv[1]
src = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE.parent / 'scenarios' / 'ladder'
filt = sys.argv[3] if len(sys.argv) > 3 else ''
out = Path.home() / '.cache' / 'px4-ladder' / time.strftime('%Y%m%dT%H%M%S')
out.mkdir(parents=True, exist_ok=True)
rows = []
for f in sorted(src.glob('*.json')):
    if filt not in f.stem:
        continue
    spec = json.loads(f.read_text())
    for attempt in range(3):
        d = out / (f.stem + (f'-retry{attempt}' if attempt else ''))
        with open(out / f'{d.name}.log', 'w') as log:
            rc = subprocess.run([sys.executable, str(HERE / 'scenario.py'), inst, str(f), str(d)],
                                stdout=log, stderr=subprocess.STDOUT).returncode
        if rc != 3:
            break
    m = json.loads((d / 'metrics.json').read_text()) if (d / 'metrics.json').exists() else {}
    got = {0: 'pass', 1: 'fail', 3: 'sim-fault'}.get(rc, 'no-run')
    nums = {k: round(v, 2) for k, v in m.get('metrics', {}).items() if isinstance(v, float)}
    rows.append({'name': f.stem, 'expect': spec.get('expect'), 'got': got, 'match': got == spec.get('expect'),
                 'why': spec.get('why', ''), 'metrics': nums, 'dir': str(d)})
    print(f'{f.stem:<30} expect {spec.get("expect"):<5} got {got:<9} {"OK " if rows[-1]["match"] else "MISS"} {nums}',
          flush=True)
(out / 'ladder.json').write_text(json.dumps(rows, indent=1))
md = ['| scenario | expect | got | match | key metrics | prediction |', '|---|---|---|---|---|---|']
md += [f'| {r["name"]} | {r["expect"]} | {r["got"]} | {"yes" if r["match"] else "NO"} | '
       f'{", ".join(f"{k} {v}" for k, v in r["metrics"].items())} | {r["why"]} |' for r in rows]
(out / 'ladder.md').write_text('\n'.join(md) + '\n')
print(f'{sum(r["match"] for r in rows)}/{len(rows)} matched -> {out}')
sys.exit(0 if all(r['match'] for r in rows) else 1)
