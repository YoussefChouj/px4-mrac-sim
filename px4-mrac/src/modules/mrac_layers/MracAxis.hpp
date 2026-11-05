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
 *
 * v2 blocks (research/notes/three-block-v2.md), each off by default so the default stays the original law:
 *   block 1, MRF_ULAG: known-delay command lag ub(t) - ub(t - d), the part of the baseline command the plant has
 *            not received yet under a known transport delay d (a physics term of the delayed plant);
 *   block 2, scheduler (MracSched): s = 1 / (1 + k rho^2), rho = P_hf / (P_e + ef^2): the high-band power of e
 *            (first-order high-pass at fc, powers averaged over tav) over the total plus a noise floor ef^2, so
 *            small noise-like error (rms << ef) leaves s ~ 1 and only a large high-band error cuts (amplitude gate;
 *            ef = 0 is the pure share of wave K). s scales the adaptation gain (bit 1) and/or u_ad (bit 2).
 *            s is a known function of measured e in [1/(1+k), 1]; projection and the umax clamp keep Theta and u_ad
 *            bounded whatever s does, so the scheduler can only lower the adaptive authority;
 *   block 3, known-physics reference: xm follows r delayed by the known delay d, so e no longer asks the
 *            adaptation to undo a delay no controller can remove (reference model realizable by the delayed plant).
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
	MRF_GATE = 512,                                 // block 2: gated fast copy of every active term
	MRF_ULAG = 1024                                 // v2 block 1: known-delay command lag ub(t) - ub(t - d)
};

// v2 block 2 scheduler: mode bits 1 = scale the adaptation gain, 2 = scale u_ad; 0 = off (s = 1)
struct MracSched {
	int mode{0};
	float fc{1.5f}, k{20.f}, tav{0.5f}, ef{0.f};
};

struct MracAxis {
	static constexpr int NPHI = 3;                  // status layout: x, r, bias
	static constexpr int NRBF = 5;
	static constexpr int NB = 9 + NRBF;             // ungated basis size
	static constexpr int NBUF = 64;                 // known-delay history (64 x 4 ms rate loop = 256 ms)
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
	// v2: known delay d [s] for block 1 (ULAG) and block 3 (delayed reference); scheduler state
	float kdly{0.f};
	bool ref_dly{false};
	MracSched sch{};
	float rbuf[NBUF] {}, ubuf[NBUF] {};
	int bi{0};
	float ulag{0.f}, ehp{0.f}, eprev{0.f}, phf{0.f}, ptot{0.f}, sc{1.f};
	int nphi{NPHI};
	// false drops the constant regressor: on a layer whose baseline already integrates the constant (PX4 vz
	// integrator + hover thrust estimate) the two biases share one null direction and only sigma splits them
	bool bias{true};

	void reset()
	{
		xm = 0.f; e = 0.f; u_raw = 0.f; g = 0.f; rdot = 0.f; rinit = false; ulag = 0.f;
		ehp = 0.f; eprev = 0.f; phf = 0.f; ptot = 0.f; sc = 1.f;

		for (float &t : theta) { t = 0.f; }
	}

	// newest - oldest-by-d sample of a history ring (bi = next write slot)
	float hist(const float *b, int n) const { return b[(bi - 1 - n + 2 * NBUF) % NBUF]; }

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
		phi[8] = (feat & MRF_ULAG) ? ulag : 0.f;

		for (int k = 0; k < NRBF; k++) {
			const float d = (x / xs - (-1.f + 0.5f * k)) / 0.35f;
			phi[9 + k] = (feat & MRF_RBF) ? expf(-0.5f * d * d) : 0.f;
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
		// known-delay history: d in samples of this loop, at most NBUF - 1
		rbuf[bi] = r; ubuf[bi] = ub; bi = (bi + 1) % NBUF;
		const int nd = math::constrain((int)lroundf(kdly / math::max(dt, 1e-4f)), 0, NBUF - 1);
		ulag = ub - hist(ubuf, nd);
		xm += dt * ((ref_dly ? hist(rbuf, nd) : r) - xm) / math::max(gn.tau, 0.005f);
		e = x - xm;

		// block 2 scheduler: high-band share of the power of e
		if (sch.mode) {
			const float tc = 1.f / (6.2831853f * math::max(sch.fc, 0.01f));
			ehp = tc / (tc + dt) * (ehp + e - eprev);
			const float b = math::min(dt / math::max(sch.tav, 0.01f), 1.f);
			phf += (ehp * ehp - phf) * b;
			ptot += (e * e - ptot) * b;
			const float rho = math::constrain(phf / (ptot + sch.ef * sch.ef + 1e-6f), 0.f, 1.f);
			sc = 1.f / (1.f + math::max(sch.k, 0.f) * rho * rho);

		} else {
			sc = 1.f;
		}

		eprev = e;

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
				const float gam = gn.gam * (i >= NB ? gk : 1.f) * ((sch.mode & 1) ? sc : 1.f);
				theta[i] = math::constrain(theta[i] + dt * gam * (-grad * e * phi[i] / denom - gn.sig * theta[i]), -gn.lim, gn.lim);
			}
		}

		float u = 0.f;

		for (int i = 0; i < n; i++) { u += theta[i] * phi[i]; }

		if (sch.mode & 2) { u *= sc; }

		u_raw = u;
		return math::constrain(u, -gn.umax, gn.umax);
	}
};
