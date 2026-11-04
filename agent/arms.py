#!/usr/bin/env python3
"""Fly several scenario arms on ONE PX4 tree and compare inner-loop metrics read from each run's ULog.

Usage: arms.py INSTANCE SRC RUNS ARM.json [ARM.json ...]
Each arm is a scenario file (scenario.py spec) that differs only in params, e.g. MRL_EN_RATE 0 / 2 / 1.
Every arm flies RUNS times, one sim at a time. Per run the ULog (flight.ulg) gives, airborne only:
  rate_rms_rp     RMS of roll+pitch rate error (vehicle_angular_velocity - vehicle_rates_setpoint) [rad/s]
  dist_rate_rms   the same in the 3 s after MRL_DIST_R/P is switched on (none if the arm sets no disturbance)
  dist_peak_rp    peak |roll|,|pitch| rate error in that window [rad/s]
  dist_roll_peak_deg  peak |roll - roll_sp| in that window [deg]
  att_track_rms_deg   RMS of roll and pitch error vs attitude setpoint, whole airborne flight [deg]
  dist_z_peak_m   peak |z - z_sp| in the 5 s after MRL_DIST_T is switched on [m]
  uad_max         peak |u_ad| from mrac_rate_status (0 when the layer is off or route-only); att_/pos_ prefixes
                  for mrac_att_status / mrac_pos_status
  theta_end       |Theta| (all axes) at the end of the log
Writes ~/.cache/px4-arms/<time>/arms.json and prints a mean [min..max] table per arm.
"""
import hashlib
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from pyulog import ULog

HERE = Path(__file__).resolve().parent


def sha(p):
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16] if p.is_file() else None


def git_id(d):
    """Commit and a hash of the uncommitted diff, so a dirty tree is never mistaken for its commit."""
    def g(*a):
        r = subprocess.run(['git', '-C', str(d), *a], capture_output=True, text=True)
        return r.stdout if r.returncode == 0 else ''
    rev = g('rev-parse', 'HEAD').strip()
    diff = g('diff', 'HEAD') + g('status', '--porcelain')
    return {'rev': rev or None, 'dirty': hashlib.sha256(diff.encode()).hexdigest()[:16] if diff.strip() else None}


def manifest(src, arms):
    src = Path(src).expanduser()
    return {'time': time.strftime('%Y-%m-%dT%H:%M:%S'), 'tools': git_id(HERE.parent), 'tree': git_id(src),
            'px4_bin': sha(src / 'build/px4_sitl_default/bin/px4'),
            'decks': {Path(x).stem: sha(x) for x in arms}, 'run0': int(os.environ.get('ARMS_RUN0', 0))}


def topic(ulog, name):
    for d in ulog.data_list:
        if d.name == name and d.multi_id == 0:
            return d.data
    return None


