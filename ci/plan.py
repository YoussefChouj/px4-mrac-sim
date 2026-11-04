#!/usr/bin/env python3
"""CI (arms plan job): build the fly matrix; prints the GITHUB_OUTPUT lines matrix=, label=, error=.

push: every waves/<name>.txt the push added or modified (format: waves/README.md); label = their names joined by +.
workflow_dispatch: env SCEN (scenario names), RUNS, FIRST; label = dispatch.
A bad input gives error=<one line> (the workflow then fails the plan job) and a one-job dummy matrix.
"""
import json
import os
import re
import subprocess
from pathlib import Path

NAME = re.compile(r'[A-Za-z0-9._-]+')
WAVE = re.compile(r'waves/[A-Za-z0-9._-]+\.txt')
MAX_JOBS = 256  # GitHub matrix limit


def git(*a):
    return subprocess.run(['git', *a], capture_output=True, text=True).stdout


def changed_waves():
    ev = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
    files = []
    for c in (ev.get('commits') or []) + [ev.get('head_commit') or {}]:
        files += (c.get('added') or []) + (c.get('modified') or [])
    if not any(WAVE.fullmatch(f) for f in files):  # payload without file lists: diff the pushed range instead
        before = ev.get('before') or ''
        if not before.strip('0'):  # new branch
            base = (ev.get('repository') or {}).get('default_branch', 'main')
            before = git('merge-base', f'origin/{base}', 'HEAD').strip() or 'HEAD~1'
        files = git('diff', '--name-only', '--diff-filter=AM', before, 'HEAD', '--', 'waves').split()
    return sorted({f for f in files if WAVE.fullmatch(f) and Path(f).is_file()})


def expand(scen, runs, first, where):
    if not scen:
        raise ValueError(f'{where}: no scenario names')
    if not (str(runs).isdigit() and 1 <= int(runs) <= 50):
        raise ValueError(f'{where}: runs must be 1-50, got "{runs}"')
    if not (str(first).isdigit() and int(first) >= 1):
        raise ValueError(f'{where}: first must be a run index >= 1, got "{first}"')
    for s in scen:
        p = Path('scenarios') / f'{s}.json'
        if not NAME.fullmatch(s) or not p.is_file():
            raise ValueError(f'{where}: no scenario file scenarios/{s}.json')
        try:
            json.loads(p.read_text())
        except ValueError as e:
            raise ValueError(f'{where}: scenarios/{s}.json is not valid JSON ({e})')
    return [(s, i) for s in scen for i in range(int(first), int(first) + int(runs))]


def parse_wave(path):
    opt, scen = {'runs': '5', 'first': '1'}, []
    for n, ln in enumerate(Path(path).read_text().splitlines(), 1):
        w = ln.split('#', 1)[0].split()
        if w and w[0] in opt:
            if len(w) != 2:
                raise ValueError(f'{path}:{n}: want "{w[0]} N"')
            opt[w[0]] = w[1]
        else:
            scen += w
    return expand(scen, opt['runs'], opt['first'], path)


def main():
    label, jobs, err = 'dispatch', [], ''
    try:
        if os.environ.get('GITHUB_EVENT_NAME') == 'push':
            waves = changed_waves()
            if not waves:
                raise ValueError('this push added or modified no waves/<name>.txt file')
            label = '+'.join(Path(w).stem for w in waves)
            for w in waves:
                jobs += parse_wave(w)
        else:
            jobs = expand(os.environ.get('SCEN', '').split(), os.environ.get('RUNS') or '2',
                          os.environ.get('FIRST') or '1', 'inputs')
        jobs = list(dict.fromkeys(jobs))
        if len(jobs) > MAX_JOBS:
            raise ValueError(f'{len(jobs)} jobs > {MAX_JOBS} (GitHub matrix limit): push the wave files one at a time')
    except (ValueError, OSError) as e:
        err, jobs = ' '.join(str(e).split()), []
    inc = [{'scen': s, 'run': i} for s, i in jobs] or [{'scen': 'none', 'run': 0}]
    print('matrix=' + json.dumps({'include': inc}))
    print('label=' + re.sub(r'[^A-Za-z0-9._+-]', '_', label)[:60])
    print('error=' + err[:400])


if __name__ == '__main__':
    main()
