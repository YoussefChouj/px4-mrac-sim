# Three-block adaptive framework v2 (operator correction 2026-11-04, draft for planning)

The V9 code (MRL_*_FEAT masks: a few structured terms, 5 RBFs, a sigmoid gate, r_dot feedforward) is a
SIMPLIFIED first cut. The operator's design:

## Block 1: feature library (memory bank of representations)
- A library of terms drawn from advanced quadrotor models AND from operating scenarios: rigid-body
  (gyroscopic, Coriolis, inertia cross terms), aero (rotor drag ~v, induced drag, blade flapping, v|v|,
  ground effect vs height, ceiling/wall effect), actuator (thrust ~w^2, motor lag, battery sag, saturation),
  payload (slung load pendulum, CG shift, mass change), wind (steady, gust, turbulence spectra), kinematics
  (rotation-matrix terms, tilt coupling).
- Plus stacked approximators: multi-layer RBF, any basis, or a neural net feature extractor (Neural-Fly style:
  learned phi(x) offline/meta-learned, last layer adapted online).
- Code consequence: a feature REGISTRY (term id -> function of a shared state struct), per-loop selection lists,
  and a pluggable approximator interface (RBF layers / NN weights loaded from a file), not a bit mask.

## Block 2: nonlinear scheduler (can run alone)
- Sets HOW block 1 adapts and HOW MUCH each block-1 output contributes: per-feature (or per-group) adaptation
  rates and output scales, driven by measured signals: frequency content of e (spectral bands), error size,
  excitation level, flight phase. Must stay a known function of measured signals (one Lyapunov argument).

## Block 3: known-physics model (idealized simulation / reference model)
- Our known knowledge: nominal rigid-body + inverse kinematics / differential flatness, constraints that must
  hold while adapting; acts as the reference model (possibly predictive, MPC-like) that drives blocks 1 and 2.

## Weight memory (operator idea)
- Store learned Theta per detected scenario (trajectory type, disturbance signature); on detection, warm start
  or pull Theta toward that stored target instead of starting from zero. Related: concurrent learning,
  multiple-model adaptive control with switching/tuning (Narendra), Neural-Fly meta-learned features.

## Status
- V9 bit-mask code stays as the "minimal instance" (default = old law); v2 needs research + operator sign-off
  before building. Cloud matrix on the V9 cut is on hold until v2 is agreed.
