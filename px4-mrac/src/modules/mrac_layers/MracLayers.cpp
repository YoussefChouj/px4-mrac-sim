#include "MracLayers.hpp"

MracLayers::MracLayers() :
	ModuleParams(nullptr),
	WorkItem(MODULE_NAME, px4::wq_configurations::rate_ctrl)
{
}

bool MracLayers::init()
{
	if (!_torque_base_sub.registerCallback()) {
		PX4_ERR("callback registration failed");
		return false;
	}

	if (!_att_layer.init() || !_pos_layer.init() || !_xy_layer.init()) {
		PX4_ERR("outer layer callback registration failed");
		return false;
	}

	return true;
}

void MracLayers::Run()
{
	if (should_exit()) {
		_torque_base_sub.unregisterCallback();
		_att_layer.stop();
		_pos_layer.stop();
		_xy_layer.stop();
		exit_and_cleanup();
		return;
	}

	if (_parameter_update_sub.updated()) {
		parameter_update_s pupdate;
		_parameter_update_sub.copy(&pupdate);
		updateParams();
	}

	vehicle_land_detected_s land{};

	// same freeze as mc_rate_control's integrator: maybe_landed comes seconds before landed at touchdown
	if (_land_detected_sub.update(&land)) { _landed = land.landed || land.maybe_landed; }

	control_allocator_status_s cas{};

	if (_alloc_status_sub.update(&cas)) {   // same rule as mc_rate_control setSaturationStatus
		for (int i = 0; i < 3; i++) {
			_sat_pos[i] = !cas.torque_setpoint_achieved && cas.unallocated_torque[i] > FLT_EPSILON;
			_sat_neg[i] = !cas.torque_setpoint_achieved && cas.unallocated_torque[i] < -FLT_EPSILON;
		}
	}

	vehicle_rates_setpoint_s rsp{};

	if (_rates_sp_sub.update(&rsp)) {
		_rate_sp[0] = rsp.roll;
		_rate_sp[1] = rsp.pitch;
		_rate_sp[2] = rsp.yaw;
	}

	vehicle_torque_setpoint_s base{};

	if (!_torque_base_sub.update(&base)) { return; }

	vehicle_angular_velocity_s av{};
	_angular_velocity_sub.copy(&av);

	const hrt_abstime now = base.timestamp_sample;
	const float dt = (_last_t > 0) ? math::constrain((now - _last_t) * 1e-6f, 1e-4f, 0.02f) : 0.004f;
	_last_t = now;

	const int mode = _param_en_rate.get();                 // 1 route + adapt, 2 route only (u_ad = 0)
	const bool adapt = (mode == 1) && !_landed;
	const MracGains g{_param_tau.get(), _param_gamma.get(), _param_sigma.get(), _param_lim.get(), _param_umax.get()};
	float dist[3] {_param_dist_r.get(), _param_dist_p.get(), 0.f};

	if (_param_id_amp.get() > 0.f && !_landed) {           // sysid multisine, rebuilt offline from timestamp_sample
		const double ts = now * 1e-6;
		float d = 0.f;

		for (int k = 0; k < 12; k++) {
			const double f = 0.5 * pow(40.0, k / 11.0), ph = M_PI * k * (k + 1) / 12.0;
			d += (float)sin(2.0 * M_PI * f * ts + ph);
		}

		dist[math::constrain((int)_param_id_ax.get(), 0, 2)] += _param_id_amp.get() * d / 4.f;
	}

	vehicle_torque_setpoint_s out = base;
	mrac_rate_status_s st{};

	for (int a = 0; a < 3; a++) {
		const bool on = (mode == 1) && ((a < 2) || (_param_yaw.get() == 1));
		// block 1 structured terms of the rate loop: gyroscopic product w_j*w_k and the cross-axis rate
		// v2 blocks (MRL_R_V2 bits): 1 block 1 known-delay command lag, 2/4 block 2 scheduler on gain/output,
		// 8 block 3 delayed reference; MRL_R_KDLY is the known delay both use
		const int v2 = _param_v2.get();
		_ax[a].cfg(_param_feat.get() | ((v2 & 1) ? MRF_ULAG : 0), _param_xs.get(), _param_ge0.get(), _param_gw.get(),
			   _param_gk.get());
		_ax[a].kdly = math::max(_param_kdly.get(), 0.f) * 1e-3f;
		_ax[a].ref_dly = (v2 & 8) != 0;
		_ax[a].sch = MracSched{(v2 >> 1) & 3, _param_s_fc.get(), _param_s_k.get(), _param_s_tav.get(),
				       math::max(_param_s_ef.get(), 0.f)};
		_ax[a].ub = base.xyz[a];
		_ax[a].s[0] = av.xyz[(a + 1) % 3] * av.xyz[(a + 2) % 3];
		_ax[a].s[1] = av.xyz[a == 0 ? 1 : 0];
		float u_ad = 0.f;

		if (_param_law.get() == 1) {
			// L1 (L1Axis.hpp): x = body rate, command = normalized torque; nominal w_dot = b u (b measured in SIH,
			// 2026-11-05: 160-180 rad/s^2 per unit with the 50 ms motor lag); role 3 knows that lag and the delay
			const L1Cfg lc{_param_l1b.get(), _param_l1a.get(), _param_l1w.get(), _param_l1t.get(),
				       math::max(_param_kdly.get(), 0.f) * 1e-3f, _param_umax.get(), _param_l1r.get(),
				       _param_s_fc.get(), _param_s_k.get(), _param_s_tav.get(), _param_l1_ef.get(),
				       _param_l1_kf.get(), _param_l1_lk.get(), _param_l1_mv.get()};
			_l1[a].s[0] = _ax[a].s[0];
			_l1[a].s[1] = _ax[a].s[1];
			u_ad = _l1[a].step(av.xyz[a], base.xyz[a], 0.f, dt, _landed, on, lc, _sat_pos[a], _sat_neg[a]);
			_ax[a].xm = _l1[a].xh;
			_ax[a].e = _l1[a].xt;
			_ax[a].sc = _l1[a].sc;

		} else {
			u_ad = _ax[a].step(av.xyz[a], _rate_sp[a], dt, _landed, on, on, g, _sat_pos[a], _sat_neg[a]);
		}

		out.xyz[a] = math::constrain(base.xyz[a] + u_ad + (_landed ? 0.f : dist[a]), -1.f, 1.f);

		st.xm[a] = _ax[a].xm;
		st.e[a] = _ax[a].e;
		st.u_ad[a] = u_ad;

		const bool l1 = _param_law.get() == 1;

		for (int i = 0; i < MracAxis::NPHI; i++) { st.theta[a * MracAxis::NPHI + i] = l1 ? _l1[a].theta[i] : _ax[a].theta[i]; }

		st.theta_norm[a] = l1 ? _l1[a].tnorm() : _ax[a].tnorm();
		st.sched_cut[a] = 1.f - _ax[a].sc;
		st.n_phi = _ax[a].nphi;
	}

	out.timestamp = hrt_absolute_time();
	_torque_pub.publish(out);

	if (++_status_div >= 4) {                               // ~1/4 of the rate loop
		_status_div = 0;
		st.timestamp = out.timestamp;
		st.mode = (uint8_t)mode;
		st.adapting = adapt;
		_status_pub.publish(st);
	}
}

