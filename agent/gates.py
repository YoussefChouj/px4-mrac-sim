#!/usr/bin/env python3
"""Flight gates read from one run's ULog (+ its metrics.json): the numbers a deck passes or fails on.

Usage: gates.py RUN_DIR [GATES.json]   prints the gate values (and verdicts when limits are given).

Values (airborne samples only):
  osc_amp_rad_s   peak single-sided amplitude of the roll/pitch rate error spectrum in the band
                  [OSC_F_LO, 0.9*Nyquist] Hz (Hann windows of OSC_WIN_S, averaged) [rad/s]
  osc_freq_hz     frequency of that peak
  sat_pct         share of samples with any motor command >= SAT_LEVEL [%]
  max_tilt_deg, rms_track_err_m, max_hold_err_m, max_alt_err_m   from metrics.json when present
  landed          the scenario saw a landing (1/0)
Limits: {"osc_amp_rad_s": 0.1, "sat_pct": 5, ...} -> value <= limit; "landed": 1 -> must be 1.
Regression: check(values, limits, base=values_of_previous_run, tol=0.25) also fails a gate whose value
is worse than base*(1+tol) + REG_EPS[gate] (absolute slack so near-zero baselines do not trip).
"""
import json
import sys
from pathlib import Path

import numpy as np
from pyulog import ULog

OSC_F_LO, OSC_WIN_S, SAT_LEVEL = 1.5, 2.0, 0.99
REG_EPS = {'osc_amp_rad_s': 0.01, 'sat_pct': 1.0, 'max_tilt_deg': 2.0, 'rms_track_err_m': 0.05,
           'max_hold_err_m': 0.1, 'max_alt_err_m': 0.1}


def _topic(u, name):
    for d in u.data_list:
        if d.name == name and d.multi_id == 0:
            return d.data
    return None


def _airborne(u, t):
    land = _topic(u, 'vehicle_land_detected')
    if land is None:
        return np.ones_like(t, dtype=bool)
    lt = land['timestamp'] * 1e-6
    idx = np.clip(np.searchsorted(lt, t, side='right') - 1, 0, len(lt) - 1)
    return land['landed'][idx] == 0


def spectrum(t, x, win_s=OSC_WIN_S):
    """Averaged Hann amplitude spectrum of x(t) on its own median sample rate; returns (f, amp)."""
    dt = float(np.median(np.diff(t)))
    n = int(round(win_s / dt))
    if n < 16 or len(x) < n:
        return np.zeros(0), np.zeros(0)
    w = np.hanning(n)
    segs = [x[i:i + n] - np.mean(x[i:i + n]) for i in range(0, len(x) - n + 1, n // 2)]
    amp = np.mean([np.abs(np.fft.rfft(s * w)) for s in segs], 0) * 2 / w.sum()
    return np.fft.rfftfreq(n, dt), amp


def values(run_dir):
    run_dir = Path(run_dir)
    u = ULog(str(run_dir / 'flight.ulg'))
    v = {}
    av, sp = _topic(u, 'vehicle_angular_velocity'), _topic(u, 'vehicle_rates_setpoint')
    if av is not None and sp is not None:
        t = av['timestamp'] * 1e-6
        air = _airborne(u, t)
        st = sp['timestamp'] * 1e-6
        best = (0.0, 0.0)
        for k, s in (('xyz[0]', 'roll'), ('xyz[1]', 'pitch')):
            e = av[k] - np.interp(t, st, sp[s])
            # spectrum on the longest airborne stretch only (gaps would alias)
            edges = np.flatnonzero(np.diff(np.r_[0, air.astype(int), 0]))
            if len(edges) < 2:
                continue
            a, b = max(zip(edges[::2], edges[1::2]), key=lambda p: p[1] - p[0])
            f, amp = spectrum(t[a:b], e[a:b])
            band = (f >= OSC_F_LO) & (f <= 0.45 / float(np.median(np.diff(t))))
            if band.any():
                i = int(np.argmax(amp[band]))
                if amp[band][i] > best[0]:
                    best = (float(amp[band][i]), float(f[band][i]))
        v['osc_amp_rad_s'], v['osc_freq_hz'] = best
    mot = _topic(u, 'actuator_motors')
    if mot is not None:
        t = mot['timestamp'] * 1e-6
        air = _airborne(u, t)
        cols = [mot[f'control[{i}]'] for i in range(12) if f'control[{i}]' in mot]
        cols = [c for c in cols if np.isfinite(c).any() and np.nanmax(np.abs(c)) > 0]
        if cols and air.any():
            c = np.nan_to_num(np.stack(cols, 1)[air])
            v['sat_pct'] = float(100 * np.mean(np.any(c >= SAT_LEVEL, 1)))
    mj = run_dir / 'metrics.json'
    if mj.exists():
        m = json.loads(mj.read_text())
        for k in ('max_tilt_deg', 'rms_track_err_m', 'max_hold_err_m', 'max_alt_err_m'):
            if isinstance(m.get('metrics', {}).get(k), (int, float)):
                v[k] = float(m['metrics'][k])
        v['landed'] = 1.0 if m.get('metrics', {}).get('landed') else 0.0
    return v


def check(v, limits, base=None, tol=0.25):
    """Returns [(gate, value, limit_text, ok)]; the first failing gate names why a run failed."""
    rows = []
    for g, lim in limits.items():
        x = v.get(g)
        ok = x is not None and (x >= 1 if g == 'landed' else x <= lim)
        rows.append((g, x, f'<= {lim}' if g != 'landed' else 'must land', ok))
    for g, b in (base or {}).items():
        if g in REG_EPS and g in v:
            lim = b * (1 + tol) + REG_EPS[g]
            rows.append((f'regress:{g}', v[g], f'<= {lim:.3g} (prev {b:.3g})', v[g] <= lim))
    return rows


if __name__ == '__main__':
    vals = values(sys.argv[1])
    print(json.dumps(vals, indent=1))
    if len(sys.argv) > 2:
        for g, x, lim, ok in check(vals, json.loads(Path(sys.argv[2]).read_text())):
            print(f'{"PASS" if ok else "FAIL"} {g}: {x} ({lim})')
