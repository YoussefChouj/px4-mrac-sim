# Handoff

Updated 2026-11-04 by the desktop session (the owner's PC is off for 2-3 days). Read `CLAUDE.md` first, and update
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
2. Done 2026-11-04: wave I digested (`research/digests/wave-digest-I.md`, PROGRESS "Wave I"). Next: pool waves B and I
   (seeds 1-20) per pair with tools/wave_digest.py on both folders, if it accepts two folders of one deck set.
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
1. Name the check the delay failures break. Since 2026-11-04 `ci/publish.py` appends scenario.py's checks (from each
   job's `metrics.json`) to every kept failing-job log, as `== checks <run folder>` lines. Wave
   `waves/J-delay-check-replay.txt` (v5-dly35-g05, v5-dly30-g1, v5-dly24-g2: per gain the first wave-H deck that failed in every
   flight; seeds 1-3) flies with it: read those lines in `results/J-delay-check-replay-*/logs/` and record the failing
   check in PROGRESS. Since 92ddc9b+1 every all.json record also has `landed` (`agent/arms.py`, from scenario.py's metrics). H vs C run by run: PROGRESS ("Wave H vs wave C, same seeds").
2. More seeds where the layer should help but the hold interval crosses 0: B's dist, mass, slow and tmax pairs.
   Pushed 2026-11-04 as `waves/I-b-pair-seeds.txt` (8 decks, runs 10, first 11 = seeds 11-20): digest its
   results folder (`I-b-pair-seeds-*`) with `tools/wave_digest.py`; pool with B's seeds 1-10 only if both
   flew the same build.
3. 3-block v2 MRAC (`research/notes/three-block-v2.md`) in `px4-mrac/`, each block behind its own param so one build
   flies every combination; CI compiles it (the first run is slow); then leave-one-block-out waves. Keep the
   position-layer saturation cost above in view.
4. The review experiments below, then V4, V6-V8 and P13-P16 (`research/OPEN-ITEMS.md`).
5. Owner decision: heavy-hover-step's 35 deg tilt limit (PX4's default tilt maximum is 45 deg [S]). Do not change
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
- Any `.github/workflows/` change; Gazebo (gz) runs with rendering or video; local WSL caches; publishing the review.