int MracLayers::task_spawn(int argc, char *argv[])
{
	MracLayers *instance = new MracLayers();

	if (instance) {
		_object.store(instance);
		_task_id = task_id_is_work_queue;

		if (instance->init()) { return PX4_OK; }

	} else {
		PX4_ERR("alloc failed");
	}

	delete instance;
	_object.store(nullptr);
	_task_id = -1;
	return PX4_ERROR;
}

int MracLayers::print_status()
{
	PX4_INFO("mode %d landed %d", (int)_param_en_rate.get(), (int)_landed);

	for (int a = 0; a < 3; a++) {
		PX4_INFO("rate axis %d theta %.4f %.4f %.4f", a, (double)_ax[a].theta[0], (double)_ax[a].theta[1],
			 (double)_ax[a].theta[2]);
	}

	_att_layer.print();
	_pos_layer.print();
	_xy_layer.print();
	return 0;
}

int MracLayers::custom_command(int argc, char *argv[])
{
	return print_usage("unknown command");
}

int MracLayers::print_usage(const char *reason)
{
	if (reason) { PX4_WARN("%s\n", reason); }

	PRINT_MODULE_DESCRIPTION("MRAC augmentation layers at the uORB handoffs (rate layer).");
	PRINT_MODULE_USAGE_NAME("mrac_layers", "controller");
	PRINT_MODULE_USAGE_COMMAND("start");
	PRINT_MODULE_USAGE_DEFAULT_COMMANDS();
	return 0;
}

extern "C" __EXPORT int mrac_layers_main(int argc, char *argv[])
{
	return MracLayers::main(argc, argv);
}