def ulog_metrics(path):
    u = ULog(str(path))
    av, sp, land = topic(u, 'vehicle_angular_velocity'), topic(u, 'vehicle_rates_setpoint'), topic(u, 'vehicle_land_detected')
    if av is None or sp is None:
        # a run that never flew has no rate topics: report it, do not crash the whole batch
        return {'missing_topics': 'vehicle_angular_velocity,vehicle_rates_setpoint', 'pass': False}
    t = av['timestamp'] * 1e-6
    air = np.ones_like(t, dtype=bool)
    if land is not None:
        lt, ll = land['timestamp'] * 1e-6, land['landed']
        idx = np.clip(np.searchsorted(lt, t, side='right') - 1, 0, len(lt) - 1)
        air = ll[idx] == 0
    st = sp['timestamp'] * 1e-6
    err = np.stack([av['xyz[0]'] - np.interp(t, st, sp['roll']), av['xyz[1]'] - np.interp(t, st, sp['pitch'])], 1)
    m = {'rate_rms_rp': float(np.sqrt(np.mean(err[air] ** 2)))}
    on = [ts * 1e-6 for ts, n, v in u.changed_parameters if n in ('MRL_DIST_R', 'MRL_DIST_P') and abs(v) > 0]
    if on:
        w = air & (t >= on[0]) & (t < on[0] + 3.0)
        m['dist_rate_rms'] = float(np.sqrt(np.mean(err[w] ** 2)))
        m['dist_peak_rp'] = float(np.max(np.abs(err[w])))
    ton = [ts * 1e-6 for ts, n, v in u.changed_parameters if n == 'MRL_DIST_T' and abs(v) > 0]
    lp, lsp = topic(u, 'vehicle_local_position'), topic(u, 'vehicle_local_position_setpoint')
    if ton and lp is not None and lsp is not None:
        pt = lp['timestamp'] * 1e-6
        w = (pt >= ton[0]) & (pt < ton[0] + 5.0)
        zerr = lp['z'][w] - np.interp(pt[w], lsp['timestamp'] * 1e-6, lsp['z'])
        m['dist_z_peak_m'] = float(np.max(np.abs(zerr))) if w.any() else float('nan')
    att, asp = topic(u, 'vehicle_attitude'), topic(u, 'vehicle_attitude_setpoint')
    roll = lambda q: np.arctan2(2 * (q[0] * q[1] + q[2] * q[3]), 1 - 2 * (q[1] ** 2 + q[2] ** 2))
    pitch = lambda q: np.arcsin(np.clip(2 * (q[0] * q[2] - q[3] * q[1]), -1, 1))
    if on and att is not None and asp is not None:
        at = att['timestamp'] * 1e-6
        w = (at >= on[0]) & (at < on[0] + 3.0)
        q = [att[f'q[{i}]'][w] for i in range(4)]
        qd = [np.interp(at[w], asp['timestamp'] * 1e-6, asp[f'q_d[{i}]']) for i in range(4)]
        m['dist_roll_peak_deg'] = float(np.degrees(np.max(np.abs(roll(q) - roll(qd))))) if w.any() else float('nan')
    if att is not None and asp is not None:
        # Whole airborne flight: scores attitude tracking when the inner loop is degraded.
        at = att['timestamp'] * 1e-6
        w = np.interp(at, t, air.astype(float)) > 0.5
        q = [att[f'q[{i}]'][w] for i in range(4)]
        qd = [np.interp(at[w], asp['timestamp'] * 1e-6, asp[f'q_d[{i}]']) for i in range(4)]
        e = np.concatenate([roll(q) - roll(qd), pitch(q) - pitch(qd)])
        m['att_track_rms_deg'] = float(np.degrees(np.sqrt(np.mean(e ** 2)))) if w.any() else float('nan')
    # V4 (review 2026-11-04): metrics on the ULog's own timestamps, not on the runner's async telemetry.
    req = ('vehicle_attitude', 'vehicle_local_position', 'vehicle_local_position_setpoint', 'actuator_motors')
    m['missing_topics'] = ','.join(n for n in req if topic(u, n) is None)
    par = dict(u.initial_parameters)
    for ts, n, v in u.changed_parameters:
        par[n] = v  # last value wins; enough for clamp limits that are set once at the start
    if att is not None:
        at = att['timestamp'] * 1e-6
        w = np.interp(at, t, air.astype(float)) > 0.5
        # tilt of the thrust axis (body z vs world z), not the larger Euler component
        tilt = np.degrees(np.arccos(np.clip(1 - 2 * (att['q[1]'] ** 2 + att['q[2]'] ** 2), -1, 1)))
        m['tilt_geo_max_deg'] = float(np.max(tilt[w])) if w.any() else float('nan')
    if lp is not None and lsp is not None:
        pt = lp['timestamp'] * 1e-6
        # XyCtrl modes (LQR/ADRC/MPC) leave the position setpoint NaN: score against the commanded trajectory_setpoint
        ref = {k: (lsp['timestamp'] * 1e-6, lsp[k]) for k in ('x', 'y')}
        tsp = topic(u, 'trajectory_setpoint')
        if np.isfinite(lsp['x']).mean() < 0.5 and tsp is not None:
            ok = np.isfinite(tsp['position[0]']) & np.isfinite(tsp['position[1]'])
            ref = {k: (tsp['timestamp'][ok] * 1e-6, tsp[f'position[{i}]'][ok]) for i, k in enumerate(('x', 'y'))}
            m['xy_ref'] = 'trajectory_setpoint'
        e = np.stack([lp[k] - np.interp(pt, *ref[k]) for k in ('x', 'y')], 1)
        w = (np.interp(pt, t, air.astype(float)) > 0.5) & np.isfinite(e).all(1)
        if w.any():
            # offset = |mean error| (a constant bias), spread = rms about that mean: a drift metric hides the first
            m['xy_err_rms_m'] = float(np.sqrt(np.mean(np.sum(e[w] ** 2, 1))))
            m['xy_offset_m'] = float(np.linalg.norm(e[w].mean(0)))
            m['xy_spread_m'] = float(np.sqrt(np.mean(np.sum((e[w] - e[w].mean(0)) ** 2, 1))))
    mot = topic(u, 'actuator_motors')
    if mot is not None:
        w = np.interp(mot['timestamp'] * 1e-6, t, air.astype(float)) > 0.5
        c = np.stack([mot[f'control[{i}]'] for i in range(4)], 1)
        m['motor_sat_frac'] = float(np.mean(np.any((c[w] >= 0.99) | (c[w] <= 0.01), 1))) if w.any() else float('nan')
    ts_ = topic(u, 'trajectory_setpoint')
    if ts_ is not None and len(ts_['timestamp']) > 10:
        d = np.diff(ts_['timestamp'] * 1e-3)
        m['sp_dt_p99_ms'] = float(np.percentile(d, 99))
    for name, key in (('mrac_rate_status', ''), ('mrac_att_status', 'att_'), ('mrac_pos_status', 'pos_'), ('mrac_xy_status', 'xy_')):
        s = topic(u, name)
        if s is not None and len(s['timestamp']):
            m[f'{key}uad_max'] = float(max(np.max(np.abs(s[f'u_ad[{a}]'])) for a in range(3)))
            m[f'{key}theta_end'] = float(math.sqrt(sum(float(s[f'theta[{i}]'][-1]) ** 2 for i in range(9))))
            pre = {'': 'MRL_R', 'att_': 'MRL_A', 'pos_': 'MRL_P', 'xy_': 'MRL_X'}[key]
            w = np.interp(s['timestamp'] * 1e-6, t, air.astype(float)) > 0.5
            if w.any() and f'{pre}_UMAX' in par:
                ua = np.max(np.abs(np.stack([s[f'u_ad[{a}]'][w] for a in range(3)], 1)), 1)
                m[f'{key}uad_clamp_frac'] = float(np.mean(ua >= 0.99 * par[f'{pre}_UMAX']))
                th = np.max(np.abs(np.stack([s[f'theta[{i}]'][w] for i in range(9)], 1)), 1)
                m[f'{key}theta_lim_frac'] = float(np.mean(th >= 0.99 * par[f'{pre}_LIM']))
    return m


