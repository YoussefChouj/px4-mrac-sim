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
		const bool l1 = _param_alaw.get() == 1;
		float u = 0.f;

		if (l1) {
			// L1: x = angle, command = rate setpoint [rad/s], nominal angle_dot = rate (b = 1); role 3 knows the
			// inner rate loop as a first-order lag MRL_A_L1T plus the transport delay
			const L1Cfg lc = L1Cfg{_param_al1b.get(), _param_al1a.get(), _param_al1w.get(), _param_al1t.get(), math::max(_param_kdly.get(), 0.f) * 1e-3f, _param_umax.get(), _param_al1r.get(), _param_s_fc.get(), _param_s_k.get(), _param_s_tav.get(), _param_l1_ef.get(), _param_l1_kf.get(), _param_l1_lk.get(), _param_l1_mv.get()};
			_l1[a].s[0] = _ax[a].s[0];
			_l1[a].s[1] = _ax[a].s[1];
			u = _l1[a].step(x[a], *rate[a], 0.f, dt, _landed, mode == 1, lc);

		} else {
			u = _ax[a].step(x[a], _ang_sp[a], dt, _landed, mode == 1, mode == 1, g);
		}

		*rate[a] += u;
		st.xm[a] = l1 ? _l1[a].xh : _ax[a].xm;
		st.e[a] = l1 ? _l1[a].xt : _ax[a].e;
		st.u_ad[a] = u;
		st.sched_cut[a] = l1 ? 1.f - _l1[a].sc : 0.f;

		for (int i = 0; i < MracAxis::NPHI; i++) { st.theta[a * MracAxis::NPHI + i] = l1 ? _l1[a].theta[i] : _ax[a].theta[i]; }

		st.theta_norm[a] = l1 ? _l1[a].tnorm() : _ax[a].tnorm();
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
	const bool l1z = _param_plaw.get() == 1;
	float u = 0.f;

	if (l1z) {
		// L1: x = vz (NED), command = thrust_body[2] (negative up); nominal vz_dot = g + b u with b = g / hover
		// thrust (MRL_P_L1B); role 3 adds the tilt factor cos(tilt) to b, the motor lag and the delay
		const float ct = 1.f - 2.f * (base.q_d[1] * base.q_d[1] + base.q_d[2] * base.q_d[2]);
		const bool phys = _param_pl1r.get() & 4;
		const L1Cfg lc = L1Cfg{_param_pl1b.get() * (phys ? math::max(ct, 0.5f) : 1.f), _param_pl1a.get(), _param_pl1w.get(), _param_pl1t.get(), math::max(_param_kdly.get(), 0.f) * 1e-3f, _param_umax.get(), _param_pl1r.get(), _param_s_fc.get(), _param_s_k.get(), _param_s_tav.get(), _param_l1_ef.get(), _param_l1_kf.get(), _param_l1_lk.get(), _param_l1_mv.get()};
		_l1z.s[0] = _z.s[0];
		_l1z.s[1] = _z.s[1];
		u = PX4_ISFINITE(lpos.vz) ? _l1z.step(lpos.vz, base.thrust_body[2], 9.80665f, dt, _landed, mode == 1, lc) : 0.f;

	} else {
		u = _z.step(lpos.vz, _vz_sp, dt, _landed, mode == 1, mode == 1, g);
	}
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
		if (_param_xlaw.get() == 1) {
			// L1: x = velocity (NED), command = acceleration setpoint [m/s^2], nominal v_dot = u (b = 1); role 3 adds
			// linear drag -MRL_X_L1D v, the attitude-loop lag MRL_X_L1T and the delay
			const L1Cfg lc = L1Cfg{_param_xl1b.get(), _param_xl1a.get(), _param_xl1w.get(), _param_xl1t.get(), math::max(_param_kdly.get(), 0.f) * 1e-3f, _param_xy_umax.get(), _param_xl1r.get(), _param_s_fc.get(), _param_s_k.get(), _param_s_tav.get(), _param_l1_ef.get(), _param_l1_kf.get(), _param_l1_lk.get(), _param_l1_mv.get()};
			_l1xy[i].s[0] = _xy[i].s[0];
			_l1xy[i].s[1] = _xy[i].s[1];
			_l1xy[i].fk = PX4_ISFINITE(vi) ? -_param_xl1d.get() * vi : 0.f;
			uxy[i] = PX4_ISFINITE(vi) ? _l1xy[i].step(vi, _acc_sp[i], 0.f, dt, _landed, xy_mode == 1, lc, _xy_clip_pos[i],
					 _xy_clip_neg[i]) : 0.f;

		} else {
			uxy[i] = PX4_ISFINITE(acc[i]) ? _xy[i].step(acc[i], _acc_sp[i], dt, _landed, xy_mode == 1, xy_mode == 1, gx) : 0.f;
		}
	}

	// tilt budget (feasibility, MRL_X_TILT deg, 0 = off): the adaptive acceleration may not raise the horizontal
	// acceleration past g tan(budget), nor past what the baseline already commands; the clip is fed back to L1 as
	// saturation so its filter does not wind up
	_xy_clip_pos[0] = _xy_clip_pos[1] = _xy_clip_neg[0] = _xy_clip_neg[1] = false;

	if (_param_xlaw.get() == 1 && _param_xtilt.get() > 0.f) {
		const float amax = 9.80665f * tanf(math::radians(math::constrain(_param_xtilt.get(), 1.f, 80.f)));
		const float ab2 = _acc_sp[0] * _acc_sp[0] + _acc_sp[1] * _acc_sp[1];
		const float at0 = _acc_sp[0] + uxy[0], at1 = _acc_sp[1] + uxy[1];
		const float R = math::max(amax, sqrtf(ab2));
		const float uu = uxy[0] * uxy[0] + uxy[1] * uxy[1];

		if (uu > 1e-9f && at0 * at0 + at1 * at1 > R * R) {
			const float bu = _acc_sp[0] * uxy[0] + _acc_sp[1] * uxy[1];
			const float k = math::constrain((-bu + sqrtf(math::max(bu * bu - uu * (ab2 - R * R), 0.f))) / uu, 0.f, 1.f);

			for (int i = 0; i < 2; i++) {
				_xy_clip_pos[i] = uxy[i] > 0.f;
				_xy_clip_neg[i] = uxy[i] < 0.f;
				uxy[i] *= k;
				_l1xy[i].uprev = uxy[i];   // the predictor must see what was applied
			}
		}
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
	st.xm[2] = l1z ? _l1z.xh : _z.xm;
	st.e[2] = l1z ? _l1z.xt : _z.e;
	st.u_ad[2] = u;
	st.sched_cut[2] = l1z ? 1.f - _l1z.sc : 0.f;

	for (int i = 0; i < MracAxis::NPHI; i++) { st.theta[2 * MracAxis::NPHI + i] = l1z ? _l1z.theta[i] : _z.theta[i]; }

	st.theta_norm[2] = l1z ? _l1z.tnorm() : _z.tnorm();
	st.n_phi = _z.nphi;

	st.mode = (uint8_t)mode;
	st.adapting = (mode == 1) && !_landed;
	_status_pub.publish(st);

	mrac_rate_status_s sx{};
	sx.timestamp = out.timestamp;

	for (int i = 0; i < 2; i++) {
		const bool l1 = _param_xlaw.get() == 1;
		sx.xm[i] = l1 ? _l1xy[i].xh : _xy[i].xm;
		sx.e[i] = l1 ? _l1xy[i].xt : _xy[i].e;
		sx.u_ad[i] = uxy[i];
		sx.sched_cut[i] = l1 ? 1.f - _l1xy[i].sc : 0.f;

		for (int j = 0; j < MracAxis::NPHI; j++) { sx.theta[i * MracAxis::NPHI + j] = l1 ? _l1xy[i].theta[j] : _xy[i].theta[j]; }

		sx.theta_norm[i] = l1 ? _l1xy[i].tnorm() : _xy[i].tnorm();
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
