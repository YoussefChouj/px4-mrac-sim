# PX4/MRAC independent review — 2026-11-04

## 1. Bottom line

[J] Replace feature expansion with a frozen, falsifiable controller-validation campaign; PX4 is suitable, but the universal thesis claim is unsupported.
[M/J] Fix cloud seed propagation and experiment provenance before buying more statistical confidence with more runs.
[M] “Position MRAC” currently adapts vertical velocity/thrust; horizontal-wind results do not demonstrate horizontal position adaptation.
[M/J] Three numerical spot checks reproduce; causal explanations, comparison fairness, and completion criteria are the larger weaknesses.
[J] Prioritize delay–noise–saturation boundaries and held-out baseline comparisons; defer terrain, planning, cameras, and slung loads.

**Scope/evidence.** [M] Read-only snapshot: WSL repository HEAD `2408fb5af49a548779667a7b52ab60f38fb9b4f8`, clean when inspected. No simulator started, build run, process killed, or settings changed. Only this report and isolated review scratch were written. [M] means observed code/log evidence, **not physical measurement**; all reproduced flight values below are simulation-derived. [R] denotes external research; [J] denotes judgment. All proposed counts, thresholds and effort estimates are **PROPOSED**.

Citation roots: `W` = `C:\Users\Acer\Documents\Codex\2026-11-01\set\outputs\px4-setup`; `R` = `/home/acer/px4-mrac-sim`; `B` = `/home/acer/PX4-mrac`; `P` = `W/research/PROGRESS.md`; `C` = `D:\Projects\UAV_lab\FreeRTOS-adaptive-controller-codex/.claude_state.md`. WSL paths use `PX4-Ubuntu-24.04`, user `acer`. `M/` below abbreviates `R/px4-mrac/src/modules/mrac_layers/`. Findings apply to this snapshot, not subsequent CEO edits.

## 2. Ranked recommendations

### Strategic — do first

| Finding | Evidence | Impact | Effort, h (PROPOSED) | Recommendation | Confidence |
|---|---|---|---|---|---|
| 1. Claim exceeds implemented channels and theory | [M] `M/OuterLayers.cpp:114–128`: vz → collective thrust; `P:58–59,137–139` generalize layer results | Thesis validity | 4–8 to specify; proof separate | [J] Claim augmentation of **specified stable baselines within a stated envelope**. Separate rate, roll/pitch attitude, vertical velocity, and XY performance. Reopen P5/P10/P11 scientific acceptance. | High |
| 2. Cloud wind repetitions collapse to seed 1 | [M] `R/ci/run.sh:14–16` passes RUNS=1; `R/agent/arms.py:100–102` names every child `arm-1`; `scenario.py:277–289` extracts seed from that basename | False diversity/pairing | 2–4 | [J] Pass explicit run/seed IDs end-to-end. Assert distinct seeds across repetitions and identical disturbance traces across paired arms. This affects cloud wind decks; it does not prove previous non-wind batches used distinct seeds. | High |
| 3. Source and artifact identity are incomplete | [M] W/R XyCtrl SHA256 prefixes `5bf72a9aac733b7b` / `a529d9905896c661`; B source matches R. `arms.py:137` saves paths/results, not build hashes. Workflow retention: build 3 days, runs 14 (`arms.yml:48,68`) | Irreproducible thesis | 4–8 | [J] One authoritative checkout; immutable campaign manifest with commit, dirty diff, binary/patch/config/world hashes, effective parameters, dependencies and analysis version. Archive selected raw data beyond CI expiry. Source equality does not establish binary identity. | High |
| 4. Calibration changes erased the apparent failure boundary | [M] `P:295–307`: delay/noise interaction disappears after noise change; `P:303` matches one filtered noise statistic | Sim artifact mistaken for robustness | 8–16 | [J] Cross delay, noise spectrum, motor lag and saturation; retain high-noise cases as stress tests. Validate a noise spectrum and cadence, not only one standard deviation. | High |
| 5. Tuned baseline and adaptive benefit remain confounded | [M] `P:409–480`: PID and LQR tuning, then set-4 selection using few repeats; `P:307` nominal attitude cost remains | Overfit/weak comparator | 8–16 | [J] Equal tuning budgets/objectives/authority, held-out trajectories and parameters, then freeze baseline and MRAC settings before fault tests. Treat set 4 as a candidate. | High |

### Medium

