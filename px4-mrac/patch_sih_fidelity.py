"""Patch SIH (in ~/PX4-mrac only) with the higher-fidelity quad physics of sih_fidelity.hpp.

Copies sih_fidelity.hpp next to sih.cpp and wires it into: the motor model (per-motor efficiency, slower spin-down),
the quad force/torque model (thrust curve, air density, axial inflow, translational lift, ground effect, rotor drag,
quadratic body drag, battery, centre-of-mass offset) and the IMU (rotor vibration, constant biases). Every term has
its own SIH_* param, read every second, and is off at its default: a stock deck flies the stock model.
Run after patch_sih_delay.py, patch_sih_jitter.py, patch_sih_imu_noise.py and patch_sih_wind.py.
Usage: patch_sih_fidelity.py PX4_TREE. Idempotent.
"""
import shutil
import sys
from pathlib import Path

d = Path(sys.argv[1]) / 'src/modules/simulation/simulator_sih'
f, fp = d / 'sih.cpp', d / 'sih_params.c'
shutil.copy(Path(__file__).with_name('sih_fidelity.hpp'), d / 'sih_fidelity.hpp')
s, p = f.read_text(), fp.read_text()
if 'sih_fidelity.hpp' in s:
    print('SIH fidelity present (header refreshed)')
    sys.exit(0)


def rep(a, b):
    global s
    assert s.count(a) == 1, f'SIH source changed: {a[:70]!r}'
    s = s.replace(a, b)


rep('void Sih::run()\n', '''#include "sih_fidelity.hpp"

namespace
{
// research: higher-fidelity quad physics params (sih_fidelity.hpp), re-read every second
sih_fid::Params g_fid;
sih_fid::State g_fs;
hrt_abstime g_fid_chk = 0;

float fid_pf(const char *n, float dflt)
{
	const param_t h = param_find(n);
	float v = dflt;

	if (h != PARAM_INVALID) { param_get(h, &v); }

	return v;
}

void fid_refresh(hrt_abstime now)
{
	if (g_fid_chk != 0 && now - g_fid_chk < 1000000) { return; }

	g_fid_chk = now;
	g_fid.thr_fac = fid_pf("SIH_THR_FAC", 0.f);
	g_fid.tau_dn = fid_pf("SIH_T_TAU_DN", 0.f);
	g_fid.eff[0] = 1.f; // motor 1: SIH_MOT1_EFF (patch_sih_delay.py)
	g_fid.eff[1] = fid_pf("SIH_MOT2_EFF", 1.f);
	g_fid.eff[2] = fid_pf("SIH_MOT3_EFF", 1.f);
	g_fid.eff[3] = fid_pf("SIH_MOT4_EFF", 1.f);
	const param_t rh = param_find("SIH_RHO_EN");
	int32_t rho_en = 0;

	if (rh != PARAM_INVALID) { param_get(rh, &rho_en); }

	g_fid.rho_en = rho_en;
	g_fid.air_t = fid_pf("SIH_AIR_T", 15.f);
	g_fid.kax = fid_pf("SIH_RA_KAX", 0.f);
	g_fid.ktl = fid_pf("SIH_RA_KTL", 0.f);
	g_fid.prop_r = fid_pf("SIH_PROP_R", 0.f);
	g_fid.krd = fid_pf("SIH_RD_K", 0.f);
	g_fid.cda = fid_pf("SIH_CDA", 0.f);
	g_fid.bat_cap = fid_pf("SIH_BAT_CAP", 0.f);
	g_fid.bat_n = fid_pf("SIH_BAT_N", 4.f);
	g_fid.bat_r0 = fid_pf("SIH_BAT_R0", 0.05f);
	g_fid.bat_soc0 = fid_pf("SIH_BAT_SOC0", 1.f);
	g_fid.bat_eta = fid_pf("SIH_BAT_ETA", 0.5f);
	g_fid.com_x = fid_pf("SIH_COM_X", 0.f);
	g_fid.com_y = fid_pf("SIH_COM_Y", 0.f);
	g_fid.vib_acc = fid_pf("SIH_VIB_ACC", 0.f);
	g_fid.vib_gyr = fid_pf("SIH_VIB_GYR", 0.f);
	g_fid.vib_h2 = fid_pf("SIH_VIB_H2", 0.f);
	g_fid.w_max = fid_pf("SIH_W_MAX", 969.f);
	g_fid.acc_b[0] = fid_pf("SIH_ACC_BX", 0.f);
	g_fid.acc_b[1] = fid_pf("SIH_ACC_BY", 0.f);
	g_fid.acc_b[2] = fid_pf("SIH_ACC_BZ", 0.f);
	g_fid.gyr_b[0] = fid_pf("SIH_GYR_BX", 0.f);
	g_fid.gyr_b[1] = fid_pf("SIH_GYR_BY", 0.f);
	g_fid.gyr_b[2] = fid_pf("SIH_GYR_BZ", 0.f);
}
} // namespace

void Sih::run()
''')

