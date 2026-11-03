# P11 — thesis campaign in SIH (sim twins + sim-only extras)

[S] GitHub Actions run 41683452873 (`arms.yml`, runs 5, commit c4623e2): 19 arms × 5 seeds, 98/98 jobs green,
94/95 runs PASS (the one FAIL: p11-gps-lqr-plus-mrac, max_hold_err_m 0.50 at the 0.5 m limit).

Setup: research-drone SIH airframe (`airframes/research-drone.json`, PX4 gains untuned), twin of `lab_e_exp_*`
(takeoff 0.5 m, hold 3 s, figure-8 0.3 m / 18 s, hold 3 s, land). plus-mrac = MRL_EN_RATE/ATT/POS 1. Position
sensing SIM_GPS_NSCL 0.1 [A camera-class]; the `p11-gps-*` arms use stock SIH GPS. Errors are horizontal, from the
EKF estimate. Effect size = Hedges g (plus-mrac minus alone, n 5 + 5); p = Welch t. Negative diff = MRAC better
for error metrics.

## Bottom line

| question | answer [S] |
|---|---|
| Does MRAC change tracking on the twin? | No clear effect: diffs −0.03…+0.05 m, all p > 0.08 (n 5). |
| Does it change hold error? | Smaller for lqr (−0.09 m, g −1.2, p 0.09) and mpc (−0.06 m, g −1.5, p 0.03). |
| What does it cost? | Attitude tracking error +0.1…+1.2° in EVERY pair (g +1.0…+4.3, 7 of 9 p < 0.05); rate RMS up. |
| Mass +31 % mid-flight | Best case for MRAC: track 0.244 → 0.172 m (g −1.3, p 0.08). |
| Slow motors (tau 0.12) | MRAC worse: track 0.149 → 0.202 m (g +1.0, p 0.11). |
| T_MAX −25 %, injected dist, aggressive fig8 | No resolved position effect (|g| < 0.9 on track/hold, all p > 0.2). |
| ADRC (WC 2.5) | Lowest track error of all baselines (0.053 m) but tilt 15–20° and att error 2.6°: aggressive. |

Caveats: n = 5 per arm, so |g| < ~1.3 is not resolved; the camera noise level is assumed, not measured; local
2-run checks gave lqr-alone track 0.17–0.20 m vs 0.255 m here (seed spread is large at this 0.3 m scale); the
earlier local hint "MRAC raises post-figure hold drift" did NOT reproduce (cloud: hold error lower with MRAC).
Not covered yet from the P11 list: wind gusts (SIH has no wind), motor loss, added delay, per-loop layer on/off.

## Effect sizes (alone → plus-mrac)

| pair | metric | alone | plus-mrac | diff | g | p |
|---|---|---|---|---|---|---|
| p11-adrc | rms_track_err_m | 0.053 | 0.070 | +0.017 | +0.90 | 0.166 |
| p11-adrc | max_hold_err_m | 0.189 | 0.214 | +0.025 | +0.37 | 0.538 |
| p11-adrc | att_track_rms_deg | 2.639 | 3.824 | +1.185 | +3.72 | 0.00033 |
| p11-gps-lqr | rms_track_err_m | 0.334 | 0.303 | -0.031 | -0.42 | 0.483 |
| p11-gps-lqr | max_hold_err_m | 0.317 | 0.376 | +0.059 | +0.54 | 0.384 |
| p11-gps-lqr | att_track_rms_deg | 0.605 | 0.709 | +0.104 | +1.04 | 0.141 |
| p11-lqr | rms_track_err_m | 0.255 | 0.229 | -0.026 | -0.56 | 0.356 |
| p11-lqr | max_hold_err_m | 0.281 | 0.190 | -0.090 | -1.22 | 0.0888 |
| p11-lqr | att_track_rms_deg | 0.603 | 0.853 | +0.251 | +1.17 | 0.109 |
| p11-mpc | rms_track_err_m | 0.231 | 0.201 | -0.030 | -0.56 | 0.371 |
| p11-mpc | max_hold_err_m | 0.265 | 0.206 | -0.058 | -1.53 | 0.0326 |
| p11-mpc | att_track_rms_deg | 0.566 | 0.798 | +0.231 | +1.56 | 0.0483 |
| p11-x-aggr-lqr | rms_track_err_m | 0.760 | 0.778 | +0.018 | +0.35 | 0.56 |
| p11-x-aggr-lqr | max_hold_err_m | 0.364 | 0.335 | -0.029 | -0.25 | 0.683 |
| p11-x-aggr-lqr | att_track_rms_deg | 2.221 | 2.468 | +0.247 | +1.98 | 0.0122 |
| p11-x-dist-lqr | rms_track_err_m | 0.193 | 0.194 | +0.001 | +0.01 | 0.982 |
| p11-x-dist-lqr | max_hold_err_m | 0.295 | 0.241 | -0.054 | -0.82 | 0.213 |
| p11-x-dist-lqr | att_track_rms_deg | 0.611 | 0.932 | +0.320 | +4.34 | 0.000943 |
| p11-x-mass-lqr | rms_track_err_m | 0.244 | 0.172 | -0.072 | -1.30 | 0.0812 |
| p11-x-mass-lqr | max_hold_err_m | 0.265 | 0.226 | -0.040 | -0.77 | 0.229 |
| p11-x-mass-lqr | att_track_rms_deg | 0.606 | 0.923 | +0.316 | +2.16 | 0.0186 |
| p11-x-slow-lqr | rms_track_err_m | 0.149 | 0.202 | +0.053 | +1.04 | 0.114 |
| p11-x-slow-lqr | max_hold_err_m | 0.227 | 0.227 | +0.000 | +0.00 | 0.996 |
| p11-x-slow-lqr | att_track_rms_deg | 0.587 | 0.778 | +0.192 | +2.00 | 0.0208 |
| p11-x-tmax-lqr | rms_track_err_m | 0.161 | 0.177 | +0.017 | +0.47 | 0.439 |
| p11-x-tmax-lqr | max_hold_err_m | 0.231 | 0.205 | -0.026 | -0.34 | 0.569 |
| p11-x-tmax-lqr | att_track_rms_deg | 0.563 | 0.781 | +0.218 | +2.50 | 0.00697 |

