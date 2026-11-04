#!/usr/bin/env python3
"""Run one flight scenario end to end and score it: start sim, fly steps, measure, stop.

Usage: scenario.py INSTANCE FILE.json [OUTDIR]. Exit 0 = every limit passed, 1 = failed,
2 = could not run, 3 = sim fault (SIH sensor data stalled in flight, so the run says nothing about
the controller; rerun it). Writes OUTDIR/telemetry.csv, metrics.json and plot.png, and prints one
line per event plus a PASS/FAIL table, so an agent reads the verdict from stdout.

FILE.json:
  {"sim": "sih" | "gz", "vehicle": "flycart30", "speed": 5, "alt": 5,
   # vehicle: gz model (default x500), or SIH airframe quadx | hex (default quadx)
   "airframe": "flycart30",                # SIH only: boot params from airframes/<name>.json
   "boot_params": {"SYS_FAILURE_EN": 1},   # set at startup (saved params are wiped first)
   "params": {"NAME": value},              # set live before takeoff
   "world": "video",                       # gz only: worlds/NAME.sdf or a PX4 world (default "default")
   "video": ["overview", "chase"],         # gz only: cameras to record, OUTDIR/gazebo-CAM.mp4 (true = chase)
   "steps": [{"do": "takeoff"}, {"do": "hold", "s": 10},
             {"do": "goto", "n": 10, "e": 0}, {"do": "param", "name": "X", "value": 1},
             {"do": "failure", "unit": "SYSTEM_MOTOR", "type": "OFF", "instance": 1},
             {"do": "land"}],
   "limits": {"max_overshoot_m": 1.0, "max_hold_err_m": 0.5, "max_tilt_deg": 30,
              "must_land": true}}
Hold error is the horizontal distance from where the hold started; goto overshoot is the
peak past the target along the move. Speed applies to SIH only (gz runs in real time).
SIH injects only SYSTEM_MOTOR failures (commander FailureInjector, needs SYS_FAILURE_EN=1 at
boot); sensor failures such as SENSOR_GPS are not implemented there and time out.
"""
import asyncio
import csv
import glob
import json
import logging
import math
import os
import re as regex  # the fig8 step uses a local `re` (east reference)
import shutil
import subprocess
import sys
import time

from mavsdk_grpc import System
from mavsdk_grpc.failure import FailureType, FailureUnit
from mavsdk_grpc.offboard import Attitude, OffboardError, PositionNedYaw, VelocityNedYaw

PX4CTL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'px4ctl')


def gz_record(inst, cam, req):
    """Start or stop camera cam's video recorder in instance inst's Gazebo partition (see px4ctl gz)."""
    env = dict(os.environ, GZ_IP='127.0.0.1', GZ_PARTITION=f'px4-{inst}')
    r = subprocess.run(['gz', 'service', '-s', f'/{cam}/record_video', '--reqtype', 'gz.msgs.VideoRecord',
                        '--reptype', 'gz.msgs.Boolean', '--timeout', '10000', '-r', req],
                       env=env, capture_output=True, text=True)
    say(f'gz record {cam} {req.split(",")[0]}: {(r.stdout + r.stderr).strip() or r.returncode}')
inst = int(sys.argv[1])
spec = json.load(open(sys.argv[2]))
name = os.path.splitext(os.path.basename(sys.argv[2]))[0]
out = sys.argv[3] if len(sys.argv) > 3 else os.path.expanduser(
    f'~/.cache/px4-scenarios/{name}-{time.strftime("%Y%m%dT%H%M%S")}')
os.makedirs(out, exist_ok=True)
# Everything mavsdk_server prints (its abort text is unprefixed, so the library logs it at debug) goes to
# OUTDIR/mavsdk.log instead of being lost; this also keeps its ack warnings off the console.
_ml = logging.getLogger('mavsdk_server')
_ml.setLevel(logging.DEBUG)
_ml.addHandler(logging.FileHandler(os.path.join(out, 'mavsdk.log')))
t0 = time.monotonic()
rows, metrics, events = [], {}, []
simt = {'us': 0}  # vehicle boot time from the IMU stream: sim time, whatever the sim speed


