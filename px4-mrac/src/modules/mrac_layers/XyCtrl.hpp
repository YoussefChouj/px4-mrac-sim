#pragma once
// xy baselines (LQR / ADRC / MPC) ported from the firmware API/xy_ctrl.c.
// Reads trajectory_setpoint, replaces xy position/velocity tracking with an acceleration
// command, and publishes trajectory_setpoint_xyc, which mc_pos_control follows when XYC_MODE > 0.

#include <px4_platform_common/module_params.h>
#include <px4_platform_common/px4_work_queue/WorkItem.hpp>
#include <uORB/Publication.hpp>
#include <uORB/Subscription.hpp>
#include <uORB/SubscriptionCallback.hpp>
#include <uORB/topics/parameter_update.h>
#include <uORB/topics/trajectory_setpoint.h>
#include <uORB/topics/vehicle_land_detected.h>
#include <uORB/topics/vehicle_local_position.h>

#include "xyc_gains.h"

using namespace time_literals;

static constexpr int XYC_DMAX = 16;
static constexpr int XYC_DQ = XYC_DELAY > 0 ? XYC_DELAY : 1;	// ring length, never 0 for the modulo
static_assert(XYC_DELAY < XYC_DMAX, "fitted delay longer than the command pipe");

struct XyAxis {
	float z{0}, a_est{0}, u_prev{0};
	float z1{0}, z2{0}, z3{0};
	bool eso_init{false};
	float pipe[XYC_DMAX] {};
	int head{0};
	float plan[XYC_MPC_N] {};
};

class XyCtrlLayer : public ModuleParams, public px4::WorkItem
{
public:
	XyCtrlLayer();
	bool init() { return _lpos_sub.registerCallback(); }
	void stop() { _lpos_sub.unregisterCallback(); }
	void print();

private:
	void Run() override;
	float step(XyAxis &s, int kind, float des, float pos, float vel, float vff, float aff);
	void commit(XyAxis &s, float u);
	void reset();

	uORB::SubscriptionCallbackWorkItem _lpos_sub{this, ORB_ID(vehicle_local_position)};
	uORB::SubscriptionInterval _parameter_update_sub{ORB_ID(parameter_update), 1_s};
	uORB::Subscription _traj_sub{ORB_ID(trajectory_setpoint)};
	uORB::Subscription _land_detected_sub{ORB_ID(vehicle_land_detected)};
	uORB::Publication<trajectory_setpoint_s> _xyc_pub{ORB_ID(trajectory_setpoint_xyc)};

	trajectory_setpoint_s _sp{};
	XyAxis _ax[2] {};
	float _u[2] {};
	hrt_abstime _last_step{0};
	bool _landed{true};
	bool _active{false};

	DEFINE_PARAMETERS(
		(ParamInt<px4::params::XYC_MODE>) _param_mode,
		(ParamFloat<px4::params::XYC_AMAX>) _param_amax,
		(ParamFloat<px4::params::XYC_WC>) _param_wc,
		(ParamFloat<px4::params::XYC_INT_BAND>) _param_int_band,
		(ParamFloat<px4::params::XYC_INT_MAX>) _param_int_max
	)
};
