"""Wave digest: pass table, broken limits and paired arm differences for results folders of the `results` branch.

Input: results/<wave>-<run id>/ folders (all.json + meta.json), e.g. after
  git fetch origin results && mkdir -p ~/res && git archive FETCH_HEAD results | tar -x -C ~/res
Per wave:
- Pass table: every deck with failing flights, the scenario limits its failing records break (limits from
  scenarios/<deck>.json at the wave's commit; scenario.py passes a limit when value <= limit), the value range and
  the failing runs. Records from 2026-11-05 on carry `landed` (ci/collect.py), so must_land failures are named;
  a failure that still breaks no recorded limit shows as "not in record" with the limits that could not be checked.
- Paired differences treatment - control, matched by `run` (= seed): mean, 95 % percentile bootstrap interval over
  runs (10000 resamples, fixed seed; with 5-10 runs it is a little narrow); `*` = the interval excludes 0.
  Control = a deck with the name token `alone`; a treatment is a deck whose name without its arm tokens (plus, mrac,
  attonly, posonly, rateonly, gNN, tauNN) is the control's name without `alone`, e.g. v5-dly30-g2 -> v5-dly30-alone.
  --pair TREATMENT=CONTROL adds pairs.
Usage: python3 tools/wave_digest.py [--pair T=C ...] [--metrics a,b,...] FOLDER... > digest.md
"""
import argparse
import json
import math
import random
import re
import statistics
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
METRICS = ('max_hold_err_m', 'rms_track_err_m', 'max_tilt_deg', 'att_track_rms_deg', 'rate_rms_rp',
           'motor_sat_frac', 'xy_err_rms_m')
ARM = re.compile(r'plus|mrac|attonly|posonly|rateonly|g\d+|tau\d+')
NB = 10000


def num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)  # nan = no airborne data


def limits(sha, deck):
    """The deck's scenario limits at the wave's commit, else in the working tree."""
    r = subprocess.run(['git', '-C', str(REPO), 'show', f'{sha}:scenarios/{deck}.json'], capture_output=True,
                       text=True)
    p = REPO / 'scenarios' / f'{deck}.json'
    txt = r.stdout if r.returncode == 0 else p.read_text() if p.exists() else '{}'
    return json.loads(txt).get('limits', {})


def pass_table(d, sha):
    print('| deck | pass | failing flights per broken limit (value range > limit) | failing runs |')
    print('|---|---|---|---|')
    for deck, recs in d.items():
        fails = [r for r in recs if not r.get('pass')]
        if not fails:
            continue
        lim, hits, unexplained, noland = limits(sha, deck), {}, 0, 0
        for r in fails:
            bad = [k for k, v in lim.items() if num(r.get(k)) and r[k] > v]
            for k in bad:
                hits.setdefault(k, []).append(r[k])
            nl = bool(lim.get('must_land')) and r.get('landed') is False
            noland += nl
            unexplained += not bad and not nl
        parts = [f'{k} {len(v)} ({min(v):.3g}..{max(v):.3g} > {lim[k]})' for k, v in hits.items()]
        if noland:
            parts.insert(0, f'must_land {noland} (never landed)')
        if unexplained:
            rest = [k for k in lim if not num(fails[0].get(k)) and k != 'must_land'] + ['error']
            parts.append(f'not in record {unexplained} ({", ".join(rest)})')
        runs = ', '.join(str(r.get('run')) for r in fails) if len(fails) <= 3 else f'{len(fails)} runs'
        print(f'| {deck} | {len(recs) - len(fails)}/{len(recs)} | {"; ".join(parts)} | {runs} |')
    print(f'\nEvery run passed in {sum(all(r.get("pass") for r in v) for v in d.values())} of {len(d)} decks.')


def pairs(decks, extra):
    ctrl = {'-'.join(t for t in d.split('-') if t != 'alone'): d for d in decks if 'alone' in d.split('-')}
    out = []
    for d in decks:
        base = '-'.join(t for t in d.split('-') if not ARM.fullmatch(t))
        if 'alone' not in d.split('-') and base != d and base in ctrl:
            out.append((d, ctrl[base]))
    return out + [p for p in extra if p[0] in decks and p[1] in decks and p not in out]


def paired(d, prs, metrics, rng):
    print('| treatment - control | pass T, C | n | ' + ' | '.join(metrics) + ' |')
    print('|---|---|---|' + '---|' * len(metrics))
    for t, c in prs:
        bt, bc = ({r.get('run'): r for r in d[x]} for x in (t, c))
        runs = sorted(set(bt) & set(bc) - {None})
        cells = []
        for m in metrics:
            dd = [bt[i][m] - bc[i][m] for i in runs if num(bt[i].get(m)) and num(bc[i].get(m))]
            if len(dd) < 2:
                cells.append('-')
                continue
            means = sorted(statistics.fmean(rng.choices(dd, k=len(dd))) for _ in range(NB))
            lo, hi = means[int(0.025 * NB)], means[int(0.975 * NB) - 1]
            cells.append(f'{statistics.fmean(dd):+.3g} [{lo:+.3g}, {hi:+.3g}]{"*" if lo > 0 or hi < 0 else ""}')
        pt, pc = (sum(bool(r.get('pass')) for r in d[x]) for x in (t, c))
        print(f'| {t} - {c} | {pt}/{len(d[t])}, {pc}/{len(d[c])} | {len(runs)} | ' + ' | '.join(cells) + ' |')


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('folders', nargs='+', type=Path)
    ap.add_argument('--pair', action='append', default=[], metavar='TREATMENT=CONTROL')
    ap.add_argument('--metrics', default=','.join(METRICS))
    a = ap.parse_args()
    extra, metrics, rng = [tuple(p.split('=', 1)) for p in a.pair], a.metrics.split(','), random.Random(1)
    for f in a.folders:
        d, m = (json.loads((f / n).read_text()) for n in ('all.json', 'meta.json'))
        sha = m.get('sha', 'HEAD')
        print(f'\n## {f.name}: {m.get("pass")}/{m.get("flights")} flights passed (commit {sha[:7]}, '
              f'finished {m.get("finished_utc", "?")}, lost jobs {len(m.get("lost") or [])})\n')
        pass_table(d, sha)
        prs = pairs(list(d), extra)
        if prs:
            print()
            paired(d, prs, metrics, rng)
        alone = sorted(set(d) - {x for p in prs for x in p})
        if alone:
            print(f'\nNot paired: {", ".join(alone)}')


if __name__ == '__main__':
    main()
