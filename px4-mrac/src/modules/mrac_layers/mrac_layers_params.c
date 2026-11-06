/**
 * MRAC rate layer mode: 0 off (baseline publishes torque directly), 1 route + adapt, 2 route only (u_ad = 0).
 *
 * Read by mc_rate_control on every parameter update, so it can switch in flight.
 * @min 0
 * @max 2
 * @group MRAC layers
 */
PARAM_DEFINE_INT32(MRL_EN_RATE, 0);

/**
 * Rate reference model time constant [s] (first order).
 * @min 0.005
 * @max 0.5
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_R_TAU, 0.06f);

/**
 * Rate layer learning rate gamma.
 * @min 0
 * @max 50
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_R_GAM, 2.0f);

/**
 * Rate layer sigma leakage.
 * @min 0
 * @max 5
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_R_SIG, 0.05f);

/**
 * Rate layer projection bound on each Theta entry.
 * @min 0
 * @max 2
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_R_LIM, 0.5f);

/**
 * Rate layer |u_ad| clamp (normalized torque).
 * @min 0
 * @max 1
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_R_UMAX, 0.3f);

/**
 * Rate layer adapts yaw too (1) or roll and pitch only (0).
 * @boolean
 * @group MRAC layers
 */
PARAM_DEFINE_INT32(MRL_R_YAW, 0);

/**
 * Test disturbance: constant roll torque added in flight (normalized), any MRL_EN_RATE >= 1.
 * @min -0.5
 * @max 0.5
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_DIST_R, 0.0f);

/**
 * System-ID multisine torque amplitude (normalized, 0 = off), any MRL_EN_RATE >= 1, in flight only.
 *
 * Twelve log-spaced tones 0.5-20 Hz, Schroeder phases, time base hrt seconds of the torque timestamp_sample, so the
 * dither is rebuilt offline from the log. The axis is MRL_ID_AX.
 * @min 0
 * @max 0.3
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_ID_AMP, 0.0f);

/**
 * System-ID multisine axis: 0 roll, 1 pitch, 2 yaw.
 * @min 0
 * @max 2
 * @group MRAC layers
 */
PARAM_DEFINE_INT32(MRL_ID_AX, 0);

/**
 * Gazebo pure actuator delay added in the gz bridge ESC output (patch_gz_delay.py), sim only.
 *
 * The stock gz sim already shows about 10 ms rate-loop delay. 3 ms brings the fitted research-drone delay to the
 * real 12.9-14.1 ms (plant_fit.py on rd-gz-id).
 * @unit ms
 * @min 0
 * @max 50
 * @group Simulator
 */
PARAM_DEFINE_INT32(SIM_GZ_ACT_DLY, 0);

/**
 * Test disturbance: constant pitch torque added in flight (normalized), any MRL_EN_RATE >= 1.
 * @min -0.5
 * @max 0.5
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_DIST_P, 0.0f);

/**
 * MRAC attitude layer mode: 0 off, 1 route + adapt, 2 route only (u_ad = 0). Read by mc_att_control.
 * @min 0
 * @max 2
 * @group MRAC layers
 */
PARAM_DEFINE_INT32(MRL_EN_ATT, 0);

/**
 * Attitude reference model time constant [s].
 * @min 0.02
 * @max 2
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_A_TAU, 0.15f);

/**
 * Attitude layer learning rate gamma.
 * @min 0
 * @max 50
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_A_GAM, 1.0f);

/**
 * Attitude layer sigma leakage.
 * @min 0
 * @max 5
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_A_SIG, 0.05f);

/**
 * Attitude layer projection bound on each Theta entry.
 * @min 0
 * @max 5
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_A_LIM, 1.0f);

/**
 * Attitude layer |u_ad| clamp [rad/s] (rate setpoint offset).
 * @min 0
 * @max 3
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_A_UMAX, 0.5f);

/**
 * MRAC position layer (z) mode: 0 off, 1 route + adapt, 2 route only (u_ad = 0). Read by mc_pos_control.
 * @min 0
 * @max 2
 * @group MRAC layers
 */
