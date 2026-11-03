#!/usr/bin/env python3
"""Gains for the xy_ctrl baselines (LQR / ADRC / MPC), ported from the firmware API/xy_ctrl.c.

Per-axis plant on PX4 (u = horizontal acceleration command, m/s^2):
    p' = v,  v' = a,  a[k+1] = al*a[k] + b*u[k-d],  z' = p - p_des (integral)
al, b and d are fitted from a flown ULog (setpoint acceleration -> measured acceleration),
never assumed.

Usage: xyc_design.py ULOG [--dt 0.02] [--out xyc_gains.h]
Prints the fit and writes a C header with XYC_* constants.
"""
import argparse
import numpy as np
from pyulog import ULog
from scipy.linalg import solve_discrete_are


def topic(u, name):
    for d in u.data_list:
        if d.name == name and d.multi_id == 0:
            return d.data
    raise SystemExit(f'{name} not in log')


def fit_lag(path, dt, dmax=10):
    """Output-error fit: simulate a_hat[k+1] = al*a_hat[k] + b*u[k-d] from u alone (no noisy-regressor bias),
    grid over tau and d, gain b by least squares; best by residual. Returns (al, b, d, res, axis)."""
    from scipy.signal import lfilter
    u = ULog(path)
    # Input u = tilt-implied horizontal acceleration of vehicle_attitude_setpoint (logged fast); the
    # vehicle_local_position_setpoint acceleration is logged at ~10 Hz and aliases at a 50 Hz fit.
    lp, sp = topic(u, 'vehicle_local_position'), topic(u, 'vehicle_attitude_setpoint')
    q = np.column_stack([sp[f'q_d[{k}]'] for k in range(4)])
    w, x, y, z = q.T
    bz = np.column_stack([2 * (x * z + w * y), 2 * (y * z - w * x), 1 - 2 * (x * x + y * y)])  # body z in NED
    acc_xy = 9.81 * bz[:, :2] / np.maximum(bz[:, 2:3], 0.3) * -1.0   # thrust along -body z
    print(f'attitude setpoint rate {1e6 / np.median(np.diff(sp["timestamp"])):.0f} Hz')
    t0, t1 = max(lp['timestamp'][0], sp['timestamp'][0]), min(lp['timestamp'][-1], sp['timestamp'][-1])
    g = np.arange(t0, t1, dt * 1e6)
    air = np.interp(g, lp['timestamp'], -lp['z']) > 1.0
    best = None
    for i, ax in enumerate(('x', 'y')):
        a = np.interp(g, lp['timestamp'], lp['a' + ax])[air]
        vv = np.interp(g, lp['timestamp'], lp['v' + ax])[air]
        c = np.interp(g, sp['timestamp'], acc_xy[:, i])[air]
        ok = np.isfinite(a) & np.isfinite(c) & np.isfinite(vv)
        a, c, vv = a[ok], c[ok], vv[ok]
        # same zero-phase low-pass on input and output: keeps the input/output relation, drops jitter
        from scipy.signal import butter, filtfilt
        bb, aa = butter(2, 3.0 * 2 * dt)                # 3 Hz at the dt grid
        a, c, vv = filtfilt(bb, aa, a), filtfilt(bb, aa, c), filtfilt(bb, aa, vv)
        for tau in np.arange(0.02, 1.0, 0.01):
            al = float(np.exp(-dt / tau))
            unit = lfilter([1 - al], [1, -al], c)          # unit dc gain response to u
            for d in range(dmax + 1):
                h = np.concatenate([np.zeros(d), unit[:len(unit) - d]])
                X = np.column_stack([h, -vv])          # a = k*lag(u) - D*v
                (k, D), *_ = np.linalg.lstsq(X, a, rcond=None)
                res = float(np.sqrt(np.mean((a - X @ [k, D]) ** 2)))
                if best is None or res < best[3]:
                    best = (al, float(k) * (1 - al), d, res, ax, float(D))
    return best


