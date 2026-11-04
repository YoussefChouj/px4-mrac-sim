# P13b digest: per run, horizontal hold error vs the position setpoint while above 2.5 m (the windy hold),
# rms / p95 / max, tilt rms; then per arm mean and the paired per-seed difference. Usage: p13bdig.py ARMS_DIR
import sys
from collections import defaultdict
from pathlib import Path
import numpy as np
from pyulog import ULog

rows = defaultdict(dict)
for d in sorted(Path(sys.argv[1]).iterdir()):
    if not (d / 'flight.ulg').exists() or 'retry' in d.name:
        continue
    arm, seed = d.name.rsplit('-', 1)
    # reference = trajectory_setpoint (the offboard hold point); vehicle_local_position_setpoint x/y is NaN
    # when the XYC position controller (XYC_MODE > 0) replaces PX4's
    u = ULog(str(d / 'flight.ulg'), ['vehicle_local_position', 'trajectory_setpoint', 'vehicle_attitude'])
    p = u.get_dataset('vehicle_local_position').data
    s = u.get_dataset('trajectory_setpoint').data
    sx, sy = s['position[0]'], s['position[1]']
    f = np.isfinite(sx) & np.isfinite(sy)
    xs, ys = (np.interp(p['timestamp'], s['timestamp'][f], v[f]) for v in (sx, sy))
    k = (p['z'] < -2.5) & np.isfinite(xs) & np.isfinite(ys)
    if not k.any():
        print(f'{d.name:<26} no samples above 2.5 m')
        continue
    e = np.hypot(p['x'][k] - xs[k], p['y'][k] - ys[k])
    a = u.get_dataset('vehicle_attitude').data
    q = [a[f'q[{i}]'] for i in range(4)]
    tilt = np.degrees(np.arccos(np.clip(1 - 2 * (q[1] ** 2 + q[2] ** 2), -1, 1)))
    rows[arm][seed] = (np.sqrt(np.mean(e ** 2)), np.percentile(e, 95), e.max(), np.sqrt(np.mean(tilt ** 2)))
    print(f'{d.name:<26} rms {rows[arm][seed][0]:.2f}  p95 {rows[arm][seed][1]:.2f}  max {rows[arm][seed][2]:.2f} m  '
          f'tilt_rms {rows[arm][seed][3]:.1f} deg')
print()
for arm, r in rows.items():
    v = np.array(list(r.values()))
    print(f'{arm:<24} n={len(v)}  rms {v[:, 0].mean():.2f} [{v[:, 0].min():.2f}..{v[:, 0].max():.2f}]  '
          f'max {v[:, 2].mean():.2f}  tilt_rms {v[:, 3].mean():.1f}')
arms = list(rows)
for a in arms:
    for b in arms:
        if a < b:
            common = sorted(set(rows[a]) & set(rows[b]))
            dif = [rows[b][s][0] - rows[a][s][0] for s in common]
            print(f'paired rms {b} - {a}: ' + ' '.join(f'{x:+.2f}' for x in dif))