PARAM_DEFINE_INT32(MRL_EN_POS, 0);

/**
 * Vertical velocity reference model time constant [s].
 *
 * 1.0 keeps a 6.7x time-scale gap to the attitude layer (MRL_A_TAU 0.15); see research/PROGRESS.md P11-prep tau sweep.
 *
 * @min 0.05
 * @max 5
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_P_TAU, 1.0f);

/**
 * Position layer learning rate gamma.
 * @min 0
 * @max 50
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_P_GAM, 0.5f);

/**
 * Position layer sigma leakage.
 * @min 0
 * @max 5
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_P_SIG, 0.02f);

/**
 * Position layer projection bound on each Theta entry.
 * @min 0
 * @max 2
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_P_LIM, 0.3f);

/**
 * Position layer |u_ad| clamp (normalized collective thrust).
 * @min 0
 * @max 0.5
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_P_UMAX, 0.15f);

/**
 * Position layer keeps the constant (bias) regressor.
 *
 * Off by default: the PX4 vz integrator and hover thrust estimator already integrate the constant term.
 * @boolean
 * @group MRAC layers
 */
PARAM_DEFINE_INT32(MRL_P_BIAS, 0);

/**
 * Test disturbance: collective thrust offset in flight (positive = less thrust, like extra mass), MRL_EN_POS >= 1.
 * @min -0.3
 * @max 0.3
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_DIST_T, 0.0f);

/**
 * MRAC XY layer mode: 0 off, 1 adapt, 2 status only (u_ad = 0).
 *
 * Runs inside the position layer, so it needs
 * MRL_EN_POS >= 1 (MRL_EN_POS 2 gives an XY-only arm). x = measured NED acceleration, r = commanded acceleration.
 * @min 0
 * @max 2
 * @group MRAC layers
 */
PARAM_DEFINE_INT32(MRL_EN_XY, 0);

/**
 * XY layer reference model time constant (commanded to measured acceleration through the attitude loop).
 * @unit s
 * @min 0.05
 * @max 2.0
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_X_TAU, 0.3f);

/**
 * XY layer adaptation gain (normalized gradient).
 * @min 0.0
 * @max 20.0
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_X_GAM, 1.0f);

/**
 * XY layer sigma leakage.
 * @min 0.0
 * @max 1.0
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_X_SIG, 0.02f);

/**
 * XY layer Theta limit per entry.
 * @min 0.0
 * @max 5.0
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_X_LIM, 1.0f);

/**
 * XY layer adaptive acceleration clamp per axis (2 m/s^2 is about 11.5 deg of extra tilt).
 * @unit m/s^2
 * @min 0.0
 * @max 5.0
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_X_UMAX, 2.0f);

/**
 * XY layer keeps the constant (bias) regressor: on by default, the constant term is the wind drag deficit.
 * @boolean
 * @group MRAC layers
 */
PARAM_DEFINE_INT32(MRL_X_BIAS, 1);

/**
 * xy baseline controller that replaces the PX4 xy position/velocity PID (mc_pos_control follows its acceleration).
 * @value 0 PX4 PID (off)
 * @value 1 LQR
 * @value 2 ADRC
 * @value 3 MPC
 * @group MRAC layers
 */
PARAM_DEFINE_INT32(XYC_MODE, 0);

/**
 * xy baseline acceleration clamp per axis.
 * @unit m/s^2
 * @min 0.5
 * @max 10
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(XYC_AMAX, 4.0f);

/**
 * ADRC closed-loop bandwidth (observer bandwidth is 4x).
 * @unit rad/s
 * @min 0.2
 * @max 6
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(XYC_WC, 1.5f);

/**
 * LQR/MPC integral band: the position error integrates only when |e| is below this.
 * @unit m
 * @min 0
 * @max 5
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(XYC_INT_BAND, 1.0f);

/**
 * LQR gain row (xyc_gains.h XYC_LQR_SETS): 0 generated default, 1-4 stiffer (slow pole 1.78/1.88/2.31/2.67 rad/s).
 * @min 0
 * @max 4
 * @group MRAC layers
 */
