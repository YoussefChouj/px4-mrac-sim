# P16 first pass on existing logs: (1) is ground truth logged? EKF vs truth error; (2) implied drag coefficient
# from steady tilt vs wind speed (pid-alone p13b, sim 3..15 s after wind start, before the first gust);
# (3) obstacle-wind crash: events + where tilt blew up. Usage: p16a.py
import csv, json, math, re
from pathlib import Path
import numpy as np
from pyulog import ULog

H = Path.home() / '.cache/px4-arms'
d = H / 'p13b/p13-wind-pid-alone-1'
u = ULog(str(d / 'flight.ulg'))
names = sorted({x.name for x in u.data_list})
print('groundtruth topics:', [n for n in names if 'groundtruth' in n])
try:
    t = u.get_dataset('vehicle_local_position_groundtruth').data
    p = u.get_dataset('vehicle_local_position').data
    k = p['z'] < -2.5
    gx, gy, gz = (np.interp(p['timestamp'], t['timestamp'], t[c]) for c in ('x', 'y', 'z'))
    eh = np.hypot(p['x'] - gx, p['y'] - gy)[k]
    ez = (p['z'] - gz)[k]
    print(f'EKF-truth horiz rms {np.sqrt(np.mean(eh**2)):.3f} max {eh.max():.3f} m; vert rms {np.sqrt(np.mean(ez**2)):.3f} m')
except Exception as ex:
    print('no truth compare:', ex)

for arm in ('pid-alone', 'lqr-alone'):
    for seed in (1, 2, 3):
        d = H / f'p13b/p13-wind-{arm}-{seed}'
        ev = json.load(open(d / 'metrics.json'))['events']
        tw = next(float(re.match(r'\s*([\d.]+)s', e).group(1)) for e in ev if 'hold 5 s' in e)
        rows = list(csv.reader(open(d / 'wind.csv')))
        w = np.array([[float(x) for x in r[:3]] for r in rows[1:]])
        r = np.array([[float(x) for x in row] for row in list(csv.reader(open(d / 'telemetry.csv')))[1:]])
        ws = (w[:, 0] > 3) & (w[:, 0] < 15)
        wv = np.hypot(w[ws, 1], w[ws, 2]).mean()
        tt = r[:, 0] - tw
        ks = (tt > 3 / 0.8) & (tt < 15 / 0.8)
        tilt = np.arccos(np.cos(np.radians(r[ks, 6])) * np.cos(np.radians(r[ks, 7])))
        mt = np.degrees(tilt.mean())
        c = 9.81 * math.tan(tilt.mean()) / wv
        print(f'{arm}-{seed}: wind header {rows[0][:3]} mean |w| {wv:.2f} m/s, mean tilt {mt:.1f} deg -> implied linear drag {c:.2f} 1/s')

for d in sorted((H / 'p13ow').glob('*-1')) + sorted((H / 'p13ow').glob('*-2*')):
    if not (d / 'metrics.json').exists():
        continue
    m = json.load(open(d / 'metrics.json'))
    print('\n==', d.name, m.get('pass'))
    for e in m['events'][-8:]:
        print('  ', e[:150])
    mm = m['metrics']
    print('  ', {k: (round(v, 3) if isinstance(v, float) else v) for k, v in mm.items() if k in ('min_clearance_m', 'closest_obstacle', 'obstacle_intrusion_m', 'max_tilt_deg', 'landed')})
    r = np.array([[float(x) for x in row] for row in list(csv.reader(open(d / 'telemetry.csv')))[1:]])
    tilt = np.degrees(np.arccos(np.cos(np.radians(r[:, 6])) * np.cos(np.radians(r[:, 7]))))
    i = np.argmax(tilt > 60) if (tilt > 60).any() else None
    if i is not None:
        j = max(0, i - 30)
        print('   tilt>60 at t', round(r[i, 0], 1), 'pos n/e/alt', np.round(r[i, 1:4], 2), 'vel', np.round(r[i, 4:6], 2),
              '| 3 s before: tilt', np.round(tilt[j:i:6], 0))
