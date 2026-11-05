/**
 * Higher-fidelity quadrotor physics for PX4 SIH (research patch, patch_sih_fidelity.py). Pure float math, no PX4
 * dependency, so it is compiled and checked on its own (ci/test_sih_fidelity.cpp). Every term has its own SIH_* param
 * and is off at its default, so a stock deck flies the stock SIH model.
 *
 * Models (per rotor i, thrust T_i, rotor speed fraction n_i = omega_i / omega_max):
 *  - thrust curve       T_i = T_max (f u_i^2 + (1 - f) u_i)                       SIH_THR_FAC f (PX4 THR_MDL_FAC form)
 *  - motor/ESC          first-order, slower when spinning down                     SIH_T_TAU_DN
 *  - motor spread       per-motor efficiency                                       SIH_MOT2..4_EFF (motor 1: SIH_MOT1_EFF)
 *  - air density        ISA pressure at the flight altitude, given air temperature SIH_RHO_EN, SIH_AIR_T
 *                       thrust and rotor torque scale with rho / rho0 at fixed throttle
 *  - axial inflow       climbing through the rotor lowers thrust (momentum theory,
 *                       linearised): x (1 - k_ax V_climb / v_h)                     SIH_RA_KAX
 *  - translational lift edgewise flow raises thrust: x (1 + k_tl min((V_ip/v_h)^2, 1)) SIH_RA_KTL
 *  - ground effect      Cheeseman-Bennett T / (1 - (R / 4z)^2), z = rotor height   SIH_PROP_R
 *  - rotor drag         blade flapping / induced drag, linear in rotor speed and
 *                       in-plane airspeed: F_B,xy = -k_rd sum(n_i) v_air,B,xy       SIH_RD_K (Faessler et al. 2018)
 *  - body drag          quadratic -1/2 rho CdA |v_air| v_air (on top of SIH_KDV)  SIH_CDA
 *  - battery            Thevenin pack: OCV(SoC) of a LiPo cell x N - I R0; current from ideal induced power over
 *                       an efficiency; available thrust scales with (V / V_ref)^2  SIH_BAT_CAP/N/R0/SOC0/ETA
 *  - centre of mass     offset from the rotor centre: thrust gives a torque        SIH_COM_X/Y
 *  - vibration          per-rotor imbalance at the rotor frequency (+ 2nd harmonic) into the IMU, amplitude
 *                       growing with n_i^2; sampled by the sim, so it aliases as on a real board  SIH_VIB_ACC/GYR/H2, SIH_W_MAX
 *  - sensor bias        constant gyro and accelerometer bias                       SIH_GYR_BX.., SIH_ACC_BX..
 */
#pragma once

#include <math.h>

