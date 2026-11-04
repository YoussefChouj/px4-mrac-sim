/**
 * One MRAC axis, shared by the rate, attitude, vz and xy layers (base law as API/mrac.c:1356-1406):
 * first-order reference model xm on the setpoint r, e = x - xm, u_ad = Theta'Phi,
 * Theta += dt*gam_i*(-e*Phi/(1+Phi'Phi) - sig*Theta), box projection |Theta_i| <= lim, |u_ad| <= umax.
 * Sign convention: a positive u_ad must push x up (d x / d u > 0); each layer maps its output to keep that.
 *
 * Phi is built from a feature mask (thesis three-block framework, roles fixed, contents configurable):
 *   block 1, physics regressor: structured terms (x|x|, baseline command, two loop-specific terms s0/s1 the layer
 *            sets, e.g. gyroscopic coupling or drag) and/or an unstructured approximator (5 Gaussian bumps on x/xs);
 *   block 2, gate: every active term again, times g = sigmoid((|e|/xs - e0)/w), adapted gk times faster, so a
 *            large tracking error switches on a fast time scale while the ungated copy keeps the slow one; g is a
 *            known function of measured signals, so g*Phi stays one regressor under one Lyapunov function;
 *   block 3, known information: the reference derivative r_dot as an adaptive feedforward term.
 * The default mask (x, r, bias) is the original law; slots 0..2 keep that layout for the status message.
 */
#pragma once

#include <lib/mathlib/mathlib.h>

struct MracGains {
	float tau, gam, sig, lim, umax;
};

enum MracFeat : int {
	MRF_X = 1, MRF_R = 2, MRF_BIAS = 4,             // original law
	MRF_XABS = 8,                                   // block 1 structured: x|x| (quadratic aero / drag)
	MRF_RDOT = 16,                                  // block 3: reference derivative feedforward
	MRF_UBASE = 32,                                 // block 1 structured: baseline command (effectiveness error)
	MRF_S0 = 64, MRF_S1 = 128,                      // block 1 structured, loop specific (set by the layer)
	MRF_RBF = 256,                                  // block 1 unstructured: Gaussian bumps on x/xs
	MRF_GATE = 512                                  // block 2: gated fast copy of every active term
};

struct MracAxis {
	static constexpr int NPHI = 3;                  // status layout: x, r, bias
	static constexpr int NRBF = 5;
	static constexpr int NB = 8 + NRBF;             // ungated basis size
	static constexpr int NMAX = 2 * NB;
	int feat{MRF_X | MRF_R | MRF_BIAS};
	float xs{1.f}, ge0{0.5f}, gw{0.15f}, gk{5.f};
	float ub{0.f};                                  // baseline command, set by the layer each step
	float s[2] {};                                  // loop-specific structured terms, set by the layer each step
	float xm{0.f};
	float theta[NMAX] {};
	float e{0.f};
	float u_raw{0.f};     // last unclamped u_ad
	float g{0.f};         // last gate value
	float rdot{0.f};
	float rp{0.f};
	bool rinit{false};
	int nphi{NPHI};
	// false drops the constant regressor: on a layer whose baseline already integrates the constant (PX4 vz
	// integrator + hover thrust estimate) the two biases share one null direction and only sigma splits them
	bool bias{true};

	void reset() { xm = 0.f; e = 0.f; u_raw = 0.f; g = 0.f; rdot = 0.f; rinit = false; for (float &t : theta) { t = 0.f; } }

	// a feature change moves the meaning of every Theta slot, so it restarts adaptation
	void cfg(int f, float x_scale, float e0, float w, float k)
	{
		if (f != feat) { feat = f; reset(); }

		xs = math::max(x_scale, 1e-3f); ge0 = e0; gw = math::max(w, 1e-3f); gk = math::max(k, 0.f);
	}

	float tnorm() const
	{
		float n = 0.f;

		for (int i = 0; i < NMAX; i++) { n += theta[i] * theta[i]; }

		return sqrtf(n);
	}

	int basis(float x, float r, float *phi) const
	{
		phi[0] = (feat & MRF_X) ? x : 0.f;
		phi[1] = (feat & MRF_R) ? r : 0.f;
		phi[2] = ((feat & MRF_BIAS) && bias) ? 1.f : 0.f;
		phi[3] = (feat & MRF_XABS) ? x * fabsf(x) / xs : 0.f;
		phi[4] = (feat & MRF_RDOT) ? rdot : 0.f;
		phi[5] = (feat & MRF_UBASE) ? ub : 0.f;
		phi[6] = (feat & MRF_S0) ? s[0] : 0.f;
		phi[7] = (feat & MRF_S1) ? s[1] : 0.f;

		for (int k = 0; k < NRBF; k++) {
			const float d = (x / xs - (-1.f + 0.5f * k)) / 0.35f;
			phi[8 + k] = (feat & MRF_RBF) ? expf(-0.5f * d * d) : 0.f;
		}

		return NB;
	}

	// landed: hold xm on the plant and freeze Theta. adapt: update Theta. Returns u_ad (0 when !on).
	// sat_pos/sat_neg: the mixer cannot deliver more in that direction (control_allocator_status, as
	// mc_rate_control's integrator). Like there, Theta is not pushed further into a saturated direction;
	// the own u_ad clamp counts as saturation too. Leakage still runs.
	float step(float x, float r, float dt, bool landed, bool on, bool adapt, const MracGains &gn,
		   bool sat_pos = false, bool sat_neg = false)
	{
		if (landed) { xm = x; }

		if (!rinit) { rp = r; rinit = true; }

		// r_dot from a 50 ms filtered difference: the known reference, not the measured state
		rdot += ((r - rp) / math::max(dt, 1e-4f) - rdot) * math::min(dt / 0.05f, 1.f);
		rp = r;
		xm += dt * (r - xm) / math::max(gn.tau, 0.005f);
		e = x - xm;

		if (!on) { return 0.f; }

		float phi[NMAX];
		int n = basis(x, r, phi);
		g = 0.f;

		if (feat & MRF_GATE) {
			g = 1.f / (1.f + expf(-(fabsf(e) / xs - ge0) / gw));

			for (int i = 0; i < NB; i++) { phi[NB + i] = g * phi[i]; }

			n = NMAX;
		}

		nphi = n;

		if (adapt && !landed) {
			float denom = 1.f;

			for (int i = 0; i < n; i++) { denom += phi[i] * phi[i]; }

			// the gradient step moves u along -e
			const bool blocked = (-e > 0.f && (sat_pos || u_raw >= gn.umax)) || (-e < 0.f && (sat_neg || u_raw <= -gn.umax));
			const float grad = blocked ? 0.f : 1.f;

			for (int i = 0; i < n; i++) {
				const float gam = gn.gam * (i >= NB ? gk : 1.f);
				theta[i] = math::constrain(theta[i] + dt * gam * (-grad * e * phi[i] / denom - gn.sig * theta[i]), -gn.lim, gn.lim);
			}
		}

		float u = 0.f;

		for (int i = 0; i < n; i++) { u += theta[i] * phi[i]; }

		u_raw = u;
		return math::constrain(u, -gn.umax, gn.umax);
	}
};
