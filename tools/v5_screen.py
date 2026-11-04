"""V5 uncertainty screen: one roll rate axis of the research drone, PX4 rate PID +/- the MRAC rate layer law.

Grid: actuation delay x gyro noise (white / coloured) x motor lag x torque saturation. All cases run at once
(vectorised over cases). Output: CSV of every case and a dark benefit/failure map.
Model (stated, not identified): J w' = Kt * m + d, motor m' = (sat(u(t - delay)) - m) / tau_m,
gyro = w + noise -> 40 Hz first-order LPF (IMU_GYRO_CUTOFF default), PID on the filtered gyro.
Law copied from MracAxis.hpp (feat 7): phi = [x, r, 1], reference xm' = (r - xm)/tau, e = x - xm,
theta += dt*gam*(-e*phi/(1+phi'phi) - sig*theta), |theta| <= lim, |u_ad| <= umax, blocked when saturated.
Usage: python v5_screen.py OUT_DIR
"""
import csv
import itertools
import sys
from pathlib import Path

import numpy as np

J, KT = 0.01389, 0.1414 * 6.38            # SIH_IXX, SIH_L_ROLL * SIH_T_MAX (airframes/research-drone.json)
P, I, D, IMAX = 0.15, 0.2, 0.003, 0.3     # PX4 MC_ROLLRATE_P/I/D, MC_RR_INT_LIM defaults
import os
TAU, GAM, SIG, LIM, UMAX = float(os.environ.get("V5_TAU", 0.06)), float(os.environ.get("V5_GAM", 2.0)), 0.05, 0.5, 0.3   # MRL_R_* defaults
DT, T_END = 0.001, 8.0
DIST = 0.08                               # MRL_DIST_R: normalised torque step at t = 2 s (same as the SIH runs)

delays = [0, 10, 20, 30, 45, 60]                       # ms
noises = [('0', 0.0, 'w'), ('0.01w', 0.01, 'w'), ('0.044w', 0.044, 'w'), ('0.1w', 0.1, 'w'), ('0.044c', 0.044, 'c')]
lags = [0.03, 0.0505, 0.08, 0.12]                      # s, SIH_T_TAU 0.0505 nominal
sats = [1.0, 0.5, 0.3]                                 # torque headroom (fraction of full)
cases = list(itertools.product(delays, range(len(noises)), lags, sats))


