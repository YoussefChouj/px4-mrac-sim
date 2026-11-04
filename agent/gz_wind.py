#!/usr/bin/python3
"""Wind driver for a gz world with the WindEffects system (worlds/gusty.sdf), run with the system python
(gz.transport13 bindings), started by scenario.py's "wind" step and stopped at the end of the flight.

Publishes the wind seed on /world/WORLD/wind every 20 ms of SIM time (/world/WORLD/clock; gz runs below real time
on a laptop, about 0.8x, so a wall-clock profile would shrink gusts in sim seconds). Wall clock only if no clock:
  mean wind (ENU m/s) + Dryden-form turbulence + discrete 1-cosine gusts.
Turbulence: each horizontal axis is a first-order Gauss-Markov process u' = -(V/L) u + noise with std sigma,
the first-order (longitudinal) Dryden form, also used for the lateral axis as an approximation
(MIL-F-8785C low altitude: L = h / (0.177 + 0.000823 h)^1.2 in ft, V = mean wind speed, frozen turbulence).
Gust i: amp/2 (1 - cos(2 pi (t - t0) / dur)) for t0 <= t <= t0 + dur along direction dir_deg (ENU, 0 = east).
WindEffects turns the seed into a force on every link with <enable_wind>: F = m c (v_wind - v_link), c set in
the world (force_approximation_scaling_factor). Writes OUT/wind.csv (t, vx, vy, vz commanded) for the analysis.

  gz_wind.py WORLD OUTDIR 'JSON'   JSON: {"mean": [vx, vy], "sigma": 0.8, "L_m": 23, "dur_s": 60, "seed": 1,
                                          "gusts": [{"t": 20, "amp": 4, "dur": 2, "dir_deg": 0}]}
"""
import csv
import json
import math
import random
import sys
import time

from gz.msgs10.clock_pb2 import Clock
from gz.msgs10.wind_pb2 import Wind
from gz.transport13 import Node

world, outdir, cfg = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])
mx, my = cfg.get('mean', [0.0, 0.0])
sigma, L, dur = float(cfg.get('sigma', 0.0)), float(cfg.get('L_m', 23.0)), float(cfg.get('dur_s', 60))
gusts = cfg.get('gusts', [])
rng = random.Random(cfg.get('seed', 1))
dt = 0.02
V = max(math.hypot(mx, my), 1.0)  # frozen-turbulence speed; 1 m/s floor so calm air still decorrelates
a = math.exp(-V * dt / L)
b = sigma * math.sqrt(1 - a * a)
node = Node()
sim = []  # [latest sim time in s] from the world clock


def on_clock(c):
    sim[:] = [c.sim.sec + c.sim.nsec * 1e-9]


node.subscribe(Clock, f'/world/{world}/clock', on_clock)
pub = node.advertise(f'/world/{world}/wind', Wind)
for _ in range(50):  # WindEffects must be listening (same GZ_PARTITION as the sim), else the wind does nothing
    if pub.has_connections():
        break
    time.sleep(0.1)
print(f'gz_wind: /world/{world}/wind subscriber {"found" if pub.has_connections() else "MISSING"}', flush=True)
for _ in range(50):
    if sim:
        break
    time.sleep(0.1)
clock = (lambda: sim[-1]) if sim else time.monotonic
print(f'gz_wind: timing on {"sim clock" if sim else "WALL clock (no /clock)"}', flush=True)
tu = tv = 0.0
t0 = clock()
k = 0  # 20 ms ticks done; the Gauss-Markov process steps once per tick of sim time
with open(f'{outdir}/wind.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['t', 'vx', 'vy', 'vz'])
    while (t := clock() - t0) < dur:
        if t < k * dt:
            time.sleep(0.002)
            continue
        while k * dt <= t:
            tu, tv = a * tu + b * rng.gauss(0, 1), a * tv + b * rng.gauss(0, 1)
            k += 1
        vx, vy = mx + tu, my + tv
        for g in gusts:
            if g['t'] <= t <= g['t'] + g['dur']:
                s = 0.5 * g['amp'] * (1 - math.cos(2 * math.pi * (t - g['t']) / g['dur']))
                vx += s * math.cos(math.radians(g.get('dir_deg', 0)))
                vy += s * math.sin(math.radians(g.get('dir_deg', 0)))
        m = Wind()
        m.enable_wind = True
        m.linear_velocity.x, m.linear_velocity.y = vx, vy
        pub.publish(m)
        w.writerow([f'{t:.3f}', f'{vx:.3f}', f'{vy:.3f}', '0'])
    m = Wind()
    m.enable_wind = True  # calm at the end, so the landing is not blown about
    pub.publish(m)
