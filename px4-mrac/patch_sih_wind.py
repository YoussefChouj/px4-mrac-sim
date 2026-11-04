"""Add horizontal wind to the SIH multicopter drag term (P16): _Fa_E = -SIH_KDV (v - wind). Wind = mean SIH_WIND_N/E
(m/s, NED) + Gauss-Markov turbulence per axis (SIH_WIND_SIG m/s, SIH_WIND_TAU s), seeded by SIH_WIND_SEED (reseeds on
change, so an A/B deck can give run i of every arm the same turbulence). All 0 = stock behaviour.
Usage: patch_sih_wind.py PX4_TREE. Idempotent."""
import sys
from pathlib import Path
D = Path(sys.argv[1]) / 'src/modules/simulation/simulator_sih'
cpp, hpp, prm = D / 'sih.cpp', D / 'sih.hpp', D / 'sih_params.c'
c, h, p = cpp.read_text(), hpp.read_text(), prm.read_text()
if 'SIH_WIND_N' in p:
    print('patch_sih_wind: already applied'); sys.exit(0)

def rep(s, old, new, n=1):
    assert s.count(old) == n, (old, s.count(old))
    return s.replace(old, new)

h = rep(h, '\tfloat _MASS, _T_MAX, _Q_MAX, _L_ROLL, _L_PITCH, _KDV, _KDW, _T_TAU;\n',
        '\tfloat _MASS, _T_MAX, _Q_MAX, _L_ROLL, _L_PITCH, _KDV, _KDW, _T_TAU;\n'
        '\n\t// research: horizontal wind for the multicopter drag term (P16)\n'
        '\tmatrix::Vector3f wind_E(float dt);\n'
        '\tfloat wind_gauss();\n'
        '\tmatrix::Vector2f _wind_turb{};\n'
        '\tuint32_t _wind_rng{1};\n'
        '\tint32_t _wind_seed{-1};\n')
h = rep(h, '\t\t(ParamFloat<px4::params::SIH_T_TAU>) _sih_thrust_tau,\n',
        '\t\t(ParamFloat<px4::params::SIH_T_TAU>) _sih_thrust_tau,\n'
        '\t\t(ParamFloat<px4::params::SIH_WIND_N>) _sih_wind_n,\n'
        '\t\t(ParamFloat<px4::params::SIH_WIND_E>) _sih_wind_e,\n'
        '\t\t(ParamFloat<px4::params::SIH_WIND_SIG>) _sih_wind_sig,\n'
        '\t\t(ParamFloat<px4::params::SIH_WIND_TAU>) _sih_wind_tau,\n'
        '\t\t(ParamInt<px4::params::SIH_WIND_SEED>) _sih_wind_seed,\n')

c = rep(c, '\t_KDW = _sih_kdw.get();\n',
        '\t_KDW = _sih_kdw.get();\n\n'
        '\tif (_sih_wind_seed.get() != _wind_seed) {\n'
        '\t\t// a new seed restarts the turbulence sequence, so run i of every arm sees the same wind\n'
        '\t\t_wind_seed = _sih_wind_seed.get();\n'
        '\t\t_wind_rng = 2463534242u ^ (static_cast<uint32_t>(_wind_seed) * 2654435761u);\n'
        '\t\t_wind_rng = _wind_rng ? _wind_rng : 1u;\n'
        '\t\t_wind_turb.setZero();\n'
        '\t}\n', n=1)
old_q = ('\t\t_Fa_E = -_KDV * _v_E;   // first order drag to slow down the aircraft\n'
         '\t\t_Ma_B = -_KDW * _w_B;   // first order angular damper\n')
c = rep(c, old_q, '\t\t_Fa_E = -_KDV * (_v_E - wind_E(dt));   // first order drag relative to the air (research: wind)\n'
        '\t\t_Ma_B = -_KDW * _w_B;   // first order angular damper\n')