def main():
    inst, src, runs, arms = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4:]
    # px4ctl refuses instances outside 0..8, and scenario.py then waits for a vehicle that never starts
    if inst not in '012345678' or len(inst) != 1:
        sys.exit(f'instance {inst}: px4ctl runs 0..8 only')
    out = Path(os.environ.get('ARMS_OUT') or Path.home() / '.cache' / 'px4-arms' / time.strftime('%Y%m%dT%H%M%S'))
    out.mkdir(parents=True, exist_ok=True)
    # CI runs one repetition per job: ARMS_RUN0 offsets the run index (dir NAME-i), which is also the paired seed
    run0 = int(os.environ.get('ARMS_RUN0', 0))
    man, attempts = manifest(src, arms), []
    env = dict(os.environ, PX4_SOURCE=str(Path(src).expanduser()), PYTHONUNBUFFERED='1')
    res = {}
    for arm in arms:
        name = Path(arm).stem
        res[name] = []
        for i in range(runs):
            for attempt in range(3):
                d = out / f'{name}-{run0 + i + 1}' if not attempt else out / f'{name}-{run0 + i + 1}-retry{attempt}'
                with open(f'{d}.log', 'w') as log:
                    try:
                        rc = subprocess.run([sys.executable, str(HERE / 'scenario.py'), inst, arm, str(d)],
                                            env=env, stdout=log, stderr=subprocess.STDOUT,
                                            timeout=float(os.environ.get('ARMS_TIMEOUT', 900))).returncode
                    except subprocess.TimeoutExpired:
                        # a hung run leaves PX4 behind on this instance; kill it and retry
                        subprocess.run(['pkill', '-f', f'px4 -i {inst} '])
                        time.sleep(5)
                        rc = 3
                attempts.append({'arm': name, 'run': run0 + i + 1, 'attempt': attempt, 'rc': rc, 'dir': d.name})
                if rc != 3:
                    break
            ulg = d / 'flight.ulg'
            if rc in (2, 3) or not ulg.exists():
                print(f'{d.name}: no run (rc {rc})', flush=True)
                continue
            m = ulog_metrics(ulg)
            sm = json.loads((d / 'metrics.json').read_text()) if (d / 'metrics.json').exists() else {}
            m['pass'] = bool(sm.get('pass'))
            for k in ('max_hold_err_m', 'rms_track_err_m', 'max_tilt_deg'):
                if k in sm.get('metrics', {}):
                    m[k] = sm['metrics'][k]
            res[name].append(m)
            print(f'{d.name} {"PASS" if m["pass"] else "FAIL"} ' +
                  ' '.join(f'{k}={v:.4f}' for k, v in m.items() if isinstance(v, float)), flush=True)
    keys = sorted({k for v in res.values() for m in v for k, x in m.items() if isinstance(x, float)})
    print(f'\n{"metric":<16}' + ''.join(f'{n[:24]:>28}' for n in res))
    for k in keys:
        cells = []
        for n in res:
            v = [m[k] for m in res[n] if k in m]
            cells.append(f'{sum(v) / len(v):.4f} [{min(v):.3f}..{max(v):.3f}]' if v else '-')
        print(f'{k:<16}' + ''.join(f'{c:>28}' for c in cells))
    print(f'{"pass":<16}' + ''.join(f'{sum(m["pass"] for m in res[n])}/{runs}'.rjust(28) for n in res))
    # every attempt is kept (rc 3 = infra retry, 2 = no run), so a missing run is visible, never silently dropped
    (out / 'arms.json').write_text(json.dumps({'src': src, 'runs': runs, 'arms': arms, 'manifest': man,
                                               'attempts': attempts, 'results': res}, indent=1))
    print(f'-> {out}')


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1].endswith('.ulg'):
        print(json.dumps(ulog_metrics(sys.argv[1]), indent=1))
    else:
        main()
