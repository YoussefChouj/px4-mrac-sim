#!/usr/bin/env python3
"""A/B one scenario on two PX4 source trees and diff the metrics.

Usage: ab.py INSTANCE SCENARIO.json SRC_A SRC_B [RUNS]
SRC is a PX4 tree with a finished build (the main checkout or ~/px4-worktrees/NAME). Each side flies
the scenario RUNS times (default 3), one sim at a time, because one run is not a verdict.
Prints a table of each metric's mean and range per side, the B - A difference of the means and
the pass count, and writes it with every run's metrics to ~/.cache/px4-ab/<scenario>-<time>/ab.json.
A run that ends in a sim fault (scenario.py exit 3) is rerun, up to twice, and the faults are counted.
Exit 0 when both sides ran every time (whatever the verdicts), 2 when a run could not start.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
inst, scen, src_a, src_b = sys.argv[1:5]
runs = int(sys.argv[5]) if len(sys.argv) > 5 else 3
name = Path(scen).stem
out = Path.home() / '.cache' / 'px4-ab' / f'{name}-{time.strftime("%Y%m%dT%H%M%S")}'

results, faults = {}, {'A': 0, 'B': 0}
for side, src in (('A', src_a), ('B', src_b)):
    results[side] = []
    for i in range(runs):
        env = dict(os.environ, PX4_SOURCE=str(Path(src).expanduser()), PYTHONUNBUFFERED='1')
        out.mkdir(parents=True, exist_ok=True)
        for attempt in range(3):
            tag = f'{side}{i + 1}' + (f'-retry{attempt}' if attempt else '')
            d = out / tag
            # The scenario's event lines go to a log as they happen, so a hung run shows its last step.
            with open(out / f'{tag}.log', 'w') as log:
                rc = subprocess.run([sys.executable, str(HERE / 'scenario.py'), inst, scen, str(d)],
                                    env=env, stdout=log, stderr=subprocess.STDOUT).returncode
            if rc != 3:
                break
            faults[side] += 1
            print(f'{tag} SIM-FAULT (sensor stall), rerun', flush=True)
        if rc in (2, 3) or not (d / 'metrics.json').exists():
            sys.exit(f'{tag}: scenario could not run (rc {rc}); see {d}')
        m = json.loads((d / 'metrics.json').read_text())
        results[side].append(m)
        print(f'{side}{i + 1} {"PASS" if m["pass"] else "FAIL"}', flush=True)

keys = sorted({k for side in results.values() for m in side for k, v in m['metrics'].items()
               if isinstance(v, (int, float)) and not isinstance(v, bool)})
rows = []
print(f'\n{"metric":<18}{"A mean [min..max]":>26}{"B mean [min..max]":>26}{"B-A":>9}')
for k in keys:
    cells = []
    for side in 'AB':
        v = [m['metrics'][k] for m in results[side] if k in m['metrics']]
        cells.append((sum(v) / len(v), min(v), max(v)) if v else None)
    fmt = lambda c: f'{c[0]:.3f} [{c[1]:.3f}..{c[2]:.3f}]' if c else '-'
    delta = cells[1][0] - cells[0][0] if all(cells) else None
    rows.append({'metric': k, 'A': cells[0], 'B': cells[1], 'delta': delta})
    print(f'{k:<18}{fmt(cells[0]):>26}{fmt(cells[1]):>26}{f"{delta:+.3f}" if delta is not None else "-":>9}')
passes = {side: sum(m['pass'] for m in results[side]) for side in 'AB'}
print(f'{"pass":<18}{passes["A"]:>21}/{runs}{passes["B"]:>25}/{runs}')
print(f'{"sim faults rerun":<18}{faults["A"]:>23}{faults["B"]:>27}')
(out / 'ab.json').write_text(json.dumps({'scenario': name, 'A': src_a, 'B': src_b, 'runs': runs,
                                         'table': rows, 'pass': passes, 'sim_faults': faults,
                                         'results': results}, indent=1))
print(f'-> {out}')