PARAM_DEFINE_INT32(XYC_LQR_SET, 0);

/**
 * LQR/MPC integral state clamp.
 * @unit m
 * @min 0
 * @max 10
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(XYC_INT_MAX, 2.0f);

/**
 * rate layer regressor feature mask (thesis three-block framework).
 *
 * Bits: 1 x, 2 r, 4 bias (7 = the original law); block 1 structured: 8 x|x|/xs, 32 baseline command,
 * 64 gyroscopic w_j*w_k, 128 cross-axis rate; block 1 unstructured: 256 five Gaussian bumps on x/xs; block 3: 16 reference
 * derivative feedforward; block 2: 512 gated fast copy of every active term; v2 block 1: 1024 known-delay
 * command lag (or MRL_R_V2 bit 1). A change restarts adaptation.
 * @min 0
 * @max 2047
 * @group MRAC layers
 */
PARAM_DEFINE_INT32(MRL_R_FEAT, 7);

/**
 * rate layer state scale for the x|x|, Gaussian and gate terms.
 * @unit rad/s
 * @min 0.001
 * @max 50
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_R_XS, 3.0f);

/**
 * attitude layer regressor feature mask (thesis three-block framework).
 *
 * Bits: 1 x, 2 r, 4 bias (7 = the original law); block 1 structured: 8 x|x|/xs, 32 baseline command,
 * 64 other-axis angle, 128 other-axis setpoint; block 1 unstructured: 256 five Gaussian bumps on x/xs; block 3: 16 reference
 * derivative feedforward; block 2: 512 gated fast copy of every active term; v2 block 1: 1024 known-delay
 * command lag (used by the rate layer only; 0 here). A change restarts adaptation.
 * @min 0
 * @max 2047
 * @group MRAC layers
 */
PARAM_DEFINE_INT32(MRL_A_FEAT, 7);

/**
 * attitude layer state scale for the x|x|, Gaussian and gate terms.
 * @unit rad
 * @min 0.001
 * @max 50
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_A_XS, 0.3f);

/**
 * vz layer regressor feature mask (thesis three-block framework).
 *
 * Bits: 1 x, 2 r, 4 bias (7 = the original law); block 1 structured: 8 x|x|/xs, 32 baseline command,
 * 64 1/cos(tilt)-1, 128 vx^2+vy^2; block 1 unstructured: 256 five Gaussian bumps on x/xs; block 3: 16 reference
 * derivative feedforward; block 2: 512 gated fast copy of every active term; v2 block 1: 1024 known-delay
 * command lag (used by the rate layer only; 0 here). A change restarts adaptation.
 * @min 0
 * @max 2047
 * @group MRAC layers
 */
PARAM_DEFINE_INT32(MRL_P_FEAT, 7);

/**
 * vz layer state scale for the x|x|, Gaussian and gate terms.
 * @unit m/s
 * @min 0.001
 * @max 50
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_P_XS, 1.0f);

/**
 * xy layer regressor feature mask (thesis three-block framework).
 *
 * Bits: 1 x, 2 r, 4 bias (7 = the original law); block 1 structured: 8 x|x|/xs, 32 baseline command,
 * 64 own-axis velocity v, 128 v|v|; block 1 unstructured: 256 five Gaussian bumps on x/xs; block 3: 16 reference
 * derivative feedforward; block 2: 512 gated fast copy of every active term; v2 block 1: 1024 known-delay
 * command lag (used by the rate layer only; 0 here). A change restarts adaptation.
 * @min 0
 * @max 2047
 * @group MRAC layers
 */
PARAM_DEFINE_INT32(MRL_X_FEAT, 7);

