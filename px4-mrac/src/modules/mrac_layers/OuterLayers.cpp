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
		// block 1 structured terms of the attitude loop: the other axis angle and setpoint (roll/pitch coupling)
		_ax[a].cfg(_param_feat.get(), _param_xs.get(), _param_ge0.get(), _param_gw.get(), _param_gk.get());
		_ax[a].ub = *rate[a];
		_ax[a].s[0] = x[1 - a];
		_ax[a].s[1] = _ang_sp[1 - a];
		const float u = _ax[a].step(x[a], _ang_sp[a], dt, _landed, mode == 1, mode == 1, g);
		*rate[a] += u;
		st.xm[a] = _ax[a].xm;
		st.e[a] = _ax[a].e;
		st.u_ad[a] = u;

		for (int i = 0; i < MracAxis::NPHI; i++) { st.theta[a * MracAxis::NPHI + i] = _ax[a].theta[i]; }

		st.theta_norm[a] = _ax[a].tnorm();
		st.n_phi = _ax[a].nphi;
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
	// block 1 structured terms of the vz loop: thrust lost to tilt (1/cos - 1) and quadratic horizontal speed
	_z.cfg(_param_feat.get(), _param_xs.get(), _param_ge0.get(), _param_gw.get(), _param_gk.get());
	_z.ub = base.thrust_body[2];
	{
		const float ct = 1.f - 2.f * (base.q_d[1] * base.q_d[1] + base.q_d[2] * base.q_d[2]);
		_z.s[0] = 1.f / math::max(ct, 0.5f) - 1.f;
		_z.s[1] = PX4_ISFINITE(lpos.vx) && PX4_ISFINITE(lpos.vy) ? lpos.vx * lpos.vx + lpos.vy * lpos.vy : 0.f;
	}
	const float u = _z.step(lpos.vz, _vz_sp, dt, _landed, mode == 1, mode == 1, g);
	const float dist = _landed ? 0.f : _param_dist_t.get();

	vehicle_attitude_setpoint_s out = base;
	out.thrust_body[2] = math::constrain(base.thrust_body[2] + u + dist, -1.f, 0.f);

	// XY layer: x = measured NED acceleration, r = the acceleration mc_pos_control commanded (lsp.acceleration, where
	// PID, LQR, ADRC and MPC all end), so it is controller-agnostic. u_ad [m/s^2] tilts the thrust vector; the bias
	// regressor learns a constant acceleration deficit such as wind drag. Needs routing (MRL_EN_POS >= 1).
	const int xy_mode = _param_xy_en.get();
	const MracGains gx{_param_xy_tau.get(), _param_xy_gamma.get(), _param_xy_sigma.get(), _param_xy_lim.get(),
			   _param_xy_umax.get()};
	const float acc[2] {lpos.ax, lpos.ay};
	float uxy[2] {};

	for (int i = 0; i < 2; i++) {
		if (PX4_ISFINITE(lsp.acceleration[i])) { _acc_sp[i] = lsp.acceleration[i]; }

		_xy[i].bias = _param_xy_bias.get() != 0;
		// block 1 structured terms of the xy loop: linear and quadratic drag on the own-axis velocity
		_xy[i].cfg(_param_xy_feat.get(), _param_xy_xs.get(), _param_ge0.get(), _param_gw.get(), _param_gk.get());
		const float vi = i == 0 ? lpos.vx : lpos.vy;
		_xy[i].ub = _acc_sp[i];
		_xy[i].s[0] = PX4_ISFINITE(vi) ? vi : 0.f;
		_xy[i].s[1] = PX4_ISFINITE(vi) ? vi * fabsf(vi) : 0.f;
		uxy[i] = PX4_ISFINITE(acc[i]) ? _xy[i].step(acc[i], _acc_sp[i], dt, _landed, xy_mode == 1, xy_mode == 1, gx) : 0.f;
	}

	if (xy_mode == 1 && !_landed && (fabsf(uxy[0]) > 0.f || fabsf(uxy[1]) > 0.f)) {
		// normalized thrust vector in NED; thrust per m/s^2 from its vertical part (at hover -F_z / g)
		const matrix::Quatf qb(base.q_d);
		matrix::Vector3f F = matrix::Dcmf(qb) * matrix::Vector3f(0.f, 0.f, out.thrust_body[2]);

		if (-F(2) > 0.05f) {
			const float k = -F(2) / 9.80665f;
			F(0) += uxy[0] * k;
			F(1) += uxy[1] * k;
			// same construction as PX4 ControlMath::bodyzToAttitude: keep the base yaw, body z along -F
			const float yaw = matrix::Eulerf(qb).psi();
			const matrix::Vector3f bz = -F.normalized();
			matrix::Vector3f bx = matrix::Vector3f(-sinf(yaw), cosf(yaw), 0.f) % bz;
			bx.normalize();
			const matrix::Vector3f by = bz % bx;
			matrix::Dcmf Rn;

			for (int j = 0; j < 3; j++) { Rn(j, 0) = bx(j); Rn(j, 1) = by(j); Rn(j, 2) = bz(j); }

			matrix::Quatf(Rn).copyTo(out.q_d);
			out.thrust_body[2] = math::constrain(-F.norm(), -1.f, 0.f);
		}
	}
	out.timestamp = hrt_absolute_time();
	_att_sp_pub.publish(out);

	mrac_rate_status_s st{};
	st.timestamp = out.timestamp;
	st.xm[2] = _z.xm;
	st.e[2] = _z.e;
	st.u_ad[2] = u;

	for (int i = 0; i < MracAxis::NPHI; i++) { st.theta[2 * MracAxis::NPHI + i] = _z.theta[i]; }

	st.theta_norm[2] = _z.tnorm();
	st.n_phi = _z.nphi;

	st.mode = (uint8_t)mode;
	st.adapting = (mode == 1) && !_landed;
	_status_pub.publish(st);

	mrac_rate_status_s sx{};
	sx.timestamp = out.timestamp;

	for (int i = 0; i < 2; i++) {
		sx.xm[i] = _xy[i].xm;
		sx.e[i] = _xy[i].e;
		sx.u_ad[i] = uxy[i];

		for (int j = 0; j < MracAxis::NPHI; j++) { sx.theta[i * MracAxis::NPHI + j] = _xy[i].theta[j]; }

		sx.theta_norm[i] = _xy[i].tnorm();
		sx.n_phi = _xy[i].nphi;
	}

	sx.mode = (uint8_t)xy_mode;
	sx.adapting = (xy_mode == 1) && !_landed;
	_xy_status_pub.publish(sx);
}

void MracPosLayer::print()
{
	PX4_INFO("pos: mode %d theta z %.4f %.4f %.4f", (int)_param_en.get(),
		 (double)_z.theta[0], (double)_z.theta[1], (double)_z.theta[2]);
	PX4_INFO("xy: mode %d theta x %.4f %.4f %.4f y %.4f %.4f %.4f", (int)_param_xy_en.get(),
		 (double)_xy[0].theta[0], (double)_xy[0].theta[1], (double)_xy[0].theta[2],
		 (double)_xy[1].theta[0], (double)_xy[1].theta[1], (double)_xy[1].theta[2]);
}
