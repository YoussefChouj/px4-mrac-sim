/**
 * Attitude and position MRAC layers (the slower time scales of the multi-time-scale stack).
 *
 * Attitude: mc_att_control publishes vehicle_rates_setpoint_base when MRL_EN_ATT >= 1; this layer adds a rate
 *   offset [rad/s] per roll/pitch axis from an angle reference model on the attitude setpoint and publishes
 *   vehicle_rates_setpoint.
 * Position (z): mc_pos_control publishes vehicle_attitude_setpoint_base when MRL_EN_POS >= 1; this layer adds a
 *   collective thrust offset from a vz reference model on the vz setpoint (mass and thrust-loss adaptation) and
 *   publishes vehicle_attitude_setpoint.
 * Each layer: mode 1 route + adapt, 2 route only (u_ad = 0), and publishes its status as MracRateStatus.
 */
#pragma once

#include "MracAxis.hpp"
#include "L1Axis.hpp"

#include <px4_platform_common/module_params.h>
#include <px4_platform_common/px4_work_queue/WorkItem.hpp>
#include <uORB/Publication.hpp>
#include <uORB/Subscription.hpp>
#include <uORB/SubscriptionCallback.hpp>
#include <uORB/topics/mrac_rate_status.h>
#include <uORB/topics/parameter_update.h>
#include <uORB/topics/vehicle_attitude.h>
#include <uORB/topics/vehicle_attitude_setpoint.h>
#include <uORB/topics/vehicle_land_detected.h>
#include <uORB/topics/vehicle_local_position.h>
#include <uORB/topics/vehicle_local_position_setpoint.h>
#include <uORB/topics/vehicle_rates_setpoint.h>

using namespace time_literals;

class MracAttLayer : public ModuleParams, public px4::WorkItem
{
public:
	MracAttLayer();
	bool init() { return _rates_base_sub.registerCallback(); }
	void stop() { _rates_base_sub.unregisterCallback(); }
	void print();

private:
	void Run() override;

	uORB::SubscriptionCallbackWorkItem _rates_base_sub{this, ORB_ID(vehicle_rates_setpoint_base)};
	uORB::SubscriptionInterval _parameter_update_sub{ORB_ID(parameter_update), 1_s};
	uORB::Subscription _att_sub{ORB_ID(vehicle_attitude)};
	uORB::Subscription _att_sp_sub{ORB_ID(vehicle_attitude_setpoint)};
	uORB::Subscription _land_detected_sub{ORB_ID(vehicle_land_detected)};
	uORB::Publication<vehicle_rates_setpoint_s> _rates_pub{ORB_ID(vehicle_rates_setpoint)};
	uORB::Publication<mrac_rate_status_s> _status_pub{ORB_ID(mrac_att_status)};

	MracAxis _ax[2];
	L1Axis _l1[2];
	float _ang_sp[2] {};
	bool _landed{true};
	hrt_abstime _last_t{0};
	int _status_div{0};

	DEFINE_PARAMETERS(
		(ParamInt<px4::params::MRL_EN_ATT>) _param_en,
		(ParamFloat<px4::params::MRL_A_TAU>) _param_tau,
		(ParamFloat<px4::params::MRL_A_GAM>) _param_gamma,
		(ParamFloat<px4::params::MRL_A_SIG>) _param_sigma,
		(ParamFloat<px4::params::MRL_A_LIM>) _param_lim,
		(ParamFloat<px4::params::MRL_A_UMAX>) _param_umax,
		(ParamInt<px4::params::MRL_A_FEAT>) _param_feat,
		(ParamFloat<px4::params::MRL_A_XS>) _param_xs,
		(ParamFloat<px4::params::MRL_G_E0>) _param_ge0,
		(ParamFloat<px4::params::MRL_G_W>) _param_gw,
		(ParamFloat<px4::params::MRL_G_K>) _param_gk,
		(ParamInt<px4::params::MRL_A_LAW>) _param_alaw,
		(ParamInt<px4::params::MRL_A_L1R>) _param_al1r,
		(ParamFloat<px4::params::MRL_A_L1B>) _param_al1b,
		(ParamFloat<px4::params::MRL_A_L1A>) _param_al1a,
		(ParamFloat<px4::params::MRL_A_L1W>) _param_al1w,
		(ParamFloat<px4::params::MRL_A_L1T>) _param_al1t,
		(ParamFloat<px4::params::MRL_R_KDLY>) _param_kdly,
		(ParamFloat<px4::params::MRL_S_FC>) _param_s_fc,
		(ParamFloat<px4::params::MRL_S_K>) _param_s_k,
		(ParamFloat<px4::params::MRL_S_TAV>) _param_s_tav,
		(ParamFloat<px4::params::MRL_L1_EF>) _param_l1_ef,
		(ParamFloat<px4::params::MRL_L1_KF>) _param_l1_kf,
		(ParamFloat<px4::params::MRL_L1_LK>) _param_l1_lk
	)
};

