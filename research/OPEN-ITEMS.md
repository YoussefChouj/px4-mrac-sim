# Open items: PX4 migration (priority order, 2026-11-03)

Agreed with the operator in the 2026-11-03 grilling session. Spec: RESEARCH-DRONE-SPEC.md.
Rule: when an item is done, start the next one immediately. Each item is done only when its check
(the real outcome) is pasted into PROGRESS.md.

| P | Item | Done when |
|---|---|---|
| 1 | Research: Foxglove features for ULog/MCAP (3D, plots, layouts, events) vs Rerun vs PX4 Flight Review | `research/notes/viewers.md` with an adopt/build decision and quoted sources |
| 2 | Research: open-source PX4 controllers (MRAC, L1 adaptive, MPC, LQR, ADRC, INDI), gz worlds (wind, obstacles, terrain), planners, free cloud for sweeps (GitHub Actions, Kaggle CPU) | `research/notes/{controllers,worlds,planners,cloud}.md`, each ending in adopt/port/build |
| 3 | Separate PX4 checkout `~/PX4-mrac` (same version as `~/PX4-Autopilot`); an external module skeleton that builds; a param switch | `make px4_sitl` builds; the module starts in SITL; x500 hover scenario passes |
| 4 | MRAC rate layer at the rate-sp → torque handoff, over PX4 PID, on x500 | hover + fig8 pass with the layer on; the layer adapts (its gains move) under an injected disturbance; on/off A/B report |
| 5 | MRAC attitude and vz (vertical velocity -> thrust) layers, later XY accel (V3), each switchable | per-loop on/off ladder passes; ≥5 seeds per arm |
| 6 | Sim flight decks: deck = ordered scenarios; gates (oscillation spectral peak, tilt, motor saturation %, tracking RMS, landing, regression vs the previous flight) | a deck that has a known oscillating case fails at the right gate |
| 7 | Black dark-mode reports with many organized plots and an event layer; a Rerun .rrd per run (persistent trail + preset path, one shared timeline); ONE dark index page of all runs/decks | the index opens, and every run links to its report and replay |
| 8 | Research-drone model from real data: mass 0.9885 kg (MASS_KG), inertia, bench thrust, RPM/PWM logs (use the 3 good motors for the faulty one), sysid runs → `research_drone_params.yaml` → SDF + airframe | the sim reproduces the sysid step responses (delay, time constant) within a stated tolerance; a table of sim/real ratios |
| 9 | LQR, MPC, ADRC position baselines as PX4 modules (port from open source where good, else from `API/xy_ctrl.c` designs) | each baseline hovers and tracks fig8 without oscillation gates tripping |
| 10 | MRAC layers on each new baseline | the same ladder as item 5, per baseline |
| 11 | Thesis campaign: sim twins of the real thesis flights (same names, e.g. lqr-alone / lqr-plus-mrac), then sim-only extras (wind gusts, mass change, motor degradation/loss, added delay, aggressive trajectories, per-loop layer on/off) | a report with effect sizes, ≥5 seeds per arm |
| 12 | Cloud sweep pilot (free tier only, ~10 runs), then combinatoric sweeps | results downloaded and indexed identically to local runs |
| 13 | Realistic scenes in the main track: wind, obstacle course, outdoor terrain | decks run in each scene |
| 14 | Planner track (after item 5): PX4 collision prevention vs ROS 2 planners | an obstacle-course deck passes with the planner |
| 15 | Leftovers: trajectory_setpoint logged at 5 Hz, hex motor-out rung, slung load, full-rate DDS path, closer overview camera, live-view browser check | each item closed or re-filed |

## New order after the Codex review (2026-11-04, `research/reviews/codex-review-2026-11-04.md`)

Adopted: evidence before features. V1-V8 come before P13 scenery, P14 and P15; the in-flight P14 rerun (p14b) and
the gz drag point c 0.6 finish, then those items park. The operator may veto.

