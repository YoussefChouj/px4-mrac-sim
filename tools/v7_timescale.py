"""V7 time-scale table on the V5 roll rate model: ref tau x adaptation gain x leakage x delay,
plus frozen-learned (theta learned in the disturbance window, then gam 0) and warm start (same theta, gam on).
Nominal motor lag 0.0505 s, no gyro noise, full torque headroom. Ratio = rms(PID+MRAC) / rms(PID alone).
Usage: python v7_timescale.py OUT_DIR
"""
import csv
import itertools
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import v5_screen as m

delays = [0, 20, 30, 45, 60, 78]          # 78 ms = measured real-drone delay
m.cases = [(d, 0, 0.0505, 1.0) for d in delays]
gams, taus, sigs = [0.5, 1.0, 2.0, 4.0], [0.06, 0.12, 0.2], [0.01, 0.05, 0.2]


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for tau in taus:
        m.TAU = tau
        m.TH0 = None
        base = m.run(False)[0]
        for gam, sig in itertools.product(gams, sigs):
            m.GAM, m.SIG, m.TH0 = gam, sig, None
            on = m.run(True)[0]
            learned = m.SNAP['th'].copy()
            m.TH0, m.GAM = learned, 0.0
            frozen = m.run(True)[0]
            m.GAM = gam
            warm = m.run(True)[0]
            for i, d in enumerate(delays):
                rows.append(dict(tau=tau, gam=gam, sig=sig, delay_ms=d, rms_pid=base[i], ratio_online=on[i] / base[i],
                                 ratio_frozen=frozen[i] / base[i], ratio_warm=warm[i] / base[i]))
    with open(out / 'v7_timescale.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    # configuration rule: per delay, the largest gam whose online ratio stays < 0.9 (BENEFIT) at tau 0.06, sig 0.05
    for d in delays:
        ok = [r['gam'] for r in rows if r['delay_ms'] == d and r['tau'] == 0.06 and r['sig'] == 0.05 and r['ratio_online'] < 0.9]
        best = min((r for r in rows if r['delay_ms'] == d), key=lambda r: r['ratio_online'])
        print(f"delay {d:2d} ms: max benefit gam {max(ok) if ok else 'none'}; best cell tau {best['tau']} gam {best['gam']} "
              f"sig {best['sig']} ratio {best['ratio_online']:.2f} (frozen {best['ratio_frozen']:.2f}, warm {best['ratio_warm']:.2f})")


if __name__ == '__main__':
    main()
