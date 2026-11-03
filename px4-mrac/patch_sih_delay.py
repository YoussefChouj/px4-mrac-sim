"""Patch the SIH motor input (in ~/PX4-mrac only) with a pure actuator delay, the SIH twin of patch_gz_delay.py.

SIH models the rotor lag (SIH_T_TAU) but no transport delay, while the real drone has 12.85-14.1 ms (PROGRESS M2).
The delay is the PX4 param SIH_ACT_DLY (ms, 0 = stock behaviour, re-read every second), so it is recorded in every
ULog. Each new actuator_outputs_sim sample goes into a ring buffer stamped with hrt (lockstep sim) time; the motor
model is fed the newest sample at least that old.
Usage: patch_sih_delay.py PX4_TREE. Idempotent.
"""
import sys
from pathlib import Path

d = Path(sys.argv[1]) / 'src/modules/simulation/simulator_sih'
f, fp = d / 'sih.cpp', d / 'sih_params.c'
s = f.read_text()
p = fp.read_text()
if 'SIH_MOT1_EFF' not in s:    # partial loss of motor 1 (asymmetric actuator fault), param SIH_MOT1_EFF
    old = '\t\t\t\tfloat u_sp = actuators_out.output[i];\n'
    assert old in s, 'SIH source changed'
    s = s.replace(old, '''\t\t\t\tfloat u_sp = actuators_out.output[i];

\t\t\t\tif (i == 0) { // partial loss of motor 1, param SIH_MOT1_EFF (1 = healthy), re-read every second
\t\t\t\t\tstatic const param_t eff_h = param_find("SIH_MOT1_EFF");
\t\t\t\t\tstatic float eff = 1.f;
\t\t\t\t\tstatic hrt_abstime eff_chk = 0;

\t\t\t\t\tif (eff_h != PARAM_INVALID && hrt_absolute_time() - eff_chk > 1000000) { param_get(eff_h, &eff); eff_chk = hrt_absolute_time(); }

\t\t\t\t\tu_sp *= eff;
\t\t\t\t}
''', 1)
    p += '''
/**
 * Thrust efficiency of motor 1 (research patch, 1 = healthy)
 *
 * @min 0
 * @max 1
 * @group Simulation In Hardware
 */
PARAM_DEFINE_FLOAT(SIH_MOT1_EFF, 1.0f);
'''
if 'SIH_ACT_DLY' in s:
    if '#include <parameters/param.h>' not in s:
        s = '#include <parameters/param.h>\n' + s
    f.write_text(s)
    fp.write_text(p)
    print('SIH actuator delay present; motor-1 efficiency patched')
    sys.exit(0)
old = '''	if (_actuator_out_sub.update(&actuators_out)) {
		_last_actuator_output_time = actuators_out.timestamp;
'''
assert old in s and 'float u_sp = actuators_out.output[i];' in s, 'SIH source changed'
new = '''	if (_actuator_out_sub.update(&actuators_out)) {
		_last_actuator_output_time = actuators_out.timestamp;

		// pure actuator delay, param SIH_ACT_DLY [ms] (0 = off), re-read every second
		static const param_t dly_h = param_find("SIH_ACT_DLY");
		static int32_t dly_ms = 0;
		static hrt_abstime dly_chk = 0;
		static constexpr unsigned N = 256;
		static actuator_outputs_s hist[N] {};
		static unsigned head = 0;
		const hrt_abstime now = hrt_absolute_time();

		if (dly_h != PARAM_INVALID && now - dly_chk > 1000000) { param_get(dly_h, &dly_ms); dly_chk = now; }

		head = (head + 1) % N;
		hist[head] = actuators_out;
		hist[head].timestamp = now;

		if (dly_ms > 0) {
			actuators_out = hist[(head + 1) % N]; // oldest kept sample if none is old enough yet

			for (unsigned k = 0; k < N; k++) {
				const unsigned j = (head + N - k) % N;

				if (hist[j].timestamp != 0 && now - hist[j].timestamp >= (hrt_abstime)dly_ms * 1000) { actuators_out = hist[j]; break; }
			}
		}
'''
s = s.replace(old, new, 1)
if '#include <parameters/param.h>' not in s:
    s = '#include <parameters/param.h>\n' + s
f.write_text(s)
if 'SIH_ACT_DLY' not in p:
    p += '''
/**
 * Pure actuator transport delay (research patch)
 *
 * @unit ms
 * @min 0
 * @max 200
 * @group Simulation In Hardware
 */
PARAM_DEFINE_INT32(SIH_ACT_DLY, 0);
'''
    fp.write_text(p)
print('SIH actuator delay patched')
