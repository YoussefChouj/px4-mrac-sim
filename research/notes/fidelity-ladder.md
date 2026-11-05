# Simulation fidelity ladder (2026-11-06)

Owner request 2026-11-06: raise simulation fidelity as far as possible. What runs where, what is done, what needs the
owner (hardware, private logs, desktop).

| level | what it adds | status | runs on |
|---|---|---|---|
| L0 stock SIH | rigid body, linear thrust, linear drag | baseline of waves A-N | CI |
| L1 SIH + research patches | actuator delay + jitter, IMU noise, GPS noise, wind/turbulence, motor fault | done | CI |
| L2 Monte Carlo dispersion | every vehicle, sensor and scene param drawn per seed, paired across arms; gradual changes | done, wave O | CI |
| L3 SIH high-fidelity physics | `px4-mrac/sih_fidelity.hpp`: thrust curve, spin-down lag, motor spread, air density, axial inflow, translational lift, ground effect, rotor drag, quadratic drag, LiPo battery, CoM offset, rotor vibration, IMU bias | done, wave P | CI |
| L4 parameters identified from real logs | every L3 range replaced by a measured value +- its uncertainty | needs owner logs | session |
| L5 Gazebo (gz Harmonic) | per-rotor MulticopterMotorModel, rotor drag plugin, physics engine contacts, sensor plugins | model exists (`vehicles/research_drone`), no CI job | desktop / CI after workflow change |
| L6 hardware in the loop | real STM32F4 + FreeRTOS timing, real ADC/UART/scheduling, real numeric precision | needs board + linked computer | owner bench |
| L7 flight | tethered / indoor, then outdoor; compare logs to the sim twin | owner | field |

## L3 model sources
- Rotor drag linear in rotor speed and in-plane airspeed: Faessler, Franchi, Scaramuzza, "Differential flatness of
  quadrotor dynamics subject to rotor drag", IEEE RA-L 2018.
- Ground effect: Cheeseman and Bennett, "The effect of the ground on a helicopter rotor in forward flight", ARC R&M 3021, 1955.
- Axial inflow and translational lift: momentum theory, linearised about hover (Leishman, Principles of Helicopter
  Aerodynamics, ch. 2-3); gains are [S] ranges until identified.
- Battery: first-order Thevenin pack with a LiPo OCV(SoC) curve; power = ideal induced power / efficiency [S].
- Every L3 term is off at its param default; `ci/test_sih_fidelity.cpp` checks stock equivalence and each term.

## L4: which log identifies which param (owner logs stay private; only fitted numbers go into the repo)
| param | flight / log | method |
|---|---|---|
| SIH_THR_FAC, SIH_T_MAX | hovers at several payloads, throttle vs mass | fit T = T_max (f u^2 + (1-f) u) |
| SIH_BAT_R0, OCV | battery_status voltage and current over a full flight | V = OCV(SoC) - I R0 regression |
| SIH_BAT_ETA | current at hover vs mass | P = T^1.5 / sqrt(2 rho A) / eta |
| SIH_T_TAU, SIH_T_TAU_DN | throttle steps (esc rpm if logged, else accel z) | first-order fit up / down separately |
| SIH_ACT_DLY, SIH_ACT_DJIT | multisine rate sysid (existing P8 method) + timestamp jitter of actuator_outputs | FRF delay; interval histogram |
| SIH_RD_K, SIH_CDA, SIH_KDV | constant-speed legs at 1-8 m/s, level | tilt vs speed: m g tan(tilt) = k1 v + k2 v^2 |
| SIH_PROP_R (ground effect) | slow descents to touchdown | throttle vs height below 30 cm |
| SIH_VIB_ACC/GYR/H2 | high-rate raw IMU (SDLOG_PROFILE high rate / sensor_gyro_fifo) in hover | FFT peaks at rotor frequency and 2x |
| SIH_GYR_STD/ACC_STD, biases | 10 min static on the bench | Allan variance; bias = mean |
| SIH_IXX/IYY/IZZ, SIH_COM_X/Y | rate sysid (inertia), hover trim (CoM) | existing P8 fit; steady roll/pitch torque at hover |
| SIH_RA_KAX, SIH_RA_KTL | climbs at several speeds; forward flight throttle vs speed | thrust per throttle vs inflow |

## L5 Gazebo on CI (desktop-only change, `.github/workflows/` is not editable from sessions)
Wanted: a `build-gz` job (ci/build.sh without `--no-sim-tools`, `make px4_sitl_default` with gz, pack
`build/px4_sitl_default` + `Tools/simulation/gz`) cached on its own key, and a `fly-gz` matrix that installs the gz
Harmonic runtime (`apt install gz-harmonic` from packages.osrfoundation.org) and runs `ci/run.sh` for `"sim": "gz"`
decks. Expected cost [S]: build +10-15 min once per change, fly about 1x real time (a 150 s mission ~4 min + ~4 min
install per job), so a validation subset (40 jobs) rather than full Monte Carlo. Purpose: cross-check that the
SIH L3 conclusions (arm ranking, paired effects) hold in a different physics engine.

## L6 HITL
The thesis firmware is the owner's FreeRTOS STM32F4 code (repo FreeRTOS-adaptive-controller-codex), not PX4, so PX4's
HITL mode does not apply directly. Wanted: a HIL bridge where the PC sim (SIH L3 physics compiled as a host program
from sih_fidelity.hpp + the SIH equations of motion) sends IMU/baro/GPS frames over UART at the IMU rate and reads
the motor commands back, so the controller runs on the real MCU with its real timing. Needs the board on a linked
computer.
