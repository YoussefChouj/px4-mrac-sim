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
| 5 | MRAC attitude and position layers (all loops), each switchable | per-loop on/off ladder passes; ≥5 seeds per arm |
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

Constraints: never edit `~/PX4-Autopilot` or the FreeRTOS repo (only its `.claude_state.md`); one gz sim at a time on
instance 8 (headless SIH may run 2 in parallel if CPU allows); no paid compute (Colab units stay reserved); [S] labels on all numbers.

## Status (2026-11-04)

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
