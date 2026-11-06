/**
 * Authority budget geometry (MRL_B_EN bit 1), pure matrix math so it is checked on its own (ci/test_budget.cpp).
 * F: normalized thrust vector in NED (|F| = collective in [0, 1], -F(2) = its vertical part).
 */
#pragma once

#include <lib/mathlib/mathlib.h>
#include <matrix/math.hpp>

namespace mrl_budget
{

// tilt of the thrust vector from the vertical [rad]
inline float tilt_of(const matrix::Vector3f &F)
{
	return atan2f(sqrtf(F(0) * F(0) + F(1) * F(1)), math::max(-F(2), 1e-6f));
}

// thrust vector -> attitude quaternion and collective, as PX4 ControlMath::bodyzToAttitude: keep yaw, body z along -F
inline void thrust_to_att(const matrix::Vector3f &F, float yaw, float q_d[4], float &thrust_z)
{
	const matrix::Vector3f bz = -F.normalized();
	matrix::Vector3f bx = matrix::Vector3f(-sinf(yaw), cosf(yaw), 0.f) % bz;
	bx.normalize();
	const matrix::Vector3f by = bz % bx;
	matrix::Dcmf Rn;

	for (int j = 0; j < 3; j++) { Rn(j, 0) = bx(j); Rn(j, 1) = by(j); Rn(j, 2) = bz(j); }

	matrix::Quatf(Rn).copyTo(q_d);
	thrust_z = math::constrain(-F.norm(), -1.f, 0.f);
}

// largest lambda in [0, 1] with F_b + lambda (F_f - F_b) inside {tilt <= tlim, |F| <= flim}; both sets are convex,
// so with F_b inside (tlim >= tilt(F_b), flim >= |F_b|) the feasible lambda are an interval [0, lambda*]
inline float lambda_max(const matrix::Vector3f &Fb, const matrix::Vector3f &Ff, float tlim, float flim)
{
	const matrix::Vector3f dF = Ff - Fb;
	auto ok = [&](float l) { const matrix::Vector3f F = Fb + dF * l; return tilt_of(F) <= tlim + 1e-5f && F.norm() <= flim + 1e-6f; };

	if (ok(1.f)) { return 1.f; }

	float lo = 0.f, hi = 1.f;

	for (int it = 0; it < 14; it++) {
		const float mid = 0.5f * (lo + hi);

		if (ok(mid)) { lo = mid; } else { hi = mid; }
	}

	return lo;
}

} // namespace mrl_budget
