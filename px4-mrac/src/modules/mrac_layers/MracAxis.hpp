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

	void reset() { xm = 0.f; e = 0.f; for (float &t : theta) { t = 0.f; } }

	// landed: hold xm on the plant and freeze Theta. adapt: update Theta. Returns u_ad (0 when !on).
	float step(float x, float r, float dt, bool landed, bool on, bool adapt, const MracGains &g)
	{
		if (landed) { xm = x; }

		xm += dt * (r - xm) / math::max(g.tau, 0.005f);
		e = x - xm;

		if (!on) { return 0.f; }

		const float phi[NPHI] {x, r, 1.f};

		if (adapt && !landed) {
			float denom = 1.f;

			for (int i = 0; i < NPHI; i++) { denom += phi[i] * phi[i]; }

			for (int i = 0; i < NPHI; i++) {
				theta[i] = math::constrain(theta[i] + dt * g.gam * (-e * phi[i] / denom - g.sig * theta[i]), -g.lim, g.lim);
			}
		}

		float u = 0.f;

		for (int i = 0; i < NPHI; i++) { u += theta[i] * phi[i]; }

		return math::constrain(u, -g.umax, g.umax);
	}
};