def say(msg):
    line = f'{time.monotonic() - t0:6.1f}s {msg}'
    events.append(line)
    print(line, flush=True)


SLOW = 1           # wall-clock timeouts scale by this; a recorded gz run is ~10x slower than real time
on_ready = None    # called once position is ok (starts the gz recording, so boot is not filmed)


async def wait_until(gen, ok, timeout):
    async def run():
        async for v in gen:
            if ok(v):
                return v
    return await asyncio.wait_for(run(), timeout * SLOW)


async def record(drone):
    # Latest attitude is merged into each position sample; boot time keeps sim time.
    att = {'roll': 0.0, 'pitch': 0.0}

    async def att_loop():
        async for a in drone.telemetry.attitude_euler():
            att['roll'], att['pitch'] = a.roll_deg, a.pitch_deg
    async def clock_loop():
        async for m in drone.telemetry.imu():
            simt['us'] = m.timestamp_us
    asyncio.ensure_future(att_loop())
    asyncio.ensure_future(clock_loop())
    async for p in drone.telemetry.position_velocity_ned():
        rows.append((time.monotonic() - t0, p.position.north_m, p.position.east_m,
                     -p.position.down_m, p.velocity.north_m_s, p.velocity.east_m_s,
                     att['roll'], att['pitch']))