/**
 * xy layer state scale for the x|x|, Gaussian and gate terms.
 * @unit m/s^2
 * @min 0.001
 * @max 50
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_X_XS, 2.0f);

/**
 * Gate (block 2) threshold: normalized tracking error |e|/xs where the fast copy is half on.
 * @min 0.0
 * @max 5.0
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_G_E0, 0.5f);

/**
 * Gate (block 2) width of the sigmoid in normalized error.
 * @min 0.001
 * @max 2.0
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_G_W, 0.15f);

/**
 * Gate (block 2) adaptation gain multiplier of the gated copy (the fast time scale).
 * @min 0.0
 * @max 50.0
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_G_K, 5.0f);

/**
 * rate layer v2 three-block switches (research/notes/three-block-v2.md); 0 = the law of MRL_R_FEAT alone.
 *
 * Bits: 1 block 1 known-delay command lag feature ub(t) - ub(t - MRL_R_KDLY); 2 block 2 scheduler scales the
 * adaptation gain; 4 block 2 scheduler scales u_ad; 8 block 3 reference model delayed by MRL_R_KDLY.
 * @min 0
 * @max 15
 * @group MRAC layers
 */
PARAM_DEFINE_INT32(MRL_R_V2, 0);

/**
 * known transport delay used by the rate v2 blocks 1 and 3 and by L1 role 3 in every layer.
 * @unit ms
 * @min 0
 * @max 250
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_R_KDLY, 0.0f);

/**
 * v2 block 2 scheduler: high-pass corner on the tracking error e.
 * @unit Hz
 * @min 0.1
 * @max 50
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_S_FC, 1.5f);

/**
 * v2 block 2 scheduler: strength k in s = 1 / (1 + k rho^2), rho = high-band share of the power of e.
 * @min 0
 * @max 1000
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_S_K, 20.0f);

/**
 * v2 block 2 scheduler: averaging time of the error powers.
 * @unit s
 * @min 0.02
 * @max 10
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_S_TAV, 0.5f);

/**
 * v2 block 2 scheduler: noise floor of the tracking error (amplitude gate); rho = P_hf / (P_e + MRL_S_EF^2).
 *
 * 0 = the pure high-band share (wave K). Set it between the nominal error rms and the oscillation to be caught
 * (rate layer, 2026-11-05 SIH: nominal e rms 0.028 rad/s, delay limit cycle 0.38 rad/s).
 * @unit rad/s
 * @min 0
 * @max 10
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_S_EF, 0.0f);

/**
 * rate layer adaptive law: 0 MRAC (MracAxis), 1 L1 (L1Axis.hpp: fast piecewise-constant estimate, low-pass control).
 *
 * L1 here: x = body rate [rad/s], command normalized torque.
 * @value 0 MRAC
 * @value 1 L1
 * @group MRAC layers
 */
PARAM_DEFINE_INT32(MRL_R_LAW, 0);

/**
 * rate layer L1 roles (thesis three-role framework), bits: 1 feature memory, 2 bandwidth scheduler, 4 known physics.
 * @min 0
 * @max 7
 * @group MRAC layers
 */
PARAM_DEFINE_INT32(MRL_R_L1R, 0);

/**
 * rate layer L1 nominal input gain b (rad/s^2 per unit; measured in SIH 2026-11-05 (160-180 with the 50 ms motor lag)).
 * @min -1000
 * @max 1000
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_R_L1B, 170.0f);

/**
 * rate layer L1 predictor pole a_s (error decay rate of the state predictor).
 * @unit rad/s
 * @min 0.1
 * @max 1000
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_R_L1A, 100.0f);

/**
 * rate layer L1 filter bandwidth w_c of C(s) = w_c / (s + w_c); sets robustness and delay margin.
 * @unit rad/s
 * @min 0.01
 * @max 200
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_R_L1W, 10.0f);

/**
 * rate layer L1 role 3 known first-order lag of what follows the command (motor lag (SIH_T_TAU 0.0505 on the research drone)).
 * @unit s
 * @min 0
 * @max 2
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_R_L1T, 0.0505f);

/**
 * attitude layer adaptive law: 0 MRAC (MracAxis), 1 L1 (L1Axis.hpp: fast piecewise-constant estimate, low-pass control).
 *
 * L1 here: x = roll/pitch angle [rad], command rate setpoint [rad/s].
 * @value 0 MRAC
 * @value 1 L1
 * @group MRAC layers
 */
