# PROGRESS — done-checks for OPEN-ITEMS

An item counts as done only when its check is pasted here. Labels: [S] = simulated, [D] = documented, [A] = assumed.

## P3 — mrac_layers module builds and routes (2026-11-03)
- [S] `~/PX4-mrac` (copy of v1.17.0) builds with `mrac_layers` (rate/att/pos) via `px4-mrac/rebuild.sh`, EXIT=0.
- [S] Mode 2 (route only) gives u_ad = 0 and theta = 0 on all three layers (arms run below).

## P4 — rate layer: hover + fig8 pass, adapts under disturbance, on/off A/B — DONE
Run: `arms.py 8 ~/PX4-mrac 5 mrac-off mrac-dist-route mrac-dist-adapt ...`, SIH, x500, 5 seeds per arm.
Output: `~/.cache/px4-arms/20261103T154656`, 35/35 PASS.

| metric (mean [min..max], n=5) | off | route (MRAC off, disturbance on) | adapt (MRAC on, disturbance on) |
|---|---|---|---|
| dist_rate_rms (rad/s) | – | 0.171 [0.167..0.173] | 0.107 [0.105..0.108] |
| dist_roll_peak_deg | – | 7.86 [7.37..8.97] | 4.44 [3.73..5.10] |
| dist_peak_rp (rad/s) | – | 0.853 [0.749..0.925] | 0.582 [0.428..0.645] |
| rms_track_err_m (fig8) | 3.00 | 2.98 | 2.94 |
| max_tilt_deg | 35.2 | 34.5 | 35.4 |
| theta_end / uad_max | – | 0 / 0 | 0.079 / 0.085 |

[S] The rate layer cuts the disturbance rate error by 38 % and the roll peak by 43 %. It does not hurt fig8 tracking.

## P5 — att/pos layers
- [S] Same arms run: the pos layer adapts (dist_z_peak 0.289 → 0.221 m, theta 0.22) but sits at the UMAX 0.15 clamp. The att layer barely adapts (theta 0.012, roll peak 8.05 vs 8.01°) at MRL_A_GAM 1. A gain sweep is pending.
- [S] Gain sweep, 5 seeds per arm (`~/.cache/px4-arms/20261103T162537`, 15/15 PASS): att u_ad grows with gain, but the roll peak under the rate-torque disturbance does not move.

  | metric (mean [min..max]) | route | GAM 5 | GAM 10 |
  |---|---|---|---|
  | att_uad_max | 0 | 0.134 [0.132..0.138] | 0.201 [0.194..0.212] |
  | dist_roll_peak_deg | 7.67 [6.20..8.43] | 7.90 [6.06..8.89] | 7.31 [6.83..7.77] |
  | dist_rate_rms | 0.167 | 0.166 | 0.168 |

  Reading: the disturbance (`MRL_DIST_R`) is a torque at the rate loop, and the inner rate loop already absorbs most of it, so an attitude-level layer has little left to fix. The att arm needs an attitude-level mismatch (CG offset / thrust imbalance) as its test case.
- [S] Pos UMAX 0.25 / LIM 0.5 (`~/.cache/px4-arms/20261103T161428`): 3/5 pass; max_hold_err 0.83..1.57 m vs route 0.42..0.70 m. The larger authority hurts hover hold, so keep UMAX 0.15.
- [S] Att layer with a degraded inner loop (MC_ROLLRATE_K/PITCHRATE_K 0.5, SIH_T_TAU 0.08, MRL_A_GAM 5, fig8 size 8 period 10 ×3), 5 seeds per arm, `~/.cache/px4-arms/20261103T163757`, 15/15 PASS. `att_track_rms_deg` = RMS of roll/pitch error vs vehicle_attitude_setpoint over the airborne flight.

  | metric (mean [min..max]) | healthy route | slow route | slow adapt |
  |---|---|---|---|
  | att_track_rms_deg | 2.89 [2.77..2.95] | 4.98 [4.92..5.09] | 4.51 [4.39..4.58] |
  | rms_track_err_m | 2.99 | 3.65 [3.63..3.68] | 3.48 [3.43..3.53] |
  | att_uad_max | 0 | 0 | 0.167 [0.158..0.192] |

  Reading: with a weak inner loop the att layer cuts attitude tracking error by 9 % and fig8 position error by 5 %, ranges do not overlap. It recovers about a fifth of the gap to the healthy loop.
