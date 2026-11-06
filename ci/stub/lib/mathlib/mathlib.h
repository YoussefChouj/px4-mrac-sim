// Minimal stand-in for PX4's lib/mathlib for the standalone tests in ci/ (only what the mrac_layers headers use).
#pragma once
#include <cmath>
#include <algorithm>
namespace math
{
template<class T> T constrain(T v, T lo, T hi) { return std::min(std::max(v, lo), hi); }
template<class T> T min(T a, T b) { return std::min(a, b); }
template<class T> T max(T a, T b) { return std::max(a, b); }
inline float radians(float d) { return d * 0.017453292f; }
inline float degrees(float r) { return r * 57.29578f; }
}
