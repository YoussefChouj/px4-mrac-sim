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
 * derivative feedforward; block 2: 512 gated fast copy of every active term. A change restarts adaptation.
 * @min 0
 * @max 1023
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
 * derivative feedforward; block 2: 512 gated fast copy of every active term. A change restarts adaptation.
 * @min 0
 * @max 1023
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
 * derivative feedforward; block 2: 512 gated fast copy of every active term. A change restarts adaptation.
 * @min 0
 * @max 1023
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
 * derivative feedforward; block 2: 512 gated fast copy of every active term. A change restarts adaptation.
 * @min 0
 * @max 1023
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