rep('				_u[i] = _u[i] + dt / _T_TAU * (u_sp - _u[i]); // first order transfer function with time constant tau\n',
    '''				if (i > 0 && i < 4) { u_sp *= g_fid.eff[i]; } // research: motor spread SIH_MOT2..4_EFF

				// research: slower spin-down SIH_T_TAU_DN (0 = SIH_T_TAU)
				const float tau_m = (u_sp < _u[i] && g_fid.tau_dn > 0.f) ? g_fid.tau_dn : _T_TAU;
				_u[i] = _u[i] + dt / tau_m * (u_sp - _u[i]); // first order transfer function with time constant tau
''')

rep('''	if (_vehicle == VehicleType::Quadcopter) {
		_T_B = Vector3f(0.0f, 0.0f, -_T_MAX * (+_u[0] + _u[1] + _u[2] + _u[3]));
		_Mt_B = Vector3f(_L_ROLL * _T_MAX * (-_u[0] + _u[1] + _u[2] - _u[3]),
				 _L_PITCH * _T_MAX * (+_u[0] - _u[1] + _u[2] - _u[3]),
				 _Q_MAX * (+_u[0] + _u[1] - _u[2] - _u[3]));
		_Fa_E = -_KDV * (_v_E - wind_E(dt));   // first order drag relative to the air (research: wind)
		_Ma_B = -_KDW * _w_B;   // first order angular damper
''', '''	if (_vehicle == VehicleType::Quadcopter) {
		// research: higher-fidelity quad physics (sih_fidelity.hpp); identical to stock when its params are off
		fid_refresh(hrt_absolute_time());
		const Vector3f v_air_E = _v_E - wind_E(dt);
		const Vector3f v_air_B = _q_E.rotateVectorInverse(v_air_E);
		const float um[4] {_u[0], _u[1], _u[2], _u[3]};
		const float vb[3] {v_air_B(0), v_air_B(1), v_air_B(2)};
		const float ve[3] {v_air_E(0), v_air_E(1), v_air_E(2)};
		const float h_msl = static_cast<float>(_lla.altitude());
		const float dtf = (dt > 0.f && dt < 0.1f) ? dt : 0.f;
		const sih_fid::Out fo = sih_fid::step(g_fid, g_fs, um, _T_MAX, _Q_MAX, _L_ROLL, _L_PITCH, _MASS, vb, ve, h_msl,
						      h_msl - _lpos_ref_alt, dtf);
		_T_B = Vector3f(0.0f, 0.0f, -(fo.T[0] + fo.T[1] + fo.T[2] + fo.T[3]));
		_Mt_B = Vector3f(fo.M_B[0], fo.M_B[1], fo.M_B[2]);
		_Fa_E = -_KDV * v_air_E + _q_E.rotateVector(Vector3f(fo.F_B[0], fo.F_B[1], fo.F_B[2]))
			+ Vector3f(fo.F_q[0], fo.F_q[1], fo.F_q[2]);   // drag relative to the air (research: wind)
		_Ma_B = -_KDW * _w_B;   // first order angular damper
''')

rep('''	Vector3f specific_force_B = R_E2B * _specific_force_E;
''', '''	{ // research: rotor vibration and constant IMU biases (sih_fidelity.hpp), off by default
		static hrt_abstime vib_last = 0;
		const float dtv = vib_last != 0 ? fminf(static_cast<float>(time_now_us - vib_last) * 1e-6f, 0.02f) : 0.f;
		vib_last = time_now_us;
		float va[3], vg[3];
		sih_fid::vibration(g_fid, g_fs, dtv, va, vg);
		accel_noise += Vector3f(va[0] + g_fid.acc_b[0], va[1] + g_fid.acc_b[1], va[2] + g_fid.acc_b[2]);
		gyro_noise += Vector3f(vg[0] + g_fid.gyr_b[0], vg[1] + g_fid.gyr_b[1], vg[2] + g_fid.gyr_b[2]);
	}

	Vector3f specific_force_B = R_E2B * _specific_force_E;
''')
f.write_text(s)

