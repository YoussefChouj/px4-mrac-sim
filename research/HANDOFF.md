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

- Not digested yet: no paired differences or intervals computed (next item 1).

## Caveats
- Stock SIH has no aerodynamics or wind. `p16-sihwind-*` use our SIH wind patch; other disturbances are injected
  forces/torques (MRL_DIST_R, MRL_DIST_T).
- The `-alone` baselines fly PX4 default gains on the 1 kg research drone, not a fair tuning (V6 open): "MRAC beats
  alone" is not a thesis claim before V6.
- `sp_dt_p99_ms` is bounded by the 200 ms logger interval; it is not the controller cadence.
- Compare inside one wave, paired by `run` (= seed). The 3-block v2 MRAC is not built yet.

## Questions from A-G (answer them in item 1)
1. Delay (wave C): at 20 ms every arm passed 10/10; at 30 ms `alone` passed 10/10 while `g05` passed 4/10 and `g2`
   0/10 (g = MRAC gain scale, going by the deck names: check the scenario files); at 45 and 78 ms every arm failed.
   So the layer lowers the delay margin somewhere between 20 and 30 ms. Which gate fails: oscillation or tilt?
2. ADRC (wave F): adrc-wc-08 and adrc-wc-12 failed 0/5 here but passed 3/3 each in sweep run 41678708699. A gate or
   metric change since then (8facffa, V1/V4 edits), or a real difference? Compare the failing gate fields.
3. Stress decks (wave G): heavy-hover-step and motor-out failed 0/5. Expected limit or a bug? Which gate?
4. Wave D: which run of p16-sihwind-lqr-set1 failed, and on which gate?

## Next items (in order)
1. `tools/wave_digest.py <results folder>...`: pass table per wave, failing gate per failing deck, paired differences
   (plus-mrac minus alone, same `run`) per metric with 95 % bootstrap intervals over runs. Dated PROGRESS entry with
   the tables and the answers to the 4 questions.
2. Where an interval includes 0: re-fly that pair (control included) with `first 11`, then `first 21` if needed.
3. Delay edge (question 1): one wave with delays 20/24/27/30/35 ms x (alone, gain scale 0.5, 1, 2), runs 10.
4. 3-block v2 MRAC (`research/notes/three-block-v2.md`) in `px4-mrac/`, each block behind its own param so one build
   flies every combination; CI compiles it (the first run is slow); then leave-one-block-out waves.
5. The review experiments below, then V4, V6-V8 and P13-P16 (`research/OPEN-ITEMS.md`).

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
