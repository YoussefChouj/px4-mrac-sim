# Handoff

Updated 2026-11-06 by a cloud session (branch claude/collect-landed, not merged into main yet). Read `CLAUDE.md` first, and update
this file (state + next) before every session ends.

## State
- Cloud pipeline: push `waves/<name>.txt` -> `arms` workflow (plan, cached build, fly jobs, collect) -> a folder on
  the `results` branch + one comment (one email) on the "Cloud results" issue. `waves/smoke-1job.txt` tested it.
- Waves A-G: flown 2026-11-04 05:36-05:59 UTC by workflow_dispatch from main 88c63e0 (one cached build), all 7 runs
  green, 783 of 870 flights passed their gates. Backfilled to the results branch (their fly logs were not kept);
  deck lists in `waves/archive/`.

| wave | run id | runs/deck | pass | decks that failed (passed/runs) |
|---|---|---|---|---|
| A-p11-core | 41780319812 | 10 | 70/70 | none |
| B-p11-extras | 41780372380 | 10 | 210/210 | none |
| C-v5-v6-v7 | 41780422738 | 10 | 124/190 | v5-dly30-g05 4/10, v5-dly30-g2 0/10, v5-dly45-alone/-g05/-g2 0/10, v7-dly78-alone 0/10, v7-dly78-g01-tau02 0/10 |
| D-p16-sihwind | 41780473246 | 10 | 129/130 | p16-sihwind-lqr-set1 9/10 |
| E-tau-grid | 41780523682 | 5 | 50/50 | none |
| F-nominal | 41780573202 | 5 | 105/115 | adrc-wc-08 0/5, adrc-wc-12 0/5 |
| G-p11n-mrac-unit | 41780622654 | 5 | 95/105 | heavy-hover-step 0/5, motor-out 0/5 |

- Digested 2026-11-04 by `tools/wave_digest.py`: tables in `research/digests/wave-digest-A-G.md`, findings in PROGRESS ("Wave digest A-G").

## Caveats
- Stock SIH has no aerodynamics or wind. `p16-sihwind-*` use our SIH wind patch; other disturbances are injected
  forces/torques (MRL_DIST_R, MRL_DIST_T).
- The `-alone` baselines fly PX4 default gains on the 1 kg research drone, not a fair tuning (V6 open): "MRAC beats
  alone" is not a thesis claim before V6.
- `sp_dt_p99_ms` is bounded by the 200 ms logger interval; it is not the controller cadence.
- Compare inside one wave, paired by `run` (= seed). The 3-block v2 MRAC is not built yet.

## A-G answers (digest 2026-11-04)
1. Delay (C): at 30 ms the g2 rate layer drives a saturated rate oscillation (paired vs alone: rate_rms_rp +0.568,
   motor_sat_frac +0.726), yet hold and tilt stay inside their limits in 9 of 10 flights: the failures are
   must_land or a runner error, which the record does not hold. Next item 1 names the check.
2. Done 2026-11-04: wave I digested (`research/digests/wave-digest-I.md`, PROGRESS "Wave I"). Pooled B + I (seeds 1-20):
   PROGRESS "Waves B + I pooled".
3. Stress (G): heavy-hover-step (flycart30 airframe) tilts 51.7-53.9 deg on its 10 m step against a 35 deg limit;
   hover-step tilts 35.7 deg against 45. motor-out (one motor off) flips in 5/5: expected for a quadrotor [S].
4. D: p16-sihwind-lqr-set1 failed run 6 only, with no hold or tilt value recorded (stopped before the hold step [S]).
- Main result: the full stack costs attitude/rate tracking and motor saturation in nominal and most stress decks
  and helps only with the weak motor (mot1 hold -0.134 [-0.164, -0.103] m); the position layer alone carries the
  motor-saturation cost. Input for the 3-block v2 design.

## Wave H answer (delay edge, 2026-11-04, run 41793765790)
- 116/200 pass. The alone arm passes 10/10 at 20-35 ms. Delay edge of the V5 rate layer per gain scale: g2 between
  20 and 24 ms, g1 between 24 and 27 ms (4/10 at 27), g05 between 27 and 30 ms (2/10 at 30). Past the edge comes a
  saturated rate oscillation (motor_sat_frac +0.65 to +0.75) that breaks no recorded limit (except v5-dly35-g2 hold,
  2 flights), so the failing check is must_land or an error (next item 1). Tables: `research/digests/wave-digest-H.md`.

## Next items (in order)
1. Done 2026-11-05 (PROGRESS "Delay failure traced"): past the delay edge the TimeoutError is the land step's 120 s
   `in_air` wait; on the ground the rate layer keeps a 31-45 deg/s roll-pitch oscillation (disturbance off, thrust at
   minimum), above LNDMC_ROT_MAX 20 deg/s, so maybe_landed never sets. The delay edge is a rate limit cycle, not a
   flight-limit failure. all.json records now carry `landed` (`ci/collect.py`); `tools/wave_digest.py` does not read
   it yet. Job artifacts download with `gh run download RUN_ID -p 'run-*'` (14 days); `tools/land_trace.py` reads them.