- [S] **Per-loop ladder** on the slow-inner-loop case (MC_ROLL/PITCHRATE_K 0.5, SIH_T_TAU 0.08, A_GAM 5; DIST_R 0.08 + DIST_T 0.08 step, then fig8 8 m / 10 s ×2). 5 seeds per arm, `~/.cache/px4-arms/20261103T164855`, **20/20 PASS**.

  | metric (mean [min..max]) | all off | rate | rate+att | rate+att+pos |
  |---|---|---|---|---|
  | dist_roll_peak_deg | 17.98 [15.2..19.5] | 6.26 [5.14..6.99] | 5.70 [4.73..6.32] | 5.99 [4.53..8.11] |
  | dist_rate_rms (rad/s) | 0.343 | 0.144 | 0.140 | 0.143 |
  | att_track_rms_deg | 4.25 [4.12..4.37] | 3.99 [3.87..4.07] | 3.68 [3.65..3.71] | 3.86 [3.66..4.32] |
  | dist_z_peak_m | 0.235 | 0.375 [0.12..0.84] | 0.306 | 0.213 [0.13..0.32] |
  | rms_track_err_m (fig8) | 3.67 | 3.65 | 3.47 | 3.41 [3.35..3.46] |
  | max_hold_err_m | 0.84 | 0.69 | 0.64 | 0.68 |
  | rate_rms_rp | 0.148 | 0.118 | 0.117 | 0.165 [0.119..0.260] |
  | uad_max rate / att / pos | – | 0.114 / – / – | 0.115 / 0.159 / – | 0.261 / 0.355 / 0.150 (clamp) |

  Reading: each layer added on top helps its own loop. Rate cuts the roll peak 65 %. Att cuts attitude error a further 8 %. Pos cuts the z peak and fig8 error. With all three on, two seeds show layer interaction: rate rms up to 0.26, att theta up to 1.1, att u_ad reaching its 0.5 limit, and pos sitting at its UMAX clamp. Stacked layers need a time-scale separation rule: each outer reference model slower than the inner one. That is the thesis's multi-time-scale claim, and it is now testable.
- **P5 DONE** (ladder with ≥5 seeds per arm, pasted above). Follow-up for P10/P11: sweep the outer reference-model tau (MRL_A_TAU, MRL_P_TAU) to remove the all-on interaction.
- Tooling lesson: float PX4 params in scenario JSON must be written as floats (5.0). An int makes `get_param_int` fail with WRONG_TYPE and the arm never flies.

## P8 — research-drone model from real data (M0 + M1 done; M2 log validation open)
- M0 [D]/[A]: `research/research_drone_params.yaml`, every value with range, label and source. Mass 0.9885 kg [A] (firmware MASS_KG, never weighed), inertia xx/yy/zz 0.01389/0.01539/0.01133, kF 6.80e-6 N/(rad/s)^2 (Σω² over 6 flights, drift-investigation report), ω_max 969 rad/s, kM 0.109 (7× x500, flagged), motor tau 0.0505 s, 15 ms delay (not modelled in gz).
- M0 [S]: `vehicles/research_drone/gen_model.py` builds model.sdf from the x500 base (0.1 m rotor offsets, scaled meshes, 4 MulticopterMotorModel); `gz sdf -k` → Valid. Airframe `4051_gz_research_drone` (CA rotors ±0.1, KM ±0.109, EC 150..969, MPC_THR_HOVER 0.55).
- M1 [S]: `scenario.py 1 scenarios/rd-gz-hover.json` (gz, speed 1, 3 m, 30 s hold) → PASS. Max drift 0.083 m (limit 0.3), max tilt 0.58°, landed. `~/.cache/px4-runs/rd-m1-20261103T163722`. Height error 0.28 m during hold: to check against MPC_THR_HOVER in M2.
- Tooling fix: scenario.py now stops when the sim launcher exits (the first M1 try used instance 9, px4ctl allows 0..8, and waited 600 s on a dead launcher).
- M2 hover check [S] (rd-m1 ULog, 23.7 s hold window): motor cmd 0.472 (per motor 0.468..0.476), actuator_outputs / esc_status 534..539 rad/s. Real drone [D]: hover throttle 0.545 [0.48..0.55], 5700 rpm = 597 rad/s [518..674]. **Mismatch**: the sim hovers 11 % slower in rotor speed and below the real throttle range. The SDF is correct (4 plugins, motorConstant 6.8e-6, total mass 1.053 kg), yet gz holds 10.33 N at 536 rad/s, an effective constant of 8.99e-6, 1.32× the set value. The cause is not found (candidates: the gz_bridge EC_MIN/MAX map, or a MulticopterMotorModel scaling term). Next: read gz-sim MulticopterMotorModel thrust code; then either calibrate motorConstant to 5.15e-6 (hover 597 rad/s) or fix the root cause.
- **M2 hover root cause [S] (2026-11-03 23:55).** A JointStatePublisher was added to the model to read the gz rotor joints in hover (`rd-gz-hover`). With kM 0.109, rotor_0/1 (ccw) ran at 620–640 rad/s and rotor_2/3 (cw) at 410–433, while PX4 commanded 539/539/532/532. The rotors did not follow the command, and the thrust did not balance. With kM 0.016 (x500 value) and everything else unchanged, all four joints run at 615 rad/s, esc 614.8 ×4, motors 0.567. That equals √(m g / 4 Kt) = 616 for 1.053 kg, and the real hover is 597 [518..674] rad/s at cmd 0.545. **Fix:** K_M 0.016 [A] in `gen_model.py` and CA_ROTORx_KM ±0.016 in `4051_gz_research_drone`. The 0.109 twin fit is dropped as non-physical for gz. The real yaw coefficient still needs a yaw-step fit (M2 open below).
- **M2 rate-loop delay [S] vs [D] (2026-11-04 01:40).** Method: a 12-tone multisine torque dither (0.5–20 Hz, MRL_ID_AMP 0.06, roll then pitch, 30 s each) in a gz hover (`scenarios/rd-gz-id.json`). The FRF is the instrumental-variable estimate S_dy/S_du, and the fit `k e^{-sT}/(s(τs+1))` uses the **same** `ground_station/autotune/frf.fit_plant` as the real drone's fit (`agent/plant_fit.py`). That makes this the frequency-domain method of Tischler-style rotorcraft ID, run apples to apples.

  | gz added delay | roll τ / T | pitch τ / T | rel. residual |
  |---|---|---|---|
  | 0 ms (stock) | 0.045 s / 10.2 ms | 0.046 s / 10.1 ms | 0.10 |
  | 12 ms | 0.048 / 21.4 | 0.049 / 21.1 | 0.10 |
  | **3 ms** | 0.049 / **13.3** | 0.050 / **12.7** | 0.09 |
  | real [D] | angle-roll fit 0.042 / 14.1 | rate-pitch fit 0.068 / 12.85 (rel. res. 0.49) | — |

  The added delay shows up 1:1 (12 ms → +11 ms), so the method is sound. **Decision:** +3 ms puts the sim delay inside the real 12.85–14.1 ms. Sim τ 0.045–0.050 lies inside the two real fits (0.042–0.068), so the motor time constant stays at 0.0505 s; nothing was tuned to match. gz MulticopterMotorModel has no transport delay and PX4 has no sim-delay parameter, hence a small custom patch (`px4-mrac/patch_gz_delay.py`, a ring buffer in the gz-bridge ESC output). It is driven by the PX4 param `SIM_GZ_ACT_DLY` (ms), so every ULog records it. Airframe 4051 sets the default to 3. Check after rebuild (no env var, airframe default, `rd-gz-id-20261103T232719`): the ULog shows SIM_GZ_ACT_DLY 3, and the fit gives roll 0.049 s / 13.2 ms, pitch 0.050 s / 12.8 ms, rel. residual 0.09 → **M2 delay DONE**.