| V | Item | Done when |
|---|---|---|
| V1 (DONE) | Provenance: distinct cloud seeds (ARMS_RUN0), attempt ledger, manifest (tools/tree commit + dirty hash, px4 binary hash, deck hashes) in every arms.json; collect.py denominator = intended runs; ONE source checkout for the module (W `px4-mrac/` is stale vs the sim repo) | a 2-rep cloud wind batch shows seeds 1 and 2 in the run params and the manifest; W/R module diff empty or W copy removed |
| V2 (DONE) | Claim scope + errata: the "position" layer adapts vz/thrust only; PROGRESS errata for P:139, P:307, P:322, P:452 | errata section in PROGRESS; docs call it the vz layer |
| V3 (DONE 13:15) | XY adaptation gap: decide an XY MRAC layer (on the XyCtrl accel/tilt output) or narrow the claim to rate/att/vz | decision in PROGRESS; if built, wind A/B shows the XY layer moving |
| V4 | Metrics from ULog timestamps: geometric tilt, absolute hold offset vs drift, clamp/saturation occupancy, cadence; refuse incomplete topics | reproduces 3 existing numbers, detects an injected constant offset |
| V5 | Uncertainty envelope: delay x noise spectrum x motor lag x saturation (Python screen + selected SIH), high-noise cases kept as stress tests | a benefit/failure map with the failure edge, not only passes |
| V6 | Fair baselines: equal tuning budget per baseline, held-out trajectories/faults; LQR set 4 stays a candidate until held out | held-out table; baselines and MRAC frozen before V8 |
| V7 | Time-scale evidence: ref tau x adaptation gain x leakage, frozen-learned vs online adaptation | interaction table + the configuration rule |
| V8 | P11 confirmation campaign: >=10 paired seeds, intervals on paired differences, every attempt counted | report with effect sizes and failure fractions |

Constraints: never edit `~/PX4-Autopilot` or the FreeRTOS repo (only its `.claude_state.md`); one gz sim at a time on
instance 8 (headless SIH may run 2 in parallel if CPU allows); no paid compute (Colab units stay reserved); [S] labels on all numbers.

## Status (2026-11-04)

2026-11-05: all.json records carry `landed` (ci/collect.py). V5: the SIH delay edge is a self-sustained rate limit
cycle that blocks the land detector (PROGRESS "Delay failure traced"); the gam-vs-delay rule is still model-stage [S].
V9 v2 (rate layer): built; waves K and L: scheduler moves the delay edge to >30 ms and beats a constant low gain.
L1 (all loops, three roles): waves M, N real-world mission: roles 2+3 + xy tilt budget hold ~35 % better and track
~15 % better than PX4 PID (18 seeds); memory role pays nothing in one mission, to be tested episodically (E4).

Checks live in PROGRESS.md. Done: P1-P7, P9, P10, P12 (pipeline), P8 M2 (actuator delay). P11 done except wind
gusts (SIH has no wind; moved to P13). Open: P8 gyro noise + attitude step vs lab_d_sysid_angle, P13-P15.
Seeds: every sim noise source draws from one libc rand() seeded 1234 (sih.cpp, SensorBaroSim.cpp); at speed 5 the
threads interleave differently each run, so runs differ by scheduling, not by seed. Compare arms only within one
cloud batch (same build, same runner pool), with the controls re-run in that batch.

## P16 error-scale realism (added 2026-11-04, user: "SOTA is cm-scale, we are at m-scale") — BEFORE P11
- Research with quoted sources: measured hover/tracking error of small quads in calm and in wind (outdoor GPS vs
  indoor mocap; Neural-Fly, Faessler rotor drag, PX4 flight-review numbers).
- Truth vs estimate: in gz, log true pose and compare with EKF vehicle_local_position (our metric is estimate vs setpoint).
- Wind force check: steady tilt at known wind speed vs a sourced drag coefficient; gz WindEffects + motor-model rotor
  drag may double count [S].
- Gains: PX4 default x500-style position/velocity gains on the 1 kg research drone (P13a ringing, damping ~0.05);
  LQR without integral holds a steady offset in wind (P13b figure). Tune: LQR integral state or wind-tuned weights.
- Obstacle wind run p13-obst-wind-pid-alone-1 FAILED with 128 deg tilt (crash) -> diagnose from report.html.