## Per-arm results (mean [min..max], n 5)

| arm | n | pass | rms_track_err_m | max_hold_err_m | max_tilt_deg | att_track_rms_deg | rate_rms_rp |
|---|---|---|---|---|---|---|---|
| p11-adrc-alone | 5 | 5/5 | 0.053 [0.04..0.06] | 0.189 [0.13..0.28] | 15.492 [9.60..22.69] | 2.639 [2.44..3.02] | 0.119 [0.11..0.13] |
| p11-adrc-plus-mrac | 5 | 5/5 | 0.070 [0.04..0.09] | 0.214 [0.15..0.32] | 20.060 [12.18..22.90] | 3.824 [3.59..4.39] | 0.188 [0.12..0.28] |
| p11-gps-lqr-alone | 5 | 5/5 | 0.334 [0.26..0.40] | 0.317 [0.25..0.40] | 8.009 [5.75..12.04] | 0.605 [0.59..0.63] | 0.074 [0.07..0.07] |
| p11-gps-lqr-plus-mrac | 5 | 4/5 | 0.303 [0.21..0.37] | 0.376 [0.25..0.50] | 6.343 [5.39..7.16] | 0.709 [0.61..0.93] | 0.080 [0.08..0.09] |
| p11-lqr-alone | 5 | 5/5 | 0.255 [0.21..0.31] | 0.281 [0.16..0.39] | 6.304 [5.75..6.71] | 0.603 [0.58..0.64] | 0.073 [0.07..0.07] |
| p11-lqr-plus-mrac | 5 | 5/5 | 0.229 [0.20..0.30] | 0.190 [0.14..0.22] | 6.642 [5.82..7.51] | 0.853 [0.68..1.33] | 0.087 [0.08..0.12] |
| p11-mpc-alone | 5 | 5/5 | 0.231 [0.20..0.27] | 0.265 [0.22..0.32] | 5.872 [5.29..6.18] | 0.566 [0.51..0.60] | 0.073 [0.07..0.07] |
| p11-mpc-plus-mrac | 5 | 5/5 | 0.201 [0.09..0.25] | 0.206 [0.17..0.23] | 5.505 [4.62..6.17] | 0.798 [0.64..1.00] | 0.085 [0.08..0.10] |
| p11-pid-alone | 5 | 5/5 | 0.196 [0.14..0.23] | 0.222 [0.15..0.31] | 4.673 [3.58..6.37] | 0.695 [0.66..0.72] | 0.080 [0.08..0.08] |
| p11-x-aggr-lqr-alone | 5 | 5/5 | 0.760 [0.71..0.85] | 0.364 [0.29..0.47] | 15.340 [14.59..16.87] | 2.221 [2.13..2.47] | 0.078 [0.08..0.08] |
| p11-x-aggr-lqr-plus-mrac | 5 | 5/5 | 0.778 [0.73..0.82] | 0.335 [0.17..0.45] | 15.172 [14.07..16.79] | 2.468 [2.39..2.57] | 0.104 [0.09..0.12] |
| p11-x-dist-lqr-alone | 5 | 5/5 | 0.193 [0.12..0.29] | 0.295 [0.21..0.38] | 6.454 [5.48..7.28] | 0.611 [0.58..0.65] | 0.073 [0.07..0.07] |
| p11-x-dist-lqr-plus-mrac | 5 | 5/5 | 0.194 [0.15..0.26] | 0.241 [0.21..0.28] | 5.892 [5.09..6.35] | 0.932 [0.82..1.06] | 0.092 [0.09..0.10] |
| p11-x-mass-lqr-alone | 5 | 5/5 | 0.244 [0.16..0.35] | 0.265 [0.20..0.35] | 6.194 [5.67..6.85] | 0.606 [0.58..0.62] | 0.073 [0.07..0.07] |
| p11-x-mass-lqr-plus-mrac | 5 | 5/5 | 0.172 [0.15..0.18] | 0.226 [0.20..0.26] | 6.297 [5.86..7.44] | 0.923 [0.70..1.21] | 0.090 [0.08..0.11] |
| p11-x-slow-lqr-alone | 5 | 5/5 | 0.149 [0.13..0.21] | 0.227 [0.18..0.26] | 5.918 [5.11..6.30] | 0.587 [0.55..0.63] | 0.074 [0.07..0.08] |
| p11-x-slow-lqr-plus-mrac | 5 | 5/5 | 0.202 [0.16..0.30] | 0.227 [0.21..0.26] | 5.224 [4.02..6.80] | 0.778 [0.61..0.90] | 0.088 [0.08..0.09] |
| p11-x-tmax-lqr-alone | 5 | 5/5 | 0.161 [0.12..0.20] | 0.231 [0.14..0.35] | 5.407 [4.63..6.20] | 0.563 [0.50..0.59] | 0.072 [0.07..0.07] |
| p11-x-tmax-lqr-plus-mrac | 5 | 5/5 | 0.177 [0.16..0.22] | 0.205 [0.12..0.24] | 5.894 [3.68..6.72] | 0.781 [0.63..0.92] | 0.082 [0.08..0.09] |
