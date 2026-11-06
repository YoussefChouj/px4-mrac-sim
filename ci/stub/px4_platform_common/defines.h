// Stand-in for PX4's px4_platform_common/defines.h, enough for the header-only matrix library in ci/ tests.
#pragma once
#include <cmath>
#include <cfloat>
#define PX4_ISFINITE(x) std::isfinite(x)
#ifndef M_PI_F
#define M_PI_F 3.14159265358979323846f
#endif
#ifndef M_TWOPI_F
#define M_TWOPI_F 6.28318530717958647692f
#endif