def model(al, b, dt, D=0.0):
    A = np.array([[1, dt, 0, 0], [0, 1 - dt * D, dt, 0], [0, 0, al, 0], [dt, 0, 0, 1]])
    B = np.array([[0], [0], [b], [0]])
    return A, B


def dlqr(A, B, Q, R):
    P = solve_discrete_are(A, B, Q, R)
    return np.linalg.solve(R + B.T @ P @ B, B.T @ P @ A)


def mpc(A, B, Q, R, N):
    """Condensed QP 0.5 U'HU + U'F x over N steps, terminal weight = LQR P."""
    n = A.shape[0]
    P = solve_discrete_are(A, B, Q, R)
    Phi = np.vstack([np.linalg.matrix_power(A, i + 1) for i in range(N)])
    G = np.zeros((N * n, N))
    for i in range(N):
        for j in range(i + 1):
            G[i * n:(i + 1) * n, j] = (np.linalg.matrix_power(A, i - j) @ B)[:, 0]
    Qb = np.kron(np.eye(N), Q)
    Qb[-n:, -n:] = P
    H = G.T @ Qb @ G + R[0, 0] * np.eye(N)
    F = G.T @ Qb @ Phi
    return H, F, 1.0 / np.max(np.linalg.eigvalsh(H))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('ulog')
    ap.add_argument('--dt', type=float, default=0.02)
    ap.add_argument('--out', default='xyc_gains.h')
    ap.add_argument('--wc', type=float, default=1.5, help='ADRC closed-loop bandwidth [rad/s]')
    ap.add_argument('--N', type=int, default=10)
    a = ap.parse_args()
    al, b, d, res, ax, D = fit_lag(a.ulog, a.dt)
    tau = -a.dt / np.log(al) if 0 < al < 1 else float('nan')
    print(f'fit ({ax}): al={al:.4f} (tau {tau:.3f} s) b={b:.4f} (dc gain {b / (1 - al):.3f}) drag D={D:.3f} 1/s delay d={d} ({d * a.dt * 1e3:.0f} ms) rms res {res:.3f} m/s^2')
    A, B = model(al, b, a.dt, D)
    Q, R = np.diag([4.0, 1.0, 0.1, 0.5]), np.array([[1.0]])
    K = dlqr(A, B, Q, R)[0]
    H, F, step = mpc(A, B, Q, R, a.N)
    cl = np.abs(np.linalg.eigvals(A - B @ K[None, :]))
    print('LQR K =', np.round(K, 4), 'closed-loop |eig| max', round(float(cl.max()), 4))
    wo = 4 * a.wc
    lines = ['/* generated by xyc_design.py from ' + a.ulog.split('/')[-1] + ' */',
             f'#define XYC_DT {a.dt}f', f'#define XYC_AL {al:.6f}f', f'#define XYC_B {b:.6f}f', f'#define XYC_DRAG {D:.6f}f', f'#define XYC_DELAY {d}',
             'static const float XYC_LQR_K[4] = {' + ', '.join(f'{k:.6f}f' for k in K) + '};',
             f'#define XYC_ADRC_WC {a.wc}f', '#define XYC_ADRC_B0 1.0f',
             f'#define XYC_ADRC_B1 {3 * wo:.4f}f', f'#define XYC_ADRC_B2 {3 * wo ** 2:.4f}f',
             f'#define XYC_ADRC_B3 {wo ** 3:.4f}f',
             f'#define XYC_MPC_N {a.N}', f'#define XYC_MPC_STEP {step:.6f}f',
             'static const float XYC_MPC_H[XYC_MPC_N][XYC_MPC_N] = {' +
             ', '.join('{' + ', '.join(f'{v:.6f}f' for v in r) + '}' for r in H) + '};',
             'static const float XYC_MPC_F[XYC_MPC_N][4] = {' +
             ', '.join('{' + ', '.join(f'{v:.6f}f' for v in r) + '}' for r in F) + '};']
    open(a.out, 'w').write('\n'.join(lines) + '\n')
    print('wrote', a.out)


if __name__ == '__main__':
    main()