PARAM_DEFINE_INT32(MRL_A_LAW, 0);

/**
 * attitude layer L1 roles (thesis three-role framework), bits: 1 feature memory, 2 bandwidth scheduler, 4 known physics.
 * @min 0
 * @max 7
 * @group MRAC layers
 */
PARAM_DEFINE_INT32(MRL_A_L1R, 0);

/**
 * attitude layer L1 nominal input gain b (angle rate per rate setpoint).
 * @min -1000
 * @max 1000
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_A_L1B, 1.0f);

/**
 * attitude layer L1 predictor pole a_s (error decay rate of the state predictor).
 * @unit rad/s
 * @min 0.1
 * @max 1000
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_A_L1A, 40.0f);

/**
 * attitude layer L1 filter bandwidth w_c of C(s) = w_c / (s + w_c); sets robustness and delay margin.
 * @unit rad/s
 * @min 0.01
 * @max 200
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_A_L1W, 4.0f);

/**
 * attitude layer L1 role 3 known first-order lag of what follows the command (inner rate-loop lag [S: rate loop + motor time constants]).
 * @unit s
 * @min 0
 * @max 2
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_A_L1T, 0.08f);

/**
 * vz layer adaptive law: 0 MRAC (MracAxis), 1 L1 (L1Axis.hpp: fast piecewise-constant estimate, low-pass control).
 *
 * L1 here: x = vz NED [m/s], command thrust_body[2].
 * @value 0 MRAC
 * @value 1 L1
 * @group MRAC layers
 */
PARAM_DEFINE_INT32(MRL_P_LAW, 0);

/**
 * vz layer L1 roles (thesis three-role framework), bits: 1 feature memory, 2 bandwidth scheduler, 4 known physics.
 * @min 0
 * @max 7
 * @group MRAC layers
 */
PARAM_DEFINE_INT32(MRL_P_L1R, 0);

/**
 * vz layer L1 nominal input gain b (m/s^2 per thrust unit = g / hover thrust (0.38 on the research drone)).
 * @min -1000
 * @max 1000
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_P_L1B, 25.8f);

/**
 * vz layer L1 predictor pole a_s (error decay rate of the state predictor).
 * @unit rad/s
 * @min 0.1
 * @max 1000
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_P_L1A, 30.0f);

/**
 * vz layer L1 filter bandwidth w_c of C(s) = w_c / (s + w_c); sets robustness and delay margin.
 * @unit rad/s
 * @min 0.01
 * @max 200
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_P_L1W, 3.0f);

/**
 * vz layer L1 role 3 known first-order lag of what follows the command (motor lag).
 * @unit s
 * @min 0
 * @max 2
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_P_L1T, 0.0505f);

/**
 * xy layer adaptive law: 0 MRAC (MracAxis), 1 L1 (L1Axis.hpp: fast piecewise-constant estimate, low-pass control).
 *
 * L1 here: x = horizontal velocity NED [m/s], command acceleration setpoint [m/s^2].
 * @value 0 MRAC
 * @value 1 L1
 * @group MRAC layers
 */
PARAM_DEFINE_INT32(MRL_X_LAW, 0);

/**
 * xy layer L1 roles (thesis three-role framework), bits: 1 feature memory, 2 bandwidth scheduler, 4 known physics.
 * @min 0
 * @max 7
 * @group MRAC layers
 */
PARAM_DEFINE_INT32(MRL_X_L1R, 0);