- M2 gyro noise, OPEN: the SDF sets gz IMU stddev 0.022 rad/s. Measured at sim hover: sensor_combined diff estimate 0.0105 rad/s, vehicle_angular_velocity high-pass 0.012 rad/s. The real value in `plant.py` is 12 dps at 1 kHz, mostly motor vibration, from a different estimator. These cannot be compared yet. Next: the same estimator (filtered rate std at hover) on a real hover log and on the sim.
- M2 open: attitude step response vs real `lab_d_sysid_angle` (2026-10-28) flight.

## P9 — LQR / ADRC / MPC xy baselines in PX4 (first pass)
- [S] Plant fit (`px4-mrac/xyc_design.py` on mrac-off-1 ULog): a = k·lag(u) − D·v. u = tilt-implied acceleration from vehicle_attitude_setpoint (125 Hz; lpos setpoint is logged at only 9.6 Hz and aliases). Matched 3 Hz filtfilt; output-error grid. Result: al 0.3679 (tau 0.02 s, grid floor, so the lag is absorbed into the delay), dc gain 0.927, drag D 0.886 1/s, delay 9 steps = 180 ms, residual 0.155 m/s² (0.81 without the drag term). LQR K = [2.78 1.90 0.081 0.68], closed-loop |eig| max 0.993.
- [S] Module: `mrac_layers/XyCtrl.{hpp,cpp}` (XYC_MODE 0 PID / 1 LQR / 2 ADRC / 3 MPC FISTA) publishes trajectory_setpoint_xyc (acceleration-only xy). mc_pos_control follows it when XYC_MODE ≥ 1 (`patch_pos_xyc.py`). Build PASS.
- [S] `arms.py 8 ~/PX4-mrac 5 xyc-{pid,lqr,adrc,mpc}` (SIH, hold 8 s + fig8 8 m / 12 s ×2), `~/.cache/px4-arms/20261103T171139`, **20/20 PASS**.

  | metric (mean [min..max]) | PID (stock) | LQR | ADRC | MPC |
  |---|---|---|---|---|
  | rms_track_err_m (fig8) | 3.01 [2.98..3.06] | 3.50 [3.39..3.59] | 3.67 [3.55..3.78] | 3.65 [3.42..3.81] |
  | max_hold_err_m | 0.69 [0.29..1.07] | 0.68 [0.38..1.15] | 1.11 [1.07..1.15] | 0.74 [0.48..0.87] |
  | att_track_rms_deg | 2.99 | 3.10 | 3.84 | 3.17 |
  | rate_rms_rp | 0.086 | 0.090 | 0.114 | 0.091 |
  | max_tilt_deg | 36.0 | 22.38 | 23.16 | 22.39 |

  Reading: all three fly stably. Their max tilt pins at 22.4° = atan(XYC_AMAX 4.0 / g), so they are acceleration-saturated on the fig8, while stock PID uses up to 36°. The tracking gap is therefore not yet a fair controller comparison. Next: XYC_AMAX 7.0 (35°) rerun, then a hold-only step test without saturation.
