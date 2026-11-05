/**
 * One L1 adaptive axis (Hovakimyan & Cao, piecewise-constant adaptation), shared by the rate, attitude, vz and xy
 * layers as the alternative to MracAxis (MRL_*_LAW = 1). Fast, high-gain estimation; low-frequency control.
 *
 * Nominal model of the loop (each layer supplies its own): x_dot = f0 + b (u_b + u_ad + sigma), with u_b the
 * baseline command, u_ad this layer's output and sigma the lumped matched uncertainty (in command units).
 *   predictor   xh_dot = f0 + b (u_p + sigma_hat) - a_s (xh - x)           u_p = the command the plant sees
 *   adaptation  sigma_hat = -(a_s mu / ((1 - mu) b)) (xh - x),  mu = exp(-a_s Ts)   (piecewise constant, every step)
 *   control     u_ad = -C(s) sigma_hat,  C(s) = w_c / (s + w_c)
 * The estimate is as fast as the sample rate allows; only the band below w_c reaches the plant, so w_c (not the
 * adaptation rate) sets the robustness and the delay margin, and as Ts -> 0 the loop recovers the performance of
 * the non-adaptive reference system (baseline with sigma cancelled inside w_c).
 *
 * The three roles of the thesis framework, each a bit of `roles` (0 = plain L1):
 *   1 role 1, feature memory: a slow regressor Theta' phi (phi = [1, s0, s1], loop-specific terms set by the
 *     layer) is fitted to sigma_hat by normalised gradient with leakage; it feeds forward unfiltered as a
 *     function of the measured state, and only the residual sigma_hat - Theta' phi goes through C(s). The learned
 *     map is what survives a fault-free stretch (memory), the lumped estimate handles the rest.
 *     mv = 1 (memory v2, after wave M showed v1 adds error): phi is low-passed at 2 w_c and the map is fitted to
 *     the low-frequency estimate already applied (Theta' phi_f + C(s) residual), so the memory consolidates what
 *     the filter compensates instead of chasing the raw, noisy sigma_hat; Theta survives landing resets.
 *   2 role 2, scheduler: w_c is scaled by s = 1 / (1 + k rho^2), rho = high-band power of sigma_hat (first-order
 *     high-pass at fc) over its total plus a floor (ef * umax)^2. A large high-band estimate (a delay limit cycle)
 *     lowers the filter bandwidth; noise-sized estimates leave it alone. s is a known function of measured signals
 *     in [1/(1+k), 1], so it only lowers w_c and the bounds of the fixed-w_c design hold for the lowest w_c.
 *   4 role 3, known physics: the layer's extra model terms in f0 (fk), the known transport delay d and the known
 *     first-order lag tau of what follows the command (motor or inner loop) shape u_p; off = u_p is the command
 *     itself and fk = 0, so that physics is left to sigma.
 * Saturation: the filter state is not pushed further into a direction the actuators cannot deliver (sat flags and
 * the own umax clamp); landed: predictor held on the plant, estimate and output zeroed (nothing acts on the ground).
 */
#pragma once

#include <lib/mathlib/mathlib.h>

struct L1Cfg {
	float b{1.f}, as{10.f}, wc{1.f}, tau{0.f}, dly{0.f}, umax{1.f};
	int roles{0};
	float fc{1.5f}, k{20.f}, tav{0.5f}, ef{0.2f}, kf{0.5f}, lk{0.02f};
	int mv{0};
};

struct L1Axis {
	static constexpr int NBUF = 64;
	static constexpr int NF = 3;
	float xh{0.f}, sig{0.f}, uf{0.f}, u_out{0.f}, up{0.f}, uprev{0.f};
	float theta[NF] {};
	float phif[NF] {1.f, 0.f, 0.f};
	float ubuf[NBUF] {};
	int bi{0};
	bool init{false};
	float s[2] {};                       // loop-specific feature terms, set by the layer each step
	float fk{0.f};                       // role 3 known physics term of x_dot, set by the layer each step
	float sc{1.f}, shp{0.f}, sprev{0.f}, phf{0.f}, ptot{0.f};
	float xt{0.f};                       // last predictor error xh - x

	void reset(float x)
	{
		xh = x; sig = 0.f; uf = 0.f; u_out = 0.f; up = 0.f; uprev = 0.f; bi = 0; init = true;
		phif[1] = s[0]; phif[2] = s[1];
		sc = 1.f; shp = 0.f; sprev = 0.f; phf = 0.f; ptot = 0.f; xt = 0.f;

		for (float &u : ubuf) { u = 0.f; }
	}

