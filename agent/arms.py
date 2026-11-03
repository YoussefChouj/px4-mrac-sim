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


def topic(ulog, name):
    for d in ulog.data_list:
        if d.name == name and d.multi_id == 0:
            return d.data
    return None


def ulog_metrics(path):
    u = ULog(str(path))
    av, sp, land = topic(u, 'vehicle_angular_velocity'), topic(u, 'vehicle_rates_setpoint'), topic(u, 'vehicle_land_detected')
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
    for name, key in (('mrac_rate_status', ''), ('mrac_att_status', 'att_'), ('mrac_pos_status', 'pos_')):
        s = topic(u, name)
        if s is not None and len(s['timestamp']):
            m[f'{key}uad_max'] = float(max(np.max(np.abs(s[f'u_ad[{a}]'])) for a in range(3)))
            m[f'{key}theta_end'] = float(math.sqrt(sum(float(s[f'theta[{i}]'][-1]) ** 2 for i in range(9))))
    return m


def main():
    inst, src, runs, arms = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4:]
    # px4ctl refuses instances outside 0..8, and scenario.py then waits for a vehicle that never starts
    if inst not in '012345678' or len(inst) != 1:
        sys.exit(f'instance {inst}: px4ctl runs 0..8 only')
    out = Path(os.environ.get('ARMS_OUT') or Path.home() / '.cache' / 'px4-arms' / time.strftime('%Y%m%dT%H%M%S'))
    out.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PX4_SOURCE=str(Path(src).expanduser()), PYTHONUNBUFFERED='1')
    res = {}
    for arm in arms:
        name = Path(arm).stem
        res[name] = []
        for i in range(runs):
            for attempt in range(3):
                d = out / f'{name}-{i + 1}' if not attempt else out / f'{name}-{i + 1}-retry{attempt}'
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
    (out / 'arms.json').write_text(json.dumps({'src': src, 'runs': runs, 'arms': arms, 'results': res}, indent=1))
    print(f'-> {out}')


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1].endswith('.ulg'):
        print(json.dumps(ulog_metrics(sys.argv[1]), indent=1))
    else:
        main()
