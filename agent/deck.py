#!/usr/bin/env python3
"""Fly a sim flight deck: an ordered list of scenarios, each scored by the deck's gates (gates.py).

Usage: deck.py INSTANCE DECK.json [--src PX4_TREE] [--base PREV_DECK_DIR]
DECK.json:
  {"name": "rate-osc",
   "gates": {"osc_amp_rad_s": 0.1, "sat_pct": 5, "max_tilt_deg": 35, "landed": 1},
   "flights": [{"scenario": "../mrac-off.json", "expect": "pass"},
               {"scenario": "osc-rollrate-p.json", "expect": "osc_amp_rad_s"}]}
Scenario paths are relative to the deck file. "expect" is "pass" or the gate that must fail FIRST (deck
gates in the order written, then the scenario's own limits as "scenario"); a deck matches when every
flight's first failing gate is the expected one. With --base, every flight is also checked for
regression against the same-named flight of that earlier deck (gates.check, 25 % + absolute slack).
A sim fault (scenario.py exit 3) is rerun up to twice. Writes ~/.cache/px4-decks/<name>-<time>/deck.json
and deck.md; each flight keeps its scenario folder (flight.ulg, metrics.json) for report.py.
Exit 0 when every flight matched its expectation.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import gates

HERE = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('instance')
    ap.add_argument('deck')
    ap.add_argument('--src', help='PX4 tree (PX4_SOURCE), default px4ctl default')
    ap.add_argument('--base', help='earlier deck output dir for the regression gate')
    a = ap.parse_args()
    deck_f = Path(a.deck).resolve()
    deck = json.loads(deck_f.read_text())
    out = Path.home() / '.cache' / 'px4-decks' / f'{deck["name"]}-{time.strftime("%Y%m%dT%H%M%S")}'
    out.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PYTHONUNBUFFERED='1')
    if a.src:
        env['PX4_SOURCE'] = str(Path(a.src).expanduser())
    base = {}
    if a.base:
        base = {f['name']: f['values'] for f in json.loads((Path(a.base) / 'deck.json').read_text())['flights']}
    rows = []
    for i, fl in enumerate(deck['flights']):
        scen = (deck_f.parent / fl['scenario']).resolve()
        name = f'{i + 1:02d}-{scen.stem}'
        for attempt in range(3):
            d = out / (name + (f'-retry{attempt}' if attempt else ''))
            with open(f'{d}.log', 'w') as log:
                rc = subprocess.run([sys.executable, str(HERE / 'scenario.py'), a.instance, str(scen), str(d)],
                                    env=env, stdout=log, stderr=subprocess.STDOUT).returncode
            if rc != 3:
                break
        row = {'name': name, 'scenario': str(scen), 'dir': str(d), 'expect': fl.get('expect', 'pass'),
               'rc': rc, 'values': {}, 'checks': []}
        if (d / 'flight.ulg').exists():
            row['values'] = gates.values(d)
            row['checks'] = gates.check(row['values'], deck.get('gates', {}), base.get(name))
        failed = [g for g, _, _, ok in row['checks'] if not ok]
        if rc == 1:
            failed.append('scenario')
        row['got'] = {2: 'no-run', 3: 'sim-fault'}.get(rc, failed[0] if failed else 'pass')
        row['match'] = row['got'] == row['expect']
        rows.append(row)
        v = row['values']
        print(f'{name:<34} expect {row["expect"]:<14} got {row["got"]:<14} {"OK  " if row["match"] else "MISS"} '
              f'osc {v.get("osc_amp_rad_s", float("nan")):.3f}@{v.get("osc_freq_hz", float("nan")):.1f}Hz '
              f'sat {v.get("sat_pct", float("nan")):.1f}% tilt {v.get("max_tilt_deg", float("nan")):.1f}', flush=True)
    (out / 'deck.json').write_text(json.dumps({'deck': str(deck_f), 'src': a.src, 'base': a.base,
                                               'gates': deck.get('gates', {}), 'flights': rows}, indent=1))
    md = [f'# Deck {deck["name"]}', '', '| flight | expect | got | match | failing checks |', '|---|---|---|---|---|']
    for r in rows:
        bad = '; '.join(f'{g} {x if not isinstance(x, float) else round(x, 3)} ({lim})'
                        for g, x, lim, ok in r['checks'] if not ok)
        md.append(f'| {r["name"]} | {r["expect"]} | {r["got"]} | {"yes" if r["match"] else "NO"} | {bad} |')
    (out / 'deck.md').write_text('\n'.join(md) + '\n')
    print(f'{sum(r["match"] for r in rows)}/{len(rows)} matched -> {out}')
    sys.exit(0 if all(r['match'] for r in rows) else 1)


if __name__ == '__main__':
    main()