	float tnorm() const { return sqrtf(theta[0] * theta[0] + theta[1] * theta[1] + theta[2] * theta[2]); }

	// x: measured state; ub: baseline command this step; f0: nominal drift of x_dot (always used).
	// Returns u_ad in command units (0 when !on or landed).
	float step(float x, float ub, float f0, float dt, bool landed, bool on, const L1Cfg &c,
		   bool sat_pos = false, bool sat_neg = false)
	{
		if (!init || landed || !on) {
			reset(x);
			return 0.f;
		}

		dt = math::max(dt, 1e-4f);
		const float b = (fabsf(c.b) > 1e-6f) ? c.b : 1e-6f;
		const float as = math::max(c.as, 0.1f);
		const bool phys = c.roles & 4;
		// the command the plant saw over the last step: baseline + last output, delayed and lagged if known
		const float ucmd = ub + uprev;
		ubuf[bi] = ucmd; bi = (bi + 1) % NBUF;

		if (phys) {
			const int nd = math::constrain((int)lroundf(c.dly / dt), 0, NBUF - 1);
			const float ud = ubuf[(bi - 1 - nd + 2 * NBUF) % NBUF];
			up = (c.tau > 1e-4f) ? up + (ud - up) * math::min(dt / c.tau, 1.f) : ud;

		} else {
			up = ucmd;
		}

		// predictor, then the piecewise-constant estimate from the new error
		xh += dt * (f0 + (phys ? fk : 0.f) + b * (up + sig) - as * (xh - x));
		xt = xh - x;
		const float mu = expf(-as * dt);
		sig = -(as * mu / ((1.f - mu) * b)) * xt;

		// role 1: slow feature map fitted to sigma_hat
		float phi[NF] {1.f, s[0], s[1]};
		float fm = 0.f;

		if (c.mv == 1) {   // memory v2: features low-passed at 2 w_c
			const float a2 = math::min(dt * 2.f * c.wc, 1.f);

			for (int i = 1; i < NF; i++) { phif[i] += (phi[i] - phif[i]) * a2; phi[i] = phif[i]; }
		}

		if (c.roles & 1) {
			float pp = 1.f, pred = 0.f;

			for (int i = 0; i < NF; i++) { pp += phi[i] * phi[i]; pred += theta[i] * phi[i]; }

			// v1 fits the raw estimate; v2 fits the low-frequency estimate applied last step (-u_out = map + filter)
			const float tgt = (c.mv == 1) ? -u_out : sig;

			for (int i = 0; i < NF; i++) {
				theta[i] = math::constrain(theta[i] + dt * (c.kf * (tgt - pred) * phi[i] / pp - c.lk * theta[i]),
							   -c.umax, c.umax);
				fm += theta[i] * phi[i];
			}
		}

		// role 2: bandwidth scheduler on the high band of sigma_hat, amplitude gated
		if (c.roles & 2) {
			const float tc = 1.f / (6.2831853f * math::max(c.fc, 0.01f));
			shp = tc / (tc + dt) * (shp + sig - sprev);
			const float a = math::min(dt / math::max(c.tav, 0.01f), 1.f);
			phf += (shp * shp - phf) * a;
			ptot += (sig * sig - ptot) * a;
			const float fl = c.ef * c.umax;
			const float rho = math::constrain(phf / (ptot + fl * fl + 1e-9f), 0.f, 1.f);
			sc = 1.f / (1.f + math::max(c.k, 0.f) * rho * rho);

		} else {
			sc = 1.f;
		}

		sprev = sig;

		// C(s) on the residual; hold the filter instead of pushing into saturation
		const float target = sig - fm;
		const float duf = (target - uf) * math::min(dt * c.wc * sc, 1.f);
		const float u_next = -(fm + uf + duf);
		const bool push_pos = u_next > u_out, push_neg = u_next < u_out;
		const bool blocked = (push_pos && (sat_pos || u_out >= c.umax)) || (push_neg && (sat_neg || u_out <= -c.umax));

		if (!blocked) { uf += duf; }

		u_out = math::constrain(-(fm + uf), -c.umax, c.umax);
		uprev = u_out;
		return u_out;
	}
};
