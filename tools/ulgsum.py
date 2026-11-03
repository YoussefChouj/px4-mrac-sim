"""Short digest of a PX4 ULog: altitude, attitude error, thrust, motor outputs."""
import sys
import numpy as np
from pyulog import ULog

u = ULog(sys.argv[1])
d = {x.name + ('' if x.multi_id == 0 else f'_{x.multi_id}'): x.data for x in u.data_list}
t0 = u.start_timestamp


def ts(n):
    return (d[n]['timestamp'] - t0) / 1e6


lp = d.get('vehicle_local_position')
if lp is not None:
    t = ts('vehicle_local_position')
    z = -lp['z']
    print(f"alt max {z.max():.2f} m at {t[z.argmax()]:.1f} s; xy drift max {np.hypot(lp['x'], lp['y']).max():.2f} m; flight {t[-1]:.0f} s")
air = None
if 'vehicle_land_detected' in d:
    ld = d['vehicle_land_detected']
    tl = ts('vehicle_land_detected')
    air = tl[ld['landed'] == 0]
    if len(air):
        print(f"airborne {air[0]:.1f}-{air[-1]:.1f} s")
if 'vehicle_attitude' in d and 'vehicle_attitude_setpoint' in d:
    q = d['vehicle_attitude']
    w, x, y, zq = (q[f'q[{i}]'] for i in range(4))
    roll = np.degrees(np.arctan2(2 * (w * x + y * zq), 1 - 2 * (x * x + y * y)))
    pitch = np.degrees(np.arcsin(np.clip(2 * (w * y - zq * x), -1, 1)))
    ta = ts('vehicle_attitude')
    m = (ta > air[0] + 3) & (ta < air[-1] - 2) if air is not None and len(air) else ta > 0
    print(f"airborne roll std {roll[m].std():.2f} max|{np.abs(roll[m]).max():.2f}| deg, pitch std {pitch[m].std():.2f} max|{np.abs(pitch[m]).max():.2f}| deg")
if 'vehicle_angular_velocity' in d:
    av = d['vehicle_angular_velocity']
    ta = ts('vehicle_angular_velocity')
    m = (ta > air[0] + 3) & (ta < air[-1] - 2) if air is not None and len(air) else ta > 0
    for i, n in enumerate('pqr'):
        print(f"  {n} rms {np.degrees(np.sqrt(np.mean(av[f'xyz[{i}]'][m] ** 2))):.2f} deg/s", end='')
    print()
if 'hover_thrust_estimate' in d:
    h = d['hover_thrust_estimate']['hover_thrust']
    h = h[np.isfinite(h)]  # the log holds NaN samples before the estimator starts
    if len(h):
        print(f"hover_thrust_estimate last {h[-1]:.3f} (min {h.min():.3f} max {h.max():.3f})")
if 'actuator_motors' in d:
    am = d['actuator_motors']
    ta = ts('actuator_motors')
    m = (ta > air[0] + 3) & (ta < air[-1] - 2) if air is not None and len(air) else ta > 0
    mot = np.array([am[f'control[{i}]'][m] for i in range(8)])
    print('motor mean ' + ' '.join(f'{v:.2f}' for v in mot.mean(1)) + f'  max {mot.max():.2f} min {mot.min():.2f}')
if 'hover_thrust_estimate' in d:
    print('hte valid frac', d['hover_thrust_estimate']['valid'].mean())
if air is not None and len(air) and 'actuator_motors' in d:
    tl = ts('vehicle_local_position')
    print('t  alt  motor_mean')
    for b in np.arange(air[0], air[-1], 2.0):
        ml = (tl >= b) & (tl < b + 2)
        mm = (ta >= b) & (ta < b + 2)
        mo = np.mean([am[f'control[{i}]'][mm] for i in range(8)])
        print(f'{b:5.1f} {(-lp["z"][ml]).min():.2f}-{(-lp["z"][ml]).max():.2f} {mo:.3f}')
for msg in u.logged_messages[-8:]:
    print('LOG', msg.log_level_str(), msg.message)
