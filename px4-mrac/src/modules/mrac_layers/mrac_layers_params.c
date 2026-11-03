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
 * @min 0.05
 * @max 5
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_P_TAU, 0.5f);

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
 * Test disturbance: collective thrust offset in flight (positive = less thrust, like extra mass), MRL_EN_POS >= 1.
 * @min -0.3
 * @max 0.3
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(MRL_DIST_T, 0.0f);

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
 * LQR/MPC integral state clamp.
 * @unit m
 * @min 0
 * @max 10
 * @group MRAC layers
 */
PARAM_DEFINE_FLOAT(XYC_INT_MAX, 2.0f);
