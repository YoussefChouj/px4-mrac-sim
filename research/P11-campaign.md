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


## Batch 2 — delay, partial motor loss, one layer at a time

[S] GitHub Actions run 41688393980 (sim repo 4ad8b9f), 11 arms × 5 seeds, 55/55 PASS. New sim patch
`px4-mrac/patch_sih_delay.py`: SIH_ACT_DLY (pure actuator delay, ms) and SIH_MOT1_EFF (motor 1 thrust scale).
Local check: with eff 0.7, motor 1 is commanded 0.544 vs 0.38 for the others (ratio 0.70). The two lqr twins were
re-run on this build as controls.

| question | answer [S] |
|---|---|
| With the real drone's delay (13 ms) | MRAC rate activity rate_rms 0.078 → 0.514 (×6.6, p 6e-6), att error 0.59 → 1.50° (p 0.002); hold error lower (0.305 → 0.207 m, p 0.04); tracking unchanged. |
| With 40 ms delay | MRAC near its stability edge: rate_rms 0.12 → 1.92, att error 0.63 → 5.70° (p < 1e-7); position still unchanged. |
| Motor 1 at 70 % mid-flight | The only case where MRAC LOWERS attitude error: 0.82 → 0.71° (p 0.008); position n.s. |
| One layer at a time (no delay) | track rate-only 0.227, att-only 0.183, pos-only 0.250 m vs alone 0.152 / all three 0.212; hold all 0.22–0.25 m. |
| Re-run controls | lqr-alone track 0.152 here vs 0.255 in batch 1; lqr-plus-mrac 0.212 vs 0.229. Batch 2 says MRAC tracks worse (p 0.01), batch 1 slightly better (n.s.). |

What this means:
- **Delay is the thesis-relevant risk.** The twins without delay are optimistic for MRAC. At the real 13 ms, the
  adaptive layers already turn rate activity up six-fold. Next check: which layer causes it (dly13 + one layer on).
  The candidate fix is the adaptation rate or a delay-aware reference model, not a lower bandwidth.
- **The control arm moved between batches.** lqr-alone track 0.152 vs 0.255 is a batch-to-batch shift. The only
  build difference is the SIH patch at its no-op default. So n = 5 does not resolve the tracking effects of
  ±0.05 m, and only effects that repeat across batches (attitude cost, delay sensitivity, motor-loss benefit)
  should be quoted.
- Still not covered: wind (SIH has none; it needs gz). Full motor loss is unrecoverable on a quad for every arm.
- **Next steps:**
  - pinpoint the layer at 13 ms delay;
  - seed control (fixed seeds per arm), so batches can be compared;
  - wind gusts in gz.

### Batch 2 tables (mean [min..max], n 5; pairs with Hedges g and Welch p)

| arm | n | pass | rms_track_err_m | max_hold_err_m | max_tilt_deg | att_track_rms_deg | rate_rms_rp |
|---|---|---|---|---|---|---|---|
| p11-lqr-alone | 5 | 5/5 | 0.152 [0.11..0.18] | 0.245 [0.13..0.33] | 5.193 [3.80..7.34] | 0.593 [0.57..0.61] | 0.074 [0.07..0.07] |
| p11-lqr-plus-mrac | 5 | 5/5 | 0.212 [0.18..0.25] | 0.226 [0.15..0.37] | 6.260 [5.70..6.95] | 0.684 [0.60..0.71] | 0.078 [0.08..0.08] |
| p11-x-attonly-lqr | 5 | 5/5 | 0.183 [0.12..0.27] | 0.249 [0.18..0.34] | 5.434 [4.13..5.99] | 0.586 [0.56..0.62] | 0.073 [0.07..0.07] |
| p11-x-dly13-lqr-alone | 5 | 5/5 | 0.206 [0.11..0.26] | 0.305 [0.23..0.38] | 5.186 [4.23..5.96] | 0.591 [0.52..0.64] | 0.078 [0.08..0.08] |
| p11-x-dly13-lqr-plus-mrac | 5 | 5/5 | 0.205 [0.14..0.23] | 0.207 [0.16..0.26] | 11.407 [8.23..16.91] | 1.504 [1.30..1.92] | 0.514 [0.49..0.56] |
| p11-x-dly40-lqr-alone | 5 | 5/5 | 0.199 [0.15..0.25] | 0.247 [0.19..0.30] | 5.952 [5.34..6.51] | 0.633 [0.58..0.66] | 0.124 [0.12..0.13] |
| p11-x-dly40-lqr-plus-mrac | 5 | 5/5 | 0.218 [0.15..0.28] | 0.250 [0.21..0.33] | 16.980 [13.39..22.45] | 5.698 [5.56..5.92] | 1.918 [1.88..1.96] |
| p11-x-mot1-lqr-alone | 5 | 5/5 | 0.186 [0.13..0.23] | 0.260 [0.19..0.32] | 5.112 [4.62..5.54] | 0.824 [0.79..0.84] | 0.084 [0.08..0.08] |
| p11-x-mot1-lqr-plus-mrac | 5 | 5/5 | 0.194 [0.17..0.22] | 0.346 [0.20..0.47] | 5.061 [3.97..6.08] | 0.714 [0.68..0.81] | 0.081 [0.08..0.08] |
| p11-x-posonly-lqr | 5 | 5/5 | 0.250 [0.18..0.29] | 0.237 [0.16..0.40] | 6.264 [5.22..7.46] | 0.708 [0.61..0.81] | 0.076 [0.07..0.08] |
| p11-x-rateonly-lqr | 5 | 5/5 | 0.227 [0.20..0.24] | 0.222 [0.19..0.27] | 6.216 [5.52..6.58] | 0.660 [0.64..0.69] | 0.077 [0.08..0.08] |