P = [  # name, type, default, unit, min, max, short description
    ('SIH_THR_FAC', 'FLOAT', 0.0, '', 0, 1, 'Thrust curve factor f in T = T_max (f u^2 + (1 - f) u) (research patch)'),
    ('SIH_T_TAU_DN', 'FLOAT', 0.0, 's', 0, 1, 'Motor spin-down time constant, 0 = SIH_T_TAU (research patch)'),
    ('SIH_MOT2_EFF', 'FLOAT', 1.0, '', 0, 1.2, 'Thrust efficiency of motor 2 (research patch)'),
    ('SIH_MOT3_EFF', 'FLOAT', 1.0, '', 0, 1.2, 'Thrust efficiency of motor 3 (research patch)'),
    ('SIH_MOT4_EFF', 'FLOAT', 1.0, '', 0, 1.2, 'Thrust efficiency of motor 4 (research patch)'),
    ('SIH_RHO_EN', 'INT32', 0, '', 0, 1, 'Air density from ISA altitude and SIH_AIR_T scales thrust (research patch)'),
    ('SIH_AIR_T', 'FLOAT', 15.0, 'celcius', -40, 50, 'Air temperature at the flight altitude (research patch)'),
    ('SIH_RA_KAX', 'FLOAT', 0.0, '', 0, 2, 'Thrust loss per climb speed over hover induced velocity (research patch)'),
    ('SIH_RA_KTL', 'FLOAT', 0.0, '', 0, 1, 'Translational lift gain on edgewise airspeed (research patch)'),
    ('SIH_PROP_R', 'FLOAT', 0.0, 'm', 0, 1, 'Propeller radius for ground effect, 0 = off (research patch)'),
    ('SIH_RD_K', 'FLOAT', 0.0, '', 0, 2, 'Rotor drag per rotor at full speed per m/s of in-plane airspeed (research patch)'),
    ('SIH_CDA', 'FLOAT', 0.0, 'm^2', 0, 1, 'Quadratic body drag area Cd A (research patch)'),
    ('SIH_BAT_CAP', 'FLOAT', 0.0, 'mAh', 0, 100000, 'Battery capacity, 0 = ideal supply (research patch)'),
    ('SIH_BAT_N', 'FLOAT', 4.0, '', 1, 14, 'Battery LiPo cells in series (research patch)'),
    ('SIH_BAT_R0', 'FLOAT', 0.05, 'Ohm', 0, 1, 'Battery pack internal resistance (research patch)'),
    ('SIH_BAT_SOC0', 'FLOAT', 1.0, '', 0, 1, 'Battery state of charge at start (research patch)'),
    ('SIH_BAT_ETA', 'FLOAT', 0.5, '', 0.05, 1, 'Electric to ideal induced power efficiency (research patch)'),
    ('SIH_COM_X', 'FLOAT', 0.0, 'm', -0.2, 0.2, 'Centre of mass offset forward of the rotor centre (research patch)'),
    ('SIH_COM_Y', 'FLOAT', 0.0, 'm', -0.2, 0.2, 'Centre of mass offset right of the rotor centre (research patch)'),
    ('SIH_VIB_ACC', 'FLOAT', 0.0, 'm/s^2', 0, 50, 'Accelerometer vibration per rotor at hover speed (research patch)'),
    ('SIH_VIB_GYR', 'FLOAT', 0.0, 'rad/s', 0, 5, 'Gyro vibration per rotor at hover speed (research patch)'),
    ('SIH_VIB_H2', 'FLOAT', 0.0, '', 0, 2, 'Second-harmonic share of the rotor vibration (research patch)'),
    ('SIH_W_MAX', 'FLOAT', 969.0, 'rad/s', 10, 10000, 'Rotor speed at full thrust, for vibration frequency (research patch)'),
    ('SIH_ACC_BX', 'FLOAT', 0.0, 'm/s^2', -2, 2, 'Accelerometer bias x (research patch)'),
    ('SIH_ACC_BY', 'FLOAT', 0.0, 'm/s^2', -2, 2, 'Accelerometer bias y (research patch)'),
    ('SIH_ACC_BZ', 'FLOAT', 0.0, 'm/s^2', -2, 2, 'Accelerometer bias z (research patch)'),
    ('SIH_GYR_BX', 'FLOAT', 0.0, 'rad/s', -0.5, 0.5, 'Gyro bias x (research patch)'),
    ('SIH_GYR_BY', 'FLOAT', 0.0, 'rad/s', -0.5, 0.5, 'Gyro bias y (research patch)'),
    ('SIH_GYR_BZ', 'FLOAT', 0.0, 'rad/s', -0.5, 0.5, 'Gyro bias z (research patch)'),
]
for n, t, dflt, unit, lo, hi, doc in P:
    assert len(n) <= 16, n
    if f'PARAM_DEFINE_{t}({n},' in p:  # the definition itself (a name can appear in another param's text)
        continue
    val = f'{int(dflt)}' if t == 'INT32' else f'{float(dflt)}f'
    p += f'''
/**
 * {doc}
 *
''' + (f' * @unit {unit}\n' if unit else '') + f''' * @min {lo}
 * @max {hi}
 * @group Simulation In Hardware
 */
PARAM_DEFINE_{t}({n}, {val});
'''
missing = [n for n, *_ in P if f'({n},' not in p]
assert not missing, f'params not defined: {missing}'
fp.write_text(p)
print('SIH fidelity patched')
