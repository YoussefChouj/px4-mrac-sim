#include "XyCtrl.hpp"

#include <drivers/drv_hrt.h>
#include <lib/mathlib/mathlib.h>
#include <px4_platform_common/log.h>

XyCtrlLayer::XyCtrlLayer() :
	ModuleParams(nullptr),
	WorkItem("xy_ctrl_layer", px4::wq_configurations::nav_and_controllers)
{
}

void XyCtrlLayer::reset()
{
	for (auto &s : _ax) { s = XyAxis{}; }

	_u[0] = _u[1] = 0.f;
}

// Plant input that reaches the vehicle now: the command from XYC_DELAY steps ago.
static float arriving(const XyAxis &s, float u_now)
{
	return XYC_DELAY > 0 ? s.pipe[s.head] : u_now;
}

void XyCtrlLayer::commit(XyAxis &s, float u)
{
	s.a_est = XYC_AL * s.a_est + XYC_B * arriving(s, u);

	if (XYC_DELAY > 0) {
		s.pipe[s.head] = u;
		s.head = (s.head + 1) % XYC_DQ;
	}

	s.u_prev = u;
}

float XyCtrlLayer::step(XyAxis &s, int kind, float des, float pos, float vel, float vff, float aff)
{
	const float dt = XYC_DT;
	const float amax = _param_amax.get();

	if (kind == 2) {
		// ADRC: 3rd-order linear ESO on position, b0 = 1 (u is an acceleration command)
		const float wc = _param_wc.get(), wo = 4.f * wc;

		if (!s.eso_init) { s.z1 = pos; s.z2 = vel; s.z3 = 0.f; s.eso_init = true; }

		const float e = s.z1 - pos;
		const float b = arriving(s, s.u_prev);
		s.z1 += dt * (s.z2 - 3.f * wo * e);
		s.z2 += dt * (s.z3 - 3.f * wo * wo * e + b);
		s.z3 += dt * (-wo * wo * wo * e);
		return math::constrain(wc * wc * (des - s.z1) + 2.f * wc * (vff - s.z2) + aff - s.z3, -amax, amax);
	}

	// LQR / MPC share the state x = [p - des, v - vff, a - aff, z], predicted over the delay.
	const float e_now = pos - des;

	if (fabsf(e_now) < _param_int_band.get()) {
		s.z = math::constrain(s.z + dt * e_now, -_param_int_max.get(), _param_int_max.get());
	}

	float p = pos, v = vel, a = s.a_est;

	for (int k = 0; k < XYC_DELAY; k++) {
		const float a_next = XYC_AL * a + XYC_B * s.pipe[(s.head + k) % XYC_DQ];
		p += dt * v;
		v += dt * (a - XYC_DRAG * v);
		a = a_next;
	}

	const float x[4] {p - (des + vff * dt * XYC_DELAY), v - vff, a - aff, s.z};

	if (kind == 1) {
		float u = aff;

		const float *k = XYC_LQR_SETS[math::constrain(_param_lqr_set.get(), (int32_t)0, (int32_t)4)];

		for (int i = 0; i < 4; i++) { u -= k[i] * x[i]; }

		return math::constrain(u, -amax, amax);
	}

	// MPC: condensed QP 0.5 U'HU + U'Fx with box bounds, solved by FISTA, warm-started from the shifted plan.
	float lin[XYC_MPC_N], U[XYC_MPC_N], y[XYC_MPC_N];
	const float lo = -amax - aff, hi = amax - aff;

	for (int i = 0; i < XYC_MPC_N; i++) {
		lin[i] = 0.f;

		for (int j = 0; j < 4; j++) { lin[i] += XYC_MPC_F[i][j] * x[j]; }

		U[i] = y[i] = (i + 1 < XYC_MPC_N) ? s.plan[i + 1] : s.plan[XYC_MPC_N - 1];
	}

	float t = 1.f;

	for (int it = 0; it < 30; it++) {
		float Un[XYC_MPC_N];

		for (int i = 0; i < XYC_MPC_N; i++) {
			float g = lin[i];

			for (int j = 0; j < XYC_MPC_N; j++) { g += XYC_MPC_H[i][j] * y[j]; }

			Un[i] = math::constrain(y[i] - XYC_MPC_STEP * g, lo, hi);
		}

		const float tn = 0.5f * (1.f + sqrtf(1.f + 4.f * t * t));

		for (int i = 0; i < XYC_MPC_N; i++) {
			y[i] = Un[i] + (t - 1.f) / tn * (Un[i] - U[i]);
			U[i] = Un[i];
		}

		t = tn;
	}

	for (int i = 0; i < XYC_MPC_N; i++) { s.plan[i] = U[i]; }

	return U[0] + aff;
}

void XyCtrlLayer::Run()
{
	if (_parameter_update_sub.updated()) {
		parameter_update_s pupdate;
		_parameter_update_sub.copy(&pupdate);
		updateParams();
	}

	vehicle_land_detected_s land{};

	if (_land_detected_sub.update(&land)) { _landed = land.landed; }

	const bool sp_new = _traj_sub.update(&_sp);

	vehicle_local_position_s lpos{};

	if (!_lpos_sub.update(&lpos)) { return; }

	const int mode = _param_mode.get();

	if (mode < 1 || mode > 3) { _active = false; return; }

	const bool xy_ok = PX4_ISFINITE(_sp.position[0]) && PX4_ISFINITE(_sp.position[1])
			   && lpos.xy_valid && lpos.v_xy_valid && !_landed;

	if (!xy_ok) {
		// pass through unchanged so mc_pos_control still gets every setpoint
		if (_active) { reset(); _active = false; }

		if (sp_new) { _xyc_pub.publish(_sp); }

		return;
	}

	const hrt_abstime now = hrt_absolute_time();

	if (_active && now - _last_step < (hrt_abstime)(XYC_DT * 0.75e6f)) { return; }

	if (!_active) { reset(); _active = true; }

	_last_step = now;
	const float pos[2] {lpos.x, lpos.y}, vel[2] {lpos.vx, lpos.vy};

	for (int i = 0; i < 2; i++) {
		const float vff = PX4_ISFINITE(_sp.velocity[i]) ? _sp.velocity[i] : 0.f;
		const float aff = PX4_ISFINITE(_sp.acceleration[i]) ? _sp.acceleration[i] : 0.f;
		_u[i] = step(_ax[i], mode, _sp.position[i], pos[i], vel[i], vff, aff);
		commit(_ax[i], _u[i]);
	}

	trajectory_setpoint_s out = _sp;
	out.timestamp = now;

	for (int i = 0; i < 2; i++) {
		out.position[i] = NAN;
		out.velocity[i] = NAN;
		out.acceleration[i] = _u[i];
	}

	_xyc_pub.publish(out);
}

void XyCtrlLayer::print()
{
	PX4_INFO("xy_ctrl: mode %d active %d u [%.3f %.3f] z [%.3f %.3f] (al %.4f delay %d)",
		 (int)_param_mode.get(), _active, (double)_u[0], (double)_u[1], (double)_ax[0].z, (double)_ax[1].z,
		 (double)XYC_AL, XYC_DELAY);
}