2. Done 2026-11-04 (PROGRESS "Wave I", "Waves B + I pooled"). More seeds where the layer should help but the hold interval crosses 0: B's dist, mass, slow and tmax pairs.
   Pushed 2026-11-04 as `waves/I-b-pair-seeds.txt` (8 decks, runs 10, first 11 = seeds 11-20): digest its
   results folder (`I-b-pair-seeds-*`) with `tools/wave_digest.py`; pool with B's seeds 1-10 only if both
   flew the same build.
3. Done 2026-11-05 (PROGRESS "Wave K", "Wave L"; branch claude/collect-landed): 3-block v2 rate law behind MRL_R_V2
   (bits 1 command-lag feature, 2/4 scheduler on gain/output, 8 delayed reference; MRL_R_KDLY known delay;
   MRL_S_FC/K/TAV/EF scheduler). Only block 2 (scheduler) moves the delay edge; blocks 1 and 3 add nothing there.
   The scheduler beats a constant low gain at 0/20/30 ms. Best delay margin: gain scheduling without floor (b2g);
   best nominal: floored output scaling (f2o), which keeps a small oscillation at 30 ms. Outer layers untouched.
   Owner approved 2026-11-05: L1 in every loop with the three roles, flown on a real-world mission.
3b. Done 2026-11-05 (PROGRESS "Wave M", "Wave N"): L1 law in all four loops (L1Axis.hpp; MRL_*_LAW 1, roles MRL_*_L1R
   bits 1 memory, 2 bandwidth scheduler, 4 known physics; per-loop MRL_*_L1B/A/W/T, MRL_X_L1D drag, MRL_L1_EF/KF/LK,
   MRL_L1_MV memory version, MRL_X_TILT xy tilt budget). Realistic mission decks rw-* (battery sag) / rwf-* (motor 75 %).
   Recommended configuration: L1 roles 2+3 (L1R 6) in all loops + MRL_X_TILT 30 (decks rw-l1r6t / rwf-l1r6t):
   hold -0.34 / -0.38 m, track -0.13 m vs PX4 PID, +1.5-1.9 deg peak tilt (18 seeds). Plain L1 and old MRAC unsafe at
   25 ms delay. Memory (role 1, v1 and v2) costs hold in a single mission: test it episodically in E4.
   2026-11-06: owner set the mission tilt gate to 45 deg (M and N re-scored, PROGRESS). Monte Carlo missions: param
   values in a deck can be {uniform|normal|scale} draws per seed (scenario.py draw, paired across arms, recorded as
   d_<NAME> in all.json), param steps can ramp (ramp_s); SIH_ACT_DJIT adds per-sample delay jitter. Wave O
   (`waves/O-montecarlo.txt`, pushed 6f72ef9, 240 jobs): mc-*/mcf-* draw all vehicle, sensor and scene params; arms
   alone, mrac, l1r6, l1r6t; digest it, then regress the paired gain on the d_ draws (sensitivity).
   Fidelity ladder (`research/notes/fidelity-ladder.md`): SIH high-fidelity physics `px4-mrac/sih_fidelity.hpp`
   (SIH_* params, off by default; test `ci/test_sih_fidelity.cpp`); wave P (`waves/P-highfidelity.txt`, pushed c6c54d8,
   decks hf-*/hff-*) flies it in Monte Carlo. Needs the owner: real logs for L4 identification, board for HITL.
   Param docs: run PX4's src/lib/parameters/px_process_params.py on changed *_params.c before pushing (wave N broke there).
   2026-11-06 results: wave O (Monte Carlo, run 42107461595) and wave P (high-fidelity physics, run 42112117524):
   L1 + tilt budget holds better than PX4 PID in 27-29/30 seeds (-0.55..-1.18 m) but adds +3.3-3.9 deg peak tilt in
   the high-fidelity physics (gate 45 binds: 20-22/30 pass vs PX4 26-27/30); L1 fails seed 8 (delay 32 ms vs 25
   assumed, slow motors). Next: tilt budget from the real tilt limit / thrust margin across all loops; robust delay
   (online estimate or lower rate bandwidth). Figures: research/figs (tools/mc_figs.py, tools/key_flight_plots.py),
   emailed to the owner 2026-11-06. Gazebo on CI works: push `waves-gz/<name>.txt` -> `.github/workflows/gz.yml`
   (ci/build_gz.sh, ci/run_gz.sh; about 5 min per flight, max 10 in parallel: validation sets only). Wave Q
   (run 42138795657, 3 seeds, gz-rw-*): L1 + tilt budget vs PX4 hold -0.21 m [-0.30, -0.09], track -0.14 m, tilt
   +4.2 deg, pass 2/3 vs 3/3; old MRAC flips 3/3. Same ranking as SIH wave P. Digest
   `research/digests/wave-digest-Q-gz.md`, figure `research/figs/Q-gz-key-seed2`, side-by-side video
   `research/videos/gz-px4-vs-l1.mp4` (vehicles/research_drone_chase, worlds/gusty_video.sdf; waves-gz/Q-gz-video*.txt).
   Both emailed to the owner 2026-11-06. Branch claude/collect-landed is not merged into main yet.
   Open inside 3b: the inner-loop share of the extra tilt (rate L1 bandwidth or a rate-loop budget); L1 vs MRAC at
   0/20/30 ms on the V5 decks (delay-margin curve).
