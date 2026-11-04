# Waves B + I pooled (B pairs, seeds 1-20)

B (main 88c63e0, seeds 1-10) and I (main 1d27f15, seeds 11-20) flew one PX4 build (px4-mrac/ and ci/build.sh unchanged). all.json records merged per deck, then tools/wave_digest.py with --pair <x>-lqr-plus-mrac=<x>-lqr-alone. * = 95% interval excludes 0.

## BI-pooled-seeds-1-20: 80/80 flights passed (commit B 88c63, finished 2026-11-04T08:00:03Z, lost jobs 0)

| deck | pass | failing flights per broken limit (value range > limit) | failing runs |
|---|---|---|---|

Every run passed in 8 of 8 decks.

| treatment - control | pass T, C | n | max_hold_err_m | rms_track_err_m | max_tilt_deg | att_track_rms_deg | rate_rms_rp | motor_sat_frac | xy_err_rms_m |
|---|---|---|---|---|---|---|---|---|---|
| p11-x-dist-lqr-plus-mrac - p11-x-dist-lqr-alone | 20/20, 20/20 | 20 | -0.011 [-0.035, +0.012] | -0.00792 [-0.0208, +0.00564] | +1.04 [+0.778, +1.3]* | +0.134 [+0.104, +0.166]* | +0.00944 [+0.00816, +0.011]* | +0.0446 [+0.0394, +0.0493]* | -0.00534 [-0.0103, -0.000177]* |
| p11-x-mass-lqr-plus-mrac - p11-x-mass-lqr-alone | 20/20, 20/20 | 20 | -0.00749 [-0.031, +0.0162] | -0.00879 [-0.0237, +0.00613] | +0.0518 [-0.297, +0.41] | +0.101 [+0.064, +0.14]* | +0.00615 [+0.00437, +0.00813]* | +0.0394 [+0.0345, +0.0438]* | -0.00607 [-0.0115, -0.000552]* |
| p11-x-slow-lqr-plus-mrac - p11-x-slow-lqr-alone | 20/20, 20/20 | 20 | -0.023 [-0.0518, +0.00492] | -0.0133 [-0.0276, +0.000638] | +0.534 [+0.0432, +1.09]* | +0.149 [+0.0807, +0.228]* | +0.0131 [+0.00903, +0.018]* | +0.0439 [+0.0381, +0.0495]* | -0.00647 [-0.0119, -0.000419]* |
| p11-x-tmax-lqr-plus-mrac - p11-x-tmax-lqr-alone | 20/20, 20/20 | 20 | +0.0122 [-0.0164, +0.0399] | -0.00917 [-0.0259, +0.0069] | +0.144 [-0.148, +0.45] | +0.102 [+0.052, +0.156]* | +0.00657 [+0.00393, +0.00959]* | +0.0361 [+0.0302, +0.0416]* | -0.00314 [-0.00991, +0.00309] |