c = rep(c, 'void Sih::generate_force_and_torques(const float dt)\n',
        '// research (P16): F = -KDV (v - w). Mean wind SIH_WIND_N/E plus first-order Gauss-Markov turbulence per\n'
        '// horizontal axis (std SIH_WIND_SIG, time constant SIH_WIND_TAU), sequence seeded by SIH_WIND_SEED.\n'
        'float Sih::wind_gauss()\n{\n'
        '\t_wind_rng ^= _wind_rng << 13; _wind_rng ^= _wind_rng >> 17; _wind_rng ^= _wind_rng << 5;\n'
        '\tconst float u1 = static_cast<float>((_wind_rng >> 8) + 1u) * (1.f / 16777217.f);\n'
        '\t_wind_rng ^= _wind_rng << 13; _wind_rng ^= _wind_rng >> 17; _wind_rng ^= _wind_rng << 5;\n'
        '\tconst float u2 = static_cast<float>(_wind_rng >> 8) * (1.f / 16777216.f);\n'
        '\treturn sqrtf(-2.f * logf(u1)) * cosf(2.f * M_PI_F * u2);\n}\n\n'
        'Vector3f Sih::wind_E(const float dt)\n{\n'
        '\tconst float sig = _sih_wind_sig.get();\n\n'
        '\tif (sig > 0.f && dt > 0.f && dt < 0.1f) {\n'
        '\t\tconst float a = expf(-dt / fmaxf(_sih_wind_tau.get(), 0.1f));\n'
        '\t\tconst float b = sig * sqrtf(1.f - a * a);\n'
        '\t\t_wind_turb(0) = a * _wind_turb(0) + b * wind_gauss();\n'
        '\t\t_wind_turb(1) = a * _wind_turb(1) + b * wind_gauss();\n\n'
        '\t} else if (sig <= 0.f) {\n'
        '\t\t_wind_turb.setZero();\n'
        '\t}\n\n'
        '\treturn _R_N2E * Vector3f(_sih_wind_n.get() + _wind_turb(0), _sih_wind_e.get() + _wind_turb(1), 0.f);\n}\n\n'
        'void Sih::generate_force_and_torques(const float dt)\n')
P = lambda name, typ, default, short, unit, mn, mx, long: (
    f'\n/**\n * {short}\n *\n * {long}\n *\n * @unit {unit}\n * @min {mn}\n * @max {mx}\n'
    + (' * @decimal 2\n' if typ == 'FLOAT' else '') + f' * @group Simulation In Hardware\n */\nPARAM_DEFINE_{typ}({name}, {default});\n')
p += (P('SIH_WIND_N', 'FLOAT', '0.0f', 'Mean wind, north (research)', 'm/s', -20, 20,
        'Air velocity in NED used by the multicopter drag term F = -SIH_KDV (v - w).')
      + P('SIH_WIND_E', 'FLOAT', '0.0f', 'Mean wind, east (research)', 'm/s', -20, 20,
          'Air velocity in NED used by the multicopter drag term F = -SIH_KDV (v - w).')
      + P('SIH_WIND_SIG', 'FLOAT', '0.0f', 'Wind turbulence std per horizontal axis (research)', 'm/s', 0, 10,
          'First-order Gauss-Markov turbulence added to SIH_WIND_N/E. 0 disables it.')
      + P('SIH_WIND_TAU', 'FLOAT', '10.0f', 'Wind turbulence correlation time (research)', 's', 0.1, 100,
          'Time constant of the Gauss-Markov turbulence (about L / V for a frozen-turbulence length L).')
      + '\n/**\n * Wind turbulence seed (research)\n *\n * A new value restarts the turbulence sequence (paired A/B: same seed, same wind).\n'
        ' *\n * @min 0\n * @max 1000000\n * @group Simulation In Hardware\n */\nPARAM_DEFINE_INT32(SIH_WIND_SEED, 1);\n')
cpp.write_text(c); hpp.write_text(h); prm.write_text(p)
print('patched'); import re
print('KDV default:', re.search(r'PARAM_DEFINE_FLOAT\(SIH_KDV,[^)]*\)', p).group(0))
