#!/usr/bin/env python3
"""CI (arms collect job): publish one finished arms run to the `results` branch.

Writes RUNS/meta.json and RUNS/summary.md, then commits results/<label>-<run id>/ (all.json, meta.json, summary.md,
logs/ = output tail of each job that did not pass, build-tail.log when the build failed) and a regenerated
results/INDEX.md to the orphan branch `results`, retrying on push races. Readers need no token:
`git fetch origin results && git show origin/results:results/INDEX.md`.

Usage: publish.py RUNS_DIR [BUILD_LOG_DIR]   env: LABEL ERR MATRIX PLAN BUILD FLY (+ Actions defaults; PUBLISH_DRY=1: no git)
       publish.py --index RESULTS_DIR        rewrite RESULTS_DIR/INDEX.md from its */meta.json
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
BOT = ['-c', 'user.name=github-actions[bot]', '-c', 'user.email=41898282+github-actions[bot]@users.noreply.github.com']
MAX_LOGS = 40


def passed(run_dir):
    """True / False from the job's arms.json files, None when the job reported nothing."""
    recs = [r for f in run_dir.rglob('arms.json') for v in json.loads(f.read_text())['results'].values() for r in v]
    return all(r.get('pass') for r in recs) if recs else None


def meta(runs, env):
    matrix = [m for m in json.loads(env.get('MATRIX') or '{}').get('include', []) if m.get('run')]
    d = json.loads((runs / 'all.json').read_text()) if (runs / 'all.json').exists() else {}
    recs = [r for v in d.values() for r in v]
    lost = [f"{m['scen']}-{m['run']}" for m in matrix if passed(runs / f"run-{m['scen']}-{m['run']}") is None]
    server, repo, rid = env.get('GITHUB_SERVER_URL', 'https://github.com'), env['GITHUB_REPOSITORY'], env['GITHUB_RUN_ID']
    label = env.get('LABEL') or 'wave'
    folder = f'{label}-{rid}'
    return {'run_id': int(rid), 'url': f'{server}/{repo}/actions/runs/{rid}', 'label': label, 'folder': folder,
            'event': env.get('GITHUB_EVENT_NAME'), 'branch': env.get('GITHUB_REF_NAME'), 'sha': env.get('GITHUB_SHA'),
            'decks': sorted({m['scen'] for m in matrix}), 'runs': sorted({m['run'] for m in matrix}),
            'jobs': len(matrix), 'flights': len(recs), 'pass': sum(bool(r.get('pass')) for r in recs), 'lost': lost,
            'plan': env.get('PLAN'), 'build': env.get('BUILD'), 'fly': env.get('FLY'), 'error': env.get('ERR') or '',
            'finished_utc': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'results_url': f'{server}/{repo}/tree/results/results/{folder}'}


def fill(dst, runs, buildlog):
    dst.mkdir(parents=True)
    for n in ('all.json', 'meta.json', 'summary.md'):
        if (runs / n).exists():
            shutil.copy(runs / n, dst / n)
    bad = [p for p in sorted(runs.glob('run-*')) if passed(p) is not True and (p / 'fly-tail.log').exists()]
    for p in bad[:MAX_LOGS]:
        (dst / 'logs').mkdir(exist_ok=True)
        shutil.copy(p / 'fly-tail.log', dst / 'logs' / f'{p.name}.log')
    for t in (sorted(buildlog.glob('*.log')) if buildlog and buildlog.is_dir() else []):
        shutil.copy(t, dst / 'build-tail.log')


def index(res):
    rows = []
    for f in res.glob('*/meta.json'):
        try:
            rows.append(json.loads(f.read_text()))
        except ValueError:
            pass
    rows.sort(key=lambda m: m.get('finished_utc') or '', reverse=True)
    out = ['# Cloud results (newest first)', '',
           'One folder per finished `arms` run: `all.json` (every flight; `run` = seed index), `meta.json` (status, '
           'lost jobs, error), `summary.md` (per-deck medians), `logs/` (output tail of jobs that did not pass), '
           '`build-tail.log` (failed build). Written by `ci/publish.py`; do not edit by hand.', '',
           '| finished UTC | wave | branch | sha | pass / jobs | lost | plan / build / fly | folder |',
           '|---|---|---|---|---|---|---|---|']
    for m in rows:
        st = ' / '.join(str(m.get(k) or '-') for k in ('plan', 'build', 'fly'))
        if m.get('error'):
            st += ': ' + m['error'][:100].replace('|', '/')
        out.append(f"| {(m.get('finished_utc') or '')[:16].replace('T', ' ')} | {m.get('label')} | {m.get('branch')} | "
                   f"{(m.get('sha') or '')[:7]} | {m.get('pass')} / {m.get('jobs')} | {len(m.get('lost') or [])} | "
                   f"{st} | [{m.get('folder')}]({m.get('folder')}/) |")
    (res / 'INDEX.md').write_text('\n'.join(out) + '\n')


def git(*a, cwd=None):
    return subprocess.run(['git', *a], cwd=cwd, capture_output=True, text=True)


def push(stage):
    for i in range(1, 7):
        wt = Path(tempfile.mkdtemp(prefix='results-')) / 'wt'
        have = git('fetch', '-q', '--depth', '1', 'origin', 'results').returncode == 0
        a = git('worktree', 'add', '-q', '--detach', str(wt), 'FETCH_HEAD' if have else 'HEAD')
        if a.returncode == 0 and not have:  # first run ever: start the orphan branch
            a = git('switch', '-q', '--orphan', f'results-new-{os.getpid()}-{i}', cwd=wt)
        if a.returncode == 0:
            dst = wt / 'results' / stage.name
            shutil.rmtree(dst, ignore_errors=True)
            shutil.copytree(stage, dst)
            index(wt / 'results')
            git('add', 'results', cwd=wt)
            git(*BOT, 'commit', '-q', '-m', f'results: {stage.name}', cwd=wt)
            a = git('push', '-q', 'origin', 'HEAD:refs/heads/results', cwd=wt)
        git('worktree', 'remove', '--force', str(wt))
        if a.returncode == 0:
            print(f'published results/{stage.name} (attempt {i})')
            return True
        print(f'attempt {i} failed: {a.stderr.strip()[-300:]}', file=sys.stderr)
        time.sleep(5 * i)
    return False


def main():
    if sys.argv[1] == '--index':
        index(Path(sys.argv[2]))
        return
    runs = Path(sys.argv[1])
    runs.mkdir(exist_ok=True)
    m = meta(runs, os.environ)
    (runs / 'meta.json').write_text(json.dumps(m, indent=1))
    s = subprocess.run([sys.executable, str(HERE / 'notify.py'), str(runs / 'all.json'), m['url'],
                        f"plan {m['plan']}, build {m['build']}, fly {m['fly']}"], capture_output=True, text=True)
    (runs / 'summary.md').write_text(s.stdout or s.stderr)
    stage = Path(tempfile.mkdtemp(prefix='stage-')) / m['folder']
    fill(stage, runs, Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    if os.environ.get('PUBLISH_DRY'):
        print(stage)
        return
    sys.exit(0 if push(stage) else 1)


if __name__ == '__main__':
    main()