async def fly(drone):
    await wait_until(drone.core.connection_state(), lambda s: s.is_connected, 60)
    await wait_until(drone.telemetry.health(),
                     lambda h: h.is_global_position_ok and h.is_home_position_ok, 120)
    say('connected, position ok')
    if on_ready:
        on_ready()
    restore = {}
    for k, v in spec.get('params', {}).items():
        restore[k] = await set_param(drone, k, v)
    await drone.telemetry.set_rate_position_velocity_ned(50)
    await drone.telemetry.set_rate_attitude_euler(50)
    await drone.telemetry.set_rate_imu(50)
    asyncio.ensure_future(record(drone))
    alt = float(spec.get('alt', 5))
    pos = lambda: rows[-1] if rows else (0, 0, 0, 0, 0, 0, 0, 0)
    offboard, ground = False, 0.0
    try:
        for step in spec['steps']:
            do = step['do']
            if do == 'takeoff':
                # MIS_TAKEOFF_ALT is set at boot (main). The climb is measured from the ground
                # point, because the local origin can sit up to ~1 m off the pad at boot.
                ground = -(await anext(drone.telemetry.position_velocity_ned())).position.down_m
                await drone.action.arm()
                await drone.action.takeoff()
                await wait_until(drone.telemetry.position_velocity_ned(),
                                 lambda p: -p.position.down_m - ground > alt - 0.3, 90)
                say(f'takeoff to {alt} m done')
            elif do == 'hold':
                n0, e0 = pos()[1], pos()[2]
                i0 = len(rows)
                us_end = simt['us'] + float(step.get('s', 10)) * 1e6  # sim seconds, not wall
                while simt['us'] < us_end:
                    await asyncio.sleep(0.01)
                err = max((math.hypot(r[1] - n0, r[2] - e0) for r in rows[i0:]), default=0)
                metrics['max_hold_err_m'] = max(metrics.get('max_hold_err_m', 0), err)
                # Height error against the commanded hold height (a payload or thrust change shows here).
                zerr = max((abs(r[3] - ground - alt) for r in rows[i0:]), default=0)
                metrics['max_alt_err_m'] = max(metrics.get('max_alt_err_m', 0), zerr)
                say(f'hold {step.get("s", 10)} s: max drift {err:.2f} m, height err {zerr:.2f} m')
            elif do == 'goto':
                n, e = float(step.get('n', 0)), float(step.get('e', 0))
                if not offboard:
                    await drone.offboard.set_position_ned(PositionNedYaw(pos()[1], pos()[2], -(ground + alt), 0))
                    await drone.offboard.start()
                    offboard = True
                n0, e0 = pos()[1], pos()[2]
                dist = math.hypot(n - n0, e - e0) or 1.0
                un, ue = (n - n0) / dist, (e - e0) / dist
                await drone.offboard.set_position_ned(PositionNedYaw(n, e, -(ground + alt), 0))
                peak, tmove = 0.0, time.monotonic()
                async for p in drone.telemetry.position_velocity_ned():
                    along = (p.position.north_m - n0) * un + (p.position.east_m - e0) * ue
                    peak = max(peak, along)
                    if (math.hypot(p.position.north_m - n, p.position.east_m - e) < 0.2
                            and math.hypot(p.velocity.north_m_s, p.velocity.east_m_s) < 0.1):
                        break
                    if time.monotonic() - tmove > 60:
                        say('goto: not settled after 60 s')
                        break
                metrics['max_overshoot_m'] = max(metrics.get('max_overshoot_m', 0), peak - dist)
                say(f'goto n={n} e={e}: overshoot {peak - dist:.2f} m')
            elif do == 'plan':
                # P14: A* over the world's obstacle table (agent/planner.py), then fly the legs: pass-through legs
                # accept within 0.4 m, the goal settles like goto (0.2 m, 0.1 m/s). The legs go in metrics['plan'].
                sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                from planner import plan as plan_path
                tab = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'worlds',
                                                  f'{spec.get("world")}.json')))
                n, e = float(step.get('n', 0)), float(step.get('e', 0))
                if not offboard:
                    await drone.offboard.set_position_ned(PositionNedYaw(pos()[1], pos()[2], -(ground + alt), 0))
                    await drone.offboard.start()
                    offboard = True
                wps = plan_path(tab, (pos()[1], pos()[2]), (n, e), float(step.get('margin', 0.6)))
                metrics.setdefault('plan', []).append(wps)
                say(f'plan to n={n} e={e}: {len(wps)} legs {wps}')
                tmove = time.monotonic()
                for k, (wn, we) in enumerate(wps):
                    last = k == len(wps) - 1
                    await drone.offboard.set_position_ned(PositionNedYaw(wn, we, -(ground + alt), 0))
                    async for p in drone.telemetry.position_velocity_ned():
                        d = math.hypot(p.position.north_m - wn, p.position.east_m - we)
                        if (d < 0.2 and math.hypot(p.velocity.north_m_s, p.velocity.east_m_s) < 0.1) if last else d < 0.4:
                            break
                        if time.monotonic() - tmove > 90:
                            say('plan: not at the goal after 90 s')
                            break
                say(f'plan reached n={n} e={e}')
            elif do == 'track':
                # Figure-8 (lemniscate of Gerono) or circle around the current point, flown in offboard
                # with velocity feedforward. The phase rate ramps up over the first ramp_s and down over
                # the last, so neither end has a velocity jump. The reference clock is the vehicle's own
                # (IMU timestamp), not wall time x speed, which drifts when the sim runs behind. Error =
                # horizontal distance to the reference, counted in the full-speed part only.
                a, T, laps = float(step.get('size', 10)), float(step.get('period', 20)), float(step.get('laps', 2))
                ramp, shape, w = float(step.get('ramp_s', T / 2)), step.get('shape', 'fig8'), 2 * math.pi / T
                cruise = laps * T - ramp  # full-speed time; ramps add ramp/2 of phase each
                if not offboard:
                    await drone.offboard.set_position_ned(PositionNedYaw(pos()[1], pos()[2], -(ground + alt), 0))
                    await drone.offboard.start()
                    offboard = True
                n0, e0 = pos()[1], pos()[2]
                def ref(t):
                    if t < ramp:
                        ph, dph = w * t * t / (2 * ramp), w * t / ramp
                    elif t < ramp + cruise:
                        ph, dph = w * (t - ramp / 2), w
                    else:
                        r = min(ramp * 2 + cruise - t, ramp)  # time left to the stop
                        ph, dph = laps * 2 * math.pi - w * r * r / (2 * ramp), w * r / ramp
                    if shape == 'circle':
                        return (n0 + a * (math.cos(ph) - 1), e0 + a * math.sin(ph),
                                -a * math.sin(ph) * dph, a * math.cos(ph) * dph)
                    return (n0 + a * math.sin(ph), e0 + a / 2 * math.sin(2 * ph),
                            a * math.cos(ph) * dph, a * math.cos(2 * ph) * dph)
                us0, errs = simt['us'], []
                while (t := (simt['us'] - us0) / 1e6) < 2 * ramp + cruise:
                    rn, re, vn, ve = ref(t)
                    await drone.offboard.set_position_velocity_ned(PositionNedYaw(rn, re, -(ground + alt), 0),
                                                                   VelocityNedYaw(vn, ve, 0, 0))
                    if ramp <= t < ramp + cruise:
                        errs.append(math.hypot(pos()[1] - rn, pos()[2] - re))
                    await asyncio.sleep(0.01)
                # MAVSDK keeps resending the last setpoint; make it a still one at the end point.
                await drone.offboard.set_position_ned(PositionNedYaw(*ref(2 * ramp + cruise)[:2], -(ground + alt), 0))
                rms = math.sqrt(sum(x * x for x in errs) / len(errs)) if errs else 0.0
                metrics['rms_track_err_m'] = max(metrics.get('rms_track_err_m', 0), rms)
                metrics['max_track_err_m'] = max(metrics.get('max_track_err_m', 0), max(errs, default=0))
                say(f'track {shape} {a} m / {T} s x{laps}: rms {rms:.2f} m, max {max(errs, default=0):.2f} m')
            elif do == 'excite':
                # Attitude multisine, the twin of the real drone's angle sysid (ground_station/autotune/excitation.py:
                # 20 log-spaced tones, Schroeder phases, f/f0 pre-emphasis, 1.5 s cosine ramps). Flown in offboard
                # attitude; height is held by a PD+I on thrust around MPC_THR_HOVER. Setpoints go at 100 Hz wall,
                # so run this scenario at speed 1. FRF: ULog vehicle_attitude_setpoint -> vehicle_attitude.
                axis, amp = step.get('axis', 'roll'), float(step.get('amp', 6))
                f0, f1, dur = float(step.get('f0', 0.2)), float(step.get('f1', 6)), float(step.get('duration_s', 30))
                K, rmp = 20, 1.5
                fk = [f0 * (f1 / f0) ** (k / (K - 1)) for k in range(K)]
                ph = [-math.pi * k * k / K for k in range(K)]
                wk = [f / f0 for f in fk]
                tone = lambda t: sum(w * math.sin(2 * math.pi * f * t + p) for f, p, w in zip(fk, ph, wk))
                norm = 1.05 * max(abs(tone(i * 0.002)) for i in range(int(min(dur, 8) / 0.002) + 1))
                hov = await drone.param.get_param_float('MPC_THR_HOVER')
                if not offboard:
                    await drone.offboard.set_position_ned(PositionNedYaw(pos()[1], pos()[2], -(ground + alt), 0))
                    await drone.offboard.start()
                    offboard = True
                href, integ, tstart = ground + alt, 0.0, time.monotonic()
                h_prev, t_prev, vz = pos()[3], tstart, 0.0
                while (t := time.monotonic() - tstart) < dur + 2 * rmp:
                    env = 0.5 * (1 - math.cos(math.pi * t / rmp)) if t < rmp else \
                        1.0 if t < rmp + dur else 0.5 * (1 + math.cos(math.pi * (t - rmp - dur) / rmp))
                    d = amp * env * tone(t) / norm
                    now, h = time.monotonic(), pos()[3]
                    if h != h_prev:  # new position sample (50 Hz stream)
                        vz, h_prev, t_prev = (h - h_prev) / max(now - t_prev, 1e-3), h, now
                    e = href - h
                    integ = max(-0.1, min(0.1, integ + 0.05 * e * 0.01))
                    thr = (hov + 0.15 * e - 0.12 * vz + integ) / max(math.cos(math.radians(d)), 0.8)
                    r, p_ = (d, 0.0) if axis == 'roll' else (0.0, d)
                    await drone.offboard.set_attitude(Attitude(r, p_, 0.0, max(0.05, min(0.9, thr))))
                    await asyncio.sleep(0.01)
                await drone.offboard.set_position_ned(PositionNedYaw(pos()[1], pos()[2], -(ground + alt), 0))
                say(f'excite {axis} multisine {f0}-{f1} Hz {amp} deg {dur} s done (hover thrust {hov:.2f})')
            elif do == 'wind':
                # gz world with WindEffects (worlds/gusty.sdf) only: start agent/gz_wind.py (system python, gz
                # bindings) in the background with this step as its profile; it ends itself after dur_s.
                prof = {k: v for k, v in step.items() if k != 'do'}
                if prof.get('seed') == 'run':  # paired A/B: run i of every arm (arms.py dir NAME-i) gets seed i
                    m = regex.search(r'-(\d+)(-retry\d+)?$', os.path.basename(os.path.normpath(out)))
                    prof['seed'] = int(m.group(1)) if m else 1
                wind_proc = subprocess.Popen(['/usr/bin/python3', os.path.join(os.path.dirname(__file__), 'gz_wind.py'),
                                              spec.get('world', 'default'), out, json.dumps(prof)],
                                             env=dict(os.environ, GZ_IP='127.0.0.1', GZ_PARTITION=f'px4-{inst}'))
                say(f'wind {prof}')
            elif do == 'param':
                v = step['value']
                if v == 'run':  # paired A/B seed (e.g. SIH_WIND_SEED): run i of every arm gets i, as in the wind step
                    m = regex.search(r'-(\d+)(-retry\d+)?$', os.path.basename(os.path.normpath(out)))
                    v = int(m.group(1)) if m else 1
                old = await set_param(drone, step['name'], v)
                restore.setdefault(step['name'], old)
            elif do == 'failure':
                await drone.failure.inject(getattr(FailureUnit, step['unit']),
                                           getattr(FailureType, step['type']),
                                           int(step.get('instance', 0)))
                say(f'failure {step["unit"]} {step["type"]} injected')
            elif do == 'land':
                if offboard:
                    await drone.offboard.stop()
                    offboard = False
                await drone.action.land()
                await wait_until(drone.telemetry.in_air(), lambda a: not a, 120)
                metrics['landed'] = True
                say('landed')
    except (OffboardError, asyncio.TimeoutError, Exception) as e:  # noqa: B014 - report any step failure
        say(f'step failed: {type(e).__name__} {e}')
        metrics['error'] = f'{type(e).__name__} {e}'
    finally:
        for k, v in restore.items():
            if v is not None:
                await set_param(drone, k, v, quiet=True)
    if rows:
        metrics['max_tilt_deg'] = max(max(abs(r[6]), abs(r[7])) for r in rows)