/**
 * xy layer L1 nominal input gain b (velocity rate per acceleration setpoint).
 * @min -1000
 * @max 1000
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_X_L1B, 1.0f);

/**
 * xy layer L1 predictor pole a_s (error decay rate of the state predictor).
 * @unit rad/s
 * @min 0.1
 * @max 1000
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_X_L1A, 15.0f);

/**
 * xy layer L1 filter bandwidth w_c of C(s) = w_c / (s + w_c); sets robustness and delay margin.
 * @unit rad/s
 * @min 0.01
 * @max 200
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_X_L1W, 1.5f);

/**
 * xy layer L1 role 3 known first-order lag of what follows the command (attitude-loop lag [S]).
 * @unit s
 * @min 0
 * @max 2
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_X_L1T, 0.15f);

/**
 * xy layer L1 role 3 known linear drag per mass (v_dot += -MRL_X_L1D v); SIH: SIH_KDV / SIH_MASS.
 * @unit 1/s
 * @min 0
 * @max 5
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_X_L1D, 0.0f);

/**
 * L1 role 2 scheduler floor as a fraction of the layer's umax (amplitude gate on the high band of sigma_hat).
 * @min 0
 * @max 5
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_L1_EF, 0.2f);

/**
 * L1 role 1 feature-memory learning gain (normalised gradient toward sigma_hat).
 * @min 0
 * @max 100
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_L1_KF, 0.5f);

/**
 * L1 role 1 feature-memory leakage.
 * @unit 1/s
 * @min 0
 * @max 10
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_L1_LK, 0.02f);

/**
 * L1 role 1 memory version.
 *
 * 0 v1: fit the raw sigma_hat with unfiltered features. 1 v2: features low-passed at 2 w_c, fitted to the
 * low-frequency estimate already applied.
 * @value 0 v1
 * @value 1 v2
 * @group MRAC layers
 */
PARAM_DEFINE_INT32(MRL_L1_MV, 0);

/**
 * xy L1 tilt budget (0 = off).
 *
 * The adaptive acceleration may not raise the horizontal acceleration past g tan(budget) nor past the baseline's
 * own command (feasibility-aware augmentation).
 * @unit deg
 * @min 0
 * @max 80
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_X_TILT, 0.0f);

/**
 * Online delay estimate (role 3 upgrade, 0 = off).
 *
 * 1: the rate-layer L1 replaces MRL_R_KDLY by a delay identified in flight per roll/pitch axis (DelayBank: band-passed
 * correlation of the measured angular acceleration with the applied command delayed by 0..24 samples, best fit by a
 * parabola, low-passed). 2: the attitude, vz and xy L1 layers use the same estimate. MRL_R_KDLY stays the prior
 * until 5 s of flight. Logged as mrac_rate_status.dly_est.
 * @min 0
 * @max 2
 * @group MRAC layers
 */
PARAM_DEFINE_INT32(MRL_R_DEST, 0);

/**
 * Authority budget across the loops (bitmask, 0 = off).
 *
 * Bit 1 (outer): the vz and xy adaptive increments together may not tilt the thrust vector past
 * MPC_TILTMAX_AIR - MRL_B_TMRG nor raise collective thrust past 1 - MRL_B_FMRG (the baseline's own command is never
 * cut), and may not grow either while the allocator saturates. Bit 2 (attitude): the attitude L1 may not push an
 * axis further into torque saturation, nor raise the tilt once within MRL_B_TMRG / 2 of MPC_TILTMAX_AIR.
 * @min 0
 * @max 3
 * @bit 0 outer loops (vz + xy)
 * @bit 1 attitude loop
 * @group MRAC layers
 */
PARAM_DEFINE_INT32(MRL_B_EN, 0);

/**
 * Authority budget tilt margin below MPC_TILTMAX_AIR.
 *
 * Room left for inner-loop overshoot: the outer adaptive part keeps the commanded tilt below
 * MPC_TILTMAX_AIR minus this margin; the attitude part stops raising the tilt at half of it.
 * @unit deg
 * @min 0
 * @max 30
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_B_TMRG, 8.0f);

/**
 * Authority budget collective thrust margin.
 *
 * Fraction of full collective thrust that the outer adaptive part leaves for attitude control.
 * @min 0
 * @max 0.5
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_B_FMRG, 0.1f);
