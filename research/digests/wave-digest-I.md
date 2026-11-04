# Wave I digest (B pairs, seeds 11-20)

Made by tools/wave_digest.py with --pair <x>-lqr-plus-mrac=<x>-lqr-alone. Treatment - control per seed: mean [95% interval], * = interval excludes 0.

## I-b-pair-seeds-41795932701: 80/80 flights passed (commit 1d27f15, finished 2026-11-04T08:00:03Z, lost jobs 0)

| deck | pass | failing flights per broken limit (value range > limit) | failing runs |
|---|---|---|---|

Every run passed in 8 of 8 decks.

| treatment - control | pass T, C | n | max_hold_err_m | rms_track_err_m | max_tilt_deg | att_track_rms_deg | rate_rms_rp | motor_sat_frac | xy_err_rms_m |
|---|---|---|---|---|---|---|---|---|---|
| p11-x-dist-lqr-plus-mrac - p11-x-dist-lqr-alone | 10/10, 10/10 | 10 | +0.00528 [-0.0264, +0.0357] | +0.00517 [-0.0125, +0.0225] | +1.17 [+0.774, +1.58]* | +0.134 [+0.0948, +0.174]* | +0.00895 [+0.00737, +0.0105]* | +0.0422 [+0.0337, +0.0498]* | +6.8e-05 [-0.00713, +0.00719] |
| p11-x-mass-lqr-plus-mrac - p11-x-mass-lqr-alone | 10/10, 10/10 | 10 | -0.0217 [-0.0541, +0.0101] | -0.00853 [-0.0284, +0.0133] | -0.153 [-0.618, +0.333] | +0.103 [+0.0426, +0.172]* | +0.00642 [+0.00354, +0.00993]* | +0.0412 [+0.0339, +0.0465]* | -0.0066 [-0.0126, +0.000337] |
| p11-x-slow-lqr-plus-mrac - p11-x-slow-lqr-alone | 10/10, 10/10 | 10 | -0.0269 [-0.0626, +0.00451] | -0.0312 [-0.0501, -0.0113]* | +0.38 [-0.333, +1.3] | +0.157 [+0.0419, +0.294]* | +0.0144 [+0.00731, +0.023]* | +0.0498 [+0.0413, +0.0561]* | -0.0132 [-0.0188, -0.00728]* |
| p11-x-tmax-lqr-plus-mrac - p11-x-tmax-lqr-alone | 10/10, 10/10 | 10 | +0.03 [-0.000204, +0.0659] | -0.0134 [-0.0385, +0.00921] | -0.17 [-0.535, +0.303] | +0.0669 [+0.0241, +0.114]* | +0.00468 [+0.00263, +0.00703]* | +0.0413 [+0.0331, +0.0474]* | -0.00463 [-0.015, +0.00494] |
