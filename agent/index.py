#!/usr/bin/env python3
"""ONE dark index page over every sim campaign: ~/.cache/px4-index.html.

Usage: index.py [ROOT]   (ROOT default ~/.cache). Scans ROOT/px4-*/<campaign>/ for runs (any folder with
metrics.json), newest campaign first. Each run row: PASS/FAIL, key metrics, links to report.html and
flight.rrd when they exist (make them with report.py / rrd.py). Links are relative, so serve ROOT with
`python3 -m http.server 8791 --bind 127.0.0.1` and open http://127.0.0.1:8791/px4-index.html.
"""
import glob
import html
import json
import os
import sys
import time

KEYS = ['rms_track_err_m', 'max_hold_err_m', 'max_tilt_deg', 'dist_rate_rms', 'dist_roll_peak_deg',
        'dist_z_peak_m', 'uad_max', 'theta_end']
CSS = ('body{background:#000;color:#ddd;font:13px system-ui,sans-serif;margin:16px}a{color:#6cf}'
       'table{border-collapse:collapse;margin:6px 0 14px}td,th{border-bottom:1px solid #222;padding:3px 8px;'
       'text-align:right}td:first-child,th:first-child{text-align:left}th{color:#888;font-weight:normal}'
       '.ok{color:#2a9d8f}.bad{color:#e76f51}summary{cursor:pointer;font-size:15px;margin:8px 0}'
       'code{color:#aaa}')


def runs(camp):
    for m in sorted(glob.glob(os.path.join(camp, '**', 'metrics.json'), recursive=True)):
        try:
            yield os.path.dirname(m), json.load(open(m))
        except (OSError, ValueError):
            continue


def build(root):
    camps = [c for c in glob.glob(os.path.join(root, 'px4-*', '*')) if os.path.isdir(c)]
    camps.sort(key=os.path.getmtime, reverse=True)
    out = [f'<!doctype html><meta charset=utf-8><title>PX4 sim runs</title><style>{CSS}</style>',
           f'<h1>PX4 sim runs</h1><p>{time.strftime("%Y-%m-%d %H:%M")} · {len(camps)} campaigns · '
           'open a .rrd with <code>rerun FILE.rrd</code></p>']
    for i, c in enumerate(camps):
        rows = list(runs(c))
        if not rows:
            continue
        deck = {}  # a deck judges by gate match, not by the scenario's own pass
        if os.path.exists(os.path.join(c, 'deck.json')):
            deck = {os.path.normpath(f['dir']): f for f in json.load(open(os.path.join(c, 'deck.json')))['flights']}
        for d, m in rows:
            f = deck.get(os.path.normpath(d))
            if f:
                m['pass'], m['verdict'] = f['match'], f'{f["got"]} (expect {f["expect"]})'
        npass = sum(bool(m.get('pass')) for _, m in rows)
        rel = os.path.relpath(c, root)
        extra = ''.join(f' · <a href="{html.escape(os.path.join(rel, f))}">{f}</a>'
                        for f in ('deck.md', 'index.html', 'arms.md') if os.path.exists(os.path.join(c, f)))
        cls = 'ok' if npass == len(rows) else 'bad'
        out.append(f'<details{" open" if i < 3 else ""}><summary>{html.escape(rel)} '
                   f'<span class={cls}>{npass}/{len(rows)} pass</span>{extra}</summary><table><tr><th>run</th>'
                   '<th>result</th>' + ''.join(f'<th>{k}</th>' for k in KEYS) + '<th>files</th></tr>')
        for d, m in rows:
            met, r = m.get('metrics', {}), os.path.relpath(d, root)
            links = ' '.join(f'<a href="{html.escape(os.path.join(r, f))}">{f.split(".")[1]}</a>'
                             for f in ('report.html', 'flight.rrd') if os.path.exists(os.path.join(d, f)))
            ok = bool(m.get('pass'))
            out.append(f'<tr><td>{html.escape(os.path.relpath(d, c))}</td>'
                       f'<td class={"ok" if ok else "bad"}>{"PASS" if ok else "FAIL"}'
                       f'{" · " + html.escape(m["verdict"]) if "verdict" in m else ""}</td>' +
                       ''.join(f'<td>{met[k]:.3g}</td>' if isinstance(met.get(k), (int, float)) else '<td></td>'
                               for k in KEYS) + f'<td>{links}</td></tr>')
        out.append('</table></details>')
    path = os.path.join(root, 'px4-index.html')
    open(path, 'w').write('\n'.join(out))
    return path


if __name__ == '__main__':
    print(build(os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/.cache')))