| pair (alone -> plus-mrac) | metric | alone | plus-mrac | diff | g | p (Welch) |
|---|---|---|---|---|---|---|
| p11-lqr | rms_track_err_m | 0.152 | 0.212 | +0.061 | +1.94 | 0.00999 |
| p11-lqr | max_hold_err_m | 0.245 | 0.226 | -0.019 | -0.21 | 0.728 |
| p11-lqr | att_track_rms_deg | 0.593 | 0.684 | +0.092 | +2.41 | 0.00829 |
| p11-lqr | rate_rms_rp | 0.074 | 0.078 | +0.005 | +1.98 | 0.0206 |
| p11-x-dly13-lqr | rms_track_err_m | 0.206 | 0.205 | -0.001 | -0.01 | 0.982 |
| p11-x-dly13-lqr | max_hold_err_m | 0.305 | 0.207 | -0.098 | -1.50 | 0.0379 |
| p11-x-dly13-lqr | att_track_rms_deg | 0.591 | 1.504 | +0.914 | +4.07 | 0.00164 |
| p11-x-dly13-lqr | rate_rms_rp | 0.078 | 0.514 | +0.436 | +17.63 | 6.49e-06 |
| p11-x-dly40-lqr | rms_track_err_m | 0.199 | 0.218 | +0.019 | +0.34 | 0.565 |
| p11-x-dly40-lqr | max_hold_err_m | 0.247 | 0.250 | +0.003 | +0.05 | 0.927 |
| p11-x-dly40-lqr | att_track_rms_deg | 0.633 | 5.698 | +5.064 | +46.21 | 3.39e-08 |
| p11-x-dly40-lqr | rate_rms_rp | 0.124 | 1.918 | +1.794 | +71.94 | 1.43e-08 |
| p11-x-mot1-lqr | rms_track_err_m | 0.186 | 0.194 | +0.009 | +0.24 | 0.693 |
| p11-x-mot1-lqr | max_hold_err_m | 0.260 | 0.346 | +0.086 | +0.86 | 0.183 |
| p11-x-mot1-lqr | att_track_rms_deg | 0.824 | 0.714 | -0.110 | -2.42 | 0.00827 |
| p11-x-mot1-lqr | rate_rms_rp | 0.084 | 0.081 | -0.003 | -1.42 | 0.0657 |


## Batch 3 — which layer reacts to the 13 ms delay

[S] GitHub Actions run 41690407503 (sim repo e804168), 5 arms × 5 runs, all at SIH_ACT_DLY 13.

| arm (13 ms) | rate_rms_rp | att err ° | rate-layer u_ad max | pass |
|---|---|---|---|---|
| lqr-alone | 0.077 | 0.60 | — | 5/5 |
| att-only | 0.078 | 0.59 | — | 5/5 |
| pos-only | 0.081 | 0.66 | — | 5/5 |
| rate-only | 0.287 | 0.61 | 0.30 (clamp) in 5/5 | 0/5 |
| all three | 0.499 | 1.25 | 0.30 (clamp) in 5/5 | 5/5 |