| Finding | Evidence | Impact | Effort, h (PROPOSED) | Recommendation | Confidence |
|---|---|---|---|---|---|
| 6. Metrics can conceal offsets and timing error | [M] `scenario.py:137–143` resets hold origin; `:224–235` compares current reference with latest asynchronous telemetry; `:312` uses max Euler component | Misranked controllers | 6–10 | [J] Recompute on simulation timestamps against logged commands and ground truth. Report absolute hold offset separately from drift, true thrust-axis tilt, tracking/estimation errors, and completeness. | High |
| 7. Failure exclusion is not an experimental policy | [M] `scenario.py:478–494` labels post-takeoff sensor loss SIM-FAULT; `arms.py:101–118` retries/skips; `ci/collect.py:25` denominator includes only retained runs | Survivorship bias | 3–5 | [J] Preserve every attempt and intended-run denominator; distinguish preflight infrastructure, in-flight system failure, and controller failure. Sensor dropout is not automatically independent of workload/controller. | High |
| 8. “Twin” contains assumed and effective parameters | [M] `W/research/research_drone_params.yaml:6–29`: unweighed mass, scaled thrust/inertia, lag-absorbing inertia; `P:68,317–322` changed yaw coefficient and unmatched responses | Transfer failure | 6–12 | [J] Call it a bounded surrogate. Validate held-out FRFs and transport/estimator latency; propagate correlated parameter uncertainty. Regenerate YAML/SIH/SDF from one versioned parameter source. | High |
| 9. Time-scale claim lacks an interaction experiment | [M] `P:148–187`: tau sweep followed by saturation fix; `MracAxis.hpp:36,53` separates reference tau from adaptation/leakage | Wrong mechanism/novelty | 8–16 | [J] Cross reference bandwidth, adaptation gain and leakage; log actual rates, delay, control spectra and saturation. Compare frozen learned compensation with online adaptation. | High |

### Tactical / quick wins

| Finding | Evidence | Impact | Effort, h (PROPOSED) | Recommendation | Confidence |
|---|---|---|---|---|---|
| 10. Queue recovery started but needs durable state | [M] `C:3488–3489` records lost waiters and a replacement WSL chain; `C:3407` reports five idle hours, not independently timed | Lost work/token churn | 3–6 | [J] Finish a WSL queue with atomic pending/running/done/failed states, instance/build locks, resume checkpoints and exit codes. Test restart with dummy jobs; nohup alone cannot survive power loss. | High |
| 11. Stale claims and manual mirroring consume attention | [M] `C:3478–3489`; `P:452` contradicts `M/XyCtrl.cpp:60–80` | Repeated wrong decisions | 1–3 | [J] Replace repeated NEXT prose with job IDs, artifact paths, decision gates and one short current-state page. Generate summaries from manifests; preserve historical results with explicit supersession links. | High |

**Re-rank OPEN-ITEMS.** [J] First P6/P12 measurement, seeds, provenance and failure accounting; then P8 uncertainty validation plus P16 fair tuning; then P5/P10 mechanism tests; then a reopened P11 confirmation campaign. P1/P2 become targeted research only. P7 gets reproducible scientific plots only. P13 wind stays; P13 scenery, P14 planning and P15 camera/hex/slung-load work wait.

**Minimum committee experiment.** [J, PROPOSED] Establish tuned PID and LQI anchors. On these, run the eight rate/attitude/vz on/off combinations under nominal conditions and a pilot-selected coupled stress case; add bypass versus route-only and learned-frozen versus adaptive controls. Then evaluate fixed off/on augmentation across PID/LQI/ADRC/MPC under nominal, mass/thrust, single-motor degradation, delay/slow motors, wind and aggressive trajectories. Include held-out combined faults and trajectories. This tests finite baseline coverage, not “any controller.”

[J, PROPOSED] Start with ten genuinely independent paired disturbance realizations to estimate variance, then size confirmation for a preregistered confidence-interval width and practically useful improvement. Randomize order, block by build/runner, analyze paired run-level effects, report failure fractions and confidence intervals, and correct planned multiple comparisons. Min/max ranges are not confidence intervals; within-batch execution alone does not establish independence. Gains stay fixed across validation faults. Report recovery time, peak transient, time-integrated error, control variation, allocation shortfall and clamp occupancy; parameter movement alone is not convergence evidence.

## 3. Assumptions to re-test

All tests/consequences below are [J, PROPOSED]; evidence is explicitly marked.

