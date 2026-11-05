// Standalone check of px4-mrac/sih_fidelity.hpp: stock equivalence when off, and physical sanity of each term.
// g++ -std=c++17 -Wall -Wextra -Werror -Wdouble-promotion -I px4-mrac ci/test_sih_fidelity.cpp -o /tmp/t && /tmp/t
#include <cstdio>
#include "sih_fidelity.hpp"

using namespace sih_fid;
static int fails = 0;
static void check(bool ok, const char *what, double got)
{
	printf("%-58s %s (%.4g)\n", what, ok ? "ok" : "FAIL", got);
	fails += !ok;
}

int main()
{
	const float tmax = 6.38f, qmax = 0.1f, l = 0.1414f, m = 0.9885f, dt = 0.005f;
	const float uh[4] {0.38f, 0.38f, 0.38f, 0.38f}, z3[3] {}, vfwd[3] {5.f, 0.f, 0.f}, vup[3] {0.f, 0.f, -2.f};
	Params off;
	State s;
	// 1 off == stock SIH: T = T_MAX u, roll/pitch torque L T_MAX (...), yaw Q_MAX (...), no extra force
	{
		const float u[4] {0.3f, 0.5f, 0.4f, 0.6f};
		Out o = step(off, s, u, tmax, qmax, l, l, m, vfwd, vfwd, 3000.f, 10.f, dt);
		float e = 0.f;

		for (int i = 0; i < 4; i++) { e += fabsf(o.T[i] - tmax * u[i]); }

		e += fabsf(o.M_B[0] - l * tmax * (-u[0] + u[1] + u[2] - u[3])) + fabsf(o.M_B[1] - l * tmax * (u[0] - u[1] + u[2] - u[3]))
		     + fabsf(o.M_B[2] - qmax * (u[0] + u[1] - u[2] - u[3]));
		e += fabsf(o.F_B[0]) + fabsf(o.F_q[0]);
		check(e < 1e-5f, "all terms off reproduce stock SIH (also at 3000 m, 5 m/s)", e);
	}
	// 2 density: 2000 m, 30 C -> rho about 0.94 kg/m3, thrust -23 %
	Params pd; pd.rho_en = 1; pd.air_t = 30.f;
	{
		Out o = step(pd, s, uh, tmax, qmax, l, l, m, z3, z3, 2000.f, 10.f, dt);
		const float ratio = o.T[0] / (tmax * 0.38f);
		check(ratio > 0.74f && ratio < 0.80f, "density 2000 m 30 C: thrust ratio 0.74-0.80", ratio);
		Out o0 = step(pd, s, uh, tmax, qmax, l, l, m, z3, z3, 0.f, 10.f, dt);
		pd.air_t = 15.f;
		Out o1 = step(pd, s, uh, tmax, qmax, l, l, m, z3, z3, 0.f, 10.f, dt);
		check(fabsf(o1.T[0] / (tmax * 0.38f) - 1.f) < 0.01f, "density sea level 15 C: ratio 1", o1.T[0] / (tmax * 0.38f));
		check(o0.T[0] < o1.T[0], "hot air gives less thrust than ISA", o0.T[0] - o1.T[0]);
	}
	// 3 ground effect: R 0.0635, on the ground (z 5 cm) +11 %, at 1 m < 0.1 %
	Params pg; pg.prop_r = 0.0635f;
	{
		const float g0 = step(pg, s, uh, tmax, qmax, l, l, m, z3, z3, 0.f, 0.f, dt).T[0] / (tmax * 0.38f);
		const float g1 = step(pg, s, uh, tmax, qmax, l, l, m, z3, z3, 0.f, 1.f, dt).T[0] / (tmax * 0.38f);
		check(g0 > 1.08f && g0 < 1.15f, "ground effect on the ground: +8..15 %", g0);
		check(g1 < 1.001f, "ground effect at 1 m: < 0.1 %", g1);
	}
	// 4 axial inflow and translational lift: climbing 2 m/s -> less thrust, 5 m/s edgewise -> more
	Params pa; pa.kax = 0.5f; pa.ktl = 0.2f;
	{
		const float c = step(pa, s, uh, tmax, qmax, l, l, m, vup, vup, 0.f, 10.f, dt).T[0] / (tmax * 0.38f);
		const float f = step(pa, s, uh, tmax, qmax, l, l, m, vfwd, vfwd, 0.f, 10.f, dt).T[0] / (tmax * 0.38f);
		check(c < 0.97f && c > 0.85f, "climb 2 m/s: thrust -3..-15 %", c);
		check(f > 1.02f && f < 1.12f, "edgewise 5 m/s: thrust +2..12 %", f);
	}
	// 5 rotor drag: 5 m/s at hover, k 0.142 -> about 0.35 N/(m/s) x 5 = 1.75 N, against the motion
	Params pr; pr.krd = 0.142f;
	{
		Out o = step(pr, s, uh, tmax, qmax, l, l, m, vfwd, vfwd, 0.f, 10.f, dt);
		check(o.F_B[0] < -1.5f && o.F_B[0] > -2.0f, "rotor drag 5 m/s at hover: -1.5..-2.0 N", o.F_B[0]);
		Params pq; pq.cda = 0.01f;
		Out q = step(pq, s, uh, tmax, qmax, l, l, m, vfwd, vfwd, 0.f, 10.f, dt);
		check(q.F_q[0] < -0.14f && q.F_q[0] > -0.17f, "quadratic drag CdA 0.01 at 5 m/s: -0.15 N", q.F_q[0]);
	}
	// 6 battery: 4S 1500 mAh, hover 80-220 W, voltage 15.5-16.8 V full; 3 min of hover takes 25-45 % SoC; thrust drops
	Params pb; pb.bat_cap = 1500.f; pb.bat_n = 4.f; pb.bat_r0 = 0.06f; pb.bat_soc0 = 1.f; pb.bat_eta = 0.5f;
	{
		State sb;
		const float u2[4] {0.39f, 0.39f, 0.39f, 0.39f};
		Out o = step(pb, sb, u2, tmax, qmax, l, l, m, z3, z3, 0.f, 10.f, dt);
		const float P = sb.v_bat * sb.i_bat, T0 = o.T[0];
		check(P > 80.f && P < 220.f, "battery hover power 80-220 W", P);
		check(sb.v_bat > 15.5f && sb.v_bat < 16.8f, "battery full, loaded voltage 15.5-16.8 V", sb.v_bat);

		for (int k = 0; k < 36000; k++) { o = step(pb, sb, u2, tmax, qmax, l, l, m, z3, z3, 0.f, 10.f, dt); }

		check(sb.soc > 0.55f && sb.soc < 0.75f, "after 180 s hover (~11 A from 1.5 Ah) SoC 0.55-0.75", sb.soc);
		check(o.T[0] < T0, "thrust at the same throttle drops with the battery", o.T[0] / T0);
	}
	// 7 CoM offset 1 cm forward: nose-down (negative? FRD pitch +) torque = x_cm * T
	Params pc; pc.com_x = 0.01f;
	{
		Out o = step(pc, s, uh, tmax, qmax, l, l, m, z3, z3, 0.f, 10.f, dt);
		check(fabsf(o.M_B[1] - 0.01f * 4.f * tmax * 0.38f) < 1e-4f, "CoM 1 cm: pitch torque x_cm T_sum", o.M_B[1]);
	}
	// 8 thrust curve f = 0.3: half throttle gives less than half thrust
	Params pt; pt.thr_fac = 0.3f;
	{
		const float uhh[4] {0.5f, 0.5f, 0.5f, 0.5f};
		const float r = step(pt, s, uhh, tmax, qmax, l, l, m, z3, z3, 0.f, 10.f, dt).T[0] / tmax;
		check(fabsf(r - 0.425f) < 1e-4f, "thrust curve f 0.3 at u 0.5: 0.425", r);
	}
	// 9 vibration: amplitude at hover equals the param, zero when off; frequency = omega
	Params pv; pv.vib_acc = 2.f; pv.vib_gyr = 0.1f;
	{
		State sv;
		const float un[4] {0.35f, 0.36f, 0.37f, 0.38f};   // n about 0.6, rotors at slightly different speeds (beating)
		step(pv, sv, un, tmax, qmax, l, l, m, z3, z3, 0.f, 10.f, dt);
		float amax = 0.f, a[3], g[3];

		for (int k = 0; k < 20000; k++) { vibration(pv, sv, 1e-4f, a, g); amax = fmaxf(amax, fabsf(a[0])); }

		check(amax > 2.f && amax <= 8.5f, "vibration x peak over 2 s of beating in (A, 4.2A]", amax);
		vibration(off, sv, 1e-4f, a, g);
		check(fabsf(a[0]) + fabsf(g[0]) < 1e-12f, "vibration off: zero", a[0]);
	}
	printf("%s\n", fails ? "FAILED" : "ALL OK");
	return fails;
}
