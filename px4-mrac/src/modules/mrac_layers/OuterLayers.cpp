#include "OuterLayers.hpp"

#include <drivers/drv_hrt.h>
#include <matrix/math.hpp>
#include <px4_platform_common/log.h>

static float layer_dt(hrt_abstime now, hrt_abstime &last, float nominal)
{
	const float dt = (last > 0 && now > last) ? math::constrain((now - last) * 1e-6f, 1e-4f, 0.1f) : nominal;
	last = now;
	return dt;
}

MracAttLayer::MracAttLayer() :
	ModuleParams(nullptr),
	WorkItem("mrac_att_layer", px4::wq_configurations::nav_and_controllers)
{
}

void MracAttLayer::Run()
{
	if (_parameter_update_sub.updated()) {
		parameter_update_s pupdate;
		_parameter_update_sub.copy(&pupdate);
		updateParams();
	}

	vehicle_land_detected_s land{};

	if (_land_detected_sub.update(&land)) { _landed = land.landed || land.maybe_landed; }

	vehicle_attitude_setpoint_s asp{};

	if (_att_sp_sub.update(&asp)) {
		const matrix::Eulerf e(matrix::Quatf(asp.q_d));
		_ang_sp[0] = e.phi();
		_ang_sp[1] = e.theta();
	}

	vehicle_rates_setpoint_s base{};

	if (!_rates_base_sub.update(&base)) { return; }

	vehicle_attitude_s att{};
	_att_sub.copy(&att);
	const matrix::Eulerf ang(matrix::Quatf(att.q));
	const float x[2] {ang.phi(), ang.theta()};

	const float dt = layer_dt(base.timestamp, _last_t, 0.004f);
	const int mode = _param_en.get();
	const MracGains g{_param_tau.get(), _param_gamma.get(), _param_sigma.get(), _param_lim.get(), _param_umax.get()};

	vehicle_rates_setpoint_s out = base;
	float *rate[2] {&out.roll, &out.pitch};
	mrac_rate_status_s st{};

	for (int a = 0; a < 2; a++) {
		const float u = _ax[a].step(x[a], _ang_sp[a], dt, _landed, mode == 1, mode == 1, g);
		*rate[a] += u;
		st.xm[a] = _ax[a].xm;
		st.e[a] = _ax[a].e;
		st.u_ad[a] = u;

		for (int i = 0; i < MracAxis::NPHI; i++) { st.theta[a * MracAxis::NPHI + i] = _ax[a].theta[i]; }
	}

	out.timestamp = hrt_absolute_time();
	_rates_pub.publish(out);

	if (++_status_div >= 2) {
		_status_div = 0;
		st.timestamp = out.timestamp;
		st.mode = (uint8_t)mode;
		st.adapting = (mode == 1) && !_landed;
		_status_pub.publish(st);
	}
}

void MracAttLayer::print()
{
	PX4_INFO("att: mode %d theta r %.4f %.4f %.4f p %.4f %.4f %.4f", (int)_param_en.get(),
		 (double)_ax[0].theta[0], (double)_ax[0].theta[1], (double)_ax[0].theta[2],
		 (double)_ax[1].theta[0], (double)_ax[1].theta[1], (double)_ax[1].theta[2]);
}

MracPosLayer::MracPosLayer() :
	ModuleParams(nullptr),
	WorkItem("mrac_pos_layer", px4::wq_configurations::nav_and_controllers)
{
}

void MracPosLayer::Run()
{
	if (_parameter_update_sub.updated()) {
		parameter_update_s pupdate;
		_parameter_update_sub.copy(&pupdate);
		updateParams();
	}

	vehicle_land_detected_s land{};

	// mc_pos_control resets its velocity integrator on ground_contact (flying_but_ground_contact): vz stops at
	// touchdown while vz_sp still descends, so adapting there only winds Theta up
	if (_land_detected_sub.update(&land)) { _landed = land.landed || land.maybe_landed || land.ground_contact; }

	vehicle_attitude_setpoint_s base{};

	if (!_att_sp_base_sub.update(&base)) { return; }

	vehicle_local_position_s lpos{};
	_lpos_sub.copy(&lpos);
	vehicle_local_position_setpoint_s lsp{};

	if (_lpos_sp_sub.copy(&lsp) && PX4_ISFINITE(lsp.vz)) { _vz_sp = lsp.vz; }

	const float dt = layer_dt(base.timestamp, _last_t, 0.02f);
	const int mode = _param_en.get();
	const MracGains g{_param_tau.get(), _param_gamma.get(), _param_sigma.get(), _param_lim.get(), _param_umax.get()};

	// x = vz (NED, down positive); less negative thrust_body[2] = less thrust = vz goes up, so d x / d u > 0.
	// PX4's vz integrator and hover thrust estimate own the constant term; adaptive augmentation of an integral
	// baseline drops the bias regressor so the two do not share one null direction (arXiv 1604.01882)
	_z.bias = _param_bias.get() != 0;
	const float u = _z.step(lpos.vz, _vz_sp, dt, _landed, mode == 1, mode == 1, g);
	const float dist = _landed ? 0.f : _param_dist_t.get();

	vehicle_attitude_setpoint_s out = base;
	out.thrust_body[2] = math::constrain(base.thrust_body[2] + u + dist, -1.f, 0.f);
	out.timestamp = hrt_absolute_time();
	_att_sp_pub.publish(out);

	mrac_rate_status_s st{};
	st.timestamp = out.timestamp;
	st.xm[2] = _z.xm;
	st.e[2] = _z.e;
	st.u_ad[2] = u;

	for (int i = 0; i < MracAxis::NPHI; i++) { st.theta[2 * MracAxis::NPHI + i] = _z.theta[i]; }

	st.mode = (uint8_t)mode;
	st.adapting = (mode == 1) && !_landed;
	_status_pub.publish(st);
}

void MracPosLayer::print()
{
	PX4_INFO("pos: mode %d theta z %.4f %.4f %.4f", (int)_param_en.get(),
		 (double)_z.theta[0], (double)_z.theta[1], (double)_z.theta[2]);
}