namespace sih_fid
{

struct Params {
	float thr_fac{0.f}, tau_dn{0.f}, eff[4] {1.f, 1.f, 1.f, 1.f};
	int rho_en{0};
	float air_t{15.f}, kax{0.f}, ktl{0.f}, prop_r{0.f}, krd{0.f}, cda{0.f};
	float bat_cap{0.f}, bat_n{4.f}, bat_r0{0.05f}, bat_soc0{1.f}, bat_eta{0.5f};
	float com_x{0.f}, com_y{0.f};
	float vib_acc{0.f}, vib_gyr{0.f}, vib_h2{0.f}, w_max{969.f};
	float acc_b[3] {}, gyr_b[3] {};
};

struct State {
	float soc{-1.f};          // < 0: not started (set from SIH_BAT_SOC0 on first use)
	float v_bat{0.f}, i_bat{0.f};
	float n[4] {};            // rotor speed fractions, for vibration
	float phase[4] {};
};

static constexpr float RHO0 = 1.225f;
static constexpr float G = 9.80665f;
static constexpr float PI_F = 3.14159265f;

inline float clampf(float x, float lo, float hi) { return x < lo ? lo : (x > hi ? hi : x); }

// ISA pressure at altitude h [m MSL], density with the given air temperature [deg C]
inline float density(float h_msl, float t_c)
{
	const float p = 101325.f * powf(clampf(1.f - 2.25577e-5f * h_msl, 0.2f, 1.2f), 5.25588f);
	return p / (287.05f * clampf(t_c + 273.15f, 200.f, 340.f));
}

// open-circuit voltage of one LiPo cell vs state of charge (typical discharge curve)
inline float ocv_cell(float soc)
{
	static const float v[11] {3.27f, 3.69f, 3.73f, 3.77f, 3.79f, 3.82f, 3.87f, 3.92f, 3.97f, 4.06f, 4.20f};
	const float x = clampf(soc, 0.f, 1.f) * 10.f;
	const int k = (int)x < 10 ? (int)x : 9;
	return v[k] + (v[k + 1] - v[k]) * (x - (float)k);
}

inline float thrust_curve(float u, float f) { return f * u * u + (1.f - f) * u; }

struct Out {
	float T[4];               // rotor thrusts [N]
	float F_B[3];             // extra body-frame force (rotor drag) [N]
	float F_q[3];             // extra earth-frame force (quadratic body drag) [N]
	float M_B[3];             // body torque from thrust (rotor torques and CoM offset) [N m]
};

/**
 * One physics step. u: motor states [0,1]; t_max/q_max/l_roll/l_pitch: SIH geometry; mass [kg];
 * v_air_B: airspeed in body frame (FRD) [m/s]; v_air_E: airspeed in the earth frame [m/s]; h_msl: altitude [m];
 * h_agl: height of the body above the ground [m]; armed: thrust is commanded.
 */
inline Out step(const Params &p, State &s, const float u[4], float t_max, float q_max, float l_roll, float l_pitch,
		float mass, const float v_air_B[3], const float v_air_E[3], float h_msl, float h_agl, float dt)
{
	Out o{};
	const float rho = p.rho_en ? density(h_msl, p.air_t) : RHO0;
	const float sig = rho / RHO0;
	const float r = p.prop_r > 0.f ? p.prop_r : 0.0635f;
	const float area = PI_F * r * r;
	const float v_h = sqrtf(mass * G / 4.f / (2.f * rho * area));      // hover induced velocity

	// battery: voltage this step from last step's power
	float kb = 1.f;

	if (p.bat_cap > 0.f) {
		if (s.soc < 0.f) { s.soc = clampf(p.bat_soc0, 0.f, 1.f); }

		const float n = p.bat_n > 0.5f ? p.bat_n : 1.f;
		const float ocv = ocv_cell(s.soc) * n;
		float P = 0.f;

		for (int i = 0; i < 4; i++) {
			const float Ti = t_max * thrust_curve(clampf(u[i], 0.f, 1.f), p.thr_fac);
			P += Ti * sqrtf(Ti / (2.f * rho * area));                 // ideal induced power
		}

		P /= clampf(p.bat_eta, 0.05f, 1.f);
		const float disc = ocv * ocv - 4.f * P * p.bat_r0;
		s.v_bat = disc > 0.f ? 0.5f * (ocv + sqrtf(disc)) : 0.5f * ocv;
		s.i_bat = s.v_bat > 0.1f ? P / s.v_bat : 0.f;
		s.soc = clampf(s.soc - s.i_bat * dt / (p.bat_cap * 3.6f), 0.f, 1.f);
		const float vr = s.v_bat / (4.0f * n);                          // T_max refers to 4.0 V per cell [S]
		kb = clampf(vr * vr, 0.f, 1.15f);
	}

	// flow through the rotors
	const float v_climb = -v_air_B[2];                                  // body up
	const float v_ip2 = v_air_B[0] * v_air_B[0] + v_air_B[1] * v_air_B[1];
	float fl = 1.f - p.kax * v_climb / v_h;
	fl *= 1.f + p.ktl * fminf(v_ip2 / (v_h * v_h), 1.f);
	fl = clampf(fl, 0.5f, 1.5f);

	float ge = 1.f;

	if (p.prop_r > 0.f) {
		const float z = fmaxf(h_agl, 0.f) + 0.05f;                     // rotor plane 5 cm above the skids [S]
		const float q = p.prop_r / (4.f * z);
		ge = q < 0.6f ? 1.f / (1.f - q * q) : 1.f / (1.f - 0.36f);
	}

	float Tsum = 0.f, nsum = 0.f;

	for (int i = 0; i < 4; i++) {
		const float uc = thrust_curve(clampf(u[i], 0.f, 1.f), p.thr_fac);
		o.T[i] = t_max * uc * p.eff[i] * sig * kb * fl * ge;
		Tsum += o.T[i];
		s.n[i] = sqrtf(fmaxf(uc * p.eff[i] * kb, 0.f));               // omega / omega_max
		nsum += s.n[i];
	}

	const float qk = t_max > 1e-6f ? q_max / t_max : 0.f;               // rotor torque per thrust
	o.M_B[0] = l_roll * (-o.T[0] + o.T[1] + o.T[2] - o.T[3]) - p.com_y * Tsum;
	o.M_B[1] = l_pitch * (+o.T[0] - o.T[1] + o.T[2] - o.T[3]) + p.com_x * Tsum;
	o.M_B[2] = qk * (+o.T[0] + o.T[1] - o.T[2] - o.T[3]);

	o.F_B[0] = -p.krd * nsum * v_air_B[0];
	o.F_B[1] = -p.krd * nsum * v_air_B[1];
	o.F_B[2] = 0.f;

	const float va = sqrtf(v_air_E[0] * v_air_E[0] + v_air_E[1] * v_air_E[1] + v_air_E[2] * v_air_E[2]);

	for (int k = 0; k < 3; k++) { o.F_q[k] = -0.5f * rho * p.cda * va * v_air_E[k]; }

	return o;
}

// IMU vibration [body FRD] from the rotor states of the last step; phases advance by omega dt
inline void vibration(const Params &p, State &s, float dt, float acc[3], float gyr[3])
{
	acc[0] = acc[1] = acc[2] = gyr[0] = gyr[1] = gyr[2] = 0.f;

	if (p.vib_acc <= 0.f && p.vib_gyr <= 0.f) { return; }

	static const float ph0[4] {0.f, 1.7f, 3.1f, 4.6f};
	const float nh = 0.6f;                                              // amplitude is given at n = 0.6 (hover) [S]

	for (int i = 0; i < 4; i++) {
		s.phase[i] = fmodf(s.phase[i] + p.w_max * s.n[i] * dt, 2.f * PI_F);
		const float ph = s.phase[i] + ph0[i];
		const float a = (s.n[i] / nh) * (s.n[i] / nh);
		const float c = cosf(ph) + p.vib_h2 * cosf(2.f * ph), sn = sinf(ph) + p.vib_h2 * sinf(2.f * ph);
		acc[0] += p.vib_acc * a * c;
		acc[1] += p.vib_acc * a * sn;
		acc[2] += 0.5f * p.vib_acc * a * sn;
		gyr[0] += p.vib_gyr * a * sn;
		gyr[1] += p.vib_gyr * a * c;
		gyr[2] += 0.3f * p.vib_gyr * a * c;
	}
}

} // namespace sih_fid
