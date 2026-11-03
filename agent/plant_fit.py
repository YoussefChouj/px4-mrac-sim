"""Fit the rate plant k e^{-sT} / (s (tau s + 1)) per axis from a sim ULog flown with the MRL_ID_AMP multisine.

Instrumental-variable FRF: the dither d is rebuilt from the torque timestamp_sample (same formula as MracLayers),
so P = S_dy / S_du with u = vehicle_torque_setpoint, y = vehicle_angular_velocity. The fit is the real drone's
(ground_station/autotune/frf.py fit_plant), so tau and delay compare directly with model_rate_*.json.
Usage: plant_fit.py LOG.ulg [FIT_REPO]   (FIT_REPO = FreeRTOS repo root holding ground_station/)
"""
import json, math, sys
import numpy as np
from scipy import signal
from pyulog import ULog

repo = sys.argv[2] if len(sys.argv) > 2 else '/mnt/d/Projects/UAV_lab/FreeRTOS-adaptive-controller-codex'
sys.path.insert(0, repo)
from ground_station.autotune.frf import Frf, fit_plant  # noqa: E402

BAND = (0.5, 20.0)


def dither(ts):
    k = np.arange(12)
    f, ph = 0.5 * 40.0 ** (k / 11.0), np.pi * k * (k + 1) / 12.0
    return np.sin(2 * np.pi * f[None, :] * ts[:, None] + ph[None, :]).sum(1) / 4.0


log = ULog(sys.argv[1])
tq = log.get_dataset('vehicle_torque_setpoint').data
av = log.get_dataset('vehicle_angular_velocity').data
t_u = tq['timestamp_sample'].astype(np.int64)
# excitation windows from the parameter change log: (start, end, axis)
amp, ax, t_on, wins = 0.0, 0, None, []
for t, name, v in sorted(log.changed_parameters, key=lambda c: c[0]):
    if name == 'MRL_ID_AX':
        ax = int(v)
    if name == 'MRL_ID_AMP':
        if v > 0 and amp == 0:
            t_on = t
        elif v == 0 and amp > 0 and t_on:
            wins.append((t_on, t, ax, amp))
        amp = float(v)
out = {'SIM_GZ_ACT_DLY': log.initial_parameters.get('SIM_GZ_ACT_DLY')}
print('SIM_GZ_ACT_DLY', out['SIM_GZ_ACT_DLY'])
for t0, t1, a, A in wins:
    m = (t_u > t0 + 2e6) & (t_u < t1 - 0.5e6)        # skip the first 2 s transient
    tu = t_u[m]
    u = tq[f'xyz[{a}]'][m]
    y = np.interp(tu, av['timestamp_sample'], av[f'xyz[{a}]'])
    d = A * dither(tu * 1e-6)
    fs = 1e6 / np.median(np.diff(tu))
    nper = int(2 ** math.floor(math.log2(len(tu) / 4)))
    _, sdd = signal.csd(d, d, fs=fs, nperseg=nper)
    _, suu = signal.csd(u, u, fs=fs, nperseg=nper)
    _, syy = signal.csd(y, y, fs=fs, nperseg=nper)
    _, sdu = signal.csd(d, u, fs=fs, nperseg=nper)
    f, sdy = signal.csd(d, y, fs=fs, nperseg=nper)
    p = sdy / sdu
    coh = np.minimum(np.abs(sdu) ** 2 / (sdd.real * suu.real), np.abs(sdy) ** 2 / (sdd.real * syy.real))
    keep = (f >= BAND[0]) & (f <= BAND[1]) & (coh >= 0.6) & np.isfinite(p)
    fit = fit_plant(Frf(f, p, np.nan_to_num(coh), keep, BAND, 1.0, len(tu) // (nper // 2)))
    pl = fit.plant
    name = 'roll pitch yaw'.split()[a]
    out[name] = dict(k=pl.k, tau_s=pl.tau_s if hasattr(pl, 'tau_s') else pl.tau, delay_s=getattr(pl, 'delay_s', None),
                     rel_residual=fit.rel_residual, bins=fit.n_bins, fs_hz=fs, n=len(tu),
                     u_rms=float(np.std(u)), y_rms=float(np.std(y)), d_u_corr=float(np.corrcoef(d, u)[0, 1]))
    print(name, {k: round(v, 4) if isinstance(v, float) else v for k, v in out[name].items()})
json.dump(out, open(sys.argv[1] + '.plant.json', 'w'), indent=1)