async def set_param(drone, k, v, quiet=False):
    # Integer params need the int setter; returns the old value so the scenario can restore it.
    if isinstance(v, int):
        old = await drone.param.get_param_int(k)
        await drone.param.set_param_int(k, v)
    else:
        old = await drone.param.get_param_float(k)
        await drone.param.set_param_float(k, float(v))
    if not quiet:
        say(f'param {k}: {old} -> {v}')
    return old


def obstacle_clearance():
    """gz world with an obstacle table (worlds/NAME.json, e.g. obstacles.json): smallest horizontal distance from
    the drone centre to an obstacle surface over the in-air samples below the obstacle top. Intrusion = drone
    radius - clearance (0 = never touched); gz physics also collides, so a hit shows in tilt and track too."""
    f = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'worlds', f'{spec.get("world")}.json')
    if spec.get('sim') != 'gz' or not os.path.exists(f):
        return
    tab = json.load(open(f))
    best, near = math.inf, ''
    for r in rows:
        if r[3] < 0.3:  # on the ground
            continue
        for o in tab['obstacles']:
            if r[3] > o['h']:
                continue
            dn, de = r[1] - o['n'], r[2] - o['e']
            if o['kind'] == 'pole':
                d = math.hypot(dn, de) - o['r']
            else:
                d = math.hypot(max(abs(dn) - o['dn'] / 2, 0), max(abs(de) - o['de'] / 2, 0))
            if d < best:
                best, near = d, o['name']
    metrics['min_clearance_m'] = best
    metrics['closest_obstacle'] = near
    metrics['obstacle_intrusion_m'] = max(0.0, tab['drone_radius_m'] - best)


