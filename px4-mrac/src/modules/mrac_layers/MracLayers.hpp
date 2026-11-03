/**
 * mrac_layers: MRAC augmentation layers that sit at the uORB handoffs of any baseline controller.
 *
 * Rate layer (this class): the baseline rate controller publishes its torque to vehicle_torque_setpoint_base when
 * MRL_EN_RATE >= 1; this module adds u_ad = Theta'Phi per axis and publishes vehicle_torque_setpoint.
 * The attitude and position layers (OuterLayers.hpp) are owned here and run on their own work items.
 * Law: MracAxis.hpp (same shape as the flown API/mrac.c).
 */
#pragma once

#include "MracAxis.hpp"
#include "OuterLayers.hpp"
#include "XyCtrl.hpp"

#include <px4_platform_common/defines.h>
#include <px4_platform_common/module.h>
#include <px4_platform_common/module_params.h>
#include <px4_platform_common/px4_work_queue/WorkItem.hpp>
#include <uORB/Publication.hpp>
#include <uORB/Subscription.hpp>
#include <uORB/SubscriptionCallback.hpp>
#include <uORB/topics/mrac_rate_status.h>
#include <uORB/topics/parameter_update.h>
#include <uORB/topics/vehicle_angular_velocity.h>
#include <uORB/topics/vehicle_land_detected.h>
#include <uORB/topics/vehicle_rates_setpoint.h>
#include <uORB/topics/vehicle_torque_setpoint.h>

using namespace time_literals;

class MracLayers : public ModuleBase<MracLayers>, public ModuleParams, public px4::WorkItem
{
public:
	MracLayers();
	~MracLayers() override = default;

	static int task_spawn(int argc, char *argv[]);
	static int custom_command(int argc, char *argv[]);
	static int print_usage(const char *reason = nullptr);

	bool init();
	int print_status() override;

private:
	void Run() override;

	uORB::SubscriptionCallbackWorkItem _torque_base_sub{this, ORB_ID(vehicle_torque_setpoint_base)};
	uORB::SubscriptionInterval _parameter_update_sub{ORB_ID(parameter_update), 1_s};
	uORB::Subscription _angular_velocity_sub{ORB_ID(vehicle_angular_velocity)};
	uORB::Subscription _rates_sp_sub{ORB_ID(vehicle_rates_setpoint)};
	uORB::Subscription _land_detected_sub{ORB_ID(vehicle_land_detected)};

	uORB::Publication<vehicle_torque_setpoint_s> _torque_pub{ORB_ID(vehicle_torque_setpoint)};
	uORB::Publication<mrac_rate_status_s> _status_pub{ORB_ID(mrac_rate_status)};

	MracAttLayer _att_layer;
	MracPosLayer _pos_layer;
	XyCtrlLayer _xy_layer;

	MracAxis _ax[3];
	float _rate_sp[3] {};
	bool _landed{true};
	hrt_abstime _last_t{0};
	int _status_div{0};

	DEFINE_PARAMETERS(
		(ParamInt<px4::params::MRL_EN_RATE>) _param_en_rate,
		(ParamFloat<px4::params::MRL_R_TAU>) _param_tau,
		(ParamFloat<px4::params::MRL_R_GAM>) _param_gamma,
		(ParamFloat<px4::params::MRL_R_SIG>) _param_sigma,
		(ParamFloat<px4::params::MRL_R_LIM>) _param_lim,
		(ParamFloat<px4::params::MRL_R_UMAX>) _param_umax,
		(ParamInt<px4::params::MRL_R_YAW>) _param_yaw,
		(ParamFloat<px4::params::MRL_DIST_R>) _param_dist_r,
		(ParamFloat<px4::params::MRL_ID_AMP>) _param_id_amp,
		(ParamInt<px4::params::MRL_ID_AX>) _param_id_ax,
		(ParamFloat<px4::params::MRL_DIST_P>) _param_dist_p
	)
};