def run(adapt, seed=1):
    n = len(cases)
    dl = np.array([c[0] for c in cases]) // 1           # ms == steps at 1 kHz
    nstd = np.array([noises[c[1]][1] for c in cases])
    col = np.array([noises[c[1]][2] == 'c' for c in cases])
    tm = np.array([c[2] for c in cases])
    us = np.array([c[3] for c in cases])
    rng = np.random.default_rng(seed)
    w = m = wf = integ = xm = cn = np.zeros(n)
    wf_prev = np.zeros(n)
    th = np.zeros((n, 3))
    buf = np.zeros((61, n))
    a_lpf = DT / (DT + 1 / (2 * np.pi * 40))
    a_col = DT / (DT + 1 / (2 * np.pi * 20))
    col_gain = np.sqrt((2 - a_col) / a_col)           # keeps the coloured noise at the same std as the white
    err2, cnt, satc, umaxc = np.zeros(n), 0, np.zeros(n), np.zeros(n)
    dead = np.zeros(n, bool)
    steps = int(T_END / DT)
    for k in range(steps):
        t = k * DT
        r = 1.0 if (t % 2.0) < 1.0 else -1.0             # +-1 rad/s square wave, period 2 s
        r = r if t > 0.5 else 0.0
        wn = rng.standard_normal(n)
        cn = cn + a_col * (wn - cn)
        noise = nstd * np.where(col, cn * col_gain, wn)
        wf = wf + a_lpf * (w + noise - wf)
        e_pid = r - wf
        integ = np.clip(integ + I * e_pid * DT, -IMAX, IMAX)
        u = P * e_pid + integ - D * (wf - wf_prev) / DT
        wf_prev = wf
        xm = xm + DT * (r - xm) / TAU
        if adapt:
            phi = np.stack([wf, np.full(n, r), np.ones(n)], 1)
            e = wf - xm
            ua_raw = np.sum(th * phi, 1)
            sat_p, sat_n = u + ua_raw >= us, u + ua_raw <= -us
            blocked = ((-e > 0) & (sat_p | (ua_raw >= UMAX))) | ((-e < 0) & (sat_n | (ua_raw <= -UMAX)))
            den = 1 + np.sum(phi * phi, 1)
            g = np.where(blocked, 0.0, 1.0)
            th = np.clip(th + DT * GAM * (-(g * e / den)[:, None] * phi - SIG * th), -LIM, LIM)
            ua = np.clip(ua_raw, -UMAX, UMAX)
            umaxc += np.abs(ua) >= 0.99 * UMAX
            u = u + ua
        satc += np.abs(u) >= us
        u = np.clip(u, -us, us)
        buf = np.roll(buf, 1, 0)
        buf[0] = u
        ud = buf[dl, np.arange(n)]
        m = m + DT * (ud - m) / tm
        d = DIST if t >= 2.0 else 0.0
        w = w + DT * (KT * (m + d * (1 if t < 6.0 else 0)) / J)
        bad = ~np.isfinite(w) | (np.abs(w) > 50)
        dead |= bad
        w = np.where(bad, 0.0, w)
        if t > 1.0:
            err2 += (w - xm) ** 2
            cnt += 1
    return np.sqrt(err2 / cnt), dead, satc / steps, umaxc / steps


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    r0, d0, s0, _ = run(False)
    r1, d1, s1, uc = run(True)
    rows = []
    for i, (dl, ni, tm, us) in enumerate(cases):
        if d1[i] and not d0[i]:
            verdict = 'MRAC_DIVERGES'
        elif d0[i] and d1[i]:
            verdict = 'BOTH_DIVERGE'
        elif d0[i]:
            verdict = 'MRAC_SAVES'
        elif r1[i] > 1.1 * r0[i]:
            verdict = 'HARM'
        elif r1[i] < 0.9 * r0[i]:
            verdict = 'BENEFIT'
        else:
            verdict = 'NEUTRAL'
        rows.append(dict(delay_ms=dl, noise=noises[ni][0], motor_tau=tm, sat=us, rms_pid=r0[i], rms_mrac=r1[i],
                         ratio=r1[i] / r0[i] if r0[i] > 0 else np.nan, sat_pid=s0[i], sat_mrac=s1[i],
                         uad_clamp_frac=uc[i], verdict=verdict))
    with open(out / 'v5_screen.csv', 'w', newline='') as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0]))
        wr.writeheader()
        wr.writerows(rows)
    from collections import Counter
    print(Counter(r['verdict'] for r in rows))
    plot(rows, out / 'v5-screen.png')


def plot(rows, path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.style.use('dark_background')
    fig, ax = plt.subplots(len(sats), len(lags), figsize=(16, 10), sharex=True, sharey=True)
    for a, us in enumerate(sats):
        for b, tm in enumerate(lags):
            g = np.full((len(delays), len(noises)), np.nan)
            mark = {}
            for r in rows:
                if r['sat'] == us and r['motor_tau'] == tm:
                    i, j = delays.index(r['delay_ms']), [n[0] for n in noises].index(r['noise'])
                    g[i, j] = np.log2(r['ratio']) if r['verdict'] not in ('BOTH_DIVERGE',) else np.nan
                    mark[(i, j)] = r['verdict']
            im = ax[a, b].imshow(g, cmap='RdYlGn_r', vmin=-1, vmax=1, aspect='auto', origin='lower')
            for (i, j), v in mark.items():
                s = {'MRAC_DIVERGES': 'X', 'BOTH_DIVERGE': '##', 'MRAC_SAVES': 'S', 'HARM': '!'}.get(v, '')
                ax[a, b].text(j, i, s, ha='center', va='center', color='white', fontsize=10, weight='bold')
            ax[a, b].set_title(f'sat {us}  motor tau {tm * 1000:.0f} ms', fontsize=9)
            ax[a, b].set_xticks(range(len(noises)), [n[0] for n in noises], fontsize=7)
            ax[a, b].set_yticks(range(len(delays)), delays, fontsize=7)
    fig.supxlabel('gyro noise std rad/s (w white, c coloured 20 Hz)')
    fig.supylabel('actuation delay ms')
    fig.colorbar(im, ax=ax, label='log2(rms MRAC / rms PID): green = MRAC better')
    fig.suptitle('V5 screen: roll rate axis, PID vs PID+MRAC rate law. X = MRAC diverges, ## = both, S = MRAC saves, ! = >10 % worse')
    fig.savefig(path, dpi=110)


if __name__ == '__main__':
    main()