class MracPosLayer : public ModuleParams, public px4::WorkItem
{
public:
	MracPosLayer();
	bool init() { return _att_sp_base_sub.registerCallback(); }
	void stop() { _att_sp_base_sub.unregisterCallback(); }
	void print();

private:
	void Run() override;

	uORB::SubscriptionCallbackWorkItem _att_sp_base_sub{this, ORB_ID(vehicle_attitude_setpoint_base)};
	uORB::SubscriptionInterval _parameter_update_sub{ORB_ID(parameter_update), 1_s};
	uORB::Subscription _lpos_sub{ORB_ID(vehicle_local_position)};
	uORB::Subscription _lpos_sp_sub{ORB_ID(vehicle_local_position_setpoint)};
	uORB::Subscription _land_detected_sub{ORB_ID(vehicle_land_detected)};
	uORB::Publication<vehicle_attitude_setpoint_s> _att_sp_pub{ORB_ID(vehicle_attitude_setpoint)};
	uORB::Publication<mrac_rate_status_s> _status_pub{ORB_ID(mrac_pos_status)};
	uORB::Publication<mrac_rate_status_s> _xy_status_pub{ORB_ID(mrac_xy_status)};

	MracAxis _z;
	MracAxis _xy[2];
	L1Axis _l1z;
	L1Axis _l1xy[2];
	float _acc_sp[2] {};
	float _vz_sp{0.f};
	bool _landed{true};
	hrt_abstime _last_t{0};

	DEFINE_PARAMETERS(
		(ParamInt<px4::params::MRL_EN_POS>) _param_en,
		(ParamFloat<px4::params::MRL_P_TAU>) _param_tau,
		(ParamFloat<px4::params::MRL_P_GAM>) _param_gamma,
		(ParamFloat<px4::params::MRL_P_SIG>) _param_sigma,
		(ParamFloat<px4::params::MRL_P_LIM>) _param_lim,
		(ParamFloat<px4::params::MRL_P_UMAX>) _param_umax,
		(ParamFloat<px4::params::MRL_DIST_T>) _param_dist_t,
		(ParamInt<px4::params::MRL_P_BIAS>) _param_bias,
		(ParamInt<px4::params::MRL_P_FEAT>) _param_feat,
		(ParamFloat<px4::params::MRL_P_XS>) _param_xs,
		(ParamInt<px4::params::MRL_EN_XY>) _param_xy_en,
		(ParamFloat<px4::params::MRL_X_TAU>) _param_xy_tau,
		(ParamFloat<px4::params::MRL_X_GAM>) _param_xy_gamma,
		(ParamFloat<px4::params::MRL_X_SIG>) _param_xy_sigma,
		(ParamFloat<px4::params::MRL_X_LIM>) _param_xy_lim,
		(ParamFloat<px4::params::MRL_X_UMAX>) _param_xy_umax,
		(ParamInt<px4::params::MRL_X_BIAS>) _param_xy_bias,
		(ParamInt<px4::params::MRL_X_FEAT>) _param_xy_feat,
		(ParamFloat<px4::params::MRL_X_XS>) _param_xy_xs,
		(ParamFloat<px4::params::MRL_G_E0>) _param_ge0,
		(ParamFloat<px4::params::MRL_G_W>) _param_gw,
		(ParamFloat<px4::params::MRL_G_K>) _param_gk,
		(ParamInt<px4::params::MRL_P_LAW>) _param_plaw,
		(ParamInt<px4::params::MRL_P_L1R>) _param_pl1r,
		(ParamFloat<px4::params::MRL_P_L1B>) _param_pl1b,
		(ParamFloat<px4::params::MRL_P_L1A>) _param_pl1a,
		(ParamFloat<px4::params::MRL_P_L1W>) _param_pl1w,
		(ParamFloat<px4::params::MRL_P_L1T>) _param_pl1t,
		(ParamInt<px4::params::MRL_X_LAW>) _param_xlaw,
		(ParamInt<px4::params::MRL_X_L1R>) _param_xl1r,
		(ParamFloat<px4::params::MRL_X_L1B>) _param_xl1b,
		(ParamFloat<px4::params::MRL_X_L1A>) _param_xl1a,
		(ParamFloat<px4::params::MRL_X_L1W>) _param_xl1w,
		(ParamFloat<px4::params::MRL_X_L1T>) _param_xl1t,
		(ParamFloat<px4::params::MRL_X_L1D>) _param_xl1d,
		(ParamFloat<px4::params::MRL_R_KDLY>) _param_kdly,
		(ParamFloat<px4::params::MRL_S_FC>) _param_s_fc,
		(ParamFloat<px4::params::MRL_S_K>) _param_s_k,
		(ParamFloat<px4::params::MRL_S_TAV>) _param_s_tav,
		(ParamFloat<px4::params::MRL_L1_EF>) _param_l1_ef,
		(ParamFloat<px4::params::MRL_L1_KF>) _param_l1_kf,
		(ParamFloat<px4::params::MRL_L1_LK>) _param_l1_lk
	)
};