| Assumption | Justified? | Test | Consequence if wrong |
|---|---|---|---|
| 0.455 s⁻¹ represents this drone's drag | No. [M] `P:389–402,429` borrows literature; 0.45/0.9885 gives the SIH value. [R] [Faessler et al., Rotor Drag](https://arxiv.org/abs/1712.02402) identifies vehicle-specific coefficients. | Sweep plausible anisotropic drag; verify force versus relative velocity, mass and yaw; retain an uncalibrated range. | Wind results are sensitivity studies, not identified aerodynamics. |
| Gazebo c=0.36 is equivalent physics | Unestablished. [R] [Gazebo WindEffects](https://gazebosim.org/api/sim/8/classgz_1_1sim_1_1systems_1_1WindEffects.html) approximates force using link mass and relative velocity; [M] `P:399–402` revises an earlier rotor-drag explanation. | Separate plugin/rotor forces and test axis/speed scaling; compare SIH and gz on the same input trace. | Retune the model, not controllers to a single favorable wind level. |
| Real plant is matched | Partial. [M] `P:76` includes a real fit residual 0.49; `P:317–320` delays are 52/53 versus 78 ms. | Held-out excitation/coherence, same coordinate conventions, frozen real gains and estimator timing; include uncertainty bands. | Limit transfer claims to validated frequency bands and channels. |
| LQR lacks integral action | False. [M] `M/XyCtrl.cpp:60–80` integrates error inside a band. | Log integral state, band occupancy and saturation during wind. | Diagnose transient bandwidth and gated integration, not a nonexistent missing state. |
| LQR model/set 4 generalizes | Unproven. [M] `xyc_design.py:40–61` chooses the lowest-residual axis; `xyc_gains.h:2–6` has fixed dt and delay; `XyCtrl.cpp:159–165` does not enforce exact cadence. | Validate both axes and command rates; closed-loop ID with independent excitation; held-out Q/R selection. | Re-identify/schedule gains; current pole calculations omit realized timing uncertainty. |
| Bias-off is generally required for integral baselines | No. [M] `P:191–214` supports a local tradeoff. [R] [Simon, Robust MRAC augmentation](https://arxiv.org/html/1604.01882v1) approximates away its baseline integral in derivation; it does not establish this universal rule. | Compare bias on/off, baseline-matched reference and anti-windup on held-out constant faults. | Keep a configurable empirical choice, not a theorem. |
| “13 ms is harmless” follows from lower-noise success | No. [M] `P:299–307` establishes conditional behavior. | Delay × colored noise × gain × saturation stress envelope. | Retain a bounded operating envelope and failure evidence. |
| Equal run index means equal disturbance | Only intended. [M] cloud seed bug above; `patch_sih_wind.py:35–65` uses a dedicated wind RNG but time-step evolution still matters. | Hash realized disturbance/noise traces at aligned simulation times. | Use verified pairing or unpaired analysis; never label scheduling variation as independent seeds. |

**Controller spot-check.** [M] `MracAxis.hpp:41–62` implements normalized `[x,r,1]` regression, gamma-scaled leakage, component clipping and output clipping. The vz thrust sign is consistent near upright flight (`OuterLayers.cpp:120–128`). However, attitude/vz calls omit downstream saturation flags (`:58,:124`), and vz clips combined thrust afterward (`:128`); only the rate layer receives allocator feedback. [J] Test saturation in every channel, stale inputs, re-enable/reset behavior and reference discretization. Bounded coefficients do not prove closed-loop stability; derive the matching/relative-degree assumptions for the augmented baseline, including delay and normalization [R: Simon, linked above].

[M/J] MPC uses a fixed iteration count without a convergence certificate (`XyCtrl.cpp:85–122`); ADRC uses a simplified ESO (`:43–54`). Validate MPC optimality residuals, coupled tilt authority and execution time before claiming equivalence with general MPC/ADRC. Shared inner PX4 loops mean P10 primarily tests common-loop augmentation across different XY controllers.

## 4. Stop doing

- [J] Stop treating passing hover/landing gates as acceptance of adaptation, robustness or time-scale separation.
- [J] Stop promoting tuning winners on the same seeds used to select them, or dismissing adverse results after changing realism parameters.
- [J] Stop expanding viewers/scenes/planners while source identity and scientific metrics remain unsettled.
- [J] Stop comparing this maximum drift metric with another paper's RMS tracking number; neither platform nor measurement conditions are matched (`P:435–444`).

**Platform and prior-art choices.** [J] Use a small deterministic Python model for analytical counterexamples, gain/delay/noise sweeps and Monte Carlo screening. Use SIH for firmware/estimator integration and CI; gz for selected independent actuator/physics/wind checks. Replay real logs for timing, FRFs and sensor spectra; replay cannot establish closed-loop benefit of a controller that was never flown. No simulator migration is justified now.

[R/J] Reuse [PX4 v1.17 MAVSDK integration tests](https://docs.px4.io/v1.17/en/test_and_ci/integration_testing_mavsdk) for flight lifecycle assertions; that version documents C++/Gazebo Classic, so current-main Python/SIH instructions are not drop-in. Keep the existing MAVSDK runner and [pyulog](https://github.com/PX4/pyulog); use [PlotJuggler](https://github.com/PlotJuggler/PlotJuggler) for ULog inspection rather than another custom viewer. Move independent SIH batches and offline analysis to existing free CI; keep one gz job locally and separately locked SIH work, with immutable binaries per batch.

[R/J] Benchmark against [L1Quad: Adaptive Augmentation of Geometric Control](https://arxiv.org/abs/2302.07208) and [Performance, Precision, and Payloads: Adaptive Nonlinear MPC](https://arxiv.org/abs/2109.04210). Their augmentation premise overlaps this thesis; novelty must lie in a demonstrated configuration/interaction rule. [L1Quad's implementation](https://github.com/sigma-pi/L1Quad) is ArduPilot-based, requiring porting. [Experimental Implementation of an Adaptive Digital Autopilot](https://arxiv.org/abs/2012.02896) provides PX4 RCAC flight precedent, but deliberately detunes its baseline: cite that limitation instead of copying the comparator design. These are non-neural alternatives.

## 5. Next 48 hours

All actions are [J, PROPOSED], in order; no campaign-wide success is promised within this window.

1. **Freeze the experiment contract.** Check: one manifest identifies sources/binary, hypothesis, channels, tuning/validation split and acceptance metrics; P5/P10/P11 status distinguishes implementation from evidence.
2. **Repair seeds and attempt accounting.** Check: dummy cloud matrix yields distinct repetition seeds, matched pair trace hashes, and an intentionally missing/failed job prevents a complete campaign verdict.
3. **Make metrics independently reproducible.** Check: ULog-based analysis reproduces existing checks, detects an injected constant offset, and refuses incomplete timestamps/topics; add saturation and cadence outputs.
4. **Validate the uncertainty envelope.** Check: a compact delay/noise/lag model sweep plus selected SIH cases maps both benefit and failure; held-out real FRFs/spectra have explicit tolerances and unresolved mismatches.
5. **Launch the anchor pilot through the durable queue.** Check: frozen tuned PID/LQI, layer ablations and paired fault cases survive a dummy-worker restart and produce a complete attempt ledger, effect intervals and archived artifacts before broader P11 expansion.

## 6. Reproduced numbers

[M] Independent Python/NumPy/pyulog analysis of finished raw files; no scenario runner executed. Root: `/home/acer/.cache/px4-arms/`.

| PROGRESS claim | Raw source and recalculation | Result |
|---|---|---|
| `P:205`: bias-off fig8 rate RMS 0.134 rad/s | `20261104T002650/tau-a015-p100-b0-{1,2,3}/flight.ulg`; interpolate rate setpoints to angular-velocity timestamps, previous-value landed mask, RMS across roll/pitch samples. Values 0.165548853, 0.115484702, 0.119931990; mean **0.133655182**. | Match |
| `P:203`: bias-off thrust-step z peak 0.220 [0.179..0.295] m | Same batch, `mrac-pos-adapt-b0-{1,2,3}/flight.ulg`; first nonzero MRL_DIST_T change, following five seconds, peak absolute interpolated z error. Values 0.295431614, 0.179119000, 0.185122569; mean **0.219891061**. | Match |
| `P:476`: set-4 first-run tilt 20.6° | `p16set5/lqrfig-set4-1/telemetry.csv`; max absolute roll/pitch column = **20.592327118°**. | Match to implemented Euler-component metric, not geometric tilt |

[M] First-file SHA256 prefixes, respectively: `b27ad9f2943e6f50`, `81a3905371128ae4a`, `66ee95507439d3de`. [J] Reproduction validates arithmetic, not experimental independence or the thesis interpretation.

## 7. Disagreements with CEO decisions

- [M] `P:139`: “claim holds in SIH for the inner loops.” [J] This supports selected common PX4 inner loops, not arbitrary baseline/controller-layer combinations.
- [M] `P:307`: “delay risk was a noise artifact.” [J] It is a demonstrated noise–delay vulnerability outside the selected calibration; disappearance does not measure robustness margin.
- [M] `P:322`: “Bandwidth and lag match within ~10-20 %.” [M/J] Reported delays are 78 versus 52/53 ms, approximately 50%/47% larger. Bandwidth agreement does not justify that lag claim or a conservative-transfer inference.
- [M] `P:480`: “make XYC_LQR_SET default 4.” [J] Premature for a thesis baseline; confirm on withheld trajectories/faults after fixing metrics/seeds.
- [M] `P:452`: “LQR has no integral.” [M] Contradicted by source and the later integral-band experiment. [J] Correct the causal narrative before building further experiments on it.

