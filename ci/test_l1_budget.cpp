// Standalone checks of the authority budget geometry (AuthorityBudget.hpp) and the online delay estimate
// (DelayBank in L1Axis.hpp). Needs PX4's header-only matrix library (src/lib/matrix of PX4 v1.17.0):
// g++ -std=c++17 -O2 -Wall -I ci/stub -I $PX4/src/lib/matrix -I px4-mrac/src/modules/mrac_layers
//   ci/test_l1_budget.cpp -o /tmp/tb && /tmp/tb
#include <cstdio>
#include <random>
#include "AuthorityBudget.hpp"
#include "L1Axis.hpp"

using namespace mrl_budget;
static int fails = 0;
static void check(bool ok, const char *what, double got)
{
	printf("%-62s %s (%.4g)\n", what, ok ? "ok" : "FAIL", got);
	fails += !ok;
}

static matrix::Vector3f tilted(float deg, float vert, float az = 0.f)   // thrust vector with this tilt and vertical part
{
	const float h = vert * tanf(math::radians(deg));
	return matrix::Vector3f(h * cosf(az), h * sinf(az), -vert);
}

// closed-loop roll-rate plant w_dot = b m(t - D) + gust, motor lag tt, PX4-like PID, L1 roles 6; DelayBank estimate
static float bank_run(float D, float tt, unsigned seed, bool ground_after = false)
{
	const float dt = 0.004f, b = 170.f, tm = 0.0505f;
	std::mt19937 g(seed);
	std::normal_distribution<float> n(0, 1);
	L1Axis l; L1Cfg c; c.b = b; c.as = 100.f; c.wc = 10.f; c.tau = tm; c.dly = 0.025f; c.umax = 0.3f; c.roles = 6;
	DelayBank bank;
	float w = 0, m = 0, I = 0, q[200] {}, wprev = 0, dd = 0, dh = 0.025f;

	for (int k = 0; k < 15000; k++) {
		const float t = k * dt, r = (int(t / 1.5f) % 2) ? 0.6f : -0.6f;
		const bool landed = t < 0.5f || (ground_after && t > 40.f);
		dd += dt / 0.5f * (0.15f * n(g) - dd);
		const float wm = w + 0.03f * n(g);
		const float ub = 0.15f * (r - wm) + I - 0.003f * (wm - wprev) / dt;
		I += dt * 0.2f * (r - wm); wprev = wm;
		c.dly = dh;
		const float ua = math::constrain(ub + l.step(wm, ub, 0.f, dt, landed, true, c), -1.f, 1.f);
		dh = bank.step(wm, ua, dt, landed, tm, 0.025f);
		const int nd = (int)lroundf(D / dt);

		for (int i = 199; i > 0; i--) { q[i] = q[i - 1]; }

		q[0] = ua;
		m += dt / tt * (q[nd] - m);
		w += dt * (b * (m + dd));
	}

	return dh;
}

int main()
{
	const float r37 = math::radians(37.f);
	// 1 geometry
	check(fabsf(math::degrees(tilt_of(tilted(30.f, 0.4f))) - 30.f) < 1e-3f, "tilt_of a 30 deg vector", math::degrees(tilt_of(tilted(30.f, 0.4f))));
	{
		float q[4], tz;
		thrust_to_att(tilted(25.f, 0.5f, 1.f), 0.3f, q, tz);
		const matrix::Vector3f F = matrix::Dcmf(matrix::Quatf(q)) * matrix::Vector3f(0.f, 0.f, tz);
		check((F - tilted(25.f, 0.5f, 1.f)).norm() < 1e-5f, "thrust_to_att round trip", (F - tilted(25.f, 0.5f, 1.f)).norm());
	}
	// 2 tilt cut: baseline 20 deg, adaptive wants 50 deg at the same vertical -> applied tilt = 37 deg
	{
		const matrix::Vector3f Fb = tilted(20.f, 0.4f), Ff = tilted(50.f, 0.4f);
		const float l = lambda_max(Fb, Ff, r37, 1.f);
		const float t = math::degrees(tilt_of(Fb + (Ff - Fb) * l));
		check(l > 0.f && l < 1.f && fabsf(t - 37.f) < 0.05f, "tilt cut to 37 deg", t);
	}
	// 3 the baseline is never cut, adaptive may not grow past it, but may reduce
	{
		const matrix::Vector3f Fb = tilted(42.f, 0.4f);
		check(lambda_max(Fb, tilted(45.f, 0.4f), fmaxf(r37, tilt_of(Fb)), 1.f) < 1e-3f, "baseline 42 deg: no growth to 45", 0);
		check(lambda_max(Fb, tilted(40.f, 0.4f), fmaxf(r37, tilt_of(Fb)), 1.f) == 1.f, "baseline 42 deg: reduction to 40 passes", 1);
	}
	// 4 thrust cut: |F_b| 0.85 -> 0.95 wanted, limit 0.9
	{
		const matrix::Vector3f Fb(0.f, 0.f, -0.85f), Ff(0.f, 0.f, -0.95f);
		const float l = lambda_max(Fb, Ff, r37, 0.9f);
		check(fabsf((Fb + (Ff - Fb) * l).norm() - 0.9f) < 1e-3f, "collective cut to 0.9", (Fb + (Ff - Fb) * l).norm());
	}
	// 5 nothing to cut inside the budget
	check(lambda_max(tilted(10.f, 0.4f), tilted(30.f, 0.45f), r37, 0.9f) == 1.f, "inside the budget: lambda 1", 1);
	// 6 delay estimate, right motor lag: within 4 ms of the truth over 10-40 ms
	{
		float worst = 0.f;

		for (float D : {0.010f, 0.020f, 0.030f, 0.040f}) { worst = fmaxf(worst, fabsf(bank_run(D, 0.0505f, 1) - D)); }

		check(worst < 0.004f, "delay estimate 10-40 ms: worst error < 4 ms", worst * 1e3f);
	}
	// 7 wrong motor lag: the estimate moves the right way (an effective delay: slower motor -> larger)
	check(bank_run(0.025f, 0.07f, 2) > bank_run(0.025f, 0.035f, 2) + 0.005f, "slower motor gives a larger effective delay", 0);
	// 8 on the ground the estimate holds
	{
		const float a = bank_run(0.035f, 0.0505f, 3, true);
		check(fabsf(a - 0.035f) < 0.005f, "estimate holds after landing (35 ms truth)", a * 1e3f);
	}
	printf("%s\n", fails ? "FAILED" : "ALL OK");
	return fails;
}