- [S] Rerun with XYC_AMAX 7.0 (cap 35.5°, same as PID's 36° use), `~/.cache/px4-arms/20261103T172349`, **15/15 PASS**:

  | metric (mean [min..max]) | PID (above) | LQR a7 | ADRC a7 | MPC a7 |
  |---|---|---|---|---|
  | rms_track_err_m (fig8) | 3.01 | **2.52** [2.48..2.57] | 2.96 [2.93..3.01] | **2.52** [2.45..2.56] |
  | max_hold_err_m | 0.69 | 0.67 [0.44..1.02] | 1.03 [0.95..1.09] | 0.61 [0.53..0.69] |
  | att_track_rms_deg | 2.99 | 3.00 | 4.49 | 3.03 |
  | rate_rms_rp | 0.086 | 0.082 | 0.107 | 0.080 |
  | max_tilt_deg | 36.0 | 35.1 | 35.4 | 35.2 |

  Reading: at equal tilt authority, LQR and MPC track the fig8 16 % better than stock PID, with the same or lower rate activity. ADRC matches PID on tracking but holds worse (1.03 m) and is busier (rate_rms +24 %). Its ESO bandwidth (4·XYC_WC = 6 rad/s) is a tuning lever, not tuned here. LQR and MPC agree to 0.01 m: the constraints are inactive at AMAX 7, so MPC reduces to LQR, as expected.
- **P9 DONE** (baselines built, fitted, flown 5 seeds each, fair comparison pasted). Follow-ups: ADRC XYC_WC sweep (P12 cloud sweep candidate).

## P6 — sim deck with gates catches a known oscillating case — DONE
- Gates (`agent/gates.py`): osc_amp_rad_s = peak of the Hann-averaged spectrum of roll/pitch rate error in [1.5 Hz, Nyquist·0.9] over the longest airborne stretch; sat_pct; max_tilt_deg; landed.
- [S] Calibration: osc_amp over all 45 healthy arm flights (hover + disturbance + fig8) = 0.030..0.040 rad/s. Gate set to 0.06 (1.5× healthy max).
- [S] Known-bad case `scenarios/decks/osc-rollrate-p.json`: SIH_T_TAU 0.2 (motor lag; the 0.05 default never rings), rate P 1.0, D 0.01 → osc 0.103 rad/s at 4 Hz.
- [S] `deck.py 8 scenarios/decks/rate-osc.json --src ~/PX4-mrac` → 01-mrac-off pass (0.034 @ 3 Hz), 02-osc-rollrate-p fails at osc_amp_rad_s. 2/2 matched, `~/.cache/px4-decks/rate-osc-20261103T161134`.
- Lesson: SIH with near-zero actuator lag hides gain-induced oscillation (P ×8 stayed stable). Decks that hunt oscillation must set a realistic SIH_T_TAU.

## P7 — black reports + Rerun .rrd + ONE dark index (in progress)
- [S] report.py: plotly_dark + `#000` page and plot backgrounds, checked by screenshot on mrac-dist-adapt-1.
- [S] `agent/rrd.py RUN_DIR...` → flight.rrd (7.4 MB for an 80 s run): static preset path (orange) + flown path (blue), moving drone pose, pos/att/rates/motors/MRAC plots, event text log on one sim-time axis.
- [S] `agent/index.py` → ONE dark page `~/.cache/px4-index.html` over every campaign in ~/.cache/px4-* (27 campaigns, newest first, collapsible). Per run: PASS/FAIL, key metrics, links to report/rrd. Decks show the gate verdict (`osc_amp_rad_s (expect osc_amp_rad_s)`). Checked by screenshot via `python3 -m http.server 8792` in ~/.cache. **P7 DONE.**

## P10 — rate+att MRAC on every xy baseline under a roll-torque disturbance — DONE (2026-11-03)
SIH, speed 5, 5 runs per arm, same scenario per arm (takeoff, hold, MRL_DIST_R step, fig8, land); arm = baseline
xy controller (XYC_MODE) x adaptive layers off / rate+att on (MRL_EN_RATE=1, MRL_EN_ATT=1). Mean [min..max]. [S]
Sources: lqr-off from ~/.cache/p10arms.log (batch 1, 5 runs); lqr-ra/adrc ~/.cache/px4-arms/20261103T223344;
mpc ~/.cache/px4-arms/20261103T224438.

| arm | pass | dist roll peak deg | dist rate rms rad/s | att track rms deg | fig8 rms m | hold max m | dist z peak m |
|---|---|---|---|---|---|---|---|
| lqr off | 5/5 | 16.5 [15.7..17.4] | 0.336 | 4.51 | 3.19 | 0.70 | 0.27 |
| lqr +MRAC | 5/5 | 5.19 [4.76..6.21] | 0.138 | 3.92 | 3.05 | 0.70 | 0.19 |
| adrc off | 4/5 | 19.9 [16.9..22.0] | 0.363 | 6.08 | 3.75 | 1.47 | 0.30 |
| adrc +MRAC | 5/5 | 5.54 [4.04..7.13] | 0.152 | 5.38 | 3.65 | 1.45 | 0.18 |
| mpc off | 5/5 | 17.0 [16.8..17.2] | 0.340 | 4.54 | 3.20 | 0.88 | 0.22 |
| mpc +MRAC | 5/5 | 4.71 [4.18..5.60] | 0.133 | 3.93 | 3.08 | 0.79 | 0.21 |

Check: the adaptive layers cut the disturbance roll peak 3.0-3.6x and the rate error 2.4x on all three baselines,
with no run failing (ADRC off had 1/5 fail). Ranges do not overlap for roll peak or rate rms. Same direction as the
PID ladder (17.98 -> 5.70 deg). uad_max 0.11-0.20, att_uad_max 0.16-0.27 (below MRL limits). Controller-agnostic
claim holds in SIH for the inner loops. Fig8 rms is dominated by the xy baseline (ADRC worst), not the layers.
Note: px4ctl accepts instances 0..8 only; instance 9 "hung" because the sim never started (arms.py now refuses it).

## P12 — cloud sweeps on GitHub Actions (pipeline done; sweeps next)
- Public repo https://github.com/YoussefChouj/px4-mrac-sim (sim tooling only, BSD-3). Workflow `arms.yml`: plan → build (PX4 v1.17.0 + px4-mrac patches, SIH-only `bin`+`etc` tarball, cached by patch hash) → fly (matrix, one scenario×run per runner, fail-fast off) → collect (Markdown table + `all.json`).
- Smoke run 1 (41657285352) failed at build: `apply.sh` needs `xyc_gains.h`, which was not in the repo. Fixed by committing the generated header (aadddfc), with the ULog paths stripped.
- **Smoke run 2 (41658077476) [S]: success.** Build 6 min (cold cache), each fly job 1 min, collect OK. `all.json`: mrac-off rate_rms_rp 0.084, hold max 1.28 m; mrac-dist-adapt dist_roll_peak 3.76°, dist_rate_rms 0.104, uad_max 0.087, hold max 0.62 m. Both pass. One run per arm, so this checks the pipeline, not the statistics. For comparison, the local P10 +MRAC arms (5 runs each, all three xy controllers) gave 4.04–7.13°.
- Next: dispatch sweeps with `runs` 10 (outer tau, ADRC XYC_WC, P11 campaign).

## P11-prep — outer reference-model tau sweep (cloud, 2026-11-04)
- **Setup.** GH Actions run 41666014724: 53 jobs, all success. Base: `ladder-all.json` (SIH, all 3 layers, degraded plant MC_*RATE_K 0.5 + SIH_T_TAU 0.08, DIST_R/T 0.08, hold + 2 fig8 laps). Arms: MRL_A_TAU {0.15, 0.30, 0.60} × MRL_P_TAU {0.5, 1.0, 2.0}, plus ladder-off; 5 runs each. Rate tau fixed at 0.06.
- **Prediction (written before the results).** Larger outer tau means less layer interaction, but slower outer rejection.
- **Medians [S]** (half-range in brackets):

| arm | fig8 rms m | dist roll peak ° | rate rms | rate u_ad max | runs with u_ad at the clamp | tilt max ° |
|---|---|---|---|---|---|---|
| ladder-off | 3.71 | 19.99 | 0.151 | – | – | 42.1 |
| a0.15 p0.5 (default) | 3.48 | 6.50 | 0.155 | 0.300 | 4/5 | 42.5 |
| a0.15 p1.0 | 3.44 | 5.70 | 0.120 (0.24) | 0.123 | 2/5 | 42.6 |
| a0.15 p2.0 | 3.41 | 5.61 | 0.119 (0.14) | 0.294 | 3/5 (≥0.29) | 42.2 |
| a0.30 p0.5 / p1.0 / p2.0 | 3.78 / 3.73 / 3.71 | 6.40 / 5.80 / 5.78 | 0.169 / 0.123 / 0.120 | 0.300 | – | ~40.6 |
| a0.60 p0.5 / p1.0 / p2.0 | 4.36 / 4.27 / 4.27 | 6.15 / 5.85 / 5.59 | 0.155 / 0.119 / 0.130 | 0.26–0.30 | – | ~36.1 |

- **Reading.**
  - Every adaptive arm cuts the disturbance roll peak about 3× (20° to 5.6–6.5°).
  - A slower attitude tau costs fig8 tracking: 0.30 matches off and 0.60 is +15%. The lower tilt there is sluggishness, not better control.
  - A slower position tau (0.5 to 1.0) lowers the rate rms (0.155 to 0.120) and the disturbance peak (6.5° to 5.7°) without hurting tracking. Going to 2.0 adds nothing.
- **Decision: keep MRL_A_TAU 0.15 and set MRL_P_TAU 1.0.** That is 2.5× rate→att and 6.7× att→pos. The literature's 3–5× per loop is roughly met; a slower attitude loop measurably hurts tracking.
- **Finding (separate problem): rate-layer parameter drift is bimodal.** In every arm, some runs end with the rate θ at about 0.9–1.1 and u_ad pinned at UMAX 0.3. The rest end at θ 0.1–0.3 and u_ad around 0.11.
  - The worst run (a0.15 p1.0 #4) has rate rms 0.60 and att rms 7.7°, which is a burst.
  - Outer tau changes how often the drift happens, not whether it happens. So the cause is in the rate law itself (σ 0.05, γ 2, the clamp acting as saturation), not in loop separation.
  - Next item (P11 blocker): find what drives θ (its time history in a drifting ULog). Then pick a standard robust-MRAC fix (dead-zone, e-mod, or a projection bound tied to the u_ad limit, as in Ioannou & Sun ch. 8) by physical cause, not to make the number pass.

## P11-prep — root cause of the θ drift, and the fix (local SIH, tau-a015-p100 ×3, 2026-11-04)
- **Cause (from the ULog θ history, `drift_digest.py`).** The rate θ wound up at 60–61 s, while the vehicle was still airborne during the fast final descent, with a motor at 0.00. The land detector reported ground_contact at 63.8 s and maybe_landed at 64.8 s. So the adaptive law kept integrating error the mixer could not act on: actuator saturation, not loop separation.
- **Attempt 1, rejected: gate on maybe_landed** (the same gate as mc_rate_control's integrator; kept because it is harmless). Arms run 20261103T235442: θ_end 0.27–0.67 and u_ad max 0.19–0.30. Not fixed.
- **Fix: saturation-aware adaptation, reusing PX4's own rule.** MracLayers subscribes to `control_allocator_status`. Per axis it sets sat_pos/sat_neg from `unallocated_torque` exactly as `MulticopterRateControl::setSaturationStatus` does. `MracAxis::step` drops the gradient term when it would push u further into a saturated direction, or past its own UMAX clamp. Leakage still runs.

| run (local, 3×) | θ_end rate | u_ad max rate | rate rms | fig8 track [m] | pos u_ad max | pass |
|---|---|---|---|---|---|---|
| maybe_landed only (…235442) | 0.27–0.67 | 0.19–0.30 | 0.148 | 3.49 | 0.150 | 3/3 |
| + saturation-aware (…000057) | 0.096 [0.090..0.106] | 0.116 [0.109..0.126] | 0.132 | 3.37 | 0.150 | 3/3 |
| + pos gate on ground_contact (…001204) | 0.098 [0.093..0.103] | 0.106 [0.101..0.110] | 0.129 | 3.35 | 0.150 | 3/3 |

- **The position layer gate now copies mc_pos_control.** It freezes on ground_contact (PX4 resets its velocity integrator on `flying_but_ground_contact`). Touchdown windup is smaller (e at touchdown went from −0.4/−0.5 to −0.19) but not gone.
- **Open finding: the position layer bias duplicates PX4's vz integrator.** θ[1] builds to about −0.15 during the takeoff climb (mean e +0.11–0.14) and stays there through the fig8. u_ad then sits at the 0.15 clamp 9–16% of the flight. PX4's velocity integrator and hover-thrust estimate already hold that constant, so the sum is fixed and the split between the two drifts, with only σ pulling it back.
  - Candidate standard fixes, to decide by cause: use the baseline closed loop as the reference model (Lavretsky & Wise, adaptive augmentation), or drop the bias regressor on a layer whose baseline has integral action.
  - Not fixed yet. The P11 thrust-disturbance arm needs it, because a layer pinned at its clamp has no authority left.
- MRL_P_TAU default set to 1.0 (the decision above).

## P11-prep — position layer drops the bias regressor (MRL_P_BIAS, local SIH, ×3 per arm, 2026-11-04)

Why: the pos layer's bias θ[1] (≈ −0.15) duplicated PX4's vz integrator and hover-thrust estimator, which already
integrate the constant thrust error. Two integrators on one constant form a null direction that only σ splits, so u_ad
sat at its 0.15 clamp mid-flight. Adaptive augmentation of a baseline with integral action drops that bias term so the
adaptive loop does not fight the nominal integrator (arXiv 1604.01882; Lavretsky & Wise style augmentation).
Change: `MracAxis::bias`; new param MRL_P_BIAS (default 0 = off), read by MracPosLayer. Rate/att layers keep the bias.

One build, arms differ only in MRL_P_BIAS. Run `~/.cache/px4-arms/20261104T002650`, all 12 flights PASS.

| Metric (mean [min..max]) | fig8 bias off | fig8 bias on | thrust step bias off | thrust step bias on |
|---|---|---|---|---|
| pos u_ad at clamp, whole flight | 0.000–0.077 | 0.069–0.121 | 0.050–0.059 | 0.000–0.114 |
| where the clamp hits | touchdown only (60–67 s) | mid-flight (19–68 s) | touchdown only (42–46 s) | mid-flight (18–27 s) in 1/3 |
| dist_z_peak_m (thrust −0.08 step) | – | – | 0.220 [0.179..0.295] | 0.289 [0.113..0.415] |
| rms_track_err_m | 3.507 [3.489..3.532] | 3.345 [3.272..3.407] | – | – |
| rate_rms_rp | 0.134 | 0.128 | 0.091 | 0.083 |

Reading:
- With the bias off, the in-flight clamp is gone. In fig8 run 1 the largest in-flight |u_ad| is 0.088 (t 57 s). The remaining
  clamp hits are at touchdown: vz stops while vz_sp still descends, so u = θ_r·vz_sp (θ_r ≈ 0.16) saturates on the
  less-thrust side. θ is frozen there (ground_contact gate + saturation-aware law), and less thrust at touchdown is
  the direction PX4's own land logic takes.
- Rejecting the constant thrust step is no worse with the bias off: the peak overlaps and the mean is lower. PX4's
  integrator does the steady part.
- Cost: fig8 tracking is 5% worse with the bias off (3.51 vs 3.34 m, the ranges do not overlap). θ_r (vz_sp
  feed-forward) settles at 0.13–0.17, so the reference model (τ 1.0) and the PX4 vz closed loop still differ. Open:
  match the reference model to the identified PX4 vz closed loop (the reference model is the baseline closed loop, as in
  the augmentation practice above) and re-check tracking.

Follow-up, does the reference model match the baseline vz loop? (same build, fig8 `tau-a015-p100`, bias off)

| Arm | Runs | rms_track_err_m | pos θ_r at end | Run dir |
|---|---|---|---|---|
| pos layer route-only (MRL_EN_POS 2, no adaptation) | 2 | 3.549 [3.536..3.561] | – | 20261104T003633 |
| adapt, MRL_P_TAU 1.0 | 3 | 3.507 [3.489..3.532] | 0.14–0.16 | 20261104T002650 |
| adapt, MRL_P_TAU 0.85 | 3 | 3.462 [3.408..3.534] | 0.15–0.19 | 20261104T003841 |

- First-order fit of PX4's vz loop alone (vz_sp → vz, airborne, scratchpad vzfit.py): τ 0.80 and 0.90 s, delay 0, R² 0.85
  and 0.79. MRL_P_TAU 1.0 is within about 20% of that.
- τ 0.85 does not shrink θ_r, and its tracking range overlaps τ 1.0, so the remaining θ_r is not a time-constant mismatch.
  The baseline is only about first order (R² ≈ 0.8), and θ_r learns the vz_sp feed-forward the first-order model leaves out.
  The default stays 1.0, which keeps the larger time-scale gap to the attitude layer.
- Tracking ranking: bias on 3.34 < τ 0.85 3.46 ≈ τ 1.0 3.51 ≈ no adaptation 3.55 m. With the bias off, the z layer's
  tracking gain is small. The bias-on gain came with in-flight clamp hits, which is the drift this item set out to remove.

Cloud A/B (GitHub Actions run 41676782877, `tau-a015-p100` bias off vs `tau-a015-p100-b1` bias on, 5 runs each, all PASS):

| Metric | bias off (default) | bias on |
|---|---|---|
| rms_track_err_m | 3.511 [3.469..3.572] | 3.425 [3.387..3.444] |
| pos_uad_max | 0.145 [0.127..0.150] | 0.150 [0.150..0.150] |
| pos_theta_end | 0.150 [0.137..0.161] | 0.093 [0.061..0.108] |
| rate_rms_rp | 0.171 [0.126..0.214] | 0.140 [0.116..0.206] |
| rate uad_max | 0.112 | 0.120 |

The cloud matches the local runs. Bias off leaves the clamp in 2 of 5 runs, which fits the local touchdown-only hits (the
artifact has no ULogs, so the timing is not checked here). Tracking costs about 2.5% (ranges just touch). The
rate_rms ranges overlap. Decision: MRL_P_BIAS stays 0. It removes the mid-flight clamp and the double integrator on
the constant, which is the property the thesis claims (no layer fights the baseline).

## P10 follow-up — ADRC xy bandwidth sweep (XYC_WC), cloud

- [S] GitHub Actions run 41678708699 (`arms.yml`, runs 3), scenarios `adrc-wc-{08,12,15,20,25,30}` = `xyc-adrc-a7`
  (SIH, XYC_MODE 2, XYC_AMAX 7, hold 8 s + fig8 8 m / 12 s ×2) with XYC_WC 0.8 … 3.0. 18 runs, 21/21 jobs green.

| XYC_WC | pass | rms_track_err_m | max_hold_err_m | att_track_rms_deg | rate_rms_rp | max_tilt_deg |
|---|---|---|---|---|---|---|
| 0.8 | 0/3 | 5.55 [5.49..5.62] | 1.66 | 2.90 | 0.076 | 35.7 |
| 1.2 | 0/3 | 3.68 [3.65..3.70] | 1.89 | 3.87 | 0.089 | 35.3 |
| 1.5 (default) | 3/3 | 2.98 [2.96..3.00] | 1.12 | 4.40 | 0.110 | 35.3 |
| 2.0 | 3/3 | 2.17 [2.06..2.25] | 0.56 | 5.20 | 0.155 | 35.6 |
| **2.5** | 3/3 | **1.07 [1.05..1.07]** | **0.40** | 5.51 | 0.198 | 35.6 |
| 3.0 | 3/3 | 0.76 [0.72..0.79] | 0.61 [0.45..0.72] | **12.09** | **0.346** | 36.5 |

- max_tilt is ~35.5° in every arm = atan(7/9.81): the XYC_AMAX 7 acceleration clamp, so tilt does not separate the arms.
- 0.8 and 1.2 fail the 1.5 m hold limit (too slow to reject the post-takeoff offset).
- 3.0 tracks best but attitude tracking error doubles (5.5 → 12.1°), roll/pitch rate RMS +75 % and hold error rises
  again with wider spread: the onset of oscillation. 2.5 is the knee (best hold, track 1.07 m, rates still smooth).
- Decision: tuned ADRC = XYC_WC 2.5 with XYC_AMAX 7, saved as `scenarios/xyc-adrc-tuned.json`. Firmware defaults are
  unchanged (XYC_WC 1.5, XYC_AMAX 4) because XYC_AMAX is shared with the other xy modes and 2.5 was only measured at
  AMAX 7. The ADRC "untuned" P10 item is CLOSED for the fig8 case.

## P11 prep — research-drone SIH airframe, twin scenarios, sim position noise

- `airframes/research-drone.json`: SIH quadx with the P8 values (mass 0.9885 kg [A], inertia, arm 0.1414 m, T_MAX 6.38 N,
  motor tau 0.0505 s); PX4 gains untuned. 19 `scenarios/p11-*.json`: twins of `lab_e_exp_*` (takeoff 0.5 m, hold 3,
  figure-8 0.3 m / 18 s, hold 3, land) for pid / lqr / adrc (WC 2.5) / mpc, alone and plus-mrac, plus lqr extras
  (mass +31 %, T_MAX −25 %, injected dist NOT wind, motor tau 0.12, aggressive fig8 1 m / 6 s) and 2 stock-GPS arms.
- [S] Diagnosis (local, `~/.cache/px4-arms/20261104T010530`): lqr-alone tracked the 0.3 m figure with rms 0.32 m at
  0.5 m alt, 0.29 m at 2 m alt and 0.28 m on stock quadx → not altitude, not airframe. Cause: SIH `sensor_gps_sim`
  adds 0.2 m white position noise; the lab drone is camera-positioned.
- Fix (standard knob, not a metric change): `px4-mrac/patch_gps_noise.py` adds `SIM_GPS_NSCL` (scales simulated GPS
  noise and reported eph/epv/s_variance; default 1 = stock). Twins use 0.1 with EKF2_GPS_P/V_NOISE 0.05 [A camera-class,
  the lab camera noise is not measured yet].
- [S] Check (`~/.cache/px4-arms/20261104T011640`, 2 runs each): lqr-alone hover drift 0.10–0.13 m, track rms 0.17–0.20 m
  (was 0.32); lqr-plus-mrac track 0.16–0.18 m but post-figure hold drift 0.32–0.39 m vs 0.07–0.13 m alone.
- Known: hold-1 starts while the 0.5 m takeoff is still settling (height err 0.29 m in every run, all airframes);
  hold limit 0.5 m kept. One alt-2 m run was a SIM-FAULT (baro dropout → flyaway), retried by arms.py.

## P11 campaign (cloud, 19 arms x 5)

- [S] run 41683452873, 94/95 PASS; report `research/P11-campaign.md`. MRAC: no tracking effect on the 0.3 m twin, hold error lower (lqr g -1.2, mpc g -1.5), attitude error higher in every pair; helps most under mass +31 % (g -1.3), hurts with slow motors (g +1.0). Still open in P11: wind, motor loss, added delay, per-loop on/off.

## P11 batch 2 (cloud, 11 arms x 5)

- [S] run 41688393980, 55/55 PASS; SIH_ACT_DLY + SIH_MOT1_EFF patch. At the real 13 ms delay MRAC rate_rms x6.6 (p 6e-6), at 40 ms att err 5.7 deg; motor-1 70 %: MRAC lowers att err (p 0.008). lqr-alone control moved 0.255 -> 0.152 m between batches: quote only effects that repeat. P11 done except wind (needs gz); follow-ups: layer at 13 ms, fixed seeds.
