"""What the land detector saw after the land command (AUTO_LAND), one line per flight.ulg.

Written for wave J (delay edge: must_land fails). Per flight: share of the land window with landed / maybe_landed /
ground_contact / freefall set, z (NED), and in the window's second half |vz|, dist_bottom, roll-pitch rate rms and
collective thrust. Prints the land-detector params of the first log.
Get the logs: gh run download RUN_ID -R YoussefChouj/px4-mrac-sim -p 'run-*' -D runs (artifacts kept 14 days).
Usage: python3 tools/land_trace.py runs/run-*/*/*/flight.ulg
"""
import sys
import numpy as np
from pyulog import ULog

AUTO_LAND = 18  # vehicle_status.nav_state NAVIGATION_STATE_AUTO_LAND


def topic(u, n):
    return next(d.data for d in u.data_list if d.name == n and d.multi_id == 0)


for f in sys.argv[1:]:
    u = ULog(f)
    st = topic(u, 'vehicle_status')
    t_land = st['timestamp'][np.argmax(st['nav_state'] == AUTO_LAND)] if (st['nav_state'] == AUTO_LAND).any() else None
    ld, lp, av, th = (topic(u, n) for n in ('vehicle_land_detected', 'vehicle_local_position',
                                            'vehicle_angular_velocity', 'vehicle_thrust_setpoint'))
    t_end = u.last_timestamp
    if t_land is None:
        print(f, 'no AUTO_LAND'); continue
    a = lambda d: d['timestamp'] >= t_land
    ldw = {k: ld[k][a(ld)] for k in ('landed', 'maybe_landed', 'ground_contact', 'freefall')}
    z = lp['z'][a(lp)]  # NED, m
    vz = lp['vz'][a(lp)]
    dist = lp['dist_bottom'][a(lp)] if 'dist_bottom' in lp else None
    w = np.sqrt(av['xyz[0]'][a(av)] ** 2 + av['xyz[1]'][a(av)] ** 2)  # roll-pitch rate, rad/s
    thz = -th['xyz[2]'][a(th)]
    late = lambda x: x[len(x) // 2:]  # second half of the landing window: settled on the ground (or not)
    print(f"{f.split('/')[-2]}: land window {(t_end - t_land) * 1e-6:.0f} s sim | "
          + ' '.join(f"{k} {ldw[k].mean():.2f}" for k in ldw)
          + f" | z first/min/last {z[0]:.2f}/{z.min():.2f}/{z[-1]:.2f} m, |vz| late med {np.median(np.abs(late(vz))):.3f}"
          + (f", dist_bottom late med {np.median(late(dist)):.3f}" if dist is not None else '')
          + f" | rp rate late rms {np.sqrt(np.mean(late(w) ** 2)):.3f} rad/s ({np.degrees(np.sqrt(np.mean(late(w) ** 2))):.1f} deg/s)"
          + f" | thrust late med {np.median(late(thz)):.3f}")
    for k in ('LNDMC_ROT_MAX', 'LNDMC_Z_VEL_MAX', 'LNDMC_TRIG_TIME', 'MPC_THR_HOVER', 'MPC_THR_MIN', 'MRL_R_DLY', 'SIM_ACT_DLY'):
        if k in u.initial_parameters and f == sys.argv[1]:
            print('  param', k, u.initial_parameters[k])