What this means:
- **The rate layer is the one that reacts to delay.** On its own it pins its 0.3 output clamp in every run, and rate
  activity is 3.7× the baseline. The attitude and position layers do nothing harmful at 13 ms.
- With all three layers on, rate activity is 6.5× and attitude error doubles. The outer layers amplify what the rate
  layer starts. Tracking does not change (0.228 vs 0.227 m, p 0.97).
- Fix direction [A]: make the rate layer delay-aware, not slower. Options: a reference model that includes the 13 ms
  delay, or adapting on the delayed error (as in the time-delay MRAC literature). Then re-run this batch.
- Seeds: all SIH noise comes from one libc rand() seeded 1234. At speed 5 the threads interleave differently each run.
  "5 seeds" means 5 scheduling realisations, and only within-batch comparisons are valid.

### Batch 3 tables (mean [min..max], n 5)

| arm | n | pass | rms_track_err_m | max_hold_err_m | max_tilt_deg | att_track_rms_deg | rate_rms_rp |
|---|---|---|---|---|---|---|---|
| p11-x-dly13-attonly-lqr | 5 | 5/5 | 0.182 [0.13..0.24] | 0.227 [0.20..0.28] | 5.981 [4.70..7.33] | 0.591 [0.55..0.68] | 0.078 [0.08..0.08] |
| p11-x-dly13-lqr-alone | 5 | 5/5 | 0.228 [0.10..0.28] | 0.254 [0.19..0.39] | 6.267 [4.84..7.12] | 0.600 [0.57..0.65] | 0.077 [0.08..0.08] |
| p11-x-dly13-lqr-plus-mrac | 5 | 5/5 | 0.227 [0.20..0.27] | 0.225 [0.19..0.25] | 7.944 [7.30..8.51] | 1.248 [1.17..1.36] | 0.499 [0.48..0.52] |
| p11-x-dly13-posonly-lqr | 5 | 5/5 | 0.201 [0.14..0.24] | 0.229 [0.18..0.36] | 5.712 [4.47..7.57] | 0.656 [0.56..0.78] | 0.081 [0.08..0.09] |
| p11-x-dly13-rateonly-lqr | 5 | 0/5 | 0.233 [0.22..0.25] | 0.277 [0.21..0.42] | 8.316 [6.90..9.49] | 0.607 [0.60..0.62] | 0.287 [0.28..0.29] |

| pair (alone -> plus-mrac) | metric | alone | plus-mrac | diff | g | p (Welch) |
|---|---|---|---|---|---|---|
| p11-x-dly13-lqr | rms_track_err_m | 0.228 | 0.227 | -0.001 | -0.02 | 0.972 |
| p11-x-dly13-lqr | max_hold_err_m | 0.254 | 0.225 | -0.029 | -0.45 | 0.467 |
| p11-x-dly13-lqr | att_track_rms_deg | 0.600 | 1.248 | +0.648 | +10.97 | 4.07e-06 |
| p11-x-dly13-lqr | rate_rms_rp | 0.077 | 0.499 | +0.422 | +31.59 | 5.4e-07 |


## Batch 4 — realistic IMU noise (supersedes the delay findings of batches 2–3)

[S] GitHub Actions run 41692068353 (sim repo d383927), 7 arms × 5 runs, 35/35 PASS. New patch
`px4-mrac/patch_sih_imu_noise.py`: SIH_GYR_STD 0.044 / SIH_ACC_STD 0.2. This gives 0.022–0.024 rad/s with the
real-log estimator (real drone 0.020–0.024). Stock SIH flies with 0.074/0.037/0.015 rad/s on the same estimator, 3× too noisy on roll.

| case | lqr-alone → lqr-plus-mrac [S] | Welch p |
|---|---|---|
| nominal | track 0.073 → 0.084 m (n.s.), att err 0.154 → 0.219° | att 0.018 |
| 13 ms delay | track 0.086 → 0.093 m, rate_rms 0.030 → 0.033, rate-layer u_ad max 0.004 (clamp 0.3) | rate 4e-4, others n.s. |
| 13 ms, rate layer only | 5/5 PASS, u_ad max 0.003 (batch 3: 0/5, pinned at 0.3) | — |
| motor 1 at 70 % | hold 0.226 → 0.111 m, att err 0.62 → 0.28°, track 0.097 → 0.084 m | hold 8e-4, att 1e-11 |

