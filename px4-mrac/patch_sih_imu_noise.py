"""Add SIH_GYR_STD / SIH_ACC_STD to SIH: isotropic IMU noise std that replaces the stock hard-coded values.

Stock SIH flies with gyro noise 0.14/0.07/0.03 rad/s and accel 0.5/1.7/1.4 m/s^2 (sih.cpp), 3-15x noisier than the
research drone (research/REALISM.md: gyro 0.020-0.024 rad/s, accel ~0.1 m/s^2 flying). 0 = stock behaviour.
The params are re-read every second, so they are recorded in every ULog. Run after patch_sih_delay.py (param.h).
Usage: python3 patch_sih_imu_noise.py <PX4 tree>
"""
import pathlib
import sys

d = pathlib.Path(sys.argv[1]) / 'src/modules/simulation/simulator_sih'
f, fp = d / 'sih.cpp', d / 'sih_params.c'
s, p = f.read_text(), fp.read_text()
if 'SIH_GYR_STD' in s:
    sys.exit(print('patch_sih_imu_noise: already applied') or 0)
a = '\t\tgyro_noise = noiseGauss3f(0.01f, 0.01f, 0.01f);\n\t}\n'
if s.count(a) != 1 or '#include <parameters/param.h>' not in s:
    sys.exit('patch_sih_imu_noise: anchor or param.h include not found (run patch_sih_delay.py first)')
s = s.replace(a, a + '''
	{ // research-drone IMU noise, params SIH_GYR_STD [rad/s] / SIH_ACC_STD [m/s^2] (0 = stock), re-read every second
		static const param_t gyr_h = param_find("SIH_GYR_STD");
		static const param_t acc_h = param_find("SIH_ACC_STD");
		static float gyr_std = 0.f;
		static float acc_std = 0.f;
		static hrt_abstime last_read = 0;

		if (time_now_us - last_read > 1000000) {
			param_get(gyr_h, &gyr_std);
			param_get(acc_h, &acc_std);
			last_read = time_now_us;
		}

		if (gyr_std > 0.f) { gyro_noise = noiseGauss3f(gyr_std, gyr_std, gyr_std); }

		if (acc_std > 0.f) { accel_noise = noiseGauss3f(acc_std, acc_std, acc_std); }
	}
''')
p += '''
/**
 * Gyro noise std (research drone), replaces the stock values when > 0
 *
 * @unit rad/s
 * @min 0
 * @max 1
 * @decimal 3
 * @group Simulation In Hardware
 */
PARAM_DEFINE_FLOAT(SIH_GYR_STD, 0.0f);

/**
 * Accelerometer noise std (research drone), replaces the stock values when > 0
 *
 * @unit m/s^2
 * @min 0
 * @max 5
 * @decimal 3
 * @group Simulation In Hardware
 */
PARAM_DEFINE_FLOAT(SIH_ACC_STD, 0.0f);
'''
f.write_text(s)
fp.write_text(p)
print('patch_sih_imu_noise ok')