def verdict():
    lim, ok = spec.get('limits', {}), True
    table = []
    for k, v in lim.items():
        if k == 'must_land':
            got, good = metrics.get('landed', False), (not v) or metrics.get('landed', False)
        else:
            got = metrics.get(k)
            good = got is not None and got <= v
        ok &= good
        table.append(f'{"PASS" if good else "FAIL"} {k}: {got if not isinstance(got, float) else round(got, 3)} (limit {v})')
    if 'error' in metrics:
        ok = False
        table.append(f'FAIL error: {metrics["error"]}')
    return ok, table


def report(ok, table):
    with open(os.path.join(out, 'telemetry.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['t_wall', 'n', 'e', 'alt', 'vn', 've', 'roll_deg', 'pitch_deg'])
        w.writerows(rows)
    json.dump({'scenario': name, 'pass': ok, 'metrics': metrics, 'checks': table,
               'events': events, 'spec': spec}, open(os.path.join(out, 'metrics.json'), 'w'), indent=1)
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        t = [r[0] for r in rows]
        fig, ax = plt.subplots(3, 1, figsize=(9, 7), sharex=True)
        for i, lab in ((1, 'north'), (2, 'east'), (3, 'alt')):
            ax[0].plot(t, [r[i] for r in rows], label=lab)
        ax[1].plot(t, [r[4] for r in rows], label='vn')
        ax[1].plot(t, [r[5] for r in rows], label='ve')
        ax[2].plot(t, [r[6] for r in rows], label='roll')
        ax[2].plot(t, [r[7] for r in rows], label='pitch')
        for a, y in zip(ax, ('m', 'm/s', 'deg')):
            a.set_ylabel(y)
            a.legend(loc='upper right')
            a.grid(alpha=.3)
        ax[2].set_xlabel('wall s')
        fig.suptitle(f'{name}: {"PASS" if ok else "FAIL"}')
        fig.tight_layout()
        fig.savefig(os.path.join(out, 'plot.png'), dpi=90)
    except ImportError:
        say('matplotlib missing: no plot')


async def main():
    # Same start every run: wipe saved params, then apply boot params (read only at startup,
    # e.g. SYS_FAILURE_EN) through PX4's PX4_PARAM_<NAME> environment override.
    subprocess.run([PX4CTL, 'reset', str(inst)], capture_output=True)
    t_boot = time.time()
    # Takeoff altitude is a boot param too: a live MAVSDK set right after connect was lost in 1 of 3 runs.
    # An airframe profile (airframes/NAME.json) is a set of SIH boot params on a stock SIH base, e.g.
    # a 95 kg coaxial octo flown as quadx; the scenario's own boot_params win over the profile's.
    af = json.load(open(os.path.join(os.path.dirname(PX4CTL), 'airframes', spec['airframe'] + '.json'))) \
        if 'airframe' in spec else {}
    # ULog at full rate by default: SDLOG_PROFILE bits default 1 + EKF replay 2 + sysid 8 + high rate 16
    # + vision 128 (PX4 module.yaml); "log": "default" keeps the SITL default 131.
    boot = {'MIS_TAKEOFF_ALT': float(spec.get('alt', 5)),
            'SDLOG_PROFILE': 131 if spec.get('log') == 'default' else 155,
            **af.get('params', {}), **spec.get('boot_params', {})}
    env = dict(os.environ, PX4_SIM_SPEED_FACTOR=str(spec.get('speed', 1)),
               **{f'PX4_PARAM_{k}': str(v) for k, v in boot.items()})
    start = ['run', str(inst), spec.get('vehicle', af.get('base', 'quadx'))] if spec.get('sim', 'sih') == 'sih' else \
        ['gz', str(inst), spec.get('vehicle', 'x500'), spec.get('world', 'default')]
    # "video" names the Gazebo cameras to record, each to OUTDIR/gazebo-CAM.mp4: "chase" rides on vehicle
    # x500_chase, "overview" stands in world "video" (worlds/video.sdf); true means ["chase"]. Rendering
    # gates the lockstep sim, so a recorded run is several times slower than real time, more so per camera.
    cams = spec.get('video') or []
    cams = ['chase'] if cams is True else cams
    video = bool(cams) and start[0] == 'gz'
    if video:
        global SLOW, on_ready
        SLOW = 15 * len(cams)
        def on_ready():
            # Rendering runs the sim at ~0.12x. PX4 sends HEARTBEAT at 1 Hz of sim time, i.e. one per
            # ~8 s of wall time, past MAVSDK's wall-clock heartbeat timeout: it drops the vehicle and
            # mavsdk_server aborts at offboard start. 20 Hz sim is ~2 Hz wall on the API link.
            subprocess.run([PX4CTL, 'cmd', str(inst), 'mavlink', 'stream', '-u', str(14580 + inst),
                            '-s', 'HEARTBEAT', '-r', '20'], capture_output=True)
            for c in cams:
                mp4 = os.path.join(os.path.abspath(out), f'gazebo-{c}.mp4')
                gz_record(inst, c, f'start: true, format: "mp4", save_filename: "{mp4}"')
    sim = subprocess.Popen([PX4CTL] + start, env=env, stdout=open(os.path.join(out, 'sim.log'), 'w'),
                           stderr=subprocess.STDOUT)
    say(f'sim {" ".join(start)} speed {spec.get("speed", 1)} -> {out}')
    drone = System(port=50051 + inst)

    async def sim_alive():
        # A launcher that dies at boot (bad instance, missing model) would otherwise leave
        # fly() waiting on a vehicle that never appears.
        while sim.poll() is None:
            await asyncio.sleep(1)
        raise RuntimeError(f'sim launcher exited rc={sim.returncode}, see sim.log')

    try:
        await drone.connect(system_address=f'udpin://0.0.0.0:{14540 + inst}')
        watch = asyncio.ensure_future(sim_alive())
        done, _ = await asyncio.wait([asyncio.ensure_future(fly(drone)), watch],
                                     return_when=asyncio.FIRST_COMPLETED)
        watch.cancel()
        for t in done:
            t.result()
    except Exception as e:  # noqa: BLE001 - connection loss still gets a report
        say(f'run failed: {type(e).__name__} {e}')
        metrics['error'] = f'{type(e).__name__} {e}'
    finally:
        if video:
            for c in cams:  # the recorder finalises the mp4 on stop, before the world goes away
                gz_record(inst, c, 'stop: true')
        subprocess.run([PX4CTL, 'cmd', str(inst), 'shutdown'], capture_output=True)
        try:
            sim.wait(20)
        except subprocess.TimeoutExpired:
            sim.kill()
        drone._stop_mavsdk_server()  # an orphaned server keeps the port and breaks the next run
    # The ULog closes at shutdown; keep this run's copy next to the report (flight.ulg).
    logs = [p for p in glob.glob(os.path.expanduser(f'~/.local/state/px4/runs/instance-{inst}/log/*/*.ulg'))
            if os.path.getmtime(p) > t_boot]
    if logs:
        shutil.copy(max(logs, key=os.path.getmtime), os.path.join(out, 'flight.ulg'))
    # SIH under load can stall baro/compass after takeoff; PX4 then blind-lands on invalid setpoints
    # (seen 2026-11-03, healthy runs show no such line after takeoff). That is the sim, not the change.
    airborne = False
    for line in open(os.path.join(out, 'sim.log'), errors='replace'):
        airborne |= 'Takeoff detected' in line
        if airborne and 'No valid data from' in line:
            metrics['sim_fault'] = line.strip()
            break
    obstacle_clearance()
    ok, table = verdict()
    if 'sim_fault' in metrics:
        table.append(f'SIM-FAULT {metrics["sim_fault"]}')
    report(ok, table)
    print('\n'.join(table))
    verdict_word = 'SIM-FAULT' if 'sim_fault' in metrics else 'PASS' if ok else 'FAIL'
    print(f'{verdict_word} {name} -> {out}', flush=True)
    os._exit(3 if 'sim_fault' in metrics else 0 if ok else 1)  # mavsdk_server threads would otherwise keep the process alive


asyncio.run(main())