What this means:
- **The batch 2–3 delay risk was a noise artifact.** Stock SIH gyro noise is 3× too high. With the 13 ms delay,
  the rate layer adapted to that noise until it saturated. With the measured noise, the layer stays quiet at 13 ms.
  Delay is not a thesis risk at the real value. Batches 1–3 overstate every error, so do not quote them.
- **Motor-1 partial loss is the clean MRAC result.** MRAC halves the hold error and cuts attitude error 55 %, with
  very large effect sizes. That is the use case adaptive control is for.
- Nominal cost: MRAC adds 0.07° attitude error and no tracking benefit when the plant is known.
- From now on, every research-drone run uses SIH_GYR_STD 0.044 / SIH_ACC_STD 0.2.

### Batch 4 tables (mean [min..max], n 5)

| arm | n | pass | rms_track_err_m | max_hold_err_m | max_tilt_deg | att_track_rms_deg | rate_rms_rp |
|---|---|---|---|---|---|---|---|
| p11n-lqr-alone | 5 | 5/5 | 0.073 [0.06..0.09] | 0.070 [0.06..0.10] | 1.802 [1.56..2.43] | 0.154 [0.15..0.16] | 0.029 [0.03..0.03] |
| p11n-lqr-plus-mrac | 5 | 5/5 | 0.084 [0.04..0.10] | 0.078 [0.06..0.10] | 1.958 [1.68..2.25] | 0.219 [0.16..0.25] | 0.032 [0.03..0.03] |
| p11n-x-dly13-lqr-alone | 5 | 5/5 | 0.086 [0.07..0.11] | 0.094 [0.05..0.15] | 1.589 [1.47..1.84] | 0.153 [0.14..0.17] | 0.030 [0.03..0.03] |
| p11n-x-dly13-lqr-plus-mrac | 5 | 5/5 | 0.093 [0.08..0.11] | 0.088 [0.06..0.12] | 2.040 [1.77..2.31] | 0.169 [0.16..0.21] | 0.033 [0.03..0.03] |
| p11n-x-dly13-rateonly-lqr | 5 | 5/5 | 0.090 [0.08..0.10] | 0.072 [0.05..0.12] | 1.895 [1.55..2.21] | 0.161 [0.15..0.18] | 0.033 [0.03..0.03] |
| p11n-x-mot1-lqr-alone | 5 | 5/5 | 0.097 [0.07..0.10] | 0.226 [0.18..0.28] | 3.234 [3.05..3.42] | 0.620 [0.61..0.64] | 0.050 [0.05..0.05] |
| p11n-x-mot1-lqr-plus-mrac | 5 | 5/5 | 0.084 [0.07..0.09] | 0.111 [0.09..0.14] | 2.129 [1.55..2.86] | 0.277 [0.26..0.28] | 0.037 [0.04..0.04] |

| pair (alone -> plus-mrac) | metric | alone | plus-mrac | diff | g | p (Welch) |
|---|---|---|---|---|---|---|
| p11n-lqr | rms_track_err_m | 0.073 | 0.084 | +0.011 | +0.48 | 0.431 |
| p11n-lqr | max_hold_err_m | 0.070 | 0.078 | +0.008 | +0.44 | 0.464 |
| p11n-lqr | att_track_rms_deg | 0.154 | 0.219 | +0.065 | +2.20 | 0.0177 |
| p11n-lqr | rate_rms_rp | 0.029 | 0.032 | +0.003 | +2.35 | 0.0132 |
| p11n-x-dly13-lqr | rms_track_err_m | 0.086 | 0.093 | +0.007 | +0.39 | 0.518 |
| p11n-x-dly13-lqr | max_hold_err_m | 0.094 | 0.088 | -0.007 | -0.18 | 0.768 |
| p11n-x-dly13-lqr | att_track_rms_deg | 0.153 | 0.169 | +0.016 | +0.82 | 0.21 |
| p11n-x-dly13-lqr | rate_rms_rp | 0.030 | 0.033 | +0.003 | +3.95 | 0.000411 |
| p11n-x-mot1-lqr | rms_track_err_m | 0.097 | 0.084 | -0.013 | -1.07 | 0.105 |
| p11n-x-mot1-lqr | max_hold_err_m | 0.226 | 0.111 | -0.115 | -3.42 | 0.000797 |
| p11n-x-mot1-lqr | att_track_rms_deg | 0.620 | 0.277 | -0.343 | -34.58 | 1.37e-11 |
| p11n-x-mot1-lqr | rate_rms_rp | 0.050 | 0.037 | -0.014 | -33.63 | 7.75e-12 |