3c. Done 2026-11-06 (PROGRESS "Wave R", "Wave R2", "Wave R3", "Gazebo wave S"; branch claude/collect-landed):
   authority budget (AuthorityBudget.hpp, MRL_B_EN/TMRG/FMRG: outer command scaled toward the baseline to stay inside
   tilt <= TILTMAX - margin and |F| <= 1 - margin; cut fed back to L1 as saturation) and online delay identification
   (DelayBank in L1Axis.hpp, MRL_R_DEST 1 rate loop, 2 all loops). The budget cuts <1 % of the time: the extra tilt
   was attitude overshoot from the inner L1 layers, not a larger outer command. Recommended configuration now:
   L1 in the outer loops only (vz, xy; roles 2+3; budget; online delay; rate and attitude route-only) = scenarios
   *-l1obd. SIH 30 seeds: hold -0.4..-0.5 m, track -0.13..-0.16 m, tilt +-0 deg vs PX4, motor fault included;
   dense path (1035 waypoints 5 cm apart) cross-track -23 % (62.9 -> 48.7 cm). Gazebo 10 seeds: same ranking.
   Dense step (agent/scenario.py 'dense', metrics dense_*), plots tools/dense_plots.py.
   Open inside 3c: the dense error left is the baseline's reference lag (lap 2 lag rms 1.3 m at 3 m/s): offboard
   position + velocity setpoints, no acceleration feed-forward. Proposed to the owner: an acceleration (curvature)
   feed-forward arm in the dense step (guidance, not adaptation). Gazebo jobs can die in apt (gz runtime install);
   wave S lost 10 of 62 that way (3 hung 30 min first).
4. The review experiments below, then V4, V6-V8 and P13-P16 (`research/OPEN-ITEMS.md`).
5. Decided 2026-11-06 (owner): 45 deg on the mission decks. Was: owner decision on the 35 deg tilt gate on the real-world mission decks (rw-*, rwf-*: PX4 PID itself peaks 35.3-36.7 deg
   in 7 of 18 flights) and heavy-hover-step's 35 deg tilt limit (PX4's default tilt maximum is 45 deg [S]). Do not change
   the gate without the owner.

## Review experiments (own summary of an external critical review; the review itself stays private)
- E1 delay/noise/frequency: sweep delay (0, 13 ms and up), sensor noise and a chirp. Arms: baseline, a fairly tuned
  constant-gain MRAC, amplitude-gated feature bank, rate scheduling only, output scaling only, both; equal limits and
  tuning budget; a negative control. Measure a Lyapunov-style check, delay margin and high-band power. The claim is
  falsified if the gain comes only from reduced control authority.
- E2 feature bank vs a size-matched RBF, vs a frozen offline map with an adaptive last layer, vs the full bank: on
  held-out conditions, with motor lag, compute cost and regressor (Gram) spectra.
- E3 physics reference: 2x2 (feedforward on/off x feasibility-aware reference on/off) vs a time-scaling governor,
  with model mismatch and an infeasible segment.
- E4 weight memory A->B->A->C: cold start, retain-last, detector warm start, leakage to a target, oracle, wrong memory.
  Accept if >= 20 % better than cold and retain-last (paired interval) and C degrades <= 5 %.
- E5 loop ladder rate -> att -> vz -> accel, leave one block out, features x scheduler 2x2, over PID/LQR/ADRC/MPC;
  compute gate: p99.9 layer time below 10 % of the loop period. Gazebo arms need a CI recipe first (desktop-only).
- Claim shape: bounded and configurable (which loops, disturbances and delay range), not "MRAC is better".

## Desktop-only (needs the owner's PC)
- 2026-11-06: gz.yml fly-gz job: cache the gz runtime apt packages (or a prebuilt runner image) and give the
  install step its own short timeout; wave S lost 10 of 62 jobs in `gz runtime install`.
- 2026-11-06: Gazebo on CI (`build-gz` + `fly-gz` jobs), see `research/notes/fidelity-ladder.md` L5.
- Any `.github/workflows/` change; Gazebo (gz) runs with rendering or video; local WSL caches; publishing the review.
