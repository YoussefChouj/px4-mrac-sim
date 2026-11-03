/**
 * One MRAC axis, shared by the rate, attitude and position layers (same law as API/mrac.c:1356-1406):
 * first-order reference model xm on the setpoint r, e = x - xm, Phi = [x, r, 1], u_ad = Theta'Phi,
 * Theta += dt*gam*(-e*Phi/(1+Phi'Phi) - sig*Theta), box projection |Theta_i| <= lim, |u_ad| <= umax.
 * Sign convention: a positive u_ad must push x up (d x / d u > 0); each layer maps its output to keep that.
 */
#pragma once

#include <lib/mathlib/mathlib.h>

struct MracGains {
	float tau, gam, sig, lim, umax;
};

struct MracAxis {
	static constexpr int NPHI = 3;
	float xm{0.f};
	float theta[NPHI] {};
	float e{0.f};
	float u_raw{0.f};     // last unclamped u_ad
	// false drops the constant regressor: on a layer whose baseline already integrates the constant (PX4 vz
	// integrator + hover thrust estimate) the two biases share one null direction and only sigma splits them
	bool bias{true};

	void reset() { xm = 0.f; e = 0.f; u_raw = 0.f; for (float &t : theta) { t = 0.f; } }

	// landed: hold xm on the plant and freeze Theta. adapt: update Theta. Returns u_ad (0 when !on).
	// sat_pos/sat_neg: the mixer cannot deliver more in that direction (control_allocator_status, as
	// mc_rate_control's integrator). Like there, Theta is not pushed further into a saturated direction;
	// the own u_ad clamp counts as saturation too. Leakage still runs.
	float step(float x, float r, float dt, bool landed, bool on, bool adapt, const MracGains &g,
		   bool sat_pos = false, bool sat_neg = false)
	{
		if (landed) { xm = x; }

		xm += dt * (r - xm) / math::max(g.tau, 0.005f);
		e = x - xm;

		if (!on) { return 0.f; }

		const float phi[NPHI] {x, r, bias ? 1.f : 0.f};

		if (adapt && !landed) {
			float denom = 1.f;

			for (int i = 0; i < NPHI; i++) { denom += phi[i] * phi[i]; }

			// the gradient step moves u along -e
			const bool blocked = (-e > 0.f && (sat_pos || u_raw >= g.umax)) || (-e < 0.f && (sat_neg || u_raw <= -g.umax));
			const float grad = blocked ? 0.f : 1.f;

			for (int i = 0; i < NPHI; i++) {
				theta[i] = math::constrain(theta[i] + dt * g.gam * (-grad * e * phi[i] / denom - g.sig * theta[i]), -g.lim, g.lim);
			}
		}

		float u = 0.f;

		for (int i = 0; i < NPHI; i++) { u += theta[i] * phi[i]; }

		u_raw = u;
		return math::constrain(u, -g.umax, g.umax);
	}
};
